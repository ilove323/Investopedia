# 📖 文档导航中心

> **一站式文档索引** - 根据你的角色快速找到需要的文档  
> Last Updated: 2026-02-01

---

## 🎯 根据角色选择阅读路径

### 👤 我是新用户（第一次使用）

**推荐阅读顺序** (总耗时 ~15分钟):

1. **[README.md](../README.md)** ⏱️ 2分钟  
   快速了解项目是什么，能做什么

2. **[01-QUICK_START.md](01-QUICK_START.md)** ⏱️ 10分钟  
   跟着步骤部署并运行系统

3. **[03-USER_GUIDE.md](03-USER_GUIDE.md)** ⏱️ 15分钟  
   学习如何使用各个功能

4. **[09-FAQ.md](09-FAQ.md)** ⏱️ 5分钟  
   遇到问题先查FAQ

---

### 👨‍💻 我是开发者（要贡献代码）

**推荐阅读顺序** (总耗时 ~60分钟):

1. **[README.md](../README.md)** ⏱️ 2分钟  
   了解项目概况

2. **[02-ARCHITECTURE.md](02-ARCHITECTURE.md)** ⏱️ 20分钟  
   理解系统架构和设计理念

3. **[technical/code-structure.md](technical/code-structure.md)** ⏱️ 15分钟  
   熟悉代码组织结构

4. **[04-DEVELOPER_GUIDE.md](04-DEVELOPER_GUIDE.md)** ⏱️ 30分钟  
   学习开发规范和扩展方法

5. **[05-API_REFERENCE.md](05-API_REFERENCE.md)** ⏱️ 30分钟  
   查阅API接口文档

6. **[07-TESTING.md](07-TESTING.md)** ⏱️ 15分钟  
   编写单元测试

**深入技术细节** (按需查阅):
- [RAGFlow集成](technical/ragflow-integration.md)
- [知识图谱实现](technical/knowledge-graph.md)
- [实体抽取方案](technical/entity-extraction.md)

---

### 🔧 我是运维人员（要配置和维护）

**推荐阅读顺序** (总耗时 ~30分钟):

1. **[01-QUICK_START.md](01-QUICK_START.md)** ⏱️ 10分钟  
   部署系统

2. **[06-CONFIGURATION.md](06-CONFIGURATION.md)** ⏱️ 20分钟  
   详细配置说明（重要！）

3. **[08-TROUBLESHOOTING.md](08-TROUBLESHOOTING.md)** ⏱️ 10分钟  
   常见问题和解决方案

4. **[09-FAQ.md](09-FAQ.md)** ⏱️ 5分钟  
   快速查询FAQ

**配置相关**:
- [config/knowledgebase/README.md](../config/knowledgebase/README.md) - 知识库配置

---

### 🧪 我要运行测试

**快速指引**:

1. **[07-TESTING.md](07-TESTING.md)** - 测试指南和规范
2. **运行所有测试**: 
   ```bash
   python tests/run_tests.py
   ```

---

### 🔍 我要解决具体问题

| 问题类型 | 查看文档 |
|---------|---------|
| 应用无法启动 | [08-TROUBLESHOOTING.md](08-TROUBLESHOOTING.md) → "应用启动问题" |
| RAGFlow连接失败 | [06-CONFIGURATION.md](06-CONFIGURATION.md) → "RAGFlow配置" |
| 图谱构建失败 | [08-TROUBLESHOOTING.md](08-TROUBLESHOOTING.md) → "图谱问题" |
| Qwen API超时 | [06-CONFIGURATION.md](06-CONFIGURATION.md) → "Qwen配置" |
| 数据库错误 | [08-TROUBLESHOOTING.md](08-TROUBLESHOOTING.md) → "数据库问题" |
| 如何添加新页面 | [04-DEVELOPER_GUIDE.md](04-DEVELOPER_GUIDE.md) → "添加新页面" |
| 如何添加新实体类型 | [technical/entity-extraction.md](technical/entity-extraction.md) |

---

## 📂 完整文档目录

### 📘 核心文档

```
Documents/
├── 00-INDEX.md                 ← 📍 你在这里（文档导航）
├── 01-QUICK_START.md           🚀 5分钟快速开始
├── 02-ARCHITECTURE.md          🏛️ 系统架构
├── 03-USER_GUIDE.md            👤 用户手册
├── 04-DEVELOPER_GUIDE.md       👨‍💻 开发者指南
├── 05-API_REFERENCE.md         📚 API文档
├── 06-CONFIGURATION.md         ⚙️ 配置详解
├── 07-TESTING.md               🧪 测试指南
├── 08-TROUBLESHOOTING.md       🔧 故障排查
└── 09-FAQ.md                   ❓ 常见问题
```

### 🔬 技术细节文档

```
Documents/technical/
├── code-structure.md           📁 代码结构详解
├── modules-inventory.md        📦 模块清单
├── ragflow-integration.md      🔗 RAGFlow集成
├── knowledge-graph.md          🕸️ 知识图谱实现
├── entity-extraction.md        🧠 实体抽取方案
├── voice-qa.md                 🎤 语音问答技术
└── pdf-parsing.md              📄 PDF解析引擎
```

### 📦 配置文档

```
config/
├── README.md                   ⚙️ 配置总览
├── config.ini.template         📝 配置模板
└── knowledgebase/
    └── README.md               📚 知识库配置说明
```

### 📜 归档文档（历史版本）

```
Documents/legacy/
├── old-README.md
├── old-SYSTEM_GUIDE.md
├── GRAPH_STORAGE_IMPLEMENTATION.md
├── PROGRESS.md
└── TODO.md
```

---

## 📊 文档状态矩阵

| 文档 | 状态 | 最后更新 | 对应代码版本 |
|------|------|---------|-------------|
| README.md | ✅ 最新 | 2026-02-01 | v2026.2 |
| 00-INDEX.md | ✅ 最新 | 2026-02-01 | v2026.2 |
| 01-QUICK_START.md | ⚠️ 待更新 | 2026-01-26 | v2026.1 |
| 02-ARCHITECTURE.md | 📝 编写中 | - | - |
| 03-USER_GUIDE.md | 📝 编写中 | - | - |
| 04-DEVELOPER_GUIDE.md | 📝 编写中 | - | - |
| 05-API_REFERENCE.md | 📝 编写中 | - | - |
| 06-CONFIGURATION.md | 📝 编写中 | - | - |
| 07-TESTING.md | ⚠️ 待更新 | 2026-01-26 | v2026.1 |
| 08-TROUBLESHOOTING.md | 📝 编写中 | - | - |
| 09-FAQ.md | 📝 编写中 | - | - |
| technical/code-structure.md | ✅ 最新 | 2026-02-01 | v2026.2 |

**图例**:
- ✅ 最新 - 与当前代码完全同步
- ⚠️ 待更新 - 内容基本正确，需要补充最新功能
- 📝 编写中 - 正在创建中

---

## 🔄 文档更新规则

为了保持文档和代码同步，遵循以下规则：

### 代码变更 → 必须更新的文档

| 代码变更类型 | 需要更新的文档 |
|------------|--------------|
| ✨ 新增页面 | [03-USER_GUIDE.md](03-USER_GUIDE.md) + [00-INDEX.md](00-INDEX.md) |
| ✨ 新增API/方法 | [05-API_REFERENCE.md](05-API_REFERENCE.md) |
| ⚙️ 新增配置项 | [06-CONFIGURATION.md](06-CONFIGURATION.md) |
| 🏗️ 架构变更 | [02-ARCHITECTURE.md](02-ARCHITECTURE.md) |
| 📦 新增依赖 | [README.md](../README.md) + [01-QUICK_START.md](01-QUICK_START.md) |
| 🐛 修复重要Bug | [08-TROUBLESHOOTING.md](08-TROUBLESHOOTING.md) |

### 文档审查清单

提交PR前检查：
- [ ] docstring是否与实际功能一致
- [ ] README是否包含最新功能
- [ ] API文档是否包含新方法
- [ ] 配置文档是否包含新配置项
- [ ] 示例代码是否可运行

---

## 🎯 按功能查找文档

### 知识图谱相关
- **概览**: [README.md](../README.md) → "知识图谱"
- **使用**: [03-USER_GUIDE.md](03-USER_GUIDE.md) → "知识图谱功能"
- **实现**: [technical/knowledge-graph.md](technical/knowledge-graph.md)
- **实体抽取**: [technical/entity-extraction.md](technical/entity-extraction.md)
- **API**: [05-API_REFERENCE.md](05-API_REFERENCE.md) → "GraphDAO"

### RAGFlow集成相关
- **配置**: [06-CONFIGURATION.md](06-CONFIGURATION.md) → "RAGFlow配置"
- **实现**: [technical/ragflow-integration.md](technical/ragflow-integration.md)
- **API**: [05-API_REFERENCE.md](05-API_REFERENCE.md) → "RAGFlowClient"
- **问题**: [08-TROUBLESHOOTING.md](08-TROUBLESHOOTING.md) → "RAGFlow问题"

### 语音问答相关
- **使用**: [03-USER_GUIDE.md](03-USER_GUIDE.md) → "语音问答"
- **实现**: [technical/voice-qa.md](technical/voice-qa.md)
- **配置**: [06-CONFIGURATION.md](06-CONFIGURATION.md) → "Whisper配置"

### 文档管理相关
- **使用**: [03-USER_GUIDE.md](03-USER_GUIDE.md) → "文档管理"
- **实现**: [technical/pdf-parsing.md](technical/pdf-parsing.md)

---

## 🆘 快速帮助

### 常见场景

#### "我是第一次使用，不知道从哪开始"
→ 按顺序读: [README.md](../README.md) → [01-QUICK_START.md](01-QUICK_START.md) → [03-USER_GUIDE.md](03-USER_GUIDE.md)

#### "应用启动失败，报错了"
→ [08-TROUBLESHOOTING.md](08-TROUBLESHOOTING.md) 查找错误信息

#### "我要开发新功能"
→ [04-DEVELOPER_GUIDE.md](04-DEVELOPER_GUIDE.md) → 对应的技术细节文档

#### "某个配置项不知道怎么填"
→ [06-CONFIGURATION.md](06-CONFIGURATION.md) 查找配置项说明

#### "想了解系统架构"
→ [02-ARCHITECTURE.md](02-ARCHITECTURE.md) + [technical/code-structure.md](technical/code-structure.md)

---

## 📞 获取更多帮助

- 📖 **文档问题** - 提交Issue或PR改进文档
- 🐛 **Bug反馈** - 先查 [08-TROUBLESHOOTING.md](08-TROUBLESHOOTING.md)，再提Issue
- 💡 **功能建议** - 欢迎提交Feature Request
- ❓ **使用疑问** - 先看 [09-FAQ.md](09-FAQ.md)

---

## 📈 文档路线图

**即将完成** (Week 1):
- ✅ 00-INDEX.md（当前文档）
- ✅ technical/code-structure.md
- 🔄 02-ARCHITECTURE.md
- 🔄 03-USER_GUIDE.md
- 🔄 04-DEVELOPER_GUIDE.md

**计划中** (Week 2):
- 05-API_REFERENCE.md
- 06-CONFIGURATION.md
- 08-TROUBLESHOOTING.md
- 09-FAQ.md
- technical/* 系列文档

---

<div align="center">

**📚 文档持续更新中，欢迎贡献！**

[返回首页](../README.md) | [快速开始](01-QUICK_START.md) | [系统架构](02-ARCHITECTURE.md)

</div>
