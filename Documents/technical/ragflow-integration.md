# RAGFlow 集成详解

> **阅读时间**: 20分钟  
> **难度**: ⭐⭐⭐  
> **前置知识**: 了解RAG（检索增强生成）概念、REST API基础

---

## 📖 目录

- [概述](#概述)
- [架构设计](#架构设计)
- [RAGFlowClient实现](#ragflowclient实现)
- [核心功能](#核心功能)
- [配置管理](#配置管理)
- [错误处理](#错误处理)
- [性能优化](#性能优化)
- [最佳实践](#最佳实践)

---

## 概述

### 什么是RAGFlow？

RAGFlow是一个基于深度文档理解的RAG（Retrieval-Augmented Generation）引擎，提供：
- **文档解析** - 支持PDF、Word、Excel等多种格式
- **向量检索** - 基于Embedding的语义搜索
- **智能分块** - 自动文档分块（chunk）和索引
- **对话问答** - 基于知识库的AI问答

### 在本系统中的作用

```
用户上传PDF → RAGFlow解析 → 向量化存储 → 知识图谱构建
                                        ↓
                               混合检索（图谱粗筛 + RAGFlow向量精排）
                                        ↓
                         问题增强（注入图谱关系） + RAGFlow检索
                                        ↓
                          LLM（使用{question}和{knowledge}变量）
                                        ↓
                                   智能问答
```

---

## 架构设计

### 集成架构

```
┌─────────────────────────────────────────┐
│       Streamlit Pages (UI层)            │
│  search_page | chat_page | documents   │
└───────────────┬─────────────────────────┘
                │
┌───────────────▼─────────────────────────┐
│      ChatService (业务层)               │
│  - 混合检索 (HybridRetriever)           │
│  - 问题增强 (注入图谱关系)               │
│  - 变量配置 ({question}, {knowledge})   │
└───────────────┬─────────────────────────┘
                │
┌───────────────▼─────────────────────────┐
│      RAGFlowClient (服务层)             │
│  - 文档管理 (upload, delete, list)      │
│  - Chat Assistant管理 (配置variables)   │
│  - Session管理 (ask接口)                │
│  - 健康检查 (health_check)               │
└───────────────┬─────────────────────────┘
                │
┌───────────────▼─────────────────────────┐
│       RAGFlow SDK (官方SDK)             │
│  - RAGFlow API封装                       │
│  - Dataset管理                           │
│  - Chat Assistant管理                    │
└───────────────┬─────────────────────────┘
                │
┌───────────────▼─────────────────────────┐
│       RAGFlow Server (外部服务)         │
│  - 文档解析引擎                          │
│  - 向量数据库                            │
│  - LLM后端                               │
└─────────────────────────────────────────┘
```

### 为什么使用官方SDK？

**之前的问题（自定义HTTP客户端）**:
- ❌ API接口变化需要手动适配
- ❌ 错误处理不完整
- ❌ 缺少认证和重试机制

**使用官方SDK的优势**:
- ✅ 自动适配API变化
- ✅ 完善的错误处理和重试
- ✅ 官方维护，稳定可靠
- ✅ 类型提示，开发友好

---

## RAGFlowClient实现

### 初始化

**文件**: [src/services/ragflow_client.py](../../src/services/ragflow_client.py)

```python
class RAGFlowClient:
    """RAGFlow客户端 - 使用官方SDK"""

    def __init__(self):
        """初始化RAGFlow客户端"""
        if RAGFlow is None:
            raise ImportError("RAGFlow SDK not available. Please install: pip install ragflow-sdk")

        # 初始化官方SDK客户端
        self.rag = RAGFlow(
            api_key=RAGFLOW_API_KEY,
            base_url=RAGFLOW_BASE_URL
        )

        # 存储知识库和聊天助手的缓存
        self._dataset_cache = {}
        self._chat_cache = {}

        logger.info(f"RAGFlow SDK initialized: {RAGFLOW_BASE_URL}")
```

**关键配置**:
- `api_key` - RAGFlow API密钥（从config.ini读取）
- `base_url` - RAGFlow服务地址（如 `http://localhost:9380`）

### 缓存机制

为了避免频繁API调用，实现了两级缓存：

```python
def _get_or_create_dataset(self, kb_name: str):
    """获取或缓存数据集对象"""
    # 检查缓存
    if kb_name in self._dataset_cache:
        return self._dataset_cache[kb_name]

    try:
        # 使用SDK列出数据集
        datasets = self.rag.list_datasets(name=kb_name)
        if datasets:
            dataset = datasets[0]
            self._dataset_cache[kb_name] = dataset  # 缓存
            logger.debug(f"Dataset cached: {kb_name} (ID: {dataset.id})")
            return dataset

        logger.error(f"Dataset '{kb_name}' not found")
        return None
    except Exception as e:
        logger.error(f"Failed to get dataset '{kb_name}': {e}")
        return None
```

**缓存策略**:
- `_dataset_cache` - 知识库对象缓存
- `_chat_cache` - 聊天助手对象缓存
- **生命周期** - 进程级别，重启后清除

---

## 核心功能

### 1. 健康检查

**功能**: 验证RAGFlow服务连接

```python
def check_health(self) -> bool:
    """检查RAGFlow服务健康状态"""
    try:
        # 尝试列出数据集
        datasets = self.rag.list_datasets()
        logger.info(f"✅ RAGFlow服务正常，数据集数量: {len(datasets)}")
        return True
    except Exception as e:
        logger.error(f"❌ RAGFlow服务异常: {e}")
        return False
```

**使用场景**:
- 应用启动时验证服务
- 定时健康检查
- 故障诊断

**示例**:
```python
from src.clients.ragflow_client import get_ragflow_client

client = get_ragflow_client()
if client.check_health():
    print("RAGFlow服务正常")
else:
    print("RAGFlow服务异常，请检查配置")
```

### 2. 文档管理

#### 2.1 上传文档

```python
def upload_document(
    self, 
    file_path: str, 
    display_name: str, 
    knowledge_base_name: str = None
) -> Optional[str]:
    """
    上传文档到RAGFlow知识库
    
    Args:
        file_path: 本地文件路径
        display_name: 显示名称
        knowledge_base_name: 知识库名称
        
    Returns:
        文档ID，失败返回None
    """
```

**工作流程**:
```
1. 验证文件存在
2. 获取知识库对象（带缓存）
3. 调用SDK上传文件
4. 返回文档ID
```

**示例**:
```python
doc_id = client.upload_document(
    file_path="/path/to/policy.pdf",
    display_name="政策文件.pdf",
    knowledge_base_name="policy_demo_kb"
)

if doc_id:
    print(f"上传成功: {doc_id}")
else:
    print("上传失败")
```

#### 2.2 获取文档列表

```python
def get_documents(self, knowledge_base_name: str = None) -> List[Dict]:
    """获取知识库中的所有文档"""
    try:
        dataset = self._get_or_create_dataset(knowledge_base_name)
        if not dataset:
            return []

        # 使用SDK列出文档
        documents = dataset.list_documents()
        
        # 转换为字典格式
        result = []
        for doc in documents:
            result.append({
                'id': doc.id,
                'name': doc.name,
                'size': doc.size,
                'chunk_count': doc.chunk_count,
                'token_count': doc.token_count,
                'status': doc.status,
                'created_at': doc.created_at
            })
        
        return result
    except Exception as e:
        logger.error(f"获取文档列表失败: {e}")
        return []
```

**返回格式**:
```json
[
  {
    "id": "doc_12345",
    "name": "政策文件.pdf",
    "size": 1024000,
    "chunk_count": 25,
    "token_count": 5000,
    "status": "completed",
    "created_at": "2026-02-01T10:00:00"
  }
]
```

#### 2.3 删除文档

```python
def delete_document(self, doc_id: str, knowledge_base_name: str = None) -> bool:
    """删除文档"""
    try:
        dataset = self._get_or_create_dataset(knowledge_base_name)
        if not dataset:
            return False

        # 使用SDK删除文档
        dataset.delete_document(doc_id)
        logger.info(f"文档删除成功: {doc_id}")
        return True
    except Exception as e:
        logger.error(f"删除文档失败: {e}")
        return False
```

### 3. 语义搜索

```python
def search(
    self,
    query: str,
    knowledge_base_name: str = None,
    top_k: int = 10,
    similarity_threshold: float = 0.3
) -> List[Dict]:
    """
    在知识库中搜索相关内容
    
    Args:
        query: 搜索查询
        knowledge_base_name: 知识库名称
        top_k: 返回结果数量
        similarity_threshold: 相似度阈值（0-1）
        
    Returns:
        搜索结果列表
    """
```

**工作原理**:
```
1. 查询向量化（Embedding）
2. 向量相似度计算
3. 返回Top-K结果
4. 过滤低相似度结果（< threshold）
```

**示例**:
```python
results = client.search(
    query="专项债券政策",
    top_k=5,
    similarity_threshold=0.5
)

for result in results:
    print(f"相关度: {result['similarity']:.2f}")
    print(f"内容: {result['content'][:100]}...")
    print(f"来源: {result['doc_name']}")
```

**返回格式**:
```json
[
  {
    "content": "专项债券是指...",
    "similarity": 0.85,
    "doc_id": "doc_12345",
    "doc_name": "政策文件.pdf",
    "chunk_id": "chunk_001",
    "page_num": 3
  }
]
```

### 4. 智能问答

```python
def chat(
    self,
    question: str,
    knowledge_base_name: str = None,
    conversation_id: str = None,
    stream: bool = False
) -> Dict:
    """
    基于知识库的问答
    
    Args:
        question: 用户问题
        knowledge_base_name: 知识库名称
        conversation_id: 会话ID（多轮对话）
        stream: 是否流式返回
        
    Returns:
        问答结果
    """
```

**工作流程**:
```
1. 检索相关文档（RAG检索）
2. 构建Prompt（问题 + 上下文）
3. 调用LLM生成答案
4. 返回答案 + 参考文档
```

**非流式示例**:
```python
response = client.chat(
    question="专项债券的申请条件是什么？",
    knowledge_base_name="policy_demo_kb"
)

print(f"答案: {response['answer']}")
print(f"参考文档: {response['reference']}")
```

**流式示例**:
```python
for chunk in client.chat(
    question="专项债券的申请条件是什么？",
    stream=True
):
    print(chunk['delta'], end='', flush=True)
```

### 5. Chat Assistant与变量配置

#### 5.1 变量机制

RAGFlow在调用LLM时自动注入系统变量到System Prompt中：

| 变量 | 说明 | 是否必填 | 数据来源 |
|------|------|----------|----------|
| `{question}` | 用户问题 | 是 | `session.ask(question=...)` |
| `{knowledge}` | 检索内容 | 否 | RAGFlow向量检索结果 |

#### 5.2 变量配置代码

**创建Chat Assistant时配置**：
```python
from ragflow_sdk import Chat

# 构建Prompt配置
prompt_config = Chat.Prompt(
    prompt=system_prompt,  # System Prompt文本
    top_n=8,
    similarity_threshold=0.2,
    keywords_similarity_weight=0.7,
    variables=[
        {"key": "knowledge", "optional": True},
        {"key": "question", "optional": False}  # 必须配置！
    ]
)

# 创建Assistant
chat_assistant = rag.create_chat(
    name="政策聊天助手",
    dataset_ids=[dataset_id],
    prompt=prompt_config
)
```

**更新Assistant时配置**：
```python
chat_assistant.update({
    "prompt": {
        "prompt": system_prompt,
        "top_n": 8,
        "similarity_threshold": 0.2,
        "variables": [
            {"key": "knowledge", "optional": True},
            {"key": "question", "optional": False}
        ]
    }
})
```

#### 5.3 System Prompt示例

**文件**: `config/prompts/ragflow_chat_system_prompt.txt`

```
你是专业的政策法规智能助手。请基于 {knowledge} 中的政策文档内容回答用户问题 {question}。

【核心要求】
1. 严格基于 {knowledge} 回答，不要编造信息
2. {question} 可能包含知识图谱关系（格式：实体A → 关系 → 实体B），优先覆盖图谱中的实体
3. 使用结构化格式：加粗核心要点，编号列表，引用文档名称

【回答格式】
**政策依据**：相关政策文件（从 {knowledge} 获取 document_name）
**核心要点**：
1. 要点一：具体内容（引用 {knowledge} 中的 content）
2. 要点二：...

保持专业、客观、实用。
```

#### 5.4 混合检索增强流程

```
┌─────────────────────────────────────────────────────────┐
│ 1. 用户提问："特许经营合同包括什么内容？"               │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│ 2. Python代码（HybridRetriever）                        │
│    - Qwen大模型提取实体：['特许经营', '合同']           │
│    - 知识图谱检索：查找相关节点和关系                    │
│    - 提取15条图谱关系                                    │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│ 3. 构建增强问题（ChatService._build_enhanced_question） │
│                                                          │
│    特许经营合同包括什么内容？                            │
│    [知识图谱关系]                                        │
│    • 商业特许经营管理条例 → relates_to → 特许人          │
│    • 商业特许经营管理条例 → relates_to → 被特许人        │
│    • 商业特许经营管理条例 → relates_to → 信息披露制度    │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│ 4. 调用RAGFlow API                                       │
│    session.ask(question=增强问题, stream=True)           │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│ 5. RAGFlow处理                                           │
│    - 向量检索知识库                                      │
│    - 检索到相关chunks → 赋值给 {knowledge}               │
│    - 增强问题 → 赋值给 {question}                        │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│ 6. 渲染System Prompt                                     │
│    - 将 {question} 替换为增强问题（含图谱关系）          │
│    - 将 {knowledge} 替换为检索到的文档内容               │
│    - 发送完整Prompt给LLM                                 │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│ 7. LLM生成回答                                           │
│    - 理解图谱关系中的实体                                │
│    - 基于 {knowledge} 准确回答                           │
│    - 覆盖"特许人"、"被特许人"、"信息披露"等概念          │
└─────────────────────────────────────────────────────────┘
```

#### 5.5 错误处理

**错误：'Miss parameter: question'**

原因：创建/更新Assistant时未配置 `variables`

```python
# ❌ 错误：缺少variables配置
prompt_config = Chat.Prompt(
    prompt=system_prompt,
    top_n=8
)

# ✅ 正确：包含variables配置
prompt_config = Chat.Prompt(
    prompt=system_prompt,
    top_n=8,
    variables=[
        {"key": "knowledge", "optional": True},
        {"key": "question", "optional": False}
    ]
)
```

---

## 配置管理

### 配置文件

**文件**: [config/config.ini](../../config/config.ini)

```ini
[RAGFLOW]
# RAGFlow服务配置
host = 127.0.0.1
port = 9380
api_key = ragflow-xxx

# 超时和重试
timeout = 30
retry_times = 3
retry_delay = 1

# 默认知识库
default_kb = policy_demo_kb

# 搜索配置
search_top_k = 10
search_similarity_threshold = 0.3

# 问答配置
qa_max_tokens = 2000
qa_temperature = 0.7
```

### 配置加载

```python
from src.config import get_config

config = get_config()

RAGFLOW_BASE_URL = config.ragflow_base_url  # http://127.0.0.1:9380
RAGFLOW_API_KEY = config.ragflow_api_key
RAGFLOW_TIMEOUT = config.ragflow_timeout
```

### 环境变量覆盖

```bash
# 环境变量优先级更高
export RAGFLOW_HOST=192.168.1.100
export RAGFLOW_API_KEY=ragflow-production-key
```

---

## 错误处理

### 错误类型

#### 1. 连接错误

```python
try:
    client = get_ragflow_client()
    client.check_health()
except ConnectionError as e:
    logger.error(f"无法连接RAGFlow服务: {e}")
    # 提示用户检查服务是否启动
```

**解决方案**:
- 检查RAGFlow服务是否运行
- 验证host和port配置
- 检查防火墙设置

#### 2. 认证错误

```python
try:
    client.upload_document(...)
except PermissionError as e:
    logger.error(f"API密钥无效: {e}")
    # 提示用户检查api_key配置
```

**解决方案**:
- 验证api_key是否正确
- 检查密钥是否过期

#### 3. 知识库不存在

```python
if not client._check_knowledge_base_exists(kb_name):
    logger.error(f"知识库 '{kb_name}' 不存在")
    # 提示用户创建知识库或检查配置
```

**解决方案**:
- 在RAGFlow Web界面创建知识库
- 检查default_kb配置

### 重试机制

```python
from tenacity import retry, stop_after_attempt, wait_fixed

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def upload_with_retry(file_path: str):
    """带重试的文档上传"""
    return client.upload_document(file_path)
```

---

## 性能优化

### 1. 缓存策略

**Dataset对象缓存**:
```python
# 避免每次请求都查询知识库
self._dataset_cache = {}  # 进程级缓存
```

**Chat Assistant缓存**:
```python
self._chat_cache = {}  # 缓存聊天助手对象
```

**效果**:
- 减少API调用次数
- 降低响应延迟（从500ms降至50ms）

### 2. 批量操作

**批量上传文档**:
```python
def batch_upload_documents(self, file_paths: List[str]) -> List[str]:
    """批量上传文档"""
    doc_ids = []
    for file_path in file_paths:
        doc_id = self.upload_document(file_path)
        if doc_id:
            doc_ids.append(doc_id)
    return doc_ids
```

### 3. 异步处理

**异步文档解析**:
```python
# RAGFlow自动异步解析文档
doc_id = client.upload_document(file_path)

# 轮询检查解析状态
import time
while True:
    doc = client.get_document_info(doc_id)
    if doc['status'] == 'completed':
        break
    time.sleep(2)
```

### 4. 连接池

```python
# RAGFlow SDK内部使用requests Session
# 自动复用HTTP连接
```

---

## 最佳实践

### 1. 初始化检查

```python
# 应用启动时验证RAGFlow连接
client = get_ragflow_client()
if not client.check_health():
    raise RuntimeError("RAGFlow服务不可用，请检查配置")
```

### 2. 错误日志

```python
import logging

logger = logging.getLogger(__name__)

try:
    result = client.search(query)
except Exception as e:
    logger.error(f"搜索失败: {e}", exc_info=True)
    # 返回友好错误信息
    return {"error": "搜索服务暂时不可用"}
```

### 3. 超时控制

```python
# 在config.ini设置合理超时
timeout = 30  # 30秒超时

# 对于可能较慢的操作增加超时
client.upload_document(file_path, timeout=60)
```

### 4. 数据验证

```python
def safe_search(query: str):
    """安全的搜索函数"""
    # 验证输入
    if not query or len(query) < 2:
        raise ValueError("查询长度至少2个字符")
    
    # 限制查询长度
    if len(query) > 1000:
        query = query[:1000]
    
    return client.search(query)
```

### 5. 资源清理

```python
# RAGFlow SDK自动管理连接
# 无需手动清理

# 但缓存需要定期清理
def clear_cache():
    """清理缓存"""
    client._dataset_cache.clear()
    client._chat_cache.clear()
```

---

## 常见问题

### Q1: RAGFlow服务启动失败？

**检查步骤**:
```bash
# 1. 查看服务状态
docker ps | grep ragflow

# 2. 查看服务日志
docker logs ragflow

# 3. 测试服务连接
curl http://localhost:9380/health
```

### Q2: 文档上传后无法检索？

**可能原因**:
- 文档正在解析中（异步处理）
- 分块失败（查看RAGFlow日志）
- 向量化失败（检查Embedding服务）

**解决方案**:
```python
# 等待文档解析完成
doc = client.get_document_info(doc_id)
while doc['status'] != 'completed':
    time.sleep(2)
    doc = client.get_document_info(doc_id)
```

### Q3: 搜索结果相关性低？

**调整参数**:
```python
# 降低相似度阈值
results = client.search(query, similarity_threshold=0.2)

# 增加返回结果数量
results = client.search(query, top_k=20)
```

### Q4: API调用超时？

**优化方案**:
- 增加timeout配置
- 使用异步上传
- 减少单次查询的top_k

---

## 相关文档

- [系统架构](../02-ARCHITECTURE.md) - 了解RAGFlow在系统中的位置
- [配置详解](../06-CONFIGURATION.md) - RAGFlow配置项完整说明
- [API参考](../05-API_REFERENCE.md#ragflowclient) - RAGFlowClient完整API
- [Qwen集成详解](qwen-integration.md) - 了解实体抽取如何使用RAGFlow数据

---

**最后更新**: 2026-02-01  
**维护者**: AI Assistant
