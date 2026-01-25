# 政策库知识库+知识图谱系统

<!-- 根目录入口文档 | 版本: 2026.1 | 更新时间: 2026-01-26 -->

一个专注于政策知识管理的智能系统，集成了RAGFlow文档处理、知识图谱可视化、语音问答等功能。

## 🚀 5分钟快速启动

```bash
# 1. 克隆和安装
git clone [repository-url] && cd Investopedia
pip install -r requirements.txt

# 2. 配置系统  
cp config/config.ini.template config/config.ini
# 编辑 config.ini 设置RAGFlow等服务参数

# 3. 启动应用
streamlit run app.py
```

## 📚 完整文档

**主要文档都在 `Documents/` 目录下：**

- **[📖 完整项目指南](Documents/README.md)** - 系统介绍、功能特性、架构说明
- **[🚀 快速部署](Documents/QUICK_START.md)** - 5分钟部署指南
- **[⚙️ 系统配置](Documents/SYSTEM_GUIDE.md)** - 详细配置和使用指南
- **[🧪 测试指南](Documents/TESTING_GUIDE.md)** - 单元测试完整文档
- **[📈 开发进度](Documents/PROGRESS.md)** - 项目状态和进展

## 🎯 核心功能

- **RAGFlow文档管理** - 查看和搜索知识库文档，支持PDF智能解析
- **知识图谱** - 政策关系可视化和分析
- **语音问答** - Whisper语音识别 + 智能问答
- **政策搜索** - 多维度筛选和语义搜索
- **PDF解析引擎** - 多库支持（pdfplumber + PyPDF2），智能编码检测

## 🔧 最新特性

### 📄 文档查看器（v2026.1）
- **类RAGFlow界面** - 左侧文档预览，右侧切片结果
- **智能PDF解析** - 使用pdfplumber和PyPDF2多重解析引擎
- **文档切片显示** - 完整/省略模式，关键词提取
- **文件类型检测** - 自动识别PDF、TXT、MD等格式
- **下载功能** - 支持原文和切片内容下载

## 🧪 快速测试

```bash
# 运行所有测试
./tests/test_runner.sh

# 验证核心功能
python -c "from src.config.config_loader import ConfigLoader; print('✅ 配置系统正常')"
```

## 🔧 系统要求

- Python 3.8+
- RAGFlow服务实例
- DeepSeek API密钥

## 📞 获取帮助

- 📖 查看 [Documents/README.md](Documents/README.md) 获取完整指南
- 🐛 问题反馈请查看 [Documents/TODO.md](Documents/TODO.md)
- 📊 项目状态查看 [Documents/PROGRESS.md](Documents/PROGRESS.md)
