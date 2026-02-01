# 📚 API 参考文档

> 所有服务、DAO、业务逻辑类的详细API文档  
> 阅读时间: 45分钟

---

## 📋 目录

- [服务层API](#服务层api)
- [数据访问层API](#数据访问层api)
- [业务逻辑层API](#业务逻辑层api)
- [模型类API](#模型类api)
- [工具函数API](#工具函数api)

---

## 🔌 服务层API

### RAGFlowClient

**模块**: `src/services/ragflow_client.py`

#### 初始化
```python
from src.clients.ragflow_client import get_ragflow_client

client = get_ragflow_client()
```

#### check_health()
```python
def check_health() -> Dict
```

检查RAGFlow服务健康状态。

**返回值**:
```python
{
    "status": "healthy",  # or "unhealthy"
    "version": "0.13.0",
    "timestamp": "2026-02-01T10:30:00Z"
}
```

**示例**:
```python
health = client.check_health()
if health['status'] == 'healthy':
    print("RAGFlow服务正常")
```

---

#### get_documents()
```python
def get_documents(kb_name: str) -> List[Dict]
```

获取指定知识库的所有文档列表。

**参数**:
- `kb_name` (str): 知识库名称

**返回值**:
```python
[
    {
        "id": "doc_123",
        "name": "政策文档.pdf",
        "size": 1024000,  # 字节
        "chunk_count": 45,
        "token_count": 12345,
        "created_at": "2024-01-15T10:30:00Z",
        "status": "completed"
    },
    ...
]
```

**异常**:
- `ConnectionError`: 无法连接到RAGFlow
- `ValueError`: 知识库不存在

**示例**:
```python
docs = client.get_documents("policy_demo_kb")
for doc in docs:
    print(f"{doc['name']}: {doc['chunk_count']} chunks")
```

---

#### get_document_content()
```python
def get_document_content(doc_id: str, kb_name: str) -> str
```

获取文档的完整内容（所有chunks拼接）。

**参数**:
- `doc_id` (str): 文档ID
- `kb_name` (str): 知识库名称

**返回值**:
- `str`: 文档完整文本内容

**异常**:
- `DocumentNotFoundError`: 文档不存在
- `ConnectionError`: 网络错误

**示例**:
```python
content = client.get_document_content("doc_123", "policy_demo_kb")
print(f"文档长度: {len(content)} 字符")
```

---

#### retrieve()
```python
def retrieve(question: str, kb_name: str, 
            top_k: int = 5, 
            similarity_threshold: float = 0.3) -> List[Dict]
```

向量检索相关文档。

**参数**:
- `question` (str): 查询问题
- `kb_name` (str): 知识库名称
- `top_k` (int, 可选): 返回Top-K个文档，默认5
- `similarity_threshold` (float, 可选): 相似度阈值，默认0.3

**返回值**:
```python
[
    {
        "doc_id": "doc_123",
        "doc_name": "政策文档.pdf",
        "chunk_id": "chunk_45",
        "content": "相关内容片段...",
        "similarity": 0.92,
        "metadata": {...}
    },
    ...
]
```

**示例**:
```python
results = client.retrieve(
    "高新技术企业税收优惠",
    "policy_demo_kb",
    top_k=10,
    similarity_threshold=0.5
)

for r in results:
    print(f"{r['doc_name']} (相似度: {r['similarity']:.2f})")
    print(r['content'][:100])
```

---

#### list_datasets()
```python
def list_datasets() -> List[str]
```

列出所有可用的知识库。

**返回值**:
- `List[str]`: 知识库名称列表

**示例**:
```python
kbs = client.list_datasets()
print(f"可用知识库: {', '.join(kbs)}")
```

---

### QwenClient

**模块**: `src/services/qwen_client.py`

#### 初始化
```python
from src.clients.qwen_client import get_qwen_client

client = get_qwen_client()
```

#### extract_entities_and_relations()
```python
def extract_entities_and_relations(text: str, 
                                   doc_title: str = "") -> Dict
```

从文本中抽取实体和关系。

**参数**:
- `text` (str): 待抽取的文本内容
- `doc_title` (str, 可选): 文档标题（作为上下文）

**返回值**:
```python
{
    "entities": [
        {
            "text": "广东省科技厅",
            "type": "AUTHORITY",
            "description": "政策发布机构"
        },
        {
            "text": "高新技术企业",
            "type": "CONCEPT",
            "description": "政策适用对象"
        }
    ],
    "relations": [
        {
            "source": "广东省科技厅",
            "target": "科技创新政策",
            "type": "ISSUED_BY"
        },
        {
            "source": "科技创新政策",
            "target": "高新技术企业",
            "type": "APPLIES_TO"
        }
    ]
}
```

**实体类型**:
- `POLICY`: 政策文档
- `AUTHORITY`: 发布机构
- `REGION`: 地区
- `CONCEPT`: 概念/领域
- `PROJECT`: 项目/计划

**关系类型**:
- `ISSUED_BY`: 发布关系
- `APPLIES_TO`: 适用关系
- `REFERENCES`: 引用关系
- `AFFECTS`: 影响关系
- `BELONGS_TO`: 从属关系

**异常**:
- `APIError`: API调用失败
- `InvalidResponseError`: 返回格式错误

**示例**:
```python
text = """
广东省科技厅发布《科技创新政策》，适用于高新技术企业。
企业研发费用可享受加计扣除优惠。
"""

result = client.extract_entities_and_relations(text, "科技创新政策")

print(f"提取实体数: {len(result['entities'])}")
print(f"提取关系数: {len(result['relations'])}")

for entity in result['entities']:
    print(f"- {entity['text']} ({entity['type']})")
```

**性能**:
- 单次调用耗时: 3-5秒
- Token消耗: ~1500-3000 (根据文档长度)
- 成本: ~￥0.01-0.02/文档 (qwen-plus)

---

### ChatService

**模块**: `src/services/chat_service.py`

#### 初始化
```python
from src.services.chat_service import get_chat_service

service = get_chat_service()
```

#### chat()
```python
def chat(question: str, 
        session_id: str = None,
        stream: bool = False) -> Dict
```

发送问题到Chat Assistant并获取答案。

**参数**:
- `question` (str): 用户问题
- `session_id` (str, 可选): 会话ID，None则创建新会话
- `stream` (bool, 可选): 是否流式输出，默认False

**返回值（非流式）**:
```python
{
    "answer": "完整答案文本...",
    "references": [
        {
            "doc_id": "doc_123",
            "doc_name": "政策文档.pdf",
            "chunk_id": "chunk_45",
            "similarity": 0.92
        }
    ],
    "session_id": "session_abc123"
}
```

**返回值（流式）**:
```python
# 生成器，逐块返回
for chunk in service.chat("问题", stream=True):
    print(chunk['delta'])  # 增量文本
    # 最后一个chunk包含完整answer和references
```

**示例（非流式）**:
```python
response = service.chat("高新技术企业有哪些税收优惠？")
print(response['answer'])
for ref in response['references']:
    print(f"参考: {ref['doc_name']}")
```

**示例（流式）**:
```python
import streamlit as st

message_placeholder = st.empty()
full_response = ""

for chunk in service.chat("问题", stream=True):
    if 'delta' in chunk:
        full_response += chunk['delta']
        message_placeholder.write(full_response)
    elif 'answer' in chunk:
        # 最后一个chunk
        full_response = chunk['answer']
        references = chunk['references']
```

---

#### create_session()
```python
def create_session(kb_name: str = None) -> str
```

创建新的对话会话。

**参数**:
- `kb_name` (str, 可选): 指定知识库，None则使用默认

**返回值**:
- `str`: 会话ID

**示例**:
```python
session_id = service.create_session("policy_demo_kb")
response = service.chat("问题1", session_id=session_id)
response = service.chat("问题2", session_id=session_id)  # 记住上下文
```

---

#### list_sessions()
```python
def list_sessions() -> List[Dict]
```

列出所有会话。

**返回值**:
```python
[
    {
        "session_id": "session_abc123",
        "created_at": "2026-02-01T10:00:00Z",
        "message_count": 10,
        "last_message_at": "2026-02-01T10:30:00Z"
    },
    ...
]
```

---

### DataSyncService

**模块**: `src/services/data_sync.py`

#### 初始化
```python
from src.services.data_sync import DataSyncService

service = DataSyncService()
```

#### sync_documents_to_database()
```python
def sync_documents_to_database(kb_name: str) -> Dict
```

从RAGFlow同步文档元数据到本地SQLite。

**参数**:
- `kb_name` (str): 知识库名称

**返回值**:
```python
{
    "synced_count": 10,    # 新增/更新文档数
    "skipped_count": 5,    # 跳过（已存在且未修改）
    "total_count": 15,     # 总文档数
    "elapsed_time": 3.2    # 耗时（秒）
}
```

**示例**:
```python
result = service.sync_documents_to_database("policy_demo_kb")
print(f"同步了 {result['synced_count']} 个文档")
```

---

#### build_knowledge_graph()
```python
def build_knowledge_graph(kb_name: str, 
                         is_incremental: bool = False) -> Dict
```

构建知识图谱（**核心方法**）。

**参数**:
- `kb_name` (str): 知识库名称
- `is_incremental` (bool, 可选): 是否增量构建，默认False（全量）

**返回值**:
```python
{
    "node_count": 40,
    "edge_count": 73,
    "document_count": 12,
    "elapsed_time": 145.6,  # 秒
    "errors": []  # 错误列表（如果有）
}
```

**流程**:
1. 获取RAGFlow文档列表
2. 遍历每个文档：
   - 获取文档内容
   - 调用Qwen抽取实体和关系
   - 构建GraphNode和GraphEdge
3. 去重（文档名、节点ID）
4. 保存到SQLite

**性能**:
- 全量构建: ~3-5分钟 (40文档)
- 增量构建: <1分钟 (5个新文档)

**示例**:
```python
# 全量构建
result = service.build_knowledge_graph("policy_demo_kb", is_incremental=False)
print(f"构建完成: {result['node_count']}节点, {result['edge_count']}边")

# 增量构建（只处理新文档）
result = service.build_knowledge_graph("policy_demo_kb", is_incremental=True)
```

---

#### get_sync_status()
```python
def get_sync_status() -> Dict
```

获取当前同步状态。

**返回值**:
```python
{
    "is_syncing": False,
    "last_sync_time": "2026-02-01T10:00:00Z",
    "current_progress": 0.0,  # 0.0-1.0
    "current_document": ""
}
```

---

### WhisperClient

**模块**: `src/services/whisper_client.py`

#### transcribe()
```python
def transcribe(audio_file: Union[str, BinaryIO]) -> str
```

转录音频文件为文本。

**参数**:
- `audio_file`: 文件路径（str）或文件对象

**返回值**:
- `str`: 转录文本

**支持格式**: WAV, MP3, M4A, FLAC, OGG

**文件大小限制**: 25MB

**示例**:
```python
from src.services.whisper_client import get_whisper_client

client = get_whisper_client()

# 方式1: 文件路径
text = client.transcribe("audio/recording.mp3")

# 方式2: 文件对象
with open("audio/recording.mp3", "rb") as f:
    text = client.transcribe(f)

print(f"转录结果: {text}")
```

---

## 🗄️ 数据访问层API

### PolicyDAO

**模块**: `src/database/policy_dao.py`

#### 初始化
```python
from src.database.policy_dao import get_policy_dao

dao = get_policy_dao()
```

#### create_policy()
```python
def create_policy(metadata: Dict) -> int
```

创建新政策记录。

**参数**:
```python
metadata = {
    "ragflow_id": "doc_123",
    "title": "科技创新政策",
    "policy_type": "科技政策",
    "region": "广东",
    "issuing_authority": "广东省科技厅",
    "document_number": "粤科〔2024〕1号",
    "effective_date": "2024-01-01",
    "expiry_date": "2025-12-31",
    "status": "有效",
    "content": "政策全文...",
    "summary": "政策摘要..."
    # ...更多字段见schema.sql
}
```

**返回值**:
- `int`: 新创建政策的ID

**示例**:
```python
policy_id = dao.create_policy({
    "ragflow_id": "doc_new",
    "title": "新政策",
    "policy_type": "财税政策",
    # ...
})
print(f"创建成功，ID: {policy_id}")
```

---

#### get_policy_by_ragflow_id()
```python
def get_policy_by_ragflow_id(doc_id: str) -> Optional[Policy]
```

根据RAGFlow文档ID查询政策。

**参数**:
- `doc_id` (str): RAGFlow文档ID

**返回值**:
- `Policy`: Policy对象，不存在返回None

**示例**:
```python
policy = dao.get_policy_by_ragflow_id("doc_123")
if policy:
    print(f"政策标题: {policy.title}")
else:
    print("政策不存在")
```

---

#### get_policies()
```python
def get_policies(filters: Dict = None, 
                limit: int = 100,
                offset: int = 0) -> List[Policy]
```

查询政策列表（支持筛选和分页）。

**参数**:
```python
filters = {
    "policy_type": "科技政策",  # 可选
    "region": "广东",          # 可选
    "status": "有效",           # 可选
    "start_date": "2024-01-01", # 可选
    "end_date": "2024-12-31",   # 可选
    "keyword": "高新技术"       # 可选（搜索标题和内容）
}
```

**返回值**:
- `List[Policy]`: Policy对象列表

**示例**:
```python
# 查询广东省的科技政策
policies = dao.get_policies(filters={
    "policy_type": "科技政策",
    "region": "广东",
    "status": "有效"
}, limit=20)

for p in policies:
    print(f"{p.title} ({p.effective_date})")

# 分页查询
page1 = dao.get_policies(limit=10, offset=0)
page2 = dao.get_policies(limit=10, offset=10)
```

---

#### update_policy()
```python
def update_policy(policy_id: int, metadata: Dict)
```

更新政策记录。

**参数**:
- `policy_id` (int): 政策ID
- `metadata` (Dict): 要更新的字段

**示例**:
```python
dao.update_policy(policy_id=123, metadata={
    "status": "已废止",
    "expiry_date": "2024-06-30"
})
```

---

#### get_stats()
```python
def get_stats() -> Dict
```

获取政策统计信息。

**返回值**:
```python
{
    "total_count": 100,
    "by_type": {
        "科技政策": 30,
        "财税政策": 25,
        "产业政策": 20,
        # ...
    },
    "by_region": {
        "广东": 40,
        "北京": 30,
        # ...
    },
    "by_status": {
        "有效": 80,
        "过期": 15,
        "即将过期": 5
    }
}
```

---

### GraphDAO

**模块**: `src/database/graph_dao.py`

#### save_graph()
```python
def save_graph(graph_data: Dict, is_incremental: bool = False)
```

保存知识图谱到数据库。

**参数**:
```python
graph_data = {
    "nodes": [
        {"id": "node_1", "label": "节点名", "type": "POLICY", ...}
    ],
    "edges": [
        {"from": "node_1", "to": "node_2", "type": "ISSUED_BY", ...}
    ]
}
```

**示例**:
```python
from src.database.graph_dao import get_graph_dao

dao = get_graph_dao()
dao.save_graph(graph_data, is_incremental=False)
```

---

#### load_graph()
```python
def load_graph() -> Optional[Dict]
```

加载最新的知识图谱。

**返回值**:
```python
{
    "nodes": [...],
    "edges": [...],
    "metadata": {
        "node_count": 40,
        "edge_count": 73,
        "created_at": "2026-02-01T10:00:00Z"
    }
}
```

**示例**:
```python
graph_data = dao.load_graph()
if graph_data:
    print(f"加载图谱: {len(graph_data['nodes'])} 节点")
else:
    print("图谱不存在，请先构建")
```

---

#### remove_duplicate_nodes()
```python
def remove_duplicate_nodes() -> int
```

清理重复节点（去除.pdf后缀等）。

**返回值**:
- `int`: 删除的重复节点数

**示例**:
```python
removed = dao.remove_duplicate_nodes()
print(f"清理了 {removed} 个重复节点")
```

---

## 💼 业务逻辑层API

### ValidityChecker

**模块**: `src/business/validity_checker.py`

#### check_validity()
```python
def check_validity(policy: Policy) -> str
```

检查政策时效性。

**返回值**:
- `"有效"`: 政策仍有效
- `"已过期"`: 政策已过期
- `"即将过期"`: 距离过期不到30天

**示例**:
```python
from src.business.validity_checker import ValidityChecker

checker = ValidityChecker()
status = checker.check_validity(policy)

if status == "已过期":
    print("警告: 政策已过期！")
```

---

### ImpactAnalyzer

**模块**: `src/business/impact_analyzer.py`

#### analyze_impact()
```python
def analyze_impact(policy: Policy) -> Dict
```

分析政策影响范围。

**返回值**:
```python
{
    "affected_entities": ["高新技术企业", "科技型中小企业"],
    "impact_scope": "全省",
    "impact_level": "高",  # 高/中/低
    "estimated_beneficiaries": 10000
}
```

---

## 🔗 相关文档

- [02-ARCHITECTURE.md](02-ARCHITECTURE.md) - 系统架构
- [04-DEVELOPER_GUIDE.md](04-DEVELOPER_GUIDE.md) - 开发者指南
- [technical/modules-inventory.md](technical/modules-inventory.md) - 模块清单

---

**Last Updated**: 2026-02-01  
**Version**: 1.0
