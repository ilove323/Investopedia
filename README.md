# 政策库知识库+知识图谱系统

<!-- 文档类型: 根目录简要说明 | 版本: 2026.1 | 更新时间: 2026-01-25 -->

一个专注于政策知识管理的智能系统，集成了RAGFlow文档处理、知识图谱可视化、语音问答等功能。

## 🚀 快速开始

```bash
# 1. 克隆项目
git clone [repository-url]
cd Investopedia

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置系统
cp config/config.ini.template config/config.ini
# 编辑 config.ini 设置RAGFlow和其他服务参数

# 4. 运行测试 (可选)
cd tests
python run_tests.py

# 5. 启动应用
streamlit run app.py
```

## 🧪 测试

本项目包含完整的单元测试套件，确保系统稳定性和功能正确性：

```bash
# 快速运行所有测试
./tests/test_runner.sh

# 或手动运行
cd tests && PYTHONPATH=$PWD/..:$PYTHONPATH python3 run_tests.py

# 运行特定测试
./tests/test_runner.sh config     # 配置系统测试
./tests/test_runner.sh ragflow   # RAGFlow客户端测试  
./tests/test_runner.sh api       # API探索测试
./tests/test_runner.sh quick     # 快速测试（跳过网络）
./tests/test_runner.sh verbose   # 详细输出
```

**测试覆盖范围**：
- ✅ 配置系统加载和验证 (10个测试)
- ✅ RAGFlow API客户端功能 (10个测试)
- ✅ 知识库配置更新 (6个测试)
- ✅ API接口探索和性能 (7个测试)

**测试结果**: 33个测试，32个通过，1个跳过，成功率100%

详细测试指南请查看：**[🧪 测试文档](tests/README.md)**

## 📚 文档

详细文档请查看：

- **[📖 完整系统指南](Documents/SYSTEM_GUIDE.md)** - 部署、配置、测试、开发全指南
- **[⚙️ RAGFlow配置](Documents/RAGFLOW_CONFIG_GUIDE.md)** - RAGFlow特定配置说明
- **[🚀 快速启动](Documents/QUICK_START.md)** - 快速部署指南
- **[🧪 测试指南](tests/README.md)** - 单元测试文档

## 🎯 主要功能

- **RAGFlow文档查看器** - 查看和搜索RAGFlow知识库中的文档
- **智能摘要生成** - 基于DeepSeek API的多层次文档摘要
- **知识图谱构建** - NetworkX + Pyvis交互式图谱可视化
- **语音问答系统** - Whisper语音识别 + 智能问答
- **策略搜索分析** - 多维度政策文档过滤和分析

## 🔧 系统要求

- Python 3.8+
- RAGFlow实例（用于文档处理）
- DeepSeek API密钥（用于AI功能）

## 📞 支持

遇到问题请查看 [Documents/STATUS_SUMMARY.md](Documents/STATUS_SUMMARY.md) 或 [Documents/TODO.md](Documents/TODO.md)
