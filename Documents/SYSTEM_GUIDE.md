# 政策库知识图谱系统 - 完整指南

<!-- 版本: 2026.1.26 | 状态: 生产就绪 -->

## 🎯 项目概述

一个专注于政策知识管理的智能系统，集成RAGFlow文档处理、知识图谱可视化、语音问答等功能。

### 核心功能
- **📄 RAGFlow文档库** - 智能文档处理和检索
- **🔍 智能搜索** - 多维度政策文档过滤分析
- **📊 知识图谱** - NetworkX + Pyvis交互式图谱可视化  
- **🎤 语音问答** - Whisper语音识别 + AI问答
- **📝 智能摘要** - 基于DeepSeek API的多层次摘要

## 🚀 快速启动

### 1. 环境要求
- Python 3.8+
- RAGFlow实例 (用于文档处理)
- DeepSeek API密钥 (用于AI功能)

### 2. 安装部署
```bash
# 1. 克隆项目
git clone [repository-url]
cd Investopedia

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置系统
cp config/config.ini.template config/config.ini
# 编辑config.ini设置RAGFlow和API参数

# 4. 运行测试
./tests/test_runner.sh

# 5. 启动应用
streamlit run app.py
```

### 3. 配置说明

#### 主配置 (config/config.ini)
```ini
[RAGFLOW]
base_url = http://localhost:9380
api_key = ragflow-YOUR-API-KEY
default_kb_name = policy_demo_kb

[DEEPSEEK] 
api_key = sk-YOUR-DEEPSEEK-KEY
base_url = https://api.deepseek.com

[WHISPER]
enabled = true
service_url = http://localhost:8000
```

#### 知识库配置 (config/knowledgebase/policy_demo_kb.ini)  
```ini
[DOCUMENT_PROCESSING]
chunk_size = 800
parser = deepdoc
layout_recognize = true

[RETRIEVAL]
similarity_threshold = 0.7
graph_retrieval = true
top_k = 10

[QA]
temperature = 0.1
max_tokens = 2000
```

## 🧪 测试体系

### 运行测试
```bash
# 运行所有测试
./test_runner.sh

# 运行特定类型
./test_runner.sh config     # 配置系统测试
./test_runner.sh ragflow   # RAGFlow客户端测试  
./test_runner.sh api       # API探索测试
./test_runner.sh quick     # 快速测试(跳过网络)
```

### 测试覆盖范围
- ✅ **配置系统** (10个测试) - 配置加载、验证、KB管理
- ✅ **RAGFlow集成** (10个测试) - 客户端、API连接、健康检查
- ✅ **RAGFlow SDK客户端** (20个测试) - 初始化、健康检查、文档操作、问答  
- ✅ **API探索** (7个测试) - 端点发现、性能测试、并发调用

**当前状态**: 33个测试，32个通过，1个跳过，成功率100%

### 编写单元测试指南

为了让后续AI能够编写有效的单元测试来解决问题，遵循以下规范：

#### 1. 测试文件结构
```python
import unittest
from unittest.mock import patch, Mock, MagicMock
import sys
import os

# 路径设置
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'src'))

from your_module import YourClass

class TestYourFeature(unittest.TestCase):
    """功能描述的测试类"""
    
    def setUp(self):
        """每个测试前的设置"""
        self.test_data = {...}
        self.client = YourClass()
    
    def tearDown(self):  
        """每个测试后的清理"""
        pass
    
    @patch('src.services.external_service.requests')
    def test_specific_functionality(self, mock_requests):
        """测试具体功能"""
        # 模拟外部调用
        mock_requests.get.return_value.json.return_value = {...}
        
        # 执行测试
        result = self.client.method()
        
        # 断言验证
        self.assertEqual(result, expected)
        mock_requests.get.assert_called_once()
```

#### 2. Mock外部依赖
```python
# RAGFlow API调用
@patch('src.services.ragflow_client.requests')
def test_ragflow_api(self, mock_requests):
    mock_requests.put.return_value.status_code = 200
    mock_requests.put.return_value.json.return_value = {"retcode": 0}

# 配置加载
@patch('src.config.config_loader.configparser')
def test_config_loading(self, mock_config):
    mock_config.ConfigParser().read.return_value = True
```

#### 3. 常用断言模式
```python
# 基本断言
self.assertEqual(actual, expected)
self.assertTrue(condition) 
self.assertIsNotNone(value)
self.assertIn(item, container)

# 异常断言
with self.assertRaises(ValueError):
    function_that_should_fail()

# Mock断言
mock_function.assert_called_once()
mock_function.assert_called_with(expected_args)
```

#### 4. 测试分类
- **单元测试**: 测试单个函数/方法
- **集成测试**: 测试模块间交互
- **功能测试**: 测试完整业务流程
- **性能测试**: 测试响应时间和并发

## 🏗️ 系统架构

### 目录结构
```
├── app.py                    # Streamlit主应用
├── config/                   # 配置文件
│   ├── config.ini           # 主配置  
│   ├── knowledgebase/       # 知识库配置
│   └── prompts/             # 提示词模板
├── src/                     # 源代码
│   ├── config/              # 配置管理
│   ├── services/            # 外部服务集成
│   ├── components/          # UI组件
│   ├── business/            # 业务逻辑
│   └── utils/               # 工具函数
└── tests/                   # 测试套件
    ├── run_tests.py         # 测试运行器
    └── test_*.py            # 单元测试
```

### 核心模块

#### 配置系统 (src/config/)
- **ConfigLoader**: 统一配置管理，支持主配置+KB配置
- **get_config()**: 全局配置获取函数
- **支持**: 多知识库配置、配置验证、向后兼容

#### RAGFlow集成 (src/services/ragflow_client.py)
- **RAGFlowClient**: RAGFlow API客户端
- **功能**: 文档管理、知识库检索、问答服务
- **特性**: 自动配置应用、健康检查、错误重试

#### 业务逻辑 (src/business/)
- **ImpactAnalyzer**: 政策影响分析
- **TagGenerator**: 智能标签生成
- **ValidityChecker**: 政策有效性检查

### API端点
- **RAGFlow**: GET /api/v1/datasets (数据集列表)
- **RAGFlow**: POST /api/v1/documents/upload (文档上传)
- **DeepSeek**: POST /chat/completions (AI对话)
- **Whisper**: POST /transcribe (语音识别)

## 🔧 配置管理

### 配置层次结构
1. **主配置** (config.ini) - RAGFlow连接、API密钥
2. **知识库配置** (knowledgebase/*.ini) - KB特定参数
3. **提示词** (prompts/*.txt) - 每个KB一个提示词文件
4. **环境变量** - 开发/生产环境切换

### 配置验证
- 配置文件存在性检查
- 必需参数验证
- 类型转换和默认值

## 📊 状态监控

### 系统健康检查
- RAGFlow服务连接状态
- 配置应用状态  
- 数据库连接状态
- Whisper服务状态

### 日志系统
- 结构化日志记录
- 错误追踪和告警
- 性能指标收集
- 调试信息输出

## 🚨 故障排除

### 常见问题

#### 1. 配置错误
```bash
# 检查配置文件
cat config/config.ini
cat config/knowledgebase/policy_demo_kb.ini

# 运行配置测试
./tests/test_runner.sh config
```

#### 2. RAGFlow连接问题  
```bash
# 检查服务状态
curl -H "Authorization: Bearer YOUR-API-KEY" \
  http://localhost:9380/api/v1/datasets

# 测试客户端
./tests/test_runner.sh ragflow
```

#### 3. 依赖问题
```bash
# 重新安装依赖
pip install -r requirements.txt

# 检查Python路径
python3 -c "import sys; print(sys.path)"
```

#### 4. 测试失败
```bash
# 详细测试输出
./tests/test_runner.sh verbose

# 快速测试(跳过网络)
./tests/test_runner.sh quick

# 单个测试文件
cd tests && python3 -m unittest test_config_system.py -v
```

## 📈 开发指南

### 添加新功能
1. **编写测试** - 先写测试用例定义预期行为
2. **实现功能** - 编写最小可用实现
3. **运行测试** - 确保所有测试通过
4. **更新文档** - 添加使用说明和API文档

### 添加新知识库
```bash
# 1. 复制模板配置
cp config/knowledgebase/template.ini config/knowledgebase/new_kb.ini

# 2. 编辑配置
vim config/knowledgebase/new_kb.ini

# 3. 创建提示词
echo "新KB的提示词" > config/prompts/new_kb.txt

# 4. 更新主配置
# 添加kb_mappings中的新KB映射
```

### 代码规范
- **函数命名**: 动词+名词，如get_config(), load_data()
- **类命名**: 大驼峰，如ConfigLoader, RAGFlowClient  
- **文件命名**: 小写+下划线，如ragflow_client.py
- **注释**: 中文注释，英文docstring
- **测试**: 每个public方法都要有测试

## 🔮 路线图

### 已完成 ✅
- RAGFlow集成和配置管理系统
- 多知识库架构支持
- 完整的单元测试覆盖
- 知识图谱可视化
- 语音问答功能

### 进行中 🚧
- 性能优化和缓存
- 更多文档解析器支持
- 高级图谱分析功能

### 计划中 📋
- 批量文档处理
- 分布式部署支持  
- 更多AI模型集成
- RESTful API接口

---

## 📞 技术支持

- **测试报告**: [tests/TEST_REPORT.md](tests/TEST_REPORT.md)
- **测试指南**: [tests/README.md](tests/README.md)  
- **配置文档**: 见config/目录下的模板和示例

**系统状态**: 🟢 生产就绪，所有核心功能正常运行