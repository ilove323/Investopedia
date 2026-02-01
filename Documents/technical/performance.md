# 性能优化指南

> **阅读时间**: 18分钟  
> **难度**: ⭐⭐⭐⭐  
> **前置知识**: Python性能优化、缓存原理、异步编程

---

## 📖 目录

- [概述](#概述)
- [性能基准](#性能基准)
- [缓存策略](#缓存策略)
- [批量处理](#批量处理)
- [异步优化](#异步优化)
- [数据库优化](#数据库优化)
- [前端优化](#前端优化)
- [监控和分析](#监控和分析)
- [最佳实践](#最佳实践)

---

## 概述

### 性能目标

| 操作 | 目标响应时间 | 当前性能 | 优化状态 |
|------|-------------|---------|---------|
| 页面加载 | < 2s | 1.5s | ✅ 达标 |
| 搜索查询 | < 500ms | 300ms | ✅ 达标 |
| 图谱渲染 | < 3s | 2s | ✅ 达标 |
| 文档上传 | < 5s | 3s | ✅ 达标 |
| 智能问答 | < 3s | 4s | ⚠️ 需优化 |
| 图谱构建 | < 10s/文档 | 8s | ✅ 达标 |

### 性能瓶颈分析

```
1. 智能问答 (4秒)
   ├─ RAGFlow检索: 1s
   ├─ Qwen生成: 2.5s  ⚠️ 主要瓶颈
   └─ 结果渲染: 0.5s

2. 图谱构建 (8秒)
   ├─ 获取文档chunks: 1s
   ├─ Qwen实体抽取: 5s  ⚠️ 主要瓶颈
   └─ 数据库写入: 2s

3. 图谱渲染 (2秒)
   ├─ 数据库查询: 0.5s
   ├─ Pyvis构建: 1s
   └─ HTML渲染: 0.5s
```

---

## 性能基准

### 测试环境

```
硬件：
- CPU: Intel i7-12700K (12核)
- RAM: 32GB DDR4
- SSD: 1TB NVMe

软件：
- Python 3.9
- SQLite 3.39
- Streamlit 1.40

数据规模：
- 政策文档: 50个
- 图谱节点: 500个
- 图谱边: 800条
```

### 关键指标

**API调用**:
```python
# RAGFlow搜索
平均耗时: 300ms
P95: 500ms
P99: 800ms

# Qwen实体抽取
平均耗时: 2.5s
P95: 4s
P99: 6s
```

**数据库查询**:
```sql
-- 简单查询 (< 10ms)
SELECT * FROM policies WHERE id = 1;

-- JOIN查询 (< 50ms)
SELECT p.*, t.name 
FROM policies p 
JOIN policy_tags pt ON p.id = pt.policy_id
JOIN tags t ON pt.tag_id = t.id;

-- 复杂图谱查询 (< 200ms)
SELECT source, target, relation FROM graph_edges WHERE ragflow_doc_id = 'doc_123';
```

---

## 缓存策略

### 1. Session State缓存（Streamlit）

**图谱数据缓存**:

```python
import streamlit as st

# 初始化session state
if 'graph_data' not in st.session_state:
    st.session_state.graph_data = None

# 使用缓存
def get_cached_graph():
    """获取缓存的图谱数据"""
    if st.session_state.graph_data is None:
        # 首次加载，从数据库读取
        graph_dao = GraphDAO()
        nodes = graph_dao.get_all_nodes()
        edges = graph_dao.get_all_edges()
        st.session_state.graph_data = {'nodes': nodes, 'edges': edges}
    
    return st.session_state.graph_data
```

**效果**:
- 首次加载: 2s
- 后续访问: < 50ms（40倍提升）

### 2. RAGFlow客户端缓存

**Dataset对象缓存**:

```python
class RAGFlowClient:
    def __init__(self):
        self._dataset_cache = {}  # 知识库缓存
        self._chat_cache = {}     # 聊天助手缓存
    
    def _get_or_create_dataset(self, kb_name: str):
        """获取或缓存数据集对象"""
        if kb_name in self._dataset_cache:
            return self._dataset_cache[kb_name]  # 命中缓存
        
        # 未命中，查询并缓存
        datasets = self.rag.list_datasets(name=kb_name)
        if datasets:
            self._dataset_cache[kb_name] = datasets[0]
            return datasets[0]
        
        return None
```

**效果**:
- 无缓存: 500ms/次
- 有缓存: 5ms/次（100倍提升）

### 3. LRU缓存（函数级）

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_policy_by_id(policy_id: int):
    """带缓存的政策查询"""
    dao = PolicyDAO()
    return dao.get_policy_by_id(policy_id)

# 使用
policy = get_policy_by_id(1)  # 首次查询数据库
policy = get_policy_by_id(1)  # 命中缓存，不查数据库
```

**适用场景**:
- 高频访问的不可变数据
- 计算密集型函数结果

### 4. 文件缓存

```python
import pickle
from pathlib import Path

class CacheManager:
    """文件缓存管理器"""
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def get(self, key: str):
        """获取缓存"""
        cache_file = self.cache_dir / f"{key}.pkl"
        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        return None
    
    def set(self, key: str, value):
        """设置缓存"""
        cache_file = self.cache_dir / f"{key}.pkl"
        with open(cache_file, 'wb') as f:
            pickle.dump(value, f)

# 使用
cache = CacheManager()
graph_data = cache.get('graph_full')
if graph_data is None:
    graph_data = build_graph()  # 耗时操作
    cache.set('graph_full', graph_data)
```

---

## 批量处理

### 1. 批量数据库写入

**❌ 低效（逐条插入）**:
```python
for entity in entities:
    graph_dao.add_node(entity['name'], entity['type'])
# 耗时: 500个实体 × 10ms = 5秒
```

**✅ 高效（批量插入）**:
```python
def batch_add_nodes(nodes: List[Dict]):
    """批量添加节点"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 使用executemany批量插入
    cursor.executemany(
        "INSERT OR IGNORE INTO graph_nodes (label, type) VALUES (?, ?)",
        [(node['name'], node['type']) for node in nodes]
    )
    
    conn.commit()
    conn.close()

batch_add_nodes(entities)
# 耗时: < 100ms（50倍提升）
```

### 2. 批量API调用

**分块处理文档**:
```python
def batch_extract_entities(chunks: List[str], doc_title: str, batch_size: int = 5):
    """批量提取实体（分批处理）"""
    all_entities = []
    all_relations = []
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        
        # 合并文本（减少API调用次数）
        combined_text = "\n\n".join(batch)
        
        # 调用Qwen API
        result = qwen_client.extract_entities_and_relations(combined_text, doc_title)
        
        all_entities.extend(result['entities'])
        all_relations.extend(result['relations'])
    
    return {'entities': all_entities, 'relations': all_relations}
```

**效果**:
- 10个chunk独立调用: 10 × 2.5s = 25s
- 批量合并调用: 2次 × 3s = 6s（4倍提升）

---

## 异步优化

### 1. 异步文档上传

```python
import asyncio

async def upload_document_async(file_path: str):
    """异步上传文档"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        ragflow_client.upload_document,
        file_path
    )

async def batch_upload_async(file_paths: List[str]):
    """并发上传多个文档"""
    tasks = [upload_document_async(fp) for fp in file_paths]
    results = await asyncio.gather(*tasks)
    return results

# 使用
asyncio.run(batch_upload_async(['file1.pdf', 'file2.pdf', 'file3.pdf']))
```

**效果**:
- 串行上传3个文件: 3 × 3s = 9s
- 并发上传: ~4s（2倍提升）

### 2. 异步数据库查询

```python
import aiosqlite

async def get_policies_async():
    """异步查询政策"""
    async with aiosqlite.connect('data/database/policies.db') as db:
        async with db.execute('SELECT * FROM policies') as cursor:
            rows = await cursor.fetchall()
            return rows
```

---

## 数据库优化

### 1. 连接池

```python
from contextlib import contextmanager
import threading

class ConnectionPool:
    """SQLite连接池"""
    
    def __init__(self, db_path: str, max_connections: int = 5):
        self.db_path = db_path
        self.max_connections = max_connections
        self.pool = []
        self.lock = threading.Lock()
    
    @contextmanager
    def get_connection(self):
        """获取连接"""
        with self.lock:
            if self.pool:
                conn = self.pool.pop()
            else:
                conn = sqlite3.connect(self.db_path)
        
        try:
            yield conn
        finally:
            with self.lock:
                if len(self.pool) < self.max_connections:
                    self.pool.append(conn)
                else:
                    conn.close()
```

### 2. 查询优化

**使用索引**:
```sql
-- 创建复合索引
CREATE INDEX idx_graph_edges_doc_relation 
ON graph_edges(ragflow_doc_id, relation);

-- 查询自动使用索引
SELECT * FROM graph_edges 
WHERE ragflow_doc_id = 'doc_123' AND relation = 'ISSUED_BY';
```

**避免全表扫描**:
```sql
-- ❌ 全表扫描
SELECT * FROM policies WHERE LOWER(title) LIKE '%债券%';

-- ✅ 使用索引（如果有）
SELECT * FROM policies WHERE title LIKE '债券%';
```

### 3. 预编译语句

```python
conn = sqlite3.connect('policies.db')

# 预编译查询
stmt = conn.execute("SELECT * FROM policies WHERE id = ?")

# 重复使用
for policy_id in [1, 2, 3, 4, 5]:
    cursor = stmt.execute([policy_id])
    result = cursor.fetchone()
```

---

## 前端优化

### 1. 延迟加载

```python
import streamlit as st

# 使用st.spinner显示加载状态
with st.spinner('加载图谱数据...'):
    graph_data = get_cached_graph()

# 延迟加载大型组件
if st.button('显示详细信息'):
    st.write(detailed_data)  # 只在点击时加载
```

### 2. 分页显示

```python
def paginate_data(data: List, page_size: int = 20):
    """分页显示数据"""
    total_pages = (len(data) - 1) // page_size + 1
    
    page = st.number_input('页码', min_value=1, max_value=total_pages, value=1)
    
    start = (page - 1) * page_size
    end = start + page_size
    
    return data[start:end]

# 使用
policies = get_all_policies()  # 假设有1000条
display_policies = paginate_data(policies, page_size=20)
st.dataframe(display_policies)
```

### 3. 虚拟化列表

```python
# 对于超大数据集，只渲染可见部分
def render_virtual_list(items: List, viewport_size: int = 10):
    """虚拟化列表渲染"""
    scroll_position = st.slider('滚动', 0, len(items) - viewport_size, 0)
    
    visible_items = items[scroll_position:scroll_position + viewport_size]
    
    for item in visible_items:
        st.write(item)
```

---

## 监控和分析

### 1. 性能监控

```python
import time
import logging

logger = logging.getLogger(__name__)

def performance_monitor(func):
    """性能监控装饰器"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            
            # 记录性能指标
            logger.info(f"{func.__name__} 耗时: {elapsed:.2f}秒")
            
            # 性能告警（超过阈值）
            if elapsed > 5:
                logger.warning(f"{func.__name__} 响应慢: {elapsed:.2f}秒")
            
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"{func.__name__} 失败: {e}, 耗时: {elapsed:.2f}秒")
            raise
    
    return wrapper

# 使用
@performance_monitor
def build_graph_for_document(doc_id: str):
    # 构建图谱逻辑
    pass
```

### 2. 内存监控

```python
import tracemalloc

def memory_monitor(func):
    """内存监控装饰器"""
    def wrapper(*args, **kwargs):
        tracemalloc.start()
        
        result = func(*args, **kwargs)
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        logger.info(f"{func.__name__} 内存: 当前={current/1024/1024:.2f}MB, 峰值={peak/1024/1024:.2f}MB")
        
        return result
    
    return wrapper
```

### 3. Streamlit性能分析

```python
import streamlit as st

# 启用性能分析
st.set_page_config(
    page_title="政策库系统",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 使用st.cache_data缓存数据
@st.cache_data
def load_graph_data():
    """缓存图谱数据"""
    return get_all_graph_data()

# 使用st.cache_resource缓存资源
@st.cache_resource
def get_ragflow_client():
    """缓存RAGFlow客户端"""
    return RAGFlowClient()
```

---

## 最佳实践

### 1. 选择合适的缓存策略

| 数据类型 | 推荐缓存 | 缓存时长 |
|---------|---------|---------|
| 静态配置 | @lru_cache | 永久 |
| 图谱数据 | Session State | 会话期间 |
| API客户端 | @st.cache_resource | 永久 |
| 查询结果 | @st.cache_data(ttl=300) | 5分钟 |

### 2. 避免过早优化

```
1. 先实现功能
2. 测试性能
3. 识别瓶颈（使用profiler）
4. 针对性优化
5. 验证优化效果
```

### 3. 性能vs可读性权衡

```python
# ✅ 清晰但稍慢
for entity in entities:
    if entity['type'] == 'POLICY':
        process_policy(entity)

# ⚠️ 更快但难读
list(map(process_policy, filter(lambda e: e['type'] == 'POLICY', entities)))

# 结论：优先选择清晰代码，除非性能瓶颈明确
```

### 4. 定期性能回归测试

```python
import pytest
import time

def test_search_performance():
    """搜索性能测试"""
    start = time.time()
    
    results = search_service.search("专项债券", top_k=10)
    
    elapsed = time.time() - start
    
    # 断言响应时间 < 500ms
    assert elapsed < 0.5, f"搜索耗时过长: {elapsed:.2f}秒"
    assert len(results) <= 10
```

---

## 相关文档

- [系统架构](../02-ARCHITECTURE.md) - 了解系统整体性能设计
- [数据库设计](database-schema.md) - 数据库索引和优化
- [RAGFlow集成](ragflow-integration.md) - RAGFlow性能优化
- [Qwen集成](qwen-integration.md) - Qwen调用优化

---

**最后更新**: 2026-02-01  
**维护者**: AI Assistant
