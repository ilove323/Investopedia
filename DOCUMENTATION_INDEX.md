# 📚 文档导航

> 快速找到你需要的文档

---

## 🚀 入门必读

| 文档 | 内容 | 阅读时间 |
|------|------|---------|
| **[STATUS_SUMMARY.md](STATUS_SUMMARY.md)** | ⭐ **首先看这个** - 系统状态、功能完成度、常见问题 | 5分钟 |
| **[SYSTEM_WORKFLOW.md](SYSTEM_WORKFLOW.md)** | 核心工作流程、数据流转、实现细节 | 15分钟 |
| **[QUICK_START.md](QUICK_START.md)** | 快速开始、最新修复、工作计划 | 10分钟 |

---

## 📖 详细参考

| 文档 | 用途 | 更新日期 |
|------|------|---------|
| [README.md](README.md) | 项目总体介绍、技术栈、功能说明 | 2026-01-24 |
| [PROGRESS.md](PROGRESS.md) | 详细进度统计、BUG修复记录、性能指标 | 2026-01-24 |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | 代码实现指导、设计模式、代码模板 | 2026-01-24 |
| [TODO.md](TODO.md) | 所有待做任务、完成状态、优先级 | 2026-01-24 |

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
