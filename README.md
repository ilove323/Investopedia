# 政策库知识库+知识图谱系统

一个专注于政策知识管理的智能系统，集成了知识搜索、知识图谱可视化、语音问答等功能，支持专项债、特许经营、数据资产三大政策领域。

## 系统架构

```
┌─────────────────────────────────────────────────┐
│      Streamlit前端应用 (http://localhost:8501)   │
├─────────────────────────────────────────────────┤
│ 页面模块 │ 组件 │ 业务逻辑 │ 知识图谱 │ 数据库 │
│ 搜索    │ UI  │ 元数据  │Network│SQLite│
│ 图谱    │    │ 标签    │Pyvis │      │
│ 语音    │    │ 时效性  │      │      │
│ 文档    │    │ 影响    │      │      │
│ 分析    │    │         │      │      │
└─────────────────────────────────────────────────┘
        │                           │
        ├──────────────────────────┤
        │                          │
┌───────▼──────────┐      ┌────────▼──────────┐
│  RAGFlow服务      │      │  Whisper服务      │
│ (Docker容器)      │      │ (Docker容器)      │
│ 端口: 9380        │      │ 端口: 9000        │
└───────────────────┘      └───────────────────┘
```

## 核心功能

### 1. 政策搜索
- 快速搜索框和高级搜索面板
- 多维度筛选（政策领域、地区、时间、状态）
- 基于RAGFlow的语义搜索
- 搜索结果展示和详情面板

### 2. 知识图谱
- 政策实体和关系可视化
- 多个节点类型（政策、机构、地区、概念、项目）
- 多种关系类型（发布、适用、引用、影响、替代）
- 交互式图谱浏览（缩放、拖拽、点击）

### 3. 语音问答
- 实时语音录制或文件上传
- 基于Whisper的语音识别
- 智能问答和政策推荐
- 历史记录管理

### 4. 文档管理
- 政策文档上传（PDF、DOCX、XLSX）
- 自动元数据提取
- 自动标签生成
- 处理状态跟踪

### 5. 政策分析
- 时效性分析（有效/失效/已更新）
- 影响分析（范围、程度、建议）
- 趋势统计和可视化

## 技术栈

- **前端框架**：Streamlit
- **知识图谱**：NetworkX + Pyvis
- **数据存储**：SQLite
- **外部服务**：
  - RAGFlow（文档处理和AI能力）
  - Whisper（语音转文字）
- **开发语言**：Python 3.8+

## 快速开始

### 1. 环境准备

**创建并激活虚拟环境：**

```bash
# 克隆项目
git clone <repository-url>
cd Investopedia

# 创建虚拟环境（使用项目根目录下的venv目录）
python3 -m venv venv
```

**激活虚拟环境：**

```bash
# Linux / macOS
source venv/bin/activate

# Windows (cmd.exe)
venv\Scripts\activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1
```

激活成功后，命令行提示符会显示 `(venv)` 前缀。

**安装依赖：**

```bash
# 确保已激活虚拟环境
pip install --upgrade pip
pip install -r requirements.txt
```

**停用虚拟环境：**

```bash
deactivate
```

### 2. 配置文件

**复制配置模板创建实际配置文件：**

```bash
cp config/config.ini.template config/config.ini
```

**⚠️ 重要：** 编辑 `config/config.ini` 时，必须注意RAGFlow知识库配置：

```ini
[RAGFLOW]
host = localhost           # RAGFlow服务器地址
port = 9380               # RAGFlow服务端口
api_key =                 # API认证（如需要）

# ⚠️ 知识库配置（必须与RAGFlow中实际创建的知识库名称一致）
kb_name = policy_demo_kb  # 在RAGFlow中手动创建此知识库！
kb_description = 政策知识库 - 专项债/特许经营/数据资产
```

**📖 详见：[RAGFLOW_SETUP.md](RAGFLOW_SETUP.md)** - 完整的RAGFlow前置设置步骤

也可以使用环境变量覆盖配置文件中的值：

```bash
# 设置RAGFlow服务地址（环境变量优先）
export RAGFLOW_HOST=localhost
export RAGFLOW_PORT=9380

# 设置Whisper服务地址（环境变量优先）
export WHISPER_HOST=localhost
export WHISPER_PORT=9000

# 设置DeepSeek API Key（RAGFlow使用）
export DEEPSEEK_API_KEY=your_api_key_here
```

**说明：** 环境变量会优先覆盖 `config.ini` 中的配置。这样可以在不修改文件的情况下快速切换配置（例如在Docker部署时）。

### 3. 启动外部服务

**⚠️ 重要前置步骤（必须先做）：**

在启动应用之前，需要完成RAGFlow的设置：

1. **启动RAGFlow和Whisper容器**
   ```bash
   docker-compose -f docker/docker-compose.ragflow.yml up -d
   docker-compose -f docker/docker-compose.whisper.yml up -d
   ```

2. **在RAGFlow中创建知识库**
   - 访问 http://localhost:9380 登录RAGFlow
   - 创建知识库，名称必须为：`policy_demo_kb`
   - 该名称必须与 config.ini 中的 `kb_name` 一致

3. **验证RAGFlow连接**
   ```bash
   python3 test_ragflow_upload.py
   ```

**详细步骤见：[RAGFLOW_SETUP.md](RAGFLOW_SETUP.md)**

本应用依赖两个外部服务：
- **RAGFlow** (端口 9380) - 用于文档处理和AI能力
- **Whisper** (端口 9000) - 用于语音转文字

请参考 `know-how.md` 中的"外部系统配置"章节了解如何部署这两个服务。

**检查服务状态：**

```bash
# 检查RAGFlow服务
curl http://localhost:9380/api/health

# 检查Whisper服务
curl http://localhost:9000/health
```

应用启动时会自动检查这些服务的可用性，并在侧边栏显示状态。

### 4. 启动应用

```bash
# 运行Streamlit应用
streamlit run app.py

# 应用会在 http://localhost:8501 打开
```

## 项目结构

```
Investopedia/
├── config/                          # 配置目录（仅存放配置文件）
│   ├── config.ini.template         # 配置文件模板
│   └── config.ini                  # 实际配置文件（需复制模板创建）
│
├── src/                            # 源代码
│   ├── config/                     # 配置加载模块
│   │   ├── __init__.py
│   │   └── config_loader.py        # 配置加载器
│   │
│   ├── pages/                      # 页面模块
│   │   ├── search_page.py         # 搜索页
│   │   ├── graph_page.py          # 图谱页
│   │   ├── voice_page.py          # 语音页
│   │   ├── documents_page.py      # 文档管理页
│   │   └── analysis_page.py       # 分析页
│   │
│   ├── components/                 # UI组件
│   │   ├── search_ui.py           # 搜索UI
│   │   ├── graph_ui.py            # 图谱UI
│   │   ├── voice_ui.py            # 语音UI
│   │   └── policy_card.py         # 卡片组件
│   │
│   ├── services/                   # 服务客户端
│   │   ├── ragflow_client.py      # RAGFlow客户端
│   │   ├── whisper_client.py      # Whisper客户端
│   │   └── api_utils.py           # API工具
│   │
│   ├── business/                   # 业务逻辑
│   │   ├── metadata_extractor.py  # 元数据提取
│   │   ├── tag_generator.py       # 标签生成
│   │   ├── validity_checker.py    # 时效性检查
│   │   └── impact_analyzer.py     # 影响分析
│   │
│   ├── models/                     # 数据模型
│   │   ├── policy.py              # 政策模型
│   │   ├── tag.py                 # 标签模型
│   │   └── graph.py               # 图谱模型
│   │
│   ├── database/                   # 数据库操作
│   │   ├── db_manager.py          # 数据库管理器
│   │   ├── policy_dao.py          # 政策DAO
│   │   └── schema.sql             # 表结构
│   │
│   └── utils/                      # 工具函数
│       ├── logger.py              # 日志工具
│       ├── file_utils.py          # 文件工具
│       └── text_utils.py          # 文本工具
│
├── venv/                           # 虚拟环境（已添加到.gitignore）
├── data/                           # 数据目录（已添加到.gitignore）
│   ├── database/                  # SQLite数据库
│   ├── uploads/                   # 上传文件
│   └── graphs/                    # 导出图谱
│
├── logs/                           # 日志目录（已添加到.gitignore）
├── tests/                          # 测试目录
├── app.py                          # 主应用入口
├── requirements.txt                # Python依赖
├── .gitignore                      # Git忽略配置
├── .aiignore                       # AI工具忽略配置
├── README.md                       # 项目说明
└── know-how.md                     # 技术方案文档
```

## 数据库

### 初始化

数据库会在应用启动时自动初始化：

```python
from src.database.db_manager import get_db_manager

db = get_db_manager()
```

### 表结构

- **policies** - 政策表
- **tags** - 标签表（三级标签体系）
- **policy_tags** - 政策-标签关联
- **policy_relations** - 政策关系
- **processing_logs** - 处理日志

### 数据访问

```python
from src.database.policy_dao import get_policy_dao

dao = get_policy_dao()

# 创建政策
policy_id = dao.create_policy({
    'title': '政策标题',
    'document_number': '文号',
    'policy_type': 'special_bonds'
})

# 查询政策
policy = dao.get_policy_by_id(policy_id)

# 添加标签
dao.add_policy_tag(policy_id, tag_id)
```

## 外部服务集成

### RAGFlow

负责文档处理和AI能力：

```python
from src.services.ragflow_client import get_ragflow_client

ragflow = get_ragflow_client()

# 上传文档
doc_id = ragflow.upload_document('path/to/file.pdf', 'file.pdf')

# 搜索
results = ragflow.search('搜索查询')

# 问答
answer = ragflow.ask('提出的问题')
```

### Whisper

负责语音转文字：

```python
from src.services.whisper_client import get_whisper_client

whisper = get_whisper_client()

# 转写音频文件
result = whisper.transcribe('path/to/audio.mp3')

# 提取文本
text = whisper.extract_text(result)
```

## 配置示例

### 配置文件 (config/config.ini)

配置系统使用两层配置：
1. **配置文件** - `config/config.ini` (从 `config.ini.template` 复制)
2. **环境变量** - 环境变量会优先覆盖配置文件

```ini
# 应用配置示例
[APP]
debug = false
default_language = zh

# RAGFlow配置示例
[RAGFLOW]
host = localhost
port = 9380
timeout = 30
deepseek_api_key = your_api_key_here

# Whisper配置示例
[WHISPER]
host = localhost
port = 9000
timeout = 60

# 数据库配置示例
[DATABASE]
sqlite_path = data/database/policy.db
auto_create_tables = true
```

### 环境变量覆盖

```bash
# 这些环境变量会覆盖配置文件中的对应值
export RAGFLOW_HOST=remote.server.com
export RAGFLOW_PORT=9380
export DEEPSEEK_API_KEY=your_api_key_here
export WHISPER_HOST=192.168.1.100
export WHISPER_PORT=9000
```

### Python代码中使用配置

```python
from src.config import get_config

config = get_config()

# 访问各个配置值
host = config.ragflow_host
port = config.ragflow_port
timeout = config.ragflow_timeout

# 或使用低级API
value = config.get("RAGFLOW", "host")
int_value = config.get_int("RAGFLOW", "port")
bool_value = config.get_bool("APP", "debug")
list_value = config.get_list("APP", "allowed_file_types")
```

## 使用示例

### 1. 上传政策文档

1. 打开应用在"文档管理"页面
2. 点击"上传文档"按钮
3. 选择PDF/DOCX文件
4. 等待处理完成（自动提取元数据、生成标签、更新图谱）

### 2. 搜索政策

1. 在"政策搜索"页面
2. 输入搜索关键词
3. 可选：使用高级筛选条件
4. 查看搜索结果和详情

### 3. 语音问答

1. 在"语音问答"页面
2. 点击"开始录音"或"上传音频"
3. 说出问题
4. 查看识别文本和答案

### 4. 浏览知识图谱

1. 在"知识图谱"页面
2. 选择视图（全局/子图/时间线）
3. 选择布局算法
4. 与图谱交互（拖拽、缩放、点击）

## 开发指南

### 添加新的页面

1. 在 `src/pages/` 中创建新文件
2. 实现页面函数
3. 在 `app.py` 中注册页面

```python
# src/pages/new_page.py
def show():
    st.title("新页面")
    # 页面内容
```

### 添加新的业务逻辑

1. 在 `src/business/` 中创建新文件
2. 实现业务逻辑类
3. 在需要的地方导入使用

```python
# src/business/new_logic.py
class NewLogic:
    def process(self, data):
        # 处理逻辑
        return result
```

### 添加数据库表

1. 在 `src/database/schema.sql` 中添加表定义
2. 在 `src/database/db_manager.py` 中添加初始化逻辑
3. 创建对应的DAO类

## 测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_services/

# 生成覆盖率报告
pytest --cov=src tests/
```

## 常见问题

### Q: RAGFlow服务连接失败
A: 检查Docker是否运行，端口是否正确，firewall是否阻止

### Q: 语音识别不工作
A: 确保Whisper服务正在运行，检查音频格式是否支持

### Q: 数据库锁定错误
A: 检查是否有多个应用实例访问同一个数据库，增加超时时间

## 贡献

欢迎提交问题和建议！

## 许可证

[选择合适的许可证]

## 联系方式

如有问题，请通过以下方式联系：
- GitHub Issues
- Email: [your-email]

---

**最后更新**: 2024年

**版本**: 1.0.0-beta
