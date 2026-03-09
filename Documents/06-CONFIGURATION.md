# ⚙️ 配置详解

> 系统配置完整参考文档  
> 阅读时间: 15分钟

---

## 📋 目录

- [配置文件结构](#配置文件结构)
- [配置项详解](#配置项详解)
- [环境变量](#环境变量)
- [配置优先级](#配置优先级)
- [常见配置场景](#常见配置场景)
- [配置验证](#配置验证)
- [故障排查](#故障排查)

---

## 📁 配置文件结构

```
config/
├── config.ini                 # 主配置文件（gitignore）
├── config.ini.template        # 配置模板（提交到Git）
├── chat_assistant_config.ini  # Chat Assistant配置
└── prompts/                   # 提示词模板
    ├── entity_extraction.txt  # 实体抽取提示词
    └── summarize_policy.txt   # 政策摘要提示词
```

---

## 🔧 配置项详解

### [APP] - 应用配置

```ini
[APP]
# 应用名称
app_name = Investopedia

# 应用版本
app_version = 1.0.0

# 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
log_level = INFO

# 日志文件路径
log_file = logs/app.log

# 数据库文件路径
database_path = data/database/policies.db

# 上传文件保存目录
upload_dir = data/uploads

# 图谱导出目录
graph_export_dir = data/graphs

# 页面标题
page_title = 政策知识库系统

# 页面图标
page_icon = 📚

# 布局模式: centered, wide
layout = wide

# 侧边栏默认状态: auto, expanded, collapsed
sidebar_state = expanded
```

**说明**:
- `log_level`: 开发环境建议DEBUG，生产环境建议INFO或WARNING
- `layout`: wide布局适合图谱等需要大屏幕的页面
- `sidebar_state`: auto让Streamlit自动决定

---

### [RAGFLOW] - RAGFlow配置

```ini
[RAGFLOW]
# RAGFlow API地址
api_url = http://localhost:9380

# RAGFlow API密钥
# 获取方式: RAGFlow Web界面 → 设置 → API密钥
api_key = ragflow-your-api-key-here

# 默认知识库名称
kb_name = policy_demo_kb

# API请求超时时间（秒）
api_timeout = 30

# 最大重试次数
max_retries = 3

# 重试间隔（秒）
retry_delay = 1

# 检索时返回的最大文档数
retrieve_top_k = 5

# 检索相似度阈值 (0.0-1.0)
# 低于此阈值的文档将被过滤
similarity_threshold = 0.3
```

**获取API密钥**:
```bash
# 1. 启动RAGFlow
docker compose -f docker/docker-compose.ragflow.yml up -d

# 2. 访问 http://localhost:9380
# 3. 登录（默认用户名: admin, 密码: admin）
# 4. 进入"设置" → "API密钥" → "创建密钥"
# 5. 复制密钥到配置文件
```

**知识库配置**:
- 知识库需要在RAGFlow Web界面手动创建
- `kb_name`必须与RAGFlow中的知识库名称完全匹配
- 支持多知识库：可在运行时切换

**性能调优**:
- `api_timeout`: 大文档检索可能需要更长时间，建议30-60秒
- `retrieve_top_k`: 数量越大结果越全面，但速度越慢，建议5-10
- `similarity_threshold`: 阈值越高结果越精准，但可能遗漏相关文档，建议0.2-0.5

---

### [QWEN] - Qwen大模型配置

```ini
[QWEN]
# DashScope API密钥
# 获取方式: https://dashscope.aliyun.com → API-KEY管理
api_key = sk-your-qwen-api-key-here

# 模型名称
# 可选值: qwen-turbo, qwen-plus, qwen-max
model = qwen-plus

# 温度参数 (0.0-2.0)
# 越低越稳定，越高越有创造性
temperature = 0.1

# 最大生成Token数
max_tokens = 2000

# Top-P采样 (0.0-1.0)
top_p = 0.9

# 提示词模板文件路径
prompt_file = config/prompts/entity_extraction.txt

# API请求超时时间（秒）
api_timeout = 60

# 最大重试次数
max_retries = 3
```

**获取API密钥**:
```bash
# 1. 访问 https://dashscope.aliyun.com
# 2. 注册/登录阿里云账号
# 3. 进入"API-KEY管理"
# 4. 创建新密钥
# 5. 复制到配置文件
```

**模型选择**:
- `qwen-turbo`: 最快，成本最低，适合简单任务
- `qwen-plus`: **推荐**，性能和成本平衡
- `qwen-max`: 最强，成本最高，适合复杂推理

**参数调优**:
- `temperature`: 实体抽取建议0.1（稳定输出），创意任务建议0.7-1.0
- `max_tokens`: 根据文档长度调整，建议1500-3000
- `top_p`: 通常保持0.9即可

**成本优化**:
```python
# 估算Token消耗
输入Token = 提示词长度 + 文档长度
输出Token ≈ (实体数 × 50) + (关系数 × 30)

# 示例: 2000字政策文档
输入Token ≈ 500 (提示词) + 2000 (文档) = 2500
输出Token ≈ (12实体 × 50) + (10关系 × 30) = 900
总Token ≈ 3400

# qwen-plus价格: ￥0.004/1K tokens
单文档成本 ≈ 3.4 × 0.004 = ￥0.0136
```

---

### [WHISPER] - 语音识别配置

```ini
[WHISPER]
# OpenAI API密钥
# 获取方式: https://platform.openai.com/api-keys
api_key = sk-your-openai-api-key-here

# 模型名称（目前仅支持whisper-1）
model = whisper-1

# 识别语言（留空为自动检测）
# 可选值: zh, en, ja, etc.
language = zh

# API请求超时时间（秒）
api_timeout = 60

# 最大音频文件大小（MB）
max_file_size = 25
```

**获取API密钥**:
```bash
# 1. 访问 https://platform.openai.com
# 2. 注册/登录账号
# 3. 进入 API Keys
# 4. 创建新密钥
# 5. 复制到配置文件
```

**国内使用**:
- OpenAI API在国内可能需要代理
- 可配置环境变量: `export HTTPS_PROXY=http://127.0.0.1:7890`
- 或使用国内替代服务（如Azure OpenAI）

---

### [CHAT] - Chat Assistant配置

```ini
[CHAT]
# Chat Assistant ID
# 获取方式: RAGFlow Web界面 → Chat Assistant → 查看ID
assistant_id = your-chat-assistant-id-here

# 默认会话ID前缀
session_prefix = session_

# 会话超时时间（小时）
session_timeout = 24

# 是否启用流式输出
stream_mode = true

# 单次对话最大轮数
max_turns = 50
```

**获取Assistant ID**:
```bash
# 1. 访问RAGFlow Web界面
# 2. 进入"Chat Assistant"
# 3. 创建新的Assistant或选择现有的
# 4. 在Assistant详情页查看ID
# 5. 复制到配置文件
```

---

### [DATABASE] - 数据库配置

```ini
[DATABASE]
# 数据库类型: sqlite, postgresql, mysql
db_type = sqlite

# SQLite数据库文件路径
sqlite_path = data/database/policies.db

# PostgreSQL配置（如果使用）
# pg_host = localhost
# pg_port = 5432
# pg_database = investopedia
# pg_user = postgres
# pg_password = password

# 连接池大小
pool_size = 5

# 查询超时时间（秒）
query_timeout = 30

# 是否启用自动初始化
auto_initialize = true
```

**迁移到PostgreSQL** (可选):
```python
# 1. 修改配置
[DATABASE]
db_type = postgresql
pg_host = localhost
pg_port = 5432
pg_database = investopedia
pg_user = your_user
pg_password = your_password

# 2. 修改db_manager.py
def get_connection(self):
    if self.db_type == 'postgresql':
        import psycopg2
        return psycopg2.connect(
            host=self.pg_host,
            port=self.pg_port,
            database=self.pg_database,
            user=self.pg_user,
            password=self.pg_password
        )
    else:
        return sqlite3.connect(self.sqlite_path)
```

---

## 🌍 环境变量

环境变量优先级**高于**配置文件。

### 设置环境变量

**macOS/Linux**:
```bash
# 临时设置（当前终端会话）
export RAGFLOW_API_KEY="ragflow-new-key"
export QWEN_API_KEY="sk-new-key"

# 永久设置（添加到 ~/.bashrc 或 ~/.zshrc）
echo 'export RAGFLOW_API_KEY="ragflow-new-key"' >> ~/.zshrc
source ~/.zshrc
```

**Windows**:
```cmd
# 临时设置
set RAGFLOW_API_KEY=ragflow-new-key

# 永久设置（系统环境变量）
setx RAGFLOW_API_KEY "ragflow-new-key"
```

---

### 环境变量映射

| 环境变量 | 对应配置项 |
|---------|----------|
| `RAGFLOW_HOST` | `[RAGFLOW] host` |
| `RAGFLOW_PORT` | `[RAGFLOW] port` |
| `RAGFLOW_API_KEY` | `[RAGFLOW] api_key` |
| `QWEN_API_KEY` | `[QWEN] api_key` |
| `QWEN_MODEL` | `[QWEN] model` |
| `OPENAI_API_KEY` | `[OPENAI] api_key` |
| `OPENAI_BASE_URL` | `[OPENAI] base_url` |
| `OPENAI_MODEL` | `[OPENAI] model` |
| `LOG_LEVEL` | `[APP] log_level` |

---

### 使用.env文件

```bash
# 创建.env文件
cat > .env << EOF
RAGFLOW_HOST=127.0.0.1
RAGFLOW_PORT=9380
RAGFLOW_API_KEY=ragflow-your-key
QWEN_API_KEY=sk-your-dashscope-key
OPENAI_API_KEY=sk-your-api-key
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_MODEL=qwen-turbo
LOG_LEVEL=DEBUG
EOF

# 添加到.gitignore
echo ".env" >> .gitignore

# 安装python-dotenv
pip install python-dotenv

# 在app.py开头加载
from dotenv import load_dotenv
load_dotenv()
```

---

## 📊 配置优先级

从高到低:

```
1. 环境变量
   ↓
2. config.ini 配置文件
   ↓
3. 代码中的默认值
```

**示例**:
```python
# config.ini
[QWEN]
model = qwen-plus

# 环境变量
export QWEN_MODEL=qwen-max

# 最终生效: qwen-max（环境变量优先）
```

---

## 🎯 常见配置场景

### 场景1: 开发环境

```ini
[APP]
provider = openai   # 使用 OpenAI 兼容接口
debug = true

[RAGFLOW]
host = 127.0.0.1
port = 9380
search_score_threshold = 0.2  # 降低阈值，便于测试

[OPENAI]
base_url = https://dashscope.aliyuncs.com/compatible-mode/v1
api_key = sk-your-key
model = qwen-turbo   # 使用更便宜的模型
max_tokens = 4000
temperature = 0.1
```

---

### 场景2: 生产环境

```ini
[APP]
provider = openai
debug = false

[RAGFLOW]
host = ragflow.yourcompany.com
port = 9380
search_score_threshold = 0.5  # 提高阈值，确保质量

[OPENAI]
base_url = https://dashscope.aliyuncs.com/compatible-mode/v1
api_key = sk-your-key
model = qwen-plus    # 平衡性能和成本
max_tokens = 4000
temperature = 0.1

[DATABASE]
type = sqlite
sqlite_path = data/database/policy.db
```

---

### 场景3: 切换为 DashScope 原生 SDK

```ini
[APP]
# 切换为 DashScope 原生 SDK 调用
provider = qwen

[QWEN]
api_key = sk-your-dashscope-key
model = qwen-turbo
max_tokens = 2000
temperature = 0.1
```

---

### 场景4: 接入本地 Ollama

```ini
[APP]
provider = openai

[OPENAI]
base_url = http://localhost:11434/v1
api_key = ollama
model = qwen2.5:7b
max_tokens = 4000
temperature = 0.1
```

---

## ✅ 配置验证

### 自动验证

系统启动时自动验证配置:

```python
# src/config/config_loader.py
def validate(self):
    """验证配置"""
    errors = []
    
    # 检查必需配置项
    if not self.ragflow_api_key:
        errors.append("缺少 RAGFLOW_API_KEY")
    
    if not self.qwen_api_key:
        errors.append("缺少 QWEN_API_KEY")
    
    # 检查路径是否存在
    if not os.path.exists(self.database_path):
        errors.append(f"数据库路径不存在: {self.database_path}")
    
    # 检查数值范围
    if not (0.0 <= self.qwen_temperature <= 2.0):
        errors.append("QWEN temperature 必须在 0.0-2.0 之间")
    
    if errors:
        raise ConfigurationError("\n".join(errors))
```

---

### 手动验证

```bash
# 运行配置验证脚本
python -c "
from src.config import get_config
config = get_config()
config.validate()
print('✅ 配置验证通过！')
"

# 测试RAGFlow连接
python -c "
from src.clients.ragflow_client import get_ragflow_client
client = get_ragflow_client()
health = client.check_health()
print(f'RAGFlow状态: {health}')
"

# 测试Qwen DashScope 连接
python3 -c "
from src.clients.qwen_client import get_llm_client
client = get_llm_client()
result = client.generate([{'role': 'user', 'content': 'hi'}], max_tokens=10)
print(f'LLM 客户端正常: {result}')
"
```

---

## 🔍 故障排查

### 问题1: RAGFlow连接失败

**症状**:
```
ConnectionError: Failed to connect to RAGFlow API
```

**排查步骤**:
```bash
# 1. 检查RAGFlow服务是否启动
docker ps | grep ragflow

# 2. 测试API连接
curl http://localhost:9380/api/health

# 3. 检查配置
cat config/config.ini | grep -A5 "\[RAGFLOW\]"

# 4. 检查API密钥
# RAGFlow Web界面 → 设置 → API密钥 → 验证
```

---

### 问题2: Qwen API调用失败

**症状**:
```
InvalidApiKeyError: Invalid API key
```

**排查步骤**:
```bash
# 1. 验证API密钥
echo $QWEN_API_KEY

# 2. 测试API
curl -X POST https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation \
  -H "Authorization: Bearer $QWEN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen-turbo","input":{"messages":[{"role":"user","content":"你好"}]}}'

# 3. 检查账户余额
# 访问 https://dashscope.console.aliyun.com → 账户余额
```

---

### 问题3: 知识图谱构建慢

**症状**:
```
构建40个文档需要5-10分钟
```

**优化方案**:
```ini
# 1. 使用更快的模型
[QWEN]
model = qwen-turbo  # 从qwen-plus降级

# 2. 减少Token数
max_tokens = 1500  # 从2000降低

# 3. 启用增量构建
# 在UI中选择"增量构建"而非"全量构建"

# 4. 并行处理（需修改代码）
# 在data_sync.py中使用ThreadPoolExecutor
```

---

### 问题4: 配置文件不生效

**症状**:
```
修改config.ini后，系统仍使用旧配置
```

**解决方法**:
```bash
# 1. 检查是否有环境变量覆盖
env | grep RAGFLOW
env | grep QWEN

# 2. 重启Streamlit
# Ctrl+C 停止
streamlit run app.py

# 3. 清除Streamlit缓存
streamlit cache clear

# 4. 检查配置文件路径
python -c "
from src.config import get_config
config = get_config()
print(f'配置文件: {config.config_file}')
print(f'API URL: {config.ragflow_api_url}')
"
```

---

## 🔗 相关文档

- [QUICK_START.md](QUICK_START.md) - 快速开始
- [02-ARCHITECTURE.md](02-ARCHITECTURE.md) - 系统架构
- [04-DEVELOPER_GUIDE.md](04-DEVELOPER_GUIDE.md) - 开发者指南
- [RAGFlow官方文档](https://ragflow.io/docs)
- [Qwen API文档](https://help.aliyun.com/zh/dashscope/)

---

**Last Updated**: 2026-02-01  
**Version**: 1.0  
**Maintainer**: Configuration Team
