# 测试指南

<!-- 文档类型: 测试指南文档 | 版本: 2026.1 | 更新时间: 2026-01-26 -->
<!-- 描述: 项目单元测试的完整指南，包含测试结构、运行方法、最佳实践 -->

## 🧪 测试概述

本项目采用**pytest**和**unittest**双框架进行单元测试，确保系统稳定性和功能正确性。测试覆盖配置系统、RAGFlow SDK客户端、API接口和核心业务逻辑。

### 测试统计

**测试框架**:
- 主框架: pytest >= 8.3.0
- 辅助框架: unittest (Python标准库)
- 覆盖率工具: pytest-cov >= 6.0.0

**测试覆盖范围**：
- ✅ 配置系统加载和验证 (10个测试)
- ✅ RAGFlow SDK客户端功能 (20个测试)
- ✅ RAGFlow配置管理 (7个测试)
- ✅ API接口探索和性能 (7个测试)
- ✅ 文档列表功能验证 (7个测试)
- ✅ 数据同步服务功能 (8个测试)
- ✅ 系统提示词集成 (5个测试)
- ✅ 其他集成测试 (3个测试)

**测试结果**: 67个测试，65个通过，2个跳过，成功率97%

## 📁 测试文件结构

```
tests/
├── run_tests.py                     # 测试运行器主程序
├── test_config_system.py            # 配置系统测试
├── test_ragflow_client.py           # RAGFlow客户端测试  
├── test_ragflow_config_update.py    # RAGFlow配置更新测试
├── test_ragflow_api_exploration.py  # RAGFlow API探索测试
├── test_document_list_fix.py        # 文档列表功能修复验证测试
├── test_data_sync.py                # 数据同步服务测试
├── test_business/                   # 业务逻辑测试
├── test_database/                   # 数据库测试
└── test_services/                   # 服务层测试
```

## 🔧 快速运行测试

### 推荐方式 - 使用pytest

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行所有测试
python -m pytest tests/ -v

# 运行所有测试并显示覆盖率
python -m pytest tests/ --cov=src --cov-report=term-missing

# 只运行失败的测试
python -m pytest tests/ --lf

# 运行到第一个失败就停止
python -m pytest tests/ -x
```

### 运行特定测试文件

```bash
# 运行RAGFlow SDK客户端测试
python -m pytest tests/test_ragflow_client.py -v

# 运行配置系统测试
python -m pytest tests/test_config_system.py -v

# 运行数据同步测试
python -m pytest tests/test_data_sync.py -v

# 运行文档列表功能测试
python -m pytest tests/test_document_list_fix.py -v
```

### 运行特定测试类或方法

```bash
# 运行特定测试类
python -m pytest tests/test_ragflow_client.py::TestRAGFlowClient -v

# 运行特定测试方法
python -m pytest tests/test_ragflow_client.py::TestRAGFlowClient::test_client_initialization -v

# 使用关键词过滤测试
python -m pytest tests/ -k "config" -v  # 运行所有包含config的测试
python -m pytest tests/ -k "sdk" -v     # 运行所有包含sdk的测试
```

### 传统方式 - 使用test_runner.sh

```bash
# 运行所有测试
./tests/test_runner.sh all

# 只运行配置系统测试
./tests/test_runner.sh config

# 只运行RAGFlow客户端测试
./tests/test_runner.sh ragflow

# 只运行数据同步测试
./tests/test_runner.sh sync

# 详细输出
./tests/test_runner.sh verbose
```

## 📝 详细测试说明

### 1. test_config_system.py
**目的**: 测试配置系统的加载、解析和验证功能

**测试内容**:
- 配置文件加载（主配置、KB配置、提示文件）
- 配置数据验证和类型转换
- 错误配置的处理
- 配置文件不存在时的默认处理

**测试类**:
- `TestConfigSystem`: 核心配置加载逻辑
- `TestConfigFiles`: 配置文件读取和解析

### 2. test_ragflow_client.py
**目的**: 测试RAGFlow SDK客户端的核心功能

**测试内容**:
- SDK客户端初始化和配置
- 数据集缓存机制
- 文档上传、删除、列表操作
- 语义搜索和检索
- 智能问答（聊天助手）
- 配置管理和更新
- 系统提示词集成
- SDK错误处理

**测试类** (20个测试):
- `TestRAGFlowClient`: 客户端基础功能（初始化、配置、健康检查）
- `TestRAGFlowAPI`: API接口配置和连接
- `TestConfigurationIntegration`: 配置集成测试
- `TestDocumentListFeature`: SDK文档列表功能测试
- `TestRealDocumentIntegration`: 真实环境集成测试
- `TestSystemPromptIntegration`: 系统提示词集成测试

**SDK测试亮点** *(2026-01-26 v2.1)*:
- ✅ 使用Mock模拟SDK对象和方法
- ✅ 测试数据集缓存和聊天助手管理
- ✅ 验证SDK返回对象的格式转换
- ✅ 覆盖所有SDK核心方法
- ✅ 测试错误降级和容错机制

### 3. test_ragflow_config_update.py
**目的**: 测试RAGFlow配置更新的完整流程

**测试内容**:
- 配置更新payload构建
- API调用执行
- 更新结果验证
- 失败场景处理

**测试类**:
- `TestRAGFlowConfigUpdate`: 配置更新集成测试

### 4. test_ragflow_api_exploration.py
**目的**: 测试RAGFlow API探索和性能评估

**测试内容**:
- API端点发现
- 响应时间测量
- 数据结构分析
- 连接稳定性测试

**测试类**:
- `TestRAGFlowAPIExploration`: API探索和性能测试

### 5. test_document_list_fix.py
**目的**: 专门验证RAGFlow文档列表功能修复 *(新增 2026-01-26)*

**测试内容**:
- API endpoint修复验证 (`/api/v1/datasets/{dataset_id}/documents`)
- Web URL配置修复验证 (端口号:9380)
- get_documents()方法完整工作流程测试
- 错误处理机制验证
- 真实环境集成测试

**测试类**:
- `TestDocumentListFix`: 核心功能修复验证
- `TestDocumentsPageIntegration`: 页面集成测试

**验证的修复内容**:
- 修复前: HTTP 404错误 `/api/documents` not found
- 修复后: 正确调用 `/api/v1/datasets/{dataset_id}/documents`
- 修复前: Web URL缺少端口号
- 修复后: 完整URL `http://117.21.184.150:9380`
- 当前状态: 成功获取1个政策文档 (672KB)

### 6. test_data_sync.py
**目的**: 测试RAGFlow文档到本地数据库的数据同步功能 *(新增 2026-01-26)*

**测试内容**:
- 数据同步服务初始化和配置
- RAGFlow文档同步到本地数据库
- 元数据提取和标签生成
- 新政策创建和现有政策更新
- 错误处理和状态报告

**测试类**:
- `TestDataSyncService`: 数据同步核心功能测试
- `TestDataSyncIntegration`: 真实环境集成测试

**核心功能验证**:
- 同步空RAGFlow知识库的处理
- 新政策文档同步和元数据提取
- 现有政策更新机制
- 同步过程中的错误处理和恢复
- 同步状态检查和报告
- 标签自动生成和关联

## 🛠️ 测试环境配置

### 1. 基础依赖
```bash
pip install -r requirements.txt
```

### 2. 测试专用依赖
已包含在requirements.txt中：
- `pytest>=8.3.0` - 主测试框架
- `pytest-cov>=6.0.0` - 代码覆盖率
- `unittest` (Python标准库) - 传统测试框架
- `unittest.mock` - Mock对象支持

### 3. Python版本要求
```bash
# 推荐使用Python 3.12+
python3 --version
# Python 3.12.x, 3.13.x 或 3.14.x

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 环境变量
```bash
export RAGFLOW_TEST_MODE=1          # 启用测试模式
export RAGFLOW_API_KEY=test_key     # 测试API密钥
export LOG_LEVEL=DEBUG              # 测试时启用调试日志
```

### 配置文件
测试使用独立的配置文件：
- `config/config.ini.test` - 测试主配置
- `config/knowledgebase/test_kb.ini` - 测试KB配置

## 💡 测试最佳实践

### 1. 测试隔离
- 每个测试方法都有独立的setUp和tearDown
- 使用mock避免真实的外部API调用
- 临时文件在测试结束后自动清理

### 2. 断言规范
```python
# 使用具体的断言方法
self.assertEqual(actual, expected)
self.assertIsNone(value)
self.assertIn(item, container)
self.assertRaises(Exception, func)

# 避免简单的assertTrue/False
# 差: self.assertTrue(len(result) > 0)
# 好: self.assertGreater(len(result), 0)
```

### 3. Mock使用

#### 传统HTTP Mock (已弃用)
```python
# 旧方式: Mock requests库 (不再使用)
with patch('src.services.api_client.requests.get') as mock_get:
    mock_get.return_value.json.return_value = {'status': 'success'}
```

#### RAGFlow SDK Mock (当前方式)
```python
# SDK对象Mock
from unittest.mock import MagicMock, patch

# Mock数据集对象
mock_dataset = MagicMock()
mock_dataset.id = 'test_dataset_id'
mock_dataset.name = 'test_kb'

# Mock文档对象
mock_doc = MagicMock()
mock_doc.id = 'doc_123'
mock_doc.name = 'test.pdf'
mock_doc.size = 1024

# Mock SDK方法
with patch.object(client.rag, 'list_datasets') as mock_list, \
     patch.object(mock_dataset, 'upload_documents') as mock_upload:

    mock_list.return_value = [mock_dataset]
    mock_upload.return_value = [mock_doc]

    # 执行测试
    doc_id = client.upload_document('test.pdf', 'test.pdf', 'test_kb')
    assert doc_id == 'doc_123'
    result = client.fetch_data()
    self.assertEqual(result['status'], 'success')
```

### 4. 测试数据管理
```python
# 使用fixture方法准备测试数据
def setUp(self):
    self.test_data = {
        'config': {'api_key': 'test_key'},
        'documents': [{'id': 1, 'title': 'Test Doc'}]
    }
```

## 🔍 调试测试

### 查看详细输出
```bash
python -m unittest test_ragflow_client.py -v
```

### 运行单个测试方法
```bash
python -m unittest test_config_system.TestConfigSystem.test_load_kb_config
```

### 使用调试模式
```python
# 在测试中添加
import pdb; pdb.set_trace()
```

### 查看测试覆盖率
```bash
coverage run -m unittest discover
coverage report
coverage html  # 生成HTML报告
```

## 🚨 常见问题

### 1. 测试失败排查
```bash
# 检查依赖
pip list

# 验证配置
python -c "from src.config.config_loader import ConfigLoader; print('Config OK')"

# 检查测试环境
cd tests && python -c "import sys; print(sys.path)"
```

### 2. 网络测试问题
如果网络测试失败，使用快速测试模式：
```bash
./tests/test_runner.sh quick
```

### 3. 配置文件问题
确保配置文件存在：
```bash
ls -la config/config.ini
ls -la config/knowledgebase/
```

## 📊 持续集成

测试可以集成到CI/CD流水线中：
```yaml
# GitHub Actions example
- name: Run Tests
  run: |
    cd tests
    python run_tests.py
```

---

**🔗 相关文档**: 
- [系统架构说明](SYSTEM_ARCHITECTURE.md)
- [RAGFlow配置指南](RAGFLOW_CONFIG_GUIDE.md)
- [开发进度](PROGRESS.md)