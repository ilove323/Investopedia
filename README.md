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

# 4. 启动应用
streamlit run app.py
```

## 📚 完整文档

所有详细文档已移动到 **[Documents/](Documents/)** 目录中：

- **[📖 文档导航](Documents/DOCUMENTATION_INDEX.md)** - 查找所需文档
- **[🚀 快速启动](Documents/QUICK_START.md)** - 详细部署指南  
- **[🏗️ 系统架构](Documents/SYSTEM_ARCHITECTURE.md)** - 技术架构说明
- **[⚙️ RAGFlow配置](Documents/RAGFLOW_CONFIG_GUIDE.md)** - 配置参数说明

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
