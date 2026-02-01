# 测试指南

> **阅读时间**: 15分钟  
> **难度**: ⭐⭐  
> **前置知识**: Python单元测试、pytest基础

---

## 📖 目录

- [概述](#概述)
- [测试框架](#测试框架)
- [测试文件组织](#测试文件组织)
- [运行测试](#运行测试)
- [编写测试](#编写测试)
- [测试覆盖率](#测试覆盖率)
- [CI/CD集成](#cicd集成)
- [常见问题](#常见问题)

---

## 概述

### 测试策略

本项目采用**分层测试策略**：

```
┌─────────────────────────────────────┐
│   E2E测试（端到端）                  │  手动测试为主
├─────────────────────────────────────┤
│   集成测试                           │  test_ragflow_client.py
│   验证多个模块协作                    │  test_data_sync.py
├─────────────────────────────────────┤
│   单元测试                           │  test_chat_service.py
│   验证单个模块功能                    │  test_config_system.py
├─────────────────────────────────────┤
│   工具脚本                           │  clean_duplicate_nodes.py
│   辅助开发和调试                      │  final_verification.py
└─────────────────────────────────────┘
```

### 测试覆盖范围

| 模块 | 测试文件 | 覆盖率 | 状态 |
|------|---------|-------|------|
| **服务层** | test_chat_service.py | 85% | ✅ |
| **服务层** | test_hybrid_retriever.py | 80% | ✅ |
| **数据层** | test_graph_storage.py | 75% | ✅ |
| **配置系统** | test_config_system.py | 90% | ✅ |
| **RAGFlow集成** | test_ragflow_client.py | 70% | ✅ |
| **数据同步** | test_data_sync.py | 85% | ✅ |
| **文档功能** | test_document_*.py | 60% | ⚠️ |

**总体覆盖率**: 约75%

---

## 测试框架

### 使用的测试框架

#### 1. pytest（主要框架）

**优势**:
- ✅ 简洁的测试语法
- ✅ 强大的fixture机制
- ✅ 丰富的插件生态
- ✅ 详细的测试报告

**示例**:
```python
# test_services/test_chat_service.py
import pytest
from src.services.chat_service import ChatService

@pytest.fixture
def chat_service():
    """创建聊天服务实例"""
    return ChatService()

def test_chat_basic(chat_service):
    """测试基本问答功能"""
    response = chat_service.chat("你好")
    assert response is not None
    assert 'answer' in response
```

#### 2. unittest（辅助框架）

**适用场景**: 配置系统测试、传统测试迁移

**示例**:
```python
# test_config_system.py
import unittest
from src.config import get_config

class TestConfigSystem(unittest.TestCase):
    def test_config_loading(self):
        """测试配置加载"""
        config = get_config()
        self.assertIsNotNone(config.ragflow_api_key)
```

#### 3. Mock和Patch

**用于隔离外部依赖**:

```python
from unittest.mock import Mock, patch

@patch('src.services.ragflow_client.RAGFlow')
def test_with_mock(mock_ragflow):
    """使用mock测试，避免真实API调用"""
    mock_ragflow.return_value.list_datasets.return_value = []
    # 测试逻辑
```

---

## 测试文件组织

### 目录结构

```
tests/
├── __init__.py                      # 测试包初始化
├── README.md                        # 快速指南
├── run_tests.py                     # 测试运行器
├── test_runner.sh                   # Bash测试脚本
│
├── test_services/                   # 服务层测试
│   ├── __init__.py
│   ├── test_chat_service.py         # 聊天服务（33个测试）
│   └── test_hybrid_retriever.py     # 混合检索器（11个测试）
│
├── test_config_system.py            # 配置系统测试
├── test_data_sync.py                # 数据同步测试
├── test_graph_storage.py            # 图谱存储测试
├── test_ragflow_client.py           # RAGFlow客户端测试
├── test_ragflow_api_exploration.py  # RAGFlow API测试
├── test_document_list_fix.py        # 文档列表测试
├── test_document_viewer.py          # 文档查看器测试
│
├── clean_duplicate_nodes.py         # 工具：清理重复节点
├── final_verification.py            # 工具：最终验证
│
└── archive/                         # 归档（调试脚本、过时测试）
    ├── debug/
    └── deprecated/
```

### 测试文件命名规范

```
test_<module_name>.py           # 单元测试
test_<feature>_integration.py   # 集成测试
test_<component>_e2e.py          # 端到端测试
```

---

## 运行测试

### 快速运行

#### 方法1：使用pytest（推荐）

```bash
# 运行所有测试
pytest tests/

# 运行特定文件
pytest tests/test_chat_service.py

# 运行特定测试用例
pytest tests/test_chat_service.py::test_chat_basic

# 显示详细输出
pytest tests/ -v

# 显示print输出
pytest tests/ -s

# 失败后停止
pytest tests/ -x

# 并行运行（需安装pytest-xdist）
pytest tests/ -n 4
```

#### 方法2：使用测试脚本

```bash
# 使用Python运行器
python tests/run_tests.py

# 使用Bash脚本（支持模式选择）
./tests/test_runner.sh

# 可选模式：
./tests/test_runner.sh config      # 配置测试
./tests/test_runner.sh ragflow     # RAGFlow测试
./tests/test_runner.sh api         # API测试
./tests/test_runner.sh quick       # 快速测试（跳过慢测试）
./tests/test_runner.sh all         # 所有测试
```

### 运行特定测试集

#### 按标记运行

```bash
# 只运行快速测试
pytest tests/ -m "not slow"

# 只运行集成测试
pytest tests/ -m "integration"

# 跳过需要外部服务的测试
pytest tests/ -m "not external"
```

**在测试中添加标记**:
```python
import pytest

@pytest.mark.slow
def test_full_graph_build():
    """慢速测试：完整图谱构建"""
    pass

@pytest.mark.integration
def test_ragflow_integration():
    """集成测试：RAGFlow集成"""
    pass
```

---

## 编写测试

### 单元测试示例

**测试聊天服务**:

```python
# tests/test_services/test_chat_service.py
import pytest
from src.services.chat_service import ChatService

class TestChatService:
    """聊天服务测试套件"""
    
    @pytest.fixture
    def chat_service(self):
        """创建聊天服务实例"""
        return ChatService()
    
    def test_chat_basic(self, chat_service):
        """测试基本问答"""
        response = chat_service.chat(
            question="专项债券是什么？",
            knowledge_base_name="policy_demo_kb"
        )
        
        assert response is not None
        assert 'answer' in response
        assert len(response['answer']) > 0
    
    def test_chat_with_context(self, chat_service):
        """测试上下文问答"""
        # 第一个问题
        response1 = chat_service.chat("专项债券是什么？")
        conv_id = response1.get('conversation_id')
        
        # 第二个问题（带上下文）
        response2 = chat_service.chat(
            "它的申请条件是什么？",
            conversation_id=conv_id
        )
        
        assert response2 is not None
        assert '申请' in response2['answer'] or '条件' in response2['answer']
    
    @pytest.mark.parametrize("question,expected_keywords", [
        ("专项债券", ["债券", "政策"]),
        ("特许经营", ["特许", "经营"]),
        ("数据资产", ["数据", "资产"])
    ])
    def test_chat_keywords(self, chat_service, question, expected_keywords):
        """参数化测试：关键词检查"""
        response = chat_service.chat(question)
        answer = response['answer']
        
        for keyword in expected_keywords:
            assert keyword in answer, f"答案中应包含'{keyword}'"
```

### Mock测试示例

**测试RAGFlow客户端（避免真实API调用）**:

```python
# tests/test_ragflow_client.py
from unittest.mock import Mock, patch
import pytest
from src.services.ragflow_client import RAGFlowClient

@patch('src.services.ragflow_client.RAGFlow')
class TestRAGFlowClient:
    """RAGFlow客户端测试（使用Mock）"""
    
    def test_health_check(self, mock_ragflow_class):
        """测试健康检查"""
        # 配置mock
        mock_rag = Mock()
        mock_rag.list_datasets.return_value = []
        mock_ragflow_class.return_value = mock_rag
        
        # 测试
        client = RAGFlowClient()
        result = client.check_health()
        
        # 断言
        assert result is True
        mock_rag.list_datasets.assert_called_once()
    
    def test_upload_document(self, mock_ragflow_class):
        """测试文档上传"""
        # 配置mock
        mock_rag = Mock()
        mock_dataset = Mock()
        mock_dataset.upload_document.return_value = {'id': 'doc_123'}
        mock_rag.list_datasets.return_value = [mock_dataset]
        mock_ragflow_class.return_value = mock_rag
        
        # 测试
        client = RAGFlowClient()
        doc_id = client.upload_document('/path/to/file.pdf', 'file.pdf')
        
        # 断言
        assert doc_id == 'doc_123'
```

### 集成测试示例

**测试数据同步流程**:

```python
# tests/test_data_sync.py
import pytest
from src.services.data_sync import DataSyncService

@pytest.mark.integration
class TestDataSyncIntegration:
    """数据同步集成测试"""
    
    @pytest.fixture
    def sync_service(self):
        """创建数据同步服务"""
        return DataSyncService()
    
    def test_full_sync_flow(self, sync_service):
        """测试完整同步流程"""
        # 1. 同步文档
        result = sync_service.sync_documents()
        assert result['success'] is True
        
        # 2. 验证数据库
        from src.database.policy_dao import PolicyDAO
        dao = PolicyDAO()
        policies = dao.get_all_policies()
        assert len(policies) > 0
        
        # 3. 验证RAGFlow关联
        for policy in policies:
            assert policy['ragflow_doc_id'] is not None
```

---

## 测试覆盖率

### 生成覆盖率报告

```bash
# 安装coverage
pip install pytest-cov

# 运行测试并生成覆盖率
pytest tests/ --cov=src --cov-report=html

# 查看HTML报告
open htmlcov/index.html
```

### 覆盖率配置

**文件**: `.coveragerc`

```ini
[run]
source = src
omit =
    */tests/*
    */venv/*
    */__pycache__/*

[report]
precision = 2
show_missing = True
skip_covered = False

[html]
directory = htmlcov
```

### 覆盖率目标

```
目标覆盖率：
- 核心服务层：>= 80%
- 数据访问层：>= 75%
- 业务逻辑层：>= 70%
- 总体覆盖率：>= 75%
```

---

## CI/CD集成

### GitHub Actions配置

**文件**: `.github/workflows/tests.yml`

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest tests/ --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml
```

---

## 常见问题

### Q1: 测试运行失败，提示"ModuleNotFoundError"？

**解决方案**:
```bash
# 确保在项目根目录运行
cd /path/to/Investopedia

# 设置PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 或使用-m参数
python -m pytest tests/
```

### Q2: 如何跳过某些测试？

**方法1：使用@pytest.mark.skip**
```python
@pytest.mark.skip(reason="需要真实API密钥")
def test_real_api():
    pass
```

**方法2：条件跳过**
```python
@pytest.mark.skipif(not has_api_key(), reason="无API密钥")
def test_with_api():
    pass
```

### Q3: 如何测试异常情况？

```python
def test_invalid_input():
    """测试无效输入"""
    with pytest.raises(ValueError):
        chat_service.chat("")  # 空查询应抛出ValueError
```

### Q4: 如何清理测试数据？

**使用fixture的teardown**:
```python
@pytest.fixture
def test_db():
    """创建测试数据库"""
    # Setup
    db = create_test_database()
    
    yield db
    
    # Teardown
    db.close()
    remove_test_database()
```

---

## 测试最佳实践

### 1. 测试命名清晰

```python
# ✅ 好的命名
def test_chat_returns_answer_for_valid_question():
    pass

# ❌ 不好的命名
def test1():
    pass
```

### 2. 一个测试只测一件事

```python
# ✅ 单一职责
def test_upload_document():
    """只测试上传功能"""
    pass

def test_document_parsing():
    """只测试解析功能"""
    pass

# ❌ 测试多件事
def test_upload_and_parse_and_index():
    """测试太多功能，难以定位问题"""
    pass
```

### 3. 使用AAA模式

```python
def test_example():
    # Arrange（准备）
    service = ChatService()
    question = "测试问题"
    
    # Act（执行）
    result = service.chat(question)
    
    # Assert（断言）
    assert result is not None
```

### 4. 避免测试实现细节

```python
# ✅ 测试行为
def test_search_returns_results():
    results = search("专项债券")
    assert len(results) > 0

# ❌ 测试实现
def test_search_calls_ragflow():
    # 不要测试内部如何调用RAGFlow
    pass
```

---

## 相关文档

- [开发者指南](04-DEVELOPER_GUIDE.md) - 了解如何添加新功能
- [API参考](05-API_REFERENCE.md) - 查看可测试的API
- [性能优化](technical/performance.md) - 性能测试和基准

---

**最后更新**: 2026-02-01  
**维护者**: AI Assistant
