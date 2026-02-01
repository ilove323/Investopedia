# 📁 代码结构详解

> 最后更新: 2026-02-01  
> 基于实际代码生成，确保准确性

---

## 🌲 完整目录树

```
Investopedia/
├── app.py                          # 🚀 Streamlit主应用入口
├── config/                         # ⚙️ 配置文件
│   ├── config.ini                  # 主配置文件（运行时）
│   ├── config.ini.template         # 配置模板
│   ├── knowledgebase/              # 知识库配置
│   │   ├── policy_demo_kb.ini      # 演示知识库配置
│   │   ├── template.ini            # 知识库模板
│   │   └── README.md               # 知识库配置说明
│   └── prompts/                    # LLM提示词模板
│       ├── entity_extraction.txt   # Qwen实体抽取提示词
│       └── summarize_policy.txt    # 政策摘要提示词
├── src/                            # 📦 源代码
│   ├── __init__.py
│   ├── business/                   # 💼 业务逻辑层
│   │   ├── __init__.py
│   │   ├── impact_analyzer.py      # 政策影响分析
│   │   ├── metadata_extractor.py   # 元数据提取
│   │   ├── tag_generator.py        # 标签生成
│   │   └── validity_checker.py     # 时效性检查
│   ├── components/                 # 🎨 UI组件
│   │   ├── __init__.py
│   │   ├── graph_ui.py             # 图谱可视化组件
│   │   ├── policy_card.py          # 政策卡片组件
│   │   ├── search_ui.py            # 搜索UI组件
│   │   └── voice_ui.py             # 语音UI组件
│   ├── config/                     # 📋 配置管理
│   │   ├── __init__.py
│   │   └── config_loader.py        # 配置加载器（核心）
│   ├── database/                   # 🗄️ 数据访问层
│   │   ├── __init__.py
│   │   ├── db_manager.py           # 数据库管理器
│   │   ├── graph_dao.py            # 图谱数据访问对象
│   │   ├── policy_dao.py           # 政策数据访问对象
│   │   └── schema.sql              # 数据库schema
│   ├── models/                     # 📊 数据模型
│   │   ├── __init__.py
│   │   ├── graph.py                # 图谱模型（NodeType, RelationType, PolicyGraph）
│   │   ├── policy.py               # 政策模型
│   │   └── tag.py                  # 标签模型
│   ├── pages/                      # 📄 页面模块
│   │   ├── __init__.py
│   │   ├── analysis_page.py        # 政策分析页面
│   │   ├── chat_page.py            # 智能问答页面
│   │   ├── documents_page.py       # 文档查看器页面
│   │   ├── graph_page.py           # 知识图谱页面
│   │   ├── search_page.py          # 政策搜索页面
│   │   └── voice_page.py           # 语音问答页面
│   ├── services/                   # 🔌 服务集成层
│   │   ├── __init__.py
│   │   ├── api_utils.py            # API工具函数
│   │   ├── chat_service.py         # 聊天服务（RAGFlow Chat）
│   │   ├── data_sync.py            # 数据同步服务（核心）
│   │   ├── hybrid_retriever.py     # 混合检索器
│   │   ├── qwen_client.py          # Qwen大模型客户端
│   │   ├── ragflow_client.py       # RAGFlow客户端
│   │   └── whisper_client.py       # Whisper语音识别客户端
│   └── utils/                      # 🛠️ 工具函数
│       ├── __init__.py
│       ├── file_utils.py           # 文件处理工具
│       ├── logger.py               # 日志工具
│       └── summarizer.py           # 摘要生成工具
├── data/                           # 📂 数据目录
│   ├── database/                   # SQLite数据库文件
│   │   ├── policies.db             # 主数据库（政策+图谱）
│   │   └── policy.db               # 备用数据库
│   ├── graphs/                     # 图谱数据（如果需要）
│   └── uploads/                    # 用户上传文件
├── logs/                           # 📝 日志目录
├── tests/                          # 🧪 测试套件
│   ├── __init__.py
│   ├── run_tests.py                # 测试运行器
│   ├── test_*.py                   # 单元测试
│   └── debug_*.py                  # 调试脚本
├── Documents/                      # 📚 项目文档
│   ├── 00-INDEX.md                 # 文档导航
│   ├── 01-QUICK_START.md           # 快速开始
│   ├── 02-ARCHITECTURE.md          # 系统架构
│   └── technical/                  # 技术细节文档
└── docker/                         # 🐳 Docker配置
    ├── Dockerfile
    ├── docker-compose.yml
    └── docker-compose.ragflow.yml
```

---

## 📦 模块详解

### 1️⃣ 业务逻辑层 (`src/business/`)

| 文件 | 核心类/函数 | 功能 | 依赖 |
|------|------------|------|------|
| `impact_analyzer.py` | `ImpactAnalyzer` | 分析政策影响范围和受影响对象 | PolicyDAO |
| `metadata_extractor.py` | `MetadataExtractor` | 从政策文本中提取元数据（发文机关、文号等） | re, datetime |
| `tag_generator.py` | `TagGenerator` | 基于政策内容生成标签 | jieba |
| `validity_checker.py` | `ValidityChecker` | 检查政策时效性（生效/失效日期） | datetime |

**设计理念**: 纯业务逻辑，不依赖UI框架，便于单元测试

---

### 2️⃣ UI组件层 (`src/components/`)

| 文件 | 核心函数 | 功能 | 技术栈 |
|------|---------|------|--------|
| `graph_ui.py` | `render_network_graph()` | 使用Pyvis渲染交互式图谱 | Pyvis, NetworkX |
| `policy_card.py` | `render_policy_card()` | 渲染政策卡片（展示摘要、元数据） | Streamlit |
| `search_ui.py` | `render_search_bar()` `render_search_results()` | 搜索栏和结果展示 | Streamlit |
| `voice_ui.py` | `render_voice_input()` `render_transcription_result()` | 语音输入和转录结果展示 | Streamlit |

**设计理念**: 可复用组件，专注渲染逻辑，不包含业务逻辑

---

### 3️⃣ 配置管理 (`src/config/`)

| 文件 | 核心类 | 功能 | 特性 |
|------|--------|------|------|
| `config_loader.py` | `ConfigLoader` | 统一配置管理，支持环境变量覆盖 | 单例模式，属性访问 |

**关键特性**:
- ✅ 自动读取 `config.ini`
- ✅ 环境变量覆盖INI配置
- ✅ 类型转换（str→int, str→bool）
- ✅ 路径自动创建
- ✅ 验证必需配置项

**使用示例**:
```python
from src.config import get_config
config = get_config()
print(config.ragflow_api_url)  # 属性访问
```

---

### 4️⃣ 数据访问层 (`src/database/`)

| 文件 | 核心类 | 功能 | 数据表 |
|------|--------|------|--------|
| `db_manager.py` | `DatabaseManager` | 数据库初始化和连接管理 | 所有表 |
| `graph_dao.py` | `GraphDAO` | 图谱CRUD操作 | `knowledge_graph` |
| `policy_dao.py` | `PolicyDAO` | 政策CRUD操作 | `policies`, `tags`, `policy_tags` |

**数据库设计**:
```sql
-- knowledge_graph 表（JSON存储）
CREATE TABLE knowledge_graph (
    id INTEGER PRIMARY KEY,
    graph_data TEXT,        -- JSON: {nodes:[], edges:[]}
    node_count INTEGER,
    edge_count INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- policies 表
CREATE TABLE policies (
    id TEXT PRIMARY KEY,
    ragflow_document_id TEXT,
    name TEXT,
    content TEXT,
    effective_date DATE,
    ...
);
```

---

### 5️⃣ 数据模型 (`src/models/`)

| 文件 | 核心类/枚举 | 用途 |
|------|-----------|------|
| `graph.py` | `NodeType`, `RelationType`, `GraphNode`, `GraphEdge`, `PolicyGraph` | 图谱数据结构 |
| `policy.py` | `Policy` | 政策数据模型 |
| `tag.py` | `Tag` | 标签数据模型 |

**关键设计**:
```python
# 节点类型
class NodeType(str, Enum):
    POLICY = "policy"
    AUTHORITY = "authority"
    REGION = "region"
    CONCEPT = "concept"

# 关系类型
class RelationType(str, Enum):
    ISSUED_BY = "issued_by"      # 发布
    APPLIES_TO = "applies_to"    # 适用于
    REFERENCES = "references"    # 引用
    AFFECTS = "affects"          # 影响
```

---

### 6️⃣ 页面模块 (`src/pages/`)

| 文件 | 页面名称 | 核心功能 | 依赖服务 |
|------|---------|---------|---------|
| `analysis_page.py` | 📈 政策分析 | 时效性分析、政策对比、趋势分析 | ValidityChecker, ImpactAnalyzer |
| `chat_page.py` | 💬 智能问答 | RAGFlow Chat Assistant对话 | ChatService, RAGFlowClient |
| `documents_page.py` | 📄 文档管理 | RAGFlow文档查看、搜索、分块展示 | RAGFlowClient, DataSyncService |
| `graph_page.py` | 📊 知识图谱 | 图谱构建、可视化、筛选、路径查询 | DataSyncService, GraphDAO |
| `search_page.py` | 🔍 政策搜索 | 关键词搜索、高级筛选、结果展示 | PolicyDAO |
| `voice_page.py` | 🎤 语音问答 | 语音识别、文本问答、历史记录 | WhisperClient, RAGFlowClient |

**页面入口规范**:
每个页面都有一个 `show()` 函数作为入口，由 `app.py` 调用：
```python
# app.py
from src.pages.search_page import show as show_search_page
show_search_page()
```

---

### 7️⃣ 服务集成层 (`src/services/`)

| 文件 | 核心类 | 功能 | 外部服务 |
|------|--------|------|---------|
| `api_utils.py` | `APIClient` | 通用API调用封装 | HTTP |
| `chat_service.py` | `ChatService` | RAGFlow Chat Assistant集成 | RAGFlow API |
| `data_sync.py` | `DataSyncService` | 数据同步、图谱构建（**核心**） | RAGFlow + Qwen |
| `hybrid_retriever.py` | `HybridRetriever` | 混合检索（RAGFlow + 向量） | RAGFlow |
| `qwen_client.py` | `QwenClient` | Qwen大模型实体抽取 | DashScope API |
| `ragflow_client.py` | `RAGFlowClient` | RAGFlow SDK封装 | RAGFlow SDK |
| `whisper_client.py` | `WhisperClient` | 语音识别 | OpenAI Whisper API |

**核心服务 - DataSyncService**:
```python
class DataSyncService:
    def build_knowledge_graph(kb_name: str) -> Dict:
        """完整图谱构建流程"""
        # 1. 从RAGFlow获取文档
        # 2. 调用Qwen提取实体和关系
        # 3. 去重节点和边
        # 4. 保存到SQLite
        # 5. 返回统计结果
```

---

### 8️⃣ 工具函数 (`src/utils/`)

| 文件 | 核心函数 | 功能 |
|------|---------|------|
| `file_utils.py` | `validate_file()`, `get_file_type()` | 文件验证、类型检测 |
| `logger.py` | `setup_logger()` | 日志配置和初始化 |
| `summarizer.py` | `generate_summary()` | 文本摘要生成 |

---

## 🔄 核心数据流

### 流程1: 文档上传 → 知识图谱

```
1. 用户在RAGFlow Web上传PDF
   ↓
2. RAGFlow自动分块（chunk_method=laws）
   ↓
3. 用户在系统点击"构建图谱"
   ↓
4. DataSyncService.build_knowledge_graph()
   ├─ ragflow_client.get_documents() - 获取文档列表
   ├─ ragflow_client.get_document_content() - 获取每个文档内容
   ├─ qwen_client.extract_entities_and_relations() - Qwen提取实体和关系
   ├─ _extract_entities_and_relations() - 构建节点和边
   └─ graph_dao.save_graph() - 保存到SQLite
   ↓
5. graph_page.py加载并可视化
   ├─ graph_dao.load_graph() - 从SQLite加载
   ├─ 转换为PolicyGraph对象
   └─ render_network_graph() - Pyvis渲染
```

### 流程2: 智能问答

```
1. 用户输入问题（文本或语音）
   ↓
2. 如果是语音: whisper_client.transcribe() - 转文字
   ↓
3. chat_service.chat() 或 ragflow_client.retrieve()
   ├─ RAGFlow检索相关文档
   └─ 返回答案 + 参考文档
   ↓
4. 前端展示答案和引用
```

### 流程3: 配置加载

```
1. 应用启动: app.py
   ↓
2. from src.config import get_config
   ↓
3. ConfigLoader.__init__()
   ├─ 读取 config/config.ini
   ├─ 检查环境变量覆盖
   ├─ 类型转换和验证
   └─ 创建必需目录
   ↓
4. 各服务使用config对象
   └─ ragflow_client = RAGFlowClient(config.ragflow_api_url)
```

---

## 🎯 扩展指南

### 添加新页面

1. **创建页面文件**: `src/pages/new_page.py`
```python
"""新页面说明"""
import streamlit as st

def show():
    st.title("新页面")
    # 实现逻辑
```

2. **注册到app.py**:
```python
PAGES = {
    "🆕 新页面": "new_page",
    # ...existing pages
}

# 在main()中添加路由
elif "新页面" in selected_page:
    from src.pages.new_page import show as show_new_page
    show_new_page()
```

### 添加新服务集成

1. **创建客户端**: `src/services/new_service.py`
```python
class NewServiceClient:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key
    
    def some_method(self):
        # 实现
        pass

# 单例
_instance = None
def get_new_service():
    global _instance
    if _instance is None:
        config = get_config()
        _instance = NewServiceClient(
            config.new_service_url,
            config.new_service_key
        )
    return _instance
```

2. **添加配置**: `config/config.ini`
```ini
[NEW_SERVICE]
api_url = http://localhost:8000
api_key = your_key_here
```

3. **更新ConfigLoader**: `src/config/config_loader.py`
```python
@property
def new_service_url(self) -> str:
    return self._get_env_or_config('NEW_SERVICE', 'api_url')
```

### 添加新实体类型

1. **更新提示词**: `config/prompts/entity_extraction.txt`
```
**提取的实体类型**:
...
9. 新实体类型 - 描述
```

2. **更新颜色映射**: `src/services/data_sync.py`
```python
def _get_entity_color(self, entity_type: str) -> str:
    color_map = {
        '新实体类型': '#颜色代码',
        # ...existing
    }
```

---

## 📊 代码统计

```
总文件数: 37个Python文件
总代码行数: ~8000行（不含注释和空行）

分层统计:
├─ pages/        ~2500行  (31%)  - UI逻辑最多
├─ services/     ~2000行  (25%)  - 服务集成
├─ components/   ~1200行  (15%)  - UI组件
├─ database/     ~800行   (10%)  - 数据访问
├─ business/     ~700行   (9%)   - 业务逻辑
├─ models/       ~500行   (6%)   - 数据模型
└─ utils/        ~300行   (4%)   - 工具函数
```

---

## 🔍 代码导航技巧

### 快速定位功能

| 需求 | 查看文件 |
|------|---------|
| 应用启动流程 | `app.py` |
| 配置如何加载 | `src/config/config_loader.py` |
| 图谱如何构建 | `src/services/data_sync.py` |
| 图谱如何存储 | `src/database/graph_dao.py` |
| 图谱如何显示 | `src/pages/graph_page.py` + `src/components/graph_ui.py` |
| 实体如何抽取 | `src/services/qwen_client.py` |
| 文档如何检索 | `src/services/ragflow_client.py` |
| 语音如何识别 | `src/services/whisper_client.py` |

### 调试入口

| 调试场景 | 设置断点位置 |
|---------|------------|
| 配置加载问题 | `config_loader.py:ConfigLoader.__init__()` |
| 图谱构建问题 | `data_sync.py:build_knowledge_graph()` |
| 实体抽取问题 | `qwen_client.py:extract_entities_and_relations()` |
| RAGFlow连接问题 | `ragflow_client.py:check_health()` |
| 数据库问题 | `db_manager.py:DatabaseManager.__init__()` |

---

**参考文档**: 
- [02-ARCHITECTURE.md](../02-ARCHITECTURE.md) - 系统架构
- [04-DEVELOPER_GUIDE.md](../04-DEVELOPER_GUIDE.md) - 开发指南
- [05-API_REFERENCE.md](../05-API_REFERENCE.md) - API详细文档
