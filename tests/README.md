# 测试指南

## 概述

本项目采用Python unittest框架进行单元测试，所有测试文件都位于 `tests/` 目录下。测试覆盖配置系统、RAGFlow客户端、API接口和核心业务逻辑。

## 测试文件结构

```
tests/
├── run_tests.py                     # 测试运行器主程序
├── test_config_system.py            # 配置系统测试
├── test_ragflow_client.py           # RAGFlow客户端测试  
├── test_ragflow_config_update.py    # RAGFlow配置更新测试
├── test_ragflow_api_exploration.py  # RAGFlow API探索测试
├── test_document_list_fix.py        # 文档列表功能修复验证测试
├── test_business/                   # 业务逻辑测试
├── test_database/                   # 数据库测试
└── test_services/                   # 服务层测试
```

## 测试文件说明

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
**目的**: 测试RAGFlow客户端的核心功能

**测试内容**:
- 客户端初始化和连接
- API请求构建和处理
- 数据格式转换
- 错误处理和重试机制
- **文档列表功能修复验证** *(新增)*

**测试类**:
- `TestRAGFlowClient`: 客户端基础功能
- `TestRAGFlowAPI`: API接口调用
- `TestDocumentListFeature`: 文档列表功能测试 *(新增)*
- `TestRealDocumentIntegration`: 真实文档集成测试 *(新增)*

**新增测试用例** *(2026-01-26)*:
- `test_get_documents_success()`: 测试成功获取文档列表
- `test_get_documents_knowledge_base_not_found()`: 测试知识库未找到场景
- `test_get_documents_api_error()`: 测试API错误处理
- `test_endpoint_configuration()`: 测试endpoint配置正确性
- `test_web_url_configuration()`: 测试Web URL配置
- `test_real_document_list_retrieval()`: 测试真实环境文档获取

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

## 运行测试

### 运行所有测试
```bash
# 方法1: 使用便捷脚本
./tests/test_runner.sh

# 方法2: 直接运行
cd tests
python run_tests.py
```

### 运行特定类型测试
```bash
# 只运行配置系统测试
./tests/test_runner.sh config

# 只运行RAGFlow客户端测试  
./tests/test_runner.sh ragflow

# 只运行API探索测试
./tests/test_runner.sh api

# 快速测试（跳过网络测试）
./tests/test_runner.sh quick

# 详细输出
./tests/test_runner.sh verbose
```

### 运行单个测试文件
```bash
python -m unittest test_config_system.py
python -m unittest test_ragflow_client.py -v

# 运行文档列表修复验证测试
python test_document_list_fix.py

# 快速验证文档列表功能
python -c "
from src.services.ragflow_client import RAGFlowClient
client = RAGFlowClient(auto_configure=False)
docs = client.get_documents('policy_demo_kb')
print(f'✅ 文档列表功能正常: {len(docs)} 个文档')
"
```

### 运行单个测试类或方法
```bash
python -m unittest test_config_system.TestConfigSystem
python -m unittest test_config_system.TestConfigSystem.test_load_kb_config
```

## 测试环境要求

### 1. 基础依赖
```bash
pip install -r requirements.txt
```

### 2. 测试专用依赖
已包含在requirements.txt中：
- `unittest` (Python标准库)
- `unittest.mock` (模拟对象)

### 3. 可选依赖
```bash
pip install coverage  # 代码覆盖率
pip install pytest    # 替代测试框架
```

## 测试配置

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

## 测试最佳实践

### 1. 测试隔离
- 每个测试方法都有独立的setUp和tearDown
- 使用mock避免真实的外部API调用
- 临时文件在测试结束后自动清理

### 2. 断言规范
```python
# 使用具体的断言方法
self.assertEqual(actual, expected)
self.assertTrue(condition)
self.assertIn(item, container)
self.assertRaises(Exception, func)

# 添加失败消息
self.assertEqual(result, expected, "配置加载失败")
```

### 3. Mock使用
```python
# Mock外部服务
@patch('src.services.ragflow_client.requests')
def test_api_call(self, mock_requests):
    mock_requests.post.return_value.json.return_value = {...}
    # 测试代码
```

### 4. 测试数据
```python
# 使用类属性定义测试数据
class TestConfig:
    SAMPLE_CONFIG = {
        'chunk_size': 800,
        'parser': 'deepdoc'
    }
```

## 代码覆盖率

### 生成覆盖率报告
```bash
coverage run -m unittest discover tests/
coverage report
coverage html  # 生成HTML报告
```

### 覆盖率目标
- 配置系统: >90%
- RAGFlow客户端: >85%
- 核心业务逻辑: >80%

## 持续集成

### GitHub Actions配置
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: cd tests && python run_tests.py
```

## 故障排除

### 常见问题

1. **导入错误**
   ```bash
   # 确保项目根目录在Python路径中
   export PYTHONPATH=$PWD:$PYTHONPATH
   ```

2. **配置文件找不到**
   ```bash
   # 检查工作目录
   pwd
   # 应该在项目根目录运行测试
   ```

3. **网络连接测试失败**
   ```bash
   # 设置测试模式跳过网络测试
   export RAGFLOW_TEST_MODE=1
   ```

4. **权限错误**
   ```bash
   # 确保测试目录有写入权限
   chmod 755 tests/
   ```

## 添加新测试

### 1. 创建测试文件
```python
import unittest
from unittest.mock import patch, MagicMock
from src.your_module import YourClass

class TestYourClass(unittest.TestCase):
    def setUp(self):
        """每个测试方法前运行"""
        pass
    
    def tearDown(self):
        """每个测试方法后运行"""
        pass
    
    def test_your_method(self):
        """测试描述"""
        # 测试代码
        pass

if __name__ == '__main__':
    unittest.main()
```

### 2. 更新测试运行器
在 `run_tests.py` 中添加新的测试类导入和运行逻辑。

### 3. 更新文档
在本文档中添加新测试文件的说明。

## 性能测试

### 基准测试
```python
import time
import unittest

class TestPerformance(unittest.TestCase):
    def test_config_loading_speed(self):
        start = time.time()
        # 测试代码
        duration = time.time() - start
        self.assertLess(duration, 0.1, "配置加载应在100ms内完成")
```

### 内存使用测试
```python
import psutil
import os

def test_memory_usage(self):
    process = psutil.Process(os.getpid())
    before = process.memory_info().rss
    # 测试代码
    after = process.memory_info().rss
    self.assertLess(after - before, 10 * 1024 * 1024, "内存增长应小于10MB")
```

## 总结

本测试系统提供了完整的单元测试框架，覆盖项目的核心功能模块。通过运行测试可以确保：

1. **功能正确性**: 所有核心功能按预期工作
2. **回归检测**: 代码更改不会破坏现有功能  
3. **文档化**: 测试作为功能使用示例
4. **质量保证**: 维持代码质量和稳定性

定期运行测试，特别是在代码更改后，可以提前发现问题并确保系统的稳定性。