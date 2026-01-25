# 系统架构设计文档

<!-- 文档类型: 技术架构文档 | 版本: 2026.1 | 更新时间: 2026-01-25 -->
<!-- 描述: 系统整体架构设计，包含模块划分、数据流和技术栈 -->

## 系统概览

```
┌─────────────────────────────────────────────────────────────────┐
│                    Streamlit Web 前端                           │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │  文档管理    │ │  知识图谱    │ │  语音处理    │            │
│  │ + 搜索      │ │  + 分析      │ │  + 语义搜索  │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│                      业务逻辑层                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ PolicyDAO (数据访问)                                     │   │
│  │ ValidityChecker (时效性检查)                             │   │
│  │ MetadataExtractor (元数据提取)                           │   │
│  │ TagGenerator (标签生成)                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
         ↓                      ↓                      ↓
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│   SQLite DB      │  │  RAGFlow         │  │  Whisper         │
│  (元数据存储)    │  │ (文件/搜索/LLM)  │  │ (语音转文字)     │
│                  │  │                  │  │                  │
│ - policies       │  │ - 文件上传       │  │ - transcribe     │
│ - tags           │  │ - 向量化         │  │ - speech-to-text │
│ - graphs         │  │ - 语义搜索       │  │                  │
│ - metadata       │  │ - 摘要生成       │  │                  │
│                  │  │ - QA接口         │  │                  │
└──────────────────┘  └──────────────────┘  └──────────────────┘
                      (内含DeepSeek集成)
```

---

## RAGFlow SDK集成

### 技术方案

系统使用**RAGFlow官方Python SDK** (ragflow-sdk >= 0.13.0) 实现所有RAGFlow功能。

```python
from ragflow_sdk import RAGFlow

# SDK客户端初始化
rag = RAGFlow(
    api_key=RAGFLOW_API_KEY,
    base_url=RAGFLOW_BASE_URL
)

# 获取数据集
datasets = rag.list_datasets(name="policy_demo_kb")
dataset = datasets[0]

# 上传文档
documents = dataset.upload_documents([{
    "display_name": "policy.pdf",
    "blob": file_content
}])

# 语义检索
chunks = dataset.retrieve(question="查询内容", limit=10)

# 创建聊天助手
chat = rag.create_chat(
    name="PolicyChat",
    dataset_ids=[dataset.id]
)

# 问答对话
session = chat.create_session("会话名称")
message = session.ask(question="问题", stream=False)
```

### 架构优势

- ✅ **代码简化**: 移除~400行自定义HTTP客户端代码
- ✅ **类型安全**: SDK提供完整类型提示
- ✅ **自动更新**: SDK自动跟随RAGFlow API更新
- ✅ **错误处理**: SDK内置完善的错误处理机制
- ✅ **性能优化**: SDK内部实现连接池和重试机制

详见：[RAGFlow SDK集成文档](RAGFLOW_SDK_INTEGRATION.md)

---

## 核心模块说明

### 1️⃣ 文件处理流程

#### ✅ 当前方案 (RAGFlow SDK)

```
用户上传
  ↓
Streamlit file_uploader
  ↓
保存为临时文件
  ↓
ragflow_client.upload_document()
  ├─ dataset = rag.list_datasets(name=kb_name)[0]
  ├─ 读取文件内容 (blob)
  └─ dataset.upload_documents([{"display_name": name, "blob": content}])
  ↓
RAGFlow SDK处理 (PDF→text, DOCX→text, TXT)
  ├─ 智能文本提取
  ├─ 自动文本分块（配置化）
  └─ 向量化存储
  ↓
返回 doc_id
  ↓
保存到SQLite (content字段存doc_id)
  ↓
成功提示
```

**RAGFlow SDK负责：**
- 智能文本提取（多种格式支持）
- 自动文本分块（通过parser_config配置）
- 向量化存储和索引
- HTTP连接管理和重试

**应用负责：**
- 表单验证（标题、文号、类型）
- 元数据管理（标题、文号、分类）
- 关系管理（与标签、图谱的关联）
- 知识库配置管理

---

### 2️⃣ 摘要生成流程

#### ✅ 最新方案 (RAGFlow-only)

```
Content (来自DB或RAGFlow)
  ↓
generate_summary(text)
  ↓
  ├─→ 尝试 _summarize_with_ragflow()
  │     - 加载 prompts/summarize_policy.txt
  │     - 调用 RAGFlow /api/llm_chat
  │     - RAGFlow内部使用 deepseek_api_key
  │     ↓ 成功？返回
  │
  └─→ 失败则回退
        - 文本截取 (max_length=1500)
```

**配置：**
```ini
[RAGFLOW]
api_key = ragflow-xxx
deepseek_api_key = sk-xxx  # RAGFlow内部使用，不需要应用层直接调用
```

**Prompt管理：**
- `prompts/summarize_policy.txt` 定义摘要结构
- RAGFlow通过API接收此Prompt
- 强制输出5个部分：政策目的/核心内容/适用范围/关键时间/主要影响

---

### 3️⃣ 知识图谱构建

```
获取所有Policy (来自DB)
  ↓
build_policy_graph()
  ↓
  ├─→ 循环遍历每个policy
  │     policy['id'], policy['title'], policy['document_number']
  │
  ├─→ 创建GraphNode对象
  │     node = GraphNode(node_id=policy['id'], label=policy['title'])
  │     graph.add_node(node)
  │
  └─→ 创建GraphEdge对象（Policy之间的关系）
        edge = GraphEdge(source=id1, target=id2, relation='相关')
        graph.add_edge(edge)
```

**关键API：**
```python
# 正确用法
node = GraphNode(node_id='xxx', label='标题')
graph.add_node(node)

# 获取统计信息
stats = graph.get_stats()  # 返回dict
# {
#   'node_count': 5,
#   'edge_count': 3,
#   'density': 0.5,
#   ...
# }
```

---

### 4️⃣ 搜索功能

```
用户输入查询词
  ↓
ragflow_client.search(query, kb_name, top_k)
  ├─ dataset = rag.list_datasets(name=kb_name)[0]
  └─ chunks = dataset.retrieve(question=query, limit=top_k)
  ↓
RAGFlow SDK内部处理
  ├─→ 语义相似度计算
  ├─→ BM25混合排序
  └─→ 返回top_k结果（Chunk对象）
  ↓
转换为标准格式
  └─ [{content, document_name, similarity, chunk_id}, ...]
```

**配置：**
```ini
[RAGFLOW]
search_top_k = 10
ragflow_similarity_threshold = 0.3
ragflow_retrieval_mode = general  # hybrid检索模式
```

---

### 5️⃣ 语音处理

```
用户上传音频
  ↓
Whisper /api/transcribe
  ↓
  ├─→ 音频编码识别
  ├─→ 模型推理
  └─→ 返回文本
      ↓
    对文本做摘要/搜索等后续处理
```

---

## 数据模型

### Policy (政策)
```python
{
    'id': int,                    # 主键
    'title': str,                 # 标题
    'content': str,               # RAGFlow doc_id (或文本)
    'summary': str,               # 摘要
    'document_number': str,       # 文号 (唯一)
    'policy_type': str,           # 类型: special_bonds/franchise/data_assets
    'region': str,                # 适用地区
    'file_path': str,             # 原始文件名
    'status': str,                # active/expired/expiring_soon
    'created_at': datetime,       # 创建时间
    'expiration_date': datetime,  # 失效日期
}
```

### GraphNode (图节点)
```python
{
    'node_id': str,        # 节点ID
    'label': str,          # 显示标签
    'node_type': str,      # 类型: policy/tag/concept
    'metadata': dict,      # 附加数据
}
```

### GraphEdge (图边)
```python
{
    'source': str,         # 源节点ID
    'target': str,         # 目标节点ID
    'relation': str,       # 关系类型: 相关/引用/包含等
    'weight': float,       # 权重 (0-1)
}
```

---

## 配置说明

### config.ini 关键配置

```ini
[RAGFLOW]
host = 117.21.184.150
port = 9380
api_key = ragflow-xxx

# 搜索配置
search_top_k = 10
search_score_threshold = 0.5
search_type = hybrid

# 文档处理
document_chunk_size = 500      # 文本块大小
document_smart_chunking = true # 智能分块

# DeepSeek配置 (RAGFlow内部使用)
deepseek_api_key = sk-xxx      # RAGFlow会使用此KEY生成摘要
deepseek_model = deepseek-chat

[WHISPER]
host = 117.21.184.150
port = 9002
transcribe_task = transcribe
transcribe_language = zh

[DATABASE]
sqlite_path = data/database/policy.db
auto_create_tables = true

[GRAPH]
graph_storage_dir = data/graphs
max_nodes = 200
max_edges = 500
```

---

## 依赖清单

### 核心Web框架
- `streamlit>=1.40.0` - Web UI框架
- `streamlit-option-menu>=0.3.13` - UI组件

### RAGFlow集成
- `ragflow-sdk>=0.13.0` - RAGFlow官方Python SDK
- `requests>=2.32.0` - HTTP客户端（SDK依赖）
- `beartype>=0.20.0` - 类型检查（SDK依赖）

### 数据处理
- `pandas>=2.2.3` - 数据处理
- `numpy>=2.0.0` - 数值计算

### 知识图谱与可视化
- `networkx>=3.4` - 图算法
- `pyvis>=0.3.2` - 图可视化
- `plotly>=5.24.0` - 数据可视化

### 音频处理
- `librosa>=0.10.2` - 音频分析
- `soundfile>=0.12.1` - 音频I/O

### 文件处理
- `openpyxl>=3.1.5` - Excel文件处理

### 开发工具
- `pytest>=8.3.0` - 单元测试
- `pytest-cov>=6.0.0` - 测试覆盖率
- `black>=24.10.0` - 代码格式化
- `flake8>=7.1.0` - 代码检查
- `mypy>=1.13.0` - 类型检查

### 已移除的依赖
- ❌ `pdfplumber` - RAGFlow SDK处理
- ❌ `PyPDF2` - RAGFlow SDK处理
- ❌ `python-docx` - RAGFlow SDK处理
- ❌ 自定义HTTP客户端代码 - SDK内置

---

## 调用流程示例

### 场景1: 上传PDF政策 (使用SDK)

```python
# 1. 用户选择文件
uploaded_file = st.file_uploader("选择PDF")

# 2. 保存临时文件
with tempfile.NamedTemporaryFile() as tmp:
    tmp.write(uploaded_file.getbuffer())

    # 3. 使用RAGFlow SDK上传
    client = get_ragflow_client()  # 获取SDK客户端
    doc_id = client.upload_document(
        file_path=tmp.name,
        file_name=uploaded_file.name,
        knowledge_base_name="policy_demo_kb"
    )

    # SDK内部执行：
    # dataset = client.rag.list_datasets(name="policy_demo_kb")[0]
    # documents = dataset.upload_documents([{
    #     "display_name": uploaded_file.name,
    #     "blob": file_content
    # }])
    # doc_id = documents[0].id

    # 4. 保存元数据到DB
    policy_data = {
        'title': '政策标题',
        'content': doc_id,  # 存RAGFlow文档ID
        'summary': f"已上传到RAGFlow: {doc_id}",
        'document_number': '财预〔2026〕001号',
        ...
    }
    dao.create_policy(policy_data)
```

### 场景2: 生成摘要

```python
from src.utils.summarizer import generate_summary

# 1. 获取文本（来自RAGFlow搜索或DB）
text = get_document_content()

# 2. 调用生成摘要
summary = generate_summary(text, max_length=1500)

# 3. 摘要流程
# - 加载 prompts/summarize_policy.txt
# - 拼接文本
# - 调用 RAGFlow /api/llm_chat
# - RAGFlow内部使用 deepseek_api_key 调用DeepSeek
# - 返回摘要
```

### 场景3: 搜索政策 (使用SDK)

```python
from src.services.ragflow_client import get_ragflow_client

client = get_ragflow_client()  # 获取SDK客户端

# 1. 语义搜索
results = client.search(
    query="特许经营相关政策",
    knowledge_base_name="policy_demo_kb",
    top_k=10
)

# SDK内部执行：
# dataset = client.rag.list_datasets(name="policy_demo_kb")[0]
# chunks = dataset.retrieve(question="特许经营相关政策", limit=10)
# 转换为标准格式返回

# 2. RAGFlow返回相关文档
# - 向量相似度 + BM25混合排序
# - 返回 [doc_id, 标题, 相关度, ...]
```

---

## 错误处理

### 常见错误及处理

| 错误 | 原因 | 处理 |
|------|------|------|
| RAGFlow连接失败 | 服务未启动 | 提示用户启动RAGFlow |
| 文件上传失败 | 格式不支持/大小超限 | 提示重新上传 |
| 摘要生成超时 | RAGFlow响应慢 | 回退到文本截取 |
| 搜索无结果 | 查询词不匹配 | 提示修改查询词 |
| 图谱构建失败 | 数据格式错误 | 检查Policy数据格式 |

---

## 扩展建议

### 1. 增强摘要功能
- [ ] 支持多种语言摘要
- [ ] 自定义摘要长度
- [ ] 摘要质量评分

### 2. 改进搜索
- [ ] 高级过滤条件
- [ ] 搜索历史记录
- [ ] 个性化排序

### 3. 图谱优化
- [ ] 自动关系抽取
- [ ] 图谱社区检测
- [ ] 动态布局优化

### 4. 功能扩展
- [ ] 政策对比功能
- [ ] 批量操作支持
- [ ] 导出为PDF/Excel
- [ ] 更新通知系统

---

## 性能指标

| 指标 | 目标 | 备注 |
|------|------|------|
| 文件上传 | < 10s | 取决于RAGFlow |
| 搜索响应 | < 2s | top_k=10 |
| 摘要生成 | < 5s | 1000字文本 |
| 图谱渲染 | < 1s | <500节点 |

---

## 总结

✅ **架构特点：**
- RAGFlow为单一后端，处理所有LLM和文件相关任务
- 应用层专注UI和业务逻辑
- 清晰的关注点分离

✅ **优势：**
- 减少外部依赖（已删除3个库）
- 简化代码维护（无重复配置）
- 更好的可扩展性

⚠️ **需要注意：**
- RAGFlow服务必须正常运行
- deepseek_api_key需要有效
- 大文件上传需要增加超时时间
