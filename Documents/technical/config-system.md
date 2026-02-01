# ⚙️ 配置系统详解

> ConfigLoader完整解析和最佳实践  
> 阅读时间: 15分钟

---

## 🎯 设计理念

ConfigLoader采用**分层配置、环境覆盖**的设计理念：

```
1. 代码默认值 (最低优先级)
   ↓
2. config.ini配置文件
   ↓
3. 环境变量 (最高优先级)
```

**优势**:
- ✅ 开发/生产环境无缝切换
- ✅ 敏感信息（API密钥）不入库
- ✅ CI/CD友好
- ✅ 类型安全

---

## 📁 配置文件结构

### config.ini完整模板

```ini
[APP]
app_name = Investopedia
app_version = 1.0.0
log_level = INFO
log_file = logs/app.log
database_path = data/database/policies.db
upload_dir = data/uploads
graph_export_dir = data/graphs

[RAGFLOW]
api_url = http://localhost:9380
api_key = ragflow-your-api-key
kb_name = policy_demo_kb
api_timeout = 30
max_retries = 3
retrieve_top_k = 5
similarity_threshold = 0.3

[QWEN]
api_key = sk-your-qwen-api-key
model = qwen-plus
temperature = 0.1
max_tokens = 2000
top_p = 0.9
prompt_file = config/prompts/entity_extraction.txt

[WHISPER]
api_key = sk-your-openai-api-key
model = whisper-1
language = zh
api_timeout = 60
max_file_size = 25

[CHAT]
assistant_id = your-chat-assistant-id
session_prefix = session_
session_timeout = 24
stream_mode = true
max_turns = 50

[DATABASE]
db_type = sqlite
sqlite_path = data/database/policies.db
pool_size = 5
query_timeout = 30
auto_initialize = true
```

---

## 🔧 ConfigLoader实现

### 核心代码

```python
# src/config/config_loader.py
import os
import configparser
from pathlib import Path
from typing import Optional, Any

class ConfigLoader:
    """
    统一配置管理类
    
    特性:
    - 读取INI配置文件
    - 环境变量覆盖
    - 类型自动转换
    - 路径自动创建
    - 配置验证
    """
    
    def __init__(self, config_file: str = 'config/config.ini'):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        
        # 读取配置文件
        if os.path.exists(config_file):
            self.config.read(config_file, encoding='utf-8')
        else:
            raise FileNotFoundError(f"配置文件不存在: {config_file}")
        
        # 验证配置
        self.validate()
        
        # 创建必需的目录
        self._ensure_directories()
    
    def get(self, section: str, key: str, default: Any = None) -> Optional[str]:
        """
        获取配置值（优先使用环境变量）
        
        查找顺序:
        1. 环境变量: {SECTION}_{KEY} (大写，下划线分隔)
        2. config.ini: [section] key
        3. default参数
        """
        # 环境变量名: RAGFLOW_API_KEY
        env_key = f"{section}_{key}".upper()
        env_value = os.getenv(env_key)
        
        if env_value is not None:
            return env_value
        
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default
    
    def get_int(self, section: str, key: str, default: int = 0) -> int:
        """获取整数配置"""
        value = self.get(section, key, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def get_float(self, section: str, key: str, default: float = 0.0) -> float:
        """获取浮点数配置"""
        value = self.get(section, key, default)
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def get_bool(self, section: str, key: str, default: bool = False) -> bool:
        """获取布尔配置"""
        value = self.get(section, key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return default
    
    def get_path(self, section: str, key: str, default: str = '') -> Path:
        """获取路径配置（自动转换为Path对象）"""
        value = self.get(section, key, default)
        return Path(value) if value else Path(default)
    
    def validate(self):
        """验证必需配置项"""
        errors = []
        
        # 必需的配置项
        required_configs = [
            ('RAGFLOW', 'api_url'),
            ('RAGFLOW', 'api_key'),
            ('RAGFLOW', 'kb_name'),
            ('QWEN', 'api_key'),
        ]
        
        for section, key in required_configs:
            value = self.get(section, key)
            if not value or value == f'your-{key}':
                errors.append(f"缺少配置: [{section}] {key}")
        
        if errors:
            error_msg = "\n".join(errors)
            raise ValueError(f"配置验证失败:\n{error_msg}")
    
    def _ensure_directories(self):
        """创建必需的目录"""
        dirs = [
            self.get_path('APP', 'upload_dir'),
            self.get_path('APP', 'graph_export_dir'),
            Path(self.get('APP', 'log_file')).parent,
            Path(self.get('APP', 'database_path')).parent,
        ]
        
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    # ===== APP配置属性 =====
    
    @property
    def app_name(self) -> str:
        return self.get('APP', 'app_name', 'Investopedia')
    
    @property
    def log_level(self) -> str:
        return self.get('APP', 'log_level', 'INFO')
    
    @property
    def log_file(self) -> str:
        return self.get('APP', 'log_file', 'logs/app.log')
    
    @property
    def database_path(self) -> str:
        return self.get('APP', 'database_path', 'data/database/policies.db')
    
    # ===== RAGFLOW配置属性 =====
    
    @property
    def ragflow_api_url(self) -> str:
        return self.get('RAGFLOW', 'api_url')
    
    @property
    def ragflow_api_key(self) -> str:
        return self.get('RAGFLOW', 'api_key')
    
    @property
    def ragflow_kb_name(self) -> str:
        return self.get('RAGFLOW', 'kb_name')
    
    @property
    def ragflow_api_timeout(self) -> int:
        return self.get_int('RAGFLOW', 'api_timeout', 30)
    
    @property
    def ragflow_max_retries(self) -> int:
        return self.get_int('RAGFLOW', 'max_retries', 3)
    
    @property
    def ragflow_retrieve_top_k(self) -> int:
        return self.get_int('RAGFLOW', 'retrieve_top_k', 5)
    
    @property
    def ragflow_similarity_threshold(self) -> float:
        return self.get_float('RAGFLOW', 'similarity_threshold', 0.3)
    
    # ===== QWEN配置属性 =====
    
    @property
    def qwen_api_key(self) -> str:
        return self.get('QWEN', 'api_key')
    
    @property
    def qwen_model(self) -> str:
        return self.get('QWEN', 'model', 'qwen-plus')
    
    @property
    def qwen_temperature(self) -> float:
        return self.get_float('QWEN', 'temperature', 0.1)
    
    @property
    def qwen_max_tokens(self) -> int:
        return self.get_int('QWEN', 'max_tokens', 2000)
    
    @property
    def qwen_top_p(self) -> float:
        return self.get_float('QWEN', 'top_p', 0.9)
    
    @property
    def qwen_prompt_file(self) -> str:
        return self.get('QWEN', 'prompt_file', 'config/prompts/entity_extraction.txt')
    
    # ===== WHISPER配置属性 =====
    
    @property
    def whisper_api_key(self) -> str:
        return self.get('WHISPER', 'api_key')
    
    @property
    def whisper_model(self) -> str:
        return self.get('WHISPER', 'model', 'whisper-1')
    
    @property
    def whisper_language(self) -> str:
        return self.get('WHISPER', 'language', 'zh')
    
    # ===== CHAT配置属性 =====
    
    @property
    def chat_assistant_id(self) -> str:
        return self.get('CHAT', 'assistant_id')
    
    @property
    def chat_stream_mode(self) -> bool:
        return self.get_bool('CHAT', 'stream_mode', True)


# 单例模式
_config_instance = None

def get_config() -> ConfigLoader:
    """获取ConfigLoader单例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigLoader()
    return _config_instance
```

---

## 🌍 环境变量使用

### 开发环境
```bash
# .env.development
export LOG_LEVEL=DEBUG
export RAGFLOW_API_URL=http://localhost:9380
export RAGFLOW_KB_NAME=test_kb
export QWEN_MODEL=qwen-turbo  # 使用便宜的模型
```

### 生产环境
```bash
# .env.production
export LOG_LEVEL=WARNING
export RAGFLOW_API_URL=https://ragflow.company.com
export RAGFLOW_API_KEY=ragflow-prod-key
export RAGFLOW_KB_NAME=production_kb
export QWEN_MODEL=qwen-plus
export DATABASE_PATH=/var/lib/investopedia/policies.db
```

### CI/CD环境
```yaml
# .github/workflows/test.yml
env:
  LOG_LEVEL: DEBUG
  RAGFLOW_API_URL: ${{ secrets.RAGFLOW_API_URL }}
  RAGFLOW_API_KEY: ${{ secrets.RAGFLOW_API_KEY }}
  QWEN_API_KEY: ${{ secrets.QWEN_API_KEY }}
```

---

## 🔐 敏感信息管理

### ❌ 不要做
```bash
# 不要在config.ini中硬编码API密钥
[QWEN]
api_key = sk-1234567890abcdef  # ❌ 会被提交到Git！
```

### ✅ 推荐做法
```bash
# 1. 在config.ini中使用占位符
[QWEN]
api_key = your-qwen-api-key

# 2. 在.gitignore中忽略实际配置
echo "config/config.ini" >> .gitignore

# 3. 使用环境变量
export QWEN_API_KEY=sk-real-key

# 4. 或使用.env文件
echo "QWEN_API_KEY=sk-real-key" >> .env
echo ".env" >> .gitignore
```

---

## 🧪 配置测试

### 单元测试
```python
# tests/test_config.py
import pytest
from src.config import get_config

def test_config_singleton():
    """测试单例模式"""
    config1 = get_config()
    config2 = get_config()
    assert config1 is config2

def test_env_variable_override(monkeypatch):
    """测试环境变量覆盖"""
    monkeypatch.setenv('QWEN_MODEL', 'qwen-max')
    config = get_config()
    assert config.qwen_model == 'qwen-max'

def test_type_conversion():
    """测试类型转换"""
    config = get_config()
    assert isinstance(config.ragflow_api_timeout, int)
    assert isinstance(config.qwen_temperature, float)
    assert isinstance(config.chat_stream_mode, bool)

def test_validation_missing_required():
    """测试缺少必需配置"""
    with pytest.raises(ValueError, match="缺少配置"):
        config = ConfigLoader('invalid_config.ini')
```

---

## 📖 使用示例

### 在服务中使用
```python
# src/services/qwen_client.py
from src.config import get_config

class QwenClient:
    def __init__(self):
        config = get_config()
        
        self.api_key = config.qwen_api_key
        self.model = config.qwen_model
        self.temperature = config.qwen_temperature
        self.max_tokens = config.qwen_max_tokens
        
        # 加载提示词模板
        with open(config.qwen_prompt_file, 'r') as f:
            self.prompt_template = f.read()
```

### 动态切换配置
```python
# 在运行时切换知识库
import os
os.environ['RAGFLOW_KB_NAME'] = 'another_kb'

# 需要重新加载ConfigLoader（当前实现为单例，需要重启）
# 或修改为支持reload()方法
```

---

## 🔗 相关文档

- [06-CONFIGURATION.md](../06-CONFIGURATION.md) - 配置详解
- [04-DEVELOPER_GUIDE.md](../04-DEVELOPER_GUIDE.md) - 开发者指南

---

**Last Updated**: 2026-02-01
