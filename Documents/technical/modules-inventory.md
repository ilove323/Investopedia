# 📦 模块功能清单

> 基于实际代码梳理，每个模块的功能、依赖和使用场景  
> Last Updated: 2026-02-01

---

## 📄 页面模块 (src/pages/)

### 🔍 search_page.py
**功能**: 政策关键词搜索和高级筛选  
**核心组件**:
- `perform_search()` - 执行搜索并更新结果
- `show()` - 主入口，渲染搜索界面

**使用的UI组件**:
- `render_search_bar()` - 搜索输入栏
- `render_advanced_search_panel()` - 高级筛选面板
- `render_search_results()` - 结果展示
- `render_search_filters_sidebar()` - 侧边栏快速筛选
- `render_search_stats()` - 搜索统计

**数据访问**: `PolicyDAO`

**特性**:
- 支持关键词搜索
- 多维度筛选（类型、地区、状态、日期）
- 分页展示
- 实时搜索统计

---

### 💬 chat_page.py
**功能**: 基于RAGFlow Chat Assistant的智能对话  
**核心函数**:
- `format_references_with_anchors()` - 格式化引用编号
- `deduplicate_references()` - 去重参考文档
- `show()` - 主入口，渲染聊天界面

**使用的服务**:
- `ChatService` - RAGFlow Chat API封装
- `GraphDAO` - 知识图谱数据

**特性**:
- 流式打字效果
- 参考文档展示（自动去重）
- 可点击的引用编号
- 知识图谱可视化
- 多轮对话支持
- 会话管理

**session_state**:
- `chat_messages` - 聊天历史
- `current_session_id` - 当前会话ID

---

### 📊 graph_page.py
**功能**: 知识图谱可视化和管理  
**核心函数**:
- `show()` - 主入口
- `load_graph_from_database()` - 从数据库加载图谱
- `render_edge_details_section()` - 显示边详情

**使用的服务**:
- `DataSyncService` - 图谱构建
- `GraphDAO` - 图谱持久化

**UI组件**:
- `render_graph_controls()` - 图谱控制
- `render_graph_filter_by_type()` - 节点类型筛选
- `render_graph_search()` - 图谱搜索
- `render_graph_path_finder()` - 路径查询
- `render_network_graph()` - Pyvis渲染

**特性**:
- 全量重建/增量更新图谱
- 节点和边类型筛选
- 路径查询（最短路径）
- 图谱导出
- 节点详情展示

**session_state**:
- `graph` - PolicyGraph对象
- `selected_node` - 选中的节点

---

### 🎤 voice_page.py
**功能**: 语音输入、转文字、智能问答  
**核心函数**:
- `show()` - 主入口
- `render_voice_qa_section()` - 语音问答区域

**使用的服务**:
- `WhisperClient` - 语音识别
- `APIClient` - 问答API

**UI组件**:
- `render_voice_input()` - 语音输入
- `render_voice_settings()` - 语音设置
- `render_transcription_result()` - 转录结果
- `render_qa_result()` - 问答结果
- `render_voice_history()` - 历史记录
- `render_voice_tips()` - 使用提示

**特性**:
- 实时录音（需要额外库）
- 上传音频文件（wav, mp3, m4a, flac, ogg）
- Whisper转录
- 基于转录内容问答
- 保存历史记录（最近10条）

**session_state**:
- `voice_history` - 问答历史
- `transcription` - 转录文本
- `voice_stats` - 统计信息

---

### 📄 documents_page.py
**功能**: RAGFlow文档查看器  
**核心函数**:
- `show()` - 主入口
- `render_documents_list()` - 文档列表
- `render_document_search()` - 文档搜索
- `render_document_viewer()` - 文档分块查看器
- `render_graph_builder()` - 图谱构建器

**使用的服务**:
- `RAGFlowClient` - 文档管理
- `DataSyncService` - 数据同步、图谱构建

**特性**:
- 显示RAGFlow知识库所有文档
- 查看文档元数据（大小、分块数、token数）
- 查看文档分块（chunk）
- 文档搜索（retrieve）
- 一键构建知识图谱（全量/增量）

**session_state**:
- `selected_doc` - 选中的文档ID

**注意**: 文档上传在RAGFlow Web界面，本页面专注查看和管理

---

### 📈 analysis_page.py
**功能**: 政策分析（时效性、对比、趋势）  
**核心函数**:
- `show()` - 主入口
- `render_single_analysis()` - 单个政策分析
- `render_policy_comparison()` - 政策对比
- `render_trends_analysis()` - 趋势分析

**使用的业务逻辑**:
- `ValidityChecker` - 时效性检查
- `ImpactAnalyzer` - 影响分析

**特性**:
- 时效性分析（是否过期、即将过期）
- 政策对比（多个政策对比）
- 趋势分析（政策发布趋势）

**session_state**:
- `selected_policies_for_compare` - 对比政策列表

---

## 🔌 服务层 (src/services/)

### 🌐 ragflow_client.py
**核心类**: `RAGFlowClient`  
**功能**: RAGFlow SDK封装，文档管理和检索

**主要方法**:
- `check_health()` - 健康检查
- `get_documents(kb_name)` - 获取知识库文档列表
- `get_document_content(doc_id, kb_name)` - 获取文档完整内容
- `retrieve(question, kb_name)` - 检索相关文档
- `list_datasets()` - 列出所有知识库

**配置项**:
- `ragflow_api_url` - API地址
- `ragflow_api_key` - API密钥
- `ragflow_kb_name` - 知识库名称

**单例模式**: `get_ragflow_client()`

**重要**: RAGFlow SDK 0.13.0+ 使用 `chunk_count` 而不是 `chunk_num`

---

### 🧠 qwen_client.py
**核心类**: `QwenClient`  
**功能**: Qwen大模型实体关系抽取

**主要方法**:
- `extract_entities_and_relations(text, doc_title)` - 提取实体和关系
- `_load_prompt_template()` - 加载提示词模板
- `_parse_extraction_result(content)` - 解析JSON结果

**配置项**:
- `qwen_api_key` - DashScope API密钥
- `qwen_model` - 模型名称（默认qwen-plus）
- `qwen_temperature` - 温度参数（默认0.1）
- `qwen_max_tokens` - 最大token数（默认2000）
- `qwen_prompt_file` - 提示词文件路径

**提示词**: `config/prompts/entity_extraction.txt`

**返回格式**:
```json
{
  "entities": [
    {"text": "实体文本", "type": "实体类型", "description": "描述"}
  ],
  "relations": [
    {"source": "源实体", "target": "目标实体", "type": "关系类型"}
  ]
}
```

**性能**:
- 单文档耗时: 3-5秒
- 实体数: 10-15个
- 关系数: 8-12个

**单例模式**: `get_qwen_client()`

---

### 💬 chat_service.py
**核心类**: `ChatService`  
**功能**: RAGFlow Chat Assistant封装

**主要方法**:
- `chat(question, session_id, stream)` - 发送问题，获取答案
- `create_session(kb_name)` - 创建新会话
- `list_sessions()` - 列出所有会话

**特性**:
- 支持流式输出
- 自动管理会话
- 返回参考文档

**配置项**:
- `chat_assistant_id` - Chat Assistant ID（从RAGFlow获取）

**单例模式**: `get_chat_service()`

---

### 🔄 data_sync.py
**核心类**: `DataSyncService`  
**功能**: RAGFlow数据同步和知识图谱构建（**最核心的服务**）

**主要方法**:
- `sync_documents_to_database(kb_name)` - 同步文档到本地数据库
- `build_knowledge_graph(kb_name, is_incremental)` - 构建知识图谱
- `_extract_entities_and_relations(text, doc_title)` - 从文档提取实体和关系
- `get_sync_status()` - 获取同步状态

**完整图谱构建流程**:
```
1. 从RAGFlow获取文档列表 (ragflow_client.get_documents)
2. 遍历每个文档
   ├─ 获取文档内容 (ragflow_client.get_document_content)
   ├─ 调用Qwen提取实体和关系 (qwen_client.extract_entities_and_relations)
   ├─ 构建节点和边 (_extract_entities_and_relations)
   └─ 去重（文档名、节点ID）
3. 保存到数据库 (graph_dao.save_graph)
4. 返回统计结果
```

**去重逻辑**:
- 文档名去重（去除.pdf后缀）
- 节点ID去重
- 关系source/target匹配验证

**依赖服务**:
- `RAGFlowClient`
- `QwenClient`
- `GraphDAO`
- `PolicyDAO`

---

### 🎙️ whisper_client.py
**核心类**: `WhisperClient`  
**功能**: 语音识别（OpenAI Whisper API）

**主要方法**:
- `transcribe(audio_file)` - 转录音频文件

**配置项**:
- `whisper_api_key` - OpenAI API密钥
- `whisper_model` - 模型名称（默认whisper-1）

**单例模式**: `get_whisper_client()`

---

### 🔍 hybrid_retriever.py
**核心类**: `HybridRetriever`  
**功能**: 混合检索（RAGFlow + 向量检索）

**主要方法**:
- `retrieve(query)` - 混合检索

---

### 🛠️ api_utils.py
**核心类**: `APIClient`  
**功能**: 通用HTTP API调用封装

**主要方法**:
- `get()` - GET请求
- `post()` - POST请求

---

## 💼 业务逻辑层 (src/business/)

### ✅ validity_checker.py
**核心类**: `ValidityChecker`  
**功能**: 检查政策时效性

**主要方法**:
- `check_validity(policy)` - 检查是否有效
- `get_expiry_warning(policy)` - 获取过期警告

**逻辑**:
- 检查 `effective_date` 和 `expiry_date`
- 判断是否过期、即将过期、仍有效

---

### 📊 impact_analyzer.py
**核心类**: `ImpactAnalyzer`  
**功能**: 分析政策影响范围

**主要方法**:
- `analyze_impact(policy)` - 分析影响
- `get_affected_entities(policy)` - 获取受影响对象

---

### 🏷️ tag_generator.py
**核心类**: `TagGenerator`  
**功能**: 基于内容生成标签

**主要方法**:
- `generate_tags(content, policy_type)` - 生成标签

**依赖**: jieba分词

---

### 📝 metadata_extractor.py
**核心类**: `MetadataExtractor`  
**功能**: 从政策文本提取元数据

**主要方法**:
- `extract_all(content)` - 提取所有元数据
- `extract_issuing_authority(content)` - 提取发文机关
- `extract_document_number(content)` - 提取文号
- `extract_dates(content)` - 提取日期

**返回字段**:
- `policy_type` - 政策类型
- `issuing_authority` - 发文机关
- `region` - 地区
- `effective_date` - 生效日期
- `document_number` - 文号

---

## 🗄️ 数据访问层 (src/database/)

### 🔧 db_manager.py
**核心类**: `DatabaseManager`  
**功能**: 数据库初始化和连接管理

**主要方法**:
- `initialize_database()` - 初始化数据库（执行schema.sql）
- `get_connection()` - 获取数据库连接

**数据库文件**: `data/database/policies.db`

**单例模式**: `get_db_manager()`

---

### 🕸️ graph_dao.py
**核心类**: `GraphDAO`  
**功能**: 知识图谱CRUD操作

**数据表**: `knowledge_graph`
```sql
CREATE TABLE knowledge_graph (
    id INTEGER PRIMARY KEY,
    graph_data TEXT,        -- JSON格式存储
    node_count INTEGER,
    edge_count INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

**主要方法**:
- `save_graph(graph_data, is_incremental)` - 保存图谱
- `load_graph()` - 加载最新图谱
- `remove_duplicate_nodes()` - 清理重复节点
- `get_stats()` - 获取统计信息

**存储格式**:
```json
{
  "nodes": [
    {"id": "node_1", "label": "节点名", "type": "节点类型", ...}
  ],
  "edges": [
    {"from": "node_1", "to": "node_2", "type": "关系类型", ...}
  ]
}
```

---

### 📄 policy_dao.py
**核心类**: `PolicyDAO`  
**功能**: 政策数据CRUD操作

**数据表**:
- `policies` - 政策主表
- `tags` - 标签表
- `policy_tags` - 政策-标签关联表

**主要方法**:
- `create_policy(metadata)` - 创建政策
- `update_policy(policy_id, metadata)` - 更新政策
- `get_policy_by_ragflow_id(doc_id)` - 根据RAGFlow文档ID查询
- `get_policies(filters)` - 查询政策列表
- `get_stats()` - 获取统计信息
- `get_or_create_tag(tag_name, tag_type)` - 获取或创建标签
- `add_policy_tag(policy_id, tag_id)` - 添加政策标签

**单例模式**: `get_policy_dao()`

---

## 🎨 UI组件层 (src/components/)

### 🕸️ graph_ui.py
**主要函数**:
- `render_network_graph(graph, title)` - 渲染Pyvis网络图
- `render_graph_stats(stats)` - 渲染图谱统计
- `render_graph_controls()` - 图谱控制面板
- `render_graph_filter_by_type()` - 节点类型筛选
- `render_graph_search()` - 图谱搜索
- `render_graph_path_finder()` - 路径查询
- `render_graph_export()` - 图谱导出

**技术**: Pyvis + NetworkX + Streamlit

---

### 🔍 search_ui.py
**主要函数**:
- `render_search_bar()` - 搜索输入栏
- `render_advanced_search_panel()` - 高级筛选
- `render_search_results()` - 搜索结果展示
- `render_search_filters_sidebar()` - 侧边栏筛选
- `render_search_stats()` - 搜索统计

---

### 🎤 voice_ui.py
**主要函数**:
- `render_voice_input()` - 语音输入
- `render_voice_settings()` - 语音设置
- `render_transcription_result()` - 转录结果
- `render_qa_result()` - 问答结果
- `render_voice_history()` - 历史记录
- `render_voice_tips()` - 使用提示

---

### 📇 policy_card.py
**主要函数**:
- `render_policy_card()` - 渲染政策卡片

---

## 📊 数据模型 (src/models/)

### 🕸️ graph.py
**枚举**:
- `NodeType` - 节点类型（POLICY, AUTHORITY, REGION, CONCEPT, PROJECT）
- `RelationType` - 关系类型（ISSUED_BY, APPLIES_TO, REFERENCES, AFFECTS, etc.）

**数据类**:
- `GraphNode` - 图谱节点
- `GraphEdge` - 图谱边

**核心类**: `PolicyGraph`
- 基于NetworkX封装
- 支持节点/边增删
- 支持图算法（最短路径、连通分量等）

---

### 📄 policy.py
**数据类**: `Policy`
- 政策数据模型

---

### 🏷️ tag.py
**数据类**: `Tag`
- 标签数据模型

---

## 🛠️ 工具函数 (src/utils/)

### 📁 file_utils.py
**主要函数**:
- `validate_file(file)` - 验证文件
- `get_file_type(file)` - 获取文件类型

---

### 📝 logger.py
**主要函数**:
- `setup_logger(log_file, log_level)` - 配置日志

---

### 📋 summarizer.py
**主要函数**:
- `generate_summary(text)` - 生成文本摘要

---

## ⚙️ 配置管理 (src/config/)

### 🔧 config_loader.py
**核心类**: `ConfigLoader`  
**功能**: 统一配置管理

**特性**:
- ✅ 读取 `config/config.ini`
- ✅ 环境变量覆盖INI配置
- ✅ 类型转换（自动转int, bool, Path）
- ✅ 路径自动创建
- ✅ 验证必需配置项

**使用方式**:
```python
from src.config import get_config
config = get_config()
print(config.ragflow_api_url)  # 属性访问
```

**配置段**:
- `[APP]` - 应用配置
- `[RAGFLOW]` - RAGFlow配置
- `[QWEN]` - Qwen配置
- `[WHISPER]` - Whisper配置
- `[CHAT]` - Chat配置

---

## 📈 依赖关系图

```
app.py
  ├─ pages/*
  │   ├─ components/*
  │   ├─ services/*
  │   └─ database/*
  │
  ├─ services/*
  │   ├─ config/
  │   ├─ database/
  │   └─ business/
  │
  └─ config/
      └─ config_loader.py
```

**核心依赖链**:
1. `app.py` → `pages/graph_page.py`
2. `graph_page.py` → `DataSyncService`
3. `DataSyncService` → `RAGFlowClient` + `QwenClient` + `GraphDAO`
4. 所有服务 → `ConfigLoader`

---

## 🎯 使用场景

### 场景1: 构建知识图谱
```python
from src.services.data_sync import DataSyncService

sync = DataSyncService()
result = sync.build_knowledge_graph(kb_name="policy_demo_kb")
print(f"节点: {result['node_count']}, 边: {result['edge_count']}")
```

### 场景2: 智能问答
```python
from src.services.chat_service import get_chat_service

chat = get_chat_service()
response = chat.chat("政策问题", session_id="session_1")
print(response['answer'])
```

### 场景3: 语音识别
```python
from src.services.whisper_client import get_whisper_client

whisper = get_whisper_client()
text = whisper.transcribe(audio_file)
print(text)
```

---

## 🔍 快速定位

| 功能 | 核心文件 |
|------|---------|
| 图谱构建 | `data_sync.py` + `qwen_client.py` |
| 图谱显示 | `graph_page.py` + `graph_ui.py` |
| 图谱存储 | `graph_dao.py` |
| 文档检索 | `ragflow_client.py` |
| 智能问答 | `chat_service.py` |
| 语音识别 | `whisper_client.py` |
| 政策搜索 | `search_page.py` + `policy_dao.py` |
| 配置管理 | `config_loader.py` |

---

**参考文档**:
- [code-structure.md](code-structure.md) - 代码结构
- [05-API_REFERENCE.md](../05-API_REFERENCE.md) - API详细文档
