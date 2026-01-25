# 📚 文档导航

<!-- 文档类型: 文档索引 | 版本: 2026.1 | 更新时间: 2026-01-25 -->
<!-- 描述: 项目所有文档的导航索引，帮助快速定位和查找文档 -->

> 快速找到你需要的文档

---

## 🚀 入门必读

| 文档 | 内容 | 阅读时间 |
|------|------|---------|
| **[README.md](README.md)** | ⭐ **项目概述** - 功能特性、系统架构、使用说明 | 15分钟 |
| **[QUICK_START.md](QUICK_START.md)** | 快速部署指南、前置要求、最小配置 | 10分钟 |
| **[STATUS_SUMMARY.md](STATUS_SUMMARY.md)** | 系统状态总结、完成功能、当前问题 | 5分钟 |

---

## 📖 详细参考

| 文档 | 用途 | 更新日期 |
|------|------|---------|
| [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) | 系统架构设计、模块划分、技术栈 | 2026-01-25 |
| [RAGFLOW_CONFIG_GUIDE.md](RAGFLOW_CONFIG_GUIDE.md) | RAGFlow配置参数说明、自动配置功能 | 2026-01-25 |
| [PROGRESS.md](PROGRESS.md) | 开发进度报告、功能完成情况、里程碑 | 2026-01-25 |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | 详细开发计划、代码模板、实现指导 | 2026-01-25 |
| [TODO.md](TODO.md) | 任务管理文档、优先级、执行计划 | 2026-01-25 |

---

## 🔧 配置与部署

| 文件 | 说明 |
|------|------|
| [config/config.ini.template](config/config.ini.template) | 配置文件模板 (复制为config.ini使用) |
| [requirements.txt](requirements.txt) | Python依赖列表 |
| [docker-compose.yml](docker-compose.yml) | Docker编排配置 |

---

## 🎯 根据目的快速查找

### 我想...

- **快速了解系统状态** → [STATUS_SUMMARY.md](STATUS_SUMMARY.md)
- **理解系统工作流程** → [SYSTEM_WORKFLOW.md](SYSTEM_WORKFLOW.md)
- **启动应用** → [QUICK_START.md](QUICK_START.md) 或 [README.md](README.md)
- **配置系统** → [config/config.ini.template](config/config.ini.template)
- **了解进度** → [PROGRESS.md](PROGRESS.md)
- **查看待做任务** → [TODO.md](TODO.md)
- **学习代码实现** → [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)
- **查看知识要点** → [know-how.md](know-how.md)

---

## 📊 关键数字

- **代码行数:** ~3500行
- **数据库表:** 5个
- **外部服务:** 3个 (DeepSeek/RAGFlow/Whisper)
- **页面模块:** 5个 (搜索/文档/图谱/语音/分析)
- **功能完成度:** 100%
- **BUG修复:** 4个已完成

---

## ✅ 最新更新 (2026-01-24)

### 新增文档
- ✨ [STATUS_SUMMARY.md](STATUS_SUMMARY.md) - 系统状态总结
- ✨ [SYSTEM_WORKFLOW.md](SYSTEM_WORKFLOW.md) - 工作流程详解

### 更新的文档
- 📝 [PROGRESS.md](PROGRESS.md) - 简化为当前逻辑说明
- 📝 [QUICK_START.md](QUICK_START.md) - 更新为实际工作流程

### 修复的BUG
1. ✅ PDF文本提取 (使用pdfplumber + PyPDF2)
2. ✅ 摘要生成完整性 (强制5部分结构)
3. ✅ 图谱构建错误 (正确使用GraphNode/GraphEdge)
4. ✅ 文档上传重复 (UNIQUE约束验证)

---

## 💡 快速命令

```bash
# 启动应用
streamlit run app.py

# 查看数据库
sqlite3 data/database/policy.db ".tables"

# 运行测试
pytest tests/

# 更新依赖
pip install -r requirements.txt
```

---

**选择一个文档开始吧！** 👇
