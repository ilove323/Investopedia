# 🛠️ 开发者指南

> 为开发者提供的完整开发文档  
> 阅读时间: 30分钟

---

## 📋 目录

- [开发环境搭建](#开发环境搭建)
- [项目结构](#项目结构)
- [核心模块开发](#核心模块开发)
- [添加新功能](#添加新功能)
- [测试指南](#测试指南)
- [调试技巧](#调试技巧)
- [代码规范](#代码规范)
- [发布流程](#发布流程)

---

## 🚀 开发环境搭建

### 前置要求
```bash
Python >= 3.9
pip >= 21.0
virtualenv (推荐)
```

### 克隆项目
```bash
git clone <repository-url>
cd Investopedia
```

### 创建虚拟环境
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### 安装依赖
```bash
pip install -r requirements.txt
```

**核心依赖**:
```
streamlit==1.28.0        # Web框架
ragflow-sdk>=0.13.0      # RAGFlow客户端
dashscope                # Qwen API
openai                   # Whisper API
networkx==3.1            # 图算法
pyvis==0.3.2             # 图可视化
pandas                   # 数据处理
jieba                    # 中文分词
```

### 配置系统
```bash
# 复制配置模板
cp config/config.ini.template config/config.ini

# 编辑配置文件（填写API密钥）
vim config/config.ini
```

**必需配置**:
```ini
[RAGFLOW]
api_url = http://localhost:9380
api_key = ragflow-your-api-key
kb_name = policy_demo_kb

[QWEN]
api_key = sk-your-qwen-api-key

[CHAT]
assistant_id = your-chat-assistant-id
```

### 初始化数据库
```bash
python -c "from src.database.db_manager import get_db_manager; get_db_manager().initialize_database()"
```

### 启动开发服务器
```bash
streamlit run app.py
```

访问 `http://localhost:8501`

---

## 📁 项目结构

```
Investopedia/
├── app.py                      # 🔥 应用入口
├── requirements.txt            # 依赖清单
├── config/                     # ⚙️ 配置文件
│   ├── config.ini              # 主配置文件（gitignore）
│   ├── config.ini.template     # 配置模板
│   └── prompts/                # 提示词模板
│       └── entity_extraction.txt
├── src/                        # 📦 源代码
│   ├── __init__.py
│   ├── pages/                  # 📄 页面模块
│   │   ├── search_page.py
│   │   ├── chat_page.py
│   │   ├── graph_page.py
│   │   ├── voice_page.py
│   │   ├── documents_page.py
│   │   └── analysis_page.py
│   ├── components/             # 🎨 UI组件
│   │   ├── graph_ui.py
│   │   ├── search_ui.py
│   │   ├── voice_ui.py
│   │   └── policy_card.py
│   ├── services/               # 🔌 服务层
│   │   ├── ragflow_client.py   # RAGFlow封装
│   │   ├── qwen_client.py      # Qwen封装
│   │   ├── chat_service.py     # Chat Assistant
│   │   ├── data_sync.py        # 数据同步（核心）
│   │   └── whisper_client.py   # 语音识别
│   ├── database/               # 🗄️ 数据访问层
│   │   ├── db_manager.py
│   │   ├── policy_dao.py
│   │   ├── graph_dao.py
│   │   └── schema.sql
│   ├── models/                 # 📊 数据模型
│   │   ├── policy.py
│   │   ├── graph.py
│   │   └── tag.py
│   ├── business/               # 💼 业务逻辑
│   │   ├── validity_checker.py
│   │   ├── impact_analyzer.py
│   │   ├── tag_generator.py
│   │   └── metadata_extractor.py
│   ├── config/                 # ⚙️ 配置管理
│   │   └── config_loader.py
│   └── utils/                  # 🛠️ 工具函数
│       ├── logger.py
│       ├── file_utils.py
│       └── summarizer.py
├── data/                       # 📁 数据目录
│   ├── database/               # SQLite数据库
│   ├── uploads/                # 上传文件
│   └── graphs/                 # 图谱导出
├── logs/                       # 📝 日志文件
├── tests/                      # 🧪 测试代码
└── Documents/                  # 📚 文档
```

---

## 🔧 核心模块开发

### 1. 页面开发 (`src/pages/`)

#### 创建新页面
```python
# src/pages/new_feature_page.py
import streamlit as st
from src.services.some_service import get_some_service

def show():
    """
    新功能页面
    """
    st.title("🆕 新功能")
    
    # 使用session_state管理状态
    if 'new_feature_data' not in st.session_state:
        st.session_state.new_feature_data = None
    
    # 用户输入
    user_input = st.text_input("输入参数")
    
    # 调用服务层
    if st.button("执行"):
        service = get_some_service()
        result = service.process(user_input)
        st.session_state.new_feature_data = result
    
    # 显示结果
    if st.session_state.new_feature_data:
        st.write(st.session_state.new_feature_data)
```

#### 注册页面到app.py
```python
# app.py
from src.pages import new_feature_page

pages = {
    "新功能": new_feature_page,
    # ... 其他页面
}
```

---

### 2. 服务层开发 (`src/services/`)

#### 创建新服务
```python
# src/services/new_service.py
from src.config import get_config
from typing import Dict, List

class NewService:
    """
    新服务功能描述
    """
    def __init__(self):
        self.config = get_config()
        self.api_url = self.config.new_service_api_url
        self.api_key = self.config.new_service_api_key
    
    def process(self, input_data: str) -> Dict:
        """
        处理业务逻辑
        
        Args:
            input_data: 输入数据
            
        Returns:
            处理结果字典
        """
        try:
            # 实现业务逻辑
            result = self._call_external_api(input_data)
            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _call_external_api(self, data: str):
        """私有方法：调用外部API"""
        # 实现API调用
        pass

# 单例模式
_instance = None

def get_new_service() -> NewService:
    """获取NewService单例"""
    global _instance
    if _instance is None:
        _instance = NewService()
    return _instance
```

#### 使用服务
```python
from src.services.new_service import get_new_service

service = get_new_service()
result = service.process("input")
```

---

### 3. 数据访问层开发 (`src/database/`)

#### 创建新DAO
```python
# src/database/new_dao.py
from src.database.db_manager import get_db_manager
from typing import List, Dict, Optional

class NewDAO:
    """
    新数据表的DAO
    """
    def __init__(self):
        self.db_manager = get_db_manager()
    
    def create(self, data: Dict) -> int:
        """
        创建新记录
        
        Args:
            data: 数据字典
            
        Returns:
            新记录的ID
        """
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO new_table (field1, field2, field3)
                VALUES (?, ?, ?)
            """, (data['field1'], data['field2'], data['field3']))
            
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
    
    def get_by_id(self, record_id: int) -> Optional[Dict]:
        """根据ID查询记录"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM new_table WHERE id = ?
            """, (record_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'field1': row[1],
                    'field2': row[2],
                    # ...
                }
            return None
        finally:
            cursor.close()
            conn.close()
    
    def update(self, record_id: int, data: Dict):
        """更新记录"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE new_table
                SET field1 = ?, field2 = ?
                WHERE id = ?
            """, (data['field1'], data['field2'], record_id))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
    
    def delete(self, record_id: int):
        """删除记录"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM new_table WHERE id = ?", (record_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

# 单例模式
_instance = None

def get_new_dao() -> NewDAO:
    global _instance
    if _instance is None:
        _instance = NewDAO()
    return _instance
```

#### 添加数据表到schema.sql
```sql
-- src/database/schema.sql
CREATE TABLE IF NOT EXISTS new_table (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field1 TEXT NOT NULL,
    field2 INTEGER,
    field3 REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_new_table_field1 ON new_table(field1);
```

---

### 4. 业务逻辑层开发 (`src/business/`)

#### 创建业务分析器
```python
# src/business/new_analyzer.py
from src.models.policy import Policy
from typing import Dict, List

class NewAnalyzer:
    """
    新的业务分析器
    """
    def analyze(self, policy: Policy) -> Dict:
        """
        分析政策
        
        Args:
            policy: Policy对象
            
        Returns:
            分析结果字典
        """
        result = {
            'score': self._calculate_score(policy),
            'category': self._classify(policy),
            'insights': self._extract_insights(policy)
        }
        return result
    
    def _calculate_score(self, policy: Policy) -> float:
        """计算评分"""
        # 实现评分逻辑
        score = 0.0
        # ...
        return score
    
    def _classify(self, policy: Policy) -> str:
        """分类"""
        # 实现分类逻辑
        return "category_name"
    
    def _extract_insights(self, policy: Policy) -> List[str]:
        """提取洞察"""
        insights = []
        # 实现洞察提取逻辑
        return insights
```

---

## 🆕 添加新功能

### 场景1: 添加新的外部API集成

**需求**: 集成新的向量数据库API

**步骤**:

1. **添加配置项** (`config/config.ini`):
```ini
[NEW_VECTOR_DB]
api_url = https://api.newvectordb.com
api_key = your-api-key
index_name = policies
```

2. **更新ConfigLoader** (`src/config/config_loader.py`):
```python
@property
def new_vector_db_api_url(self) -> str:
    return self.get('NEW_VECTOR_DB', 'api_url')

@property
def new_vector_db_api_key(self) -> str:
    return self.get('NEW_VECTOR_DB', 'api_key')
```

3. **创建客户端** (`src/services/new_vector_db_client.py`):
```python
import requests
from src.config import get_config

class NewVectorDBClient:
    def __init__(self):
        config = get_config()
        self.api_url = config.new_vector_db_api_url
        self.api_key = config.new_vector_db_api_key
    
    def search(self, query: str, top_k: int = 5):
        """向量检索"""
        response = requests.post(
            f"{self.api_url}/search",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"query": query, "top_k": top_k}
        )
        return response.json()

_instance = None
def get_new_vector_db_client():
    global _instance
    if _instance is None:
        _instance = NewVectorDBClient()
    return _instance
```

4. **使用客户端** (在页面或服务中):
```python
from src.services.new_vector_db_client import get_new_vector_db_client

client = get_new_vector_db_client()
results = client.search("政策问题")
```

---

### 场景2: 添加新的分析功能

**需求**: 添加政策风险评估功能

**步骤**:

1. **创建分析器** (`src/business/risk_analyzer.py`):
```python
from src.models.policy import Policy
from typing import Dict

class RiskAnalyzer:
    def assess_risk(self, policy: Policy) -> Dict:
        """评估政策风险"""
        risk_score = self._calculate_risk_score(policy)
        risk_level = self._determine_risk_level(risk_score)
        
        return {
            'score': risk_score,
            'level': risk_level,
            'factors': self._identify_risk_factors(policy)
        }
    
    def _calculate_risk_score(self, policy: Policy) -> float:
        # 实现评分算法
        return 0.0
    
    def _determine_risk_level(self, score: float) -> str:
        if score < 0.3:
            return "低风险"
        elif score < 0.7:
            return "中风险"
        else:
            return "高风险"
    
    def _identify_risk_factors(self, policy: Policy):
        factors = []
        # 识别风险因素
        return factors
```

2. **创建UI组件** (`src/components/risk_ui.py`):
```python
import streamlit as st

def render_risk_assessment(risk_result: dict):
    """渲染风险评估结果"""
    st.subheader("🎯 风险评估")
    
    # 显示风险等级
    level = risk_result['level']
    color = {"低风险": "green", "中风险": "orange", "高风险": "red"}[level]
    st.markdown(f"**风险等级**: :{color}[{level}]")
    
    # 显示风险评分
    st.metric("风险评分", f"{risk_result['score']:.2f}")
    
    # 显示风险因素
    if risk_result['factors']:
        st.write("**风险因素**:")
        for factor in risk_result['factors']:
            st.write(f"- {factor}")
```

3. **添加到分析页面** (`src/pages/analysis_page.py`):
```python
from src.business.risk_analyzer import RiskAnalyzer
from src.components.risk_ui import render_risk_assessment

def show():
    # ... 现有代码 ...
    
    # 添加风险评估标签页
    tab1, tab2, tab3, tab4 = st.tabs(["时效性", "对比", "趋势", "风险评估"])
    
    with tab4:
        st.header("🎯 政策风险评估")
        selected_policy = st.selectbox("选择政策", policy_list)
        
        if st.button("评估风险"):
            analyzer = RiskAnalyzer()
            risk_result = analyzer.assess_risk(selected_policy)
            render_risk_assessment(risk_result)
```

---

### 场景3: 添加新的数据模型

**需求**: 添加"政策评论"功能

**步骤**:

1. **创建数据模型** (`src/models/comment.py`):
```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PolicyComment:
    id: int
    policy_id: int
    user_name: str
    content: str
    rating: int  # 1-5星
    created_at: datetime
```

2. **更新数据库schema** (`src/database/schema.sql`):
```sql
CREATE TABLE IF NOT EXISTS policy_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_id INTEGER NOT NULL,
    user_name TEXT NOT NULL,
    content TEXT NOT NULL,
    rating INTEGER CHECK(rating >= 1 AND rating <= 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(policy_id) REFERENCES policies(id)
);
```

3. **创建DAO** (`src/database/comment_dao.py`):
```python
from src.database.db_manager import get_db_manager
from src.models.comment import PolicyComment
from typing import List

class CommentDAO:
    def __init__(self):
        self.db_manager = get_db_manager()
    
    def create_comment(self, policy_id: int, user_name: str, 
                      content: str, rating: int) -> int:
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO policy_comments (policy_id, user_name, content, rating)
                VALUES (?, ?, ?, ?)
            """, (policy_id, user_name, content, rating))
            conn.commit()
            return cursor.lastrowid
        finally:
            cursor.close()
            conn.close()
    
    def get_comments_by_policy(self, policy_id: int) -> List[PolicyComment]:
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT * FROM policy_comments 
                WHERE policy_id = ? 
                ORDER BY created_at DESC
            """, (policy_id,))
            rows = cursor.fetchall()
            return [PolicyComment(*row) for row in rows]
        finally:
            cursor.close()
            conn.close()
```

4. **添加到UI** (在政策详情页面):
```python
# 显示评论
comments = comment_dao.get_comments_by_policy(policy_id)
for comment in comments:
    st.write(f"**{comment.user_name}** - {'⭐' * comment.rating}")
    st.write(comment.content)
    st.caption(comment.created_at)

# 添加评论
with st.form("add_comment"):
    user_name = st.text_input("姓名")
    content = st.text_area("评论内容")
    rating = st.slider("评分", 1, 5, 3)
    if st.form_submit_button("提交评论"):
        comment_dao.create_comment(policy_id, user_name, content, rating)
        st.success("评论已提交！")
```

---

## 🧪 测试指南

### 运行测试
```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试文件
python -m pytest tests/test_ragflow_client.py

# 运行特定测试函数
python -m pytest tests/test_ragflow_client.py::test_get_documents

# 显示详细输出
python -m pytest tests/ -v

# 生成覆盖率报告
python -m pytest tests/ --cov=src --cov-report=html
```

### 编写单元测试
```python
# tests/test_new_service.py
import pytest
from src.services.new_service import NewService

@pytest.fixture
def service():
    """测试fixture"""
    return NewService()

def test_process_success(service):
    """测试成功场景"""
    result = service.process("test_input")
    assert result['status'] == 'success'
    assert 'data' in result

def test_process_error(service):
    """测试错误场景"""
    result = service.process("")  # 空输入
    assert result['status'] == 'error'
    assert 'message' in result

@pytest.mark.parametrize("input_data,expected", [
    ("input1", "output1"),
    ("input2", "output2"),
])
def test_process_multiple_inputs(service, input_data, expected):
    """参数化测试"""
    result = service.process(input_data)
    assert result['data'] == expected
```

### 集成测试
```python
# tests/test_integration.py
import pytest
from src.services.data_sync import DataSyncService
from src.database.graph_dao import get_graph_dao

@pytest.mark.integration
def test_full_graph_building_flow():
    """测试完整的图谱构建流程"""
    # 1. 同步文档
    sync_service = DataSyncService()
    sync_result = sync_service.sync_documents_to_database("test_kb")
    assert sync_result['synced_count'] > 0
    
    # 2. 构建图谱
    graph_result = sync_service.build_knowledge_graph("test_kb")
    assert graph_result['node_count'] > 0
    assert graph_result['edge_count'] > 0
    
    # 3. 验证数据库
    graph_dao = get_graph_dao()
    graph_data = graph_dao.load_graph()
    assert graph_data is not None
    assert len(graph_data['nodes']) > 0
```

---

## 🐛 调试技巧

### 日志配置
```python
# src/utils/logger.py
import logging

def setup_logger(name: str, log_file: str = None, level=logging.DEBUG):
    """配置logger"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 控制台handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # 文件handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
    
    # 格式化
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger
```

### 使用日志
```python
from src.utils.logger import setup_logger

logger = setup_logger(__name__, 'logs/my_module.log')

logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息", exc_info=True)  # 包含堆栈信息
```

### Streamlit调试
```python
# 使用st.write调试变量
st.write("调试变量:", variable)

# 使用st.json显示JSON数据
st.json(data_dict)

# 使用st.exception显示异常
try:
    # 代码
    pass
except Exception as e:
    st.exception(e)

# 使用st.write显示session_state
st.write("Session State:", st.session_state)
```

### 性能调试
```python
import time

def time_it(func):
    """装饰器：测量函数执行时间"""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end - start:.2f} seconds")
        return result
    return wrapper

@time_it
def slow_function():
    # 耗时操作
    pass
```

---

## 📏 代码规范

### Python代码风格
遵循 **PEP 8** 规范:

```python
# ✅ 好的代码
def calculate_policy_score(policy: Policy, 
                          weights: Dict[str, float]) -> float:
    """
    计算政策评分
    
    Args:
        policy: Policy对象
        weights: 权重字典，如 {"importance": 0.5, "urgency": 0.3}
        
    Returns:
        评分 (0.0-1.0)
        
    Raises:
        ValueError: 如果权重总和不为1.0
    """
    if sum(weights.values()) != 1.0:
        raise ValueError("权重总和必须为1.0")
    
    score = 0.0
    score += policy.importance * weights.get("importance", 0.0)
    score += policy.urgency * weights.get("urgency", 0.0)
    
    return score


# ❌ 不好的代码
def calc(p,w):  # 函数名太短，参数无类型注解
    s=0  # 变量名不清晰
    # 无文档字符串
    for k in w:
        s+=getattr(p,k)*w[k]
    return s
```

### 命名规范
```python
# 类名：大驼峰
class PolicyAnalyzer:
    pass

# 函数名、变量名：小写+下划线
def calculate_score():
    pass

user_name = "张三"

# 常量：大写+下划线
MAX_RETRIES = 3
API_TIMEOUT = 30

# 私有方法：前缀下划线
def _internal_method():
    pass
```

### 导入规范
```python
# 标准库
import os
import sys
from typing import Dict, List

# 第三方库
import streamlit as st
import pandas as pd

# 本地模块
from src.config import get_config
from src.database import get_policy_dao
```

### 文档字符串
```python
def complex_function(param1: str, param2: int, 
                    param3: bool = False) -> Dict:
    """
    函数简短描述（一行）
    
    更详细的描述（可选），解释函数的用途、算法等。
    可以分多段。
    
    Args:
        param1: 第一个参数的描述
        param2: 第二个参数的描述
        param3: 第三个参数的描述，默认False
        
    Returns:
        返回值描述，如: {"status": "success", "data": {...}}
        
    Raises:
        ValueError: 如果param2小于0
        ConnectionError: 如果无法连接到API
        
    Examples:
        >>> result = complex_function("test", 10)
        >>> print(result['status'])
        'success'
    """
    pass
```

---

## 🚀 发布流程

### 版本号规范
遵循 **语义化版本** (Semantic Versioning):

```
主版本号.次版本号.修订号
例如: 1.2.3

主版本号: 不兼容的API修改
次版本号: 向后兼容的功能性新增
修订号: 向后兼容的bug修复
```

### 发布检查清单
```bash
# 1. 运行测试
python -m pytest tests/

# 2. 检查代码风格
flake8 src/

# 3. 生成requirements.txt
pip freeze > requirements.txt

# 4. 更新文档
# - README.md
# - CHANGELOG.md
# - Documents/

# 5. 提交代码
git add .
git commit -m "Release v1.2.0"
git tag v1.2.0
git push origin main --tags

# 6. 构建Docker镜像（如果需要）
docker build -t investopedia:1.2.0 .
docker tag investopedia:1.2.0 investopedia:latest
```

---

## 🔗 相关文档

- [02-ARCHITECTURE.md](02-ARCHITECTURE.md) - 系统架构
- [05-API_REFERENCE.md](05-API_REFERENCE.md) - API详细文档
- [06-CONFIGURATION.md](06-CONFIGURATION.md) - 配置详解
- [technical/code-structure.md](technical/code-structure.md) - 代码结构
- [technical/modules-inventory.md](technical/modules-inventory.md) - 模块清单

---

**Last Updated**: 2026-02-01  
**Version**: 1.0  
**Maintainer**: Development Team
