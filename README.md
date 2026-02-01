# 政策库知识图谱系统

> **基于 RAGFlow + Qwen 的政策文档智能分析平台**  
> Version 2026.2 | Last Updated: 2026-02-01

---

## ⚡ 一句话介绍

将政策法规文档转化为**可搜索**、**可问答**、**可视化**的知识图谱，利用大模型自动提取实体关系。

---

## 🎯 核心能力

| 功能 | 说明 | 技术 |
|------|------|------|
| 📄 **智能文档管理** | RAGFlow驱动的文档检索和分块展示 | RAGFlow SDK + Streamlit |
| 🕸️ **知识图谱** | Qwen大模型自动抽取政策实体关系 | Qwen API + NetworkX + Pyvis |
| 💬 **智能问答** | 政策内容语义搜索和对话问答 | RAGFlow Chat Assistant |
| 🎤 **语音交互** | 语音识别和语音问答 | OpenAI Whisper API |
| 🔍 **高级搜索** | 多维度筛选和全文检索 | SQLite FTS + 元数据索引 |
| 📊 **政策分析** | 时效性检查和影响范围分析 | Python业务逻辑 |

---

## 🚀 快速开始

### 前置要求

- Python 3.8+
- RAGFlow 服务（用于文档处理）
- Qwen API 密钥（用于实体抽取）

### 30秒安装

```bash
# 1. 克隆仓库
git clone <repository-url>
cd Investopedia

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置系统
cp config/config.ini.template config/config.ini
# 编辑 config.ini，填入 RAGFlow 和 Qwen 配置

# 4. 启动应用
streamlit run app.py
# 访问 http://localhost:8501
```

### 5分钟快速体验

1. **上传文档** - 在RAGFlow Web界面上传PDF政策文档
2. **构建图谱** - 点击"文档管理"→"构建知识图谱"
3. **可视化** - 在"知识图谱"页面查看实体和关系
4. **智能问答** - 在"聊天"或"语音"页面提问

👉 详细步骤见 [快速开始指南](Documents/01-QUICK_START.md)

---

## 📖 文档导航

### 🎓 新手入门
- **[5分钟快速开始](Documents/01-QUICK_START.md)** - 部署和运行
- **[用户手册](Documents/03-USER_GUIDE.md)** - 功能使用说明
- **[常见问题](Documents/09-FAQ.md)** - FAQ和故障排查

### 👨‍💻 开发者
- **[系统架构](Documents/02-ARCHITECTURE.md)** - 整体设计和数据流
- **[开发者指南](Documents/04-DEVELOPER_GUIDE.md)** - 开发规范和扩展指南
- **[API文档](Documents/05-API_REFERENCE.md)** - 接口详细说明
- **[测试指南](Documents/07-TESTING.md)** - 单元测试

### 🔧 运维配置
- **[配置详解](Documents/06-CONFIGURATION.md)** - 所有配置项说明
- **[故障排查](Documents/08-TROUBLESHOOTING.md)** - 常见问题解决

### 📚 完整索引
- **[文档导航中心](Documents/00-INDEX.md)** - 按角色查找文档

---

## 🏗️ 系统架构（概览）

```
┌─────────────────────────────────────────────┐
│          Streamlit Web UI (app.py)          │
├─────────────────────────────────────────────┤
│ 🔍搜索 │ 💬聊天 │ 📊图谱 │ 🎤语音 │ 📄文档 │
├─────────────────────────────────────────────┤
│         Services Layer (src/services/)       │
│  RAGFlowClient │ QwenClient │ ChatService   │
├─────────────────────────────────────────────┤
│           Data Layer (src/database/)         │
│     GraphDAO │ PolicyDAO │ SQLite DB        │
├─────────────────────────────────────────────┤
│         External Services                    │
│  RAGFlow API │ Qwen API │ Whisper API      │
└─────────────────────────────────────────────┘
```

详见 [系统架构文档](Documents/02-ARCHITECTURE.md)

---

## 🌟 核心特性

### 📊 知识图谱（最新）

- ✅ **自动实体抽取** - Qwen大模型识别政策名称、发文机关、法律法规等8种实体
- ✅ **关系识别** - 自动抽取"发布"、"依据"、"适用于"等6种关系
- ✅ **可视化** - 基于Pyvis的交互式图谱，支持缩放、拖拽、筛选
- ✅ **去重优化** - 自动去除重复节点，保证数据质量
- ✅ **渐进式构建** - 支持全量重建和增量更新

### 💬 智能问答

- ✅ **RAGFlow Chat** - 基于知识库的对话式问答
- ✅ **参考文档** - 答案自动关联源文档
- ✅ **多轮对话** - 支持上下文理解
- ✅ **流式输出** - 类ChatGPT的打字效果

### 📄 文档管理

- ✅ **文档列表** - 显示RAGFlow知识库所有文档
- ✅ **分块查看** - 查看文档的chunk分块结果
- ✅ **内容搜索** - 在知识库中检索相关内容
- ✅ **元数据展示** - 文档大小、分块数、token数统计

---

## 📊 项目状态

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-red?logo=streamlit)
![RAGFlow](https://img.shields.io/badge/RAGFlow-0.13+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

- **当前版本**: v2026.2
- **开发状态**: 活跃开发中 🚧
- **最后更新**: 2026-02-01

---

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | Streamlit, Pyvis, NetworkX |
| **后端** | Python 3.8+, SQLite |
| **AI服务** | RAGFlow, Qwen (DashScope), Whisper |
| **数据处理** | Pandas, Jieba |
| **部署** | Docker (可选) |

---

## 📦 快速命令

```bash
# 开发
streamlit run app.py                    # 启动应用
python -m pytest tests/                 # 运行测试

# 数据库
sqlite3 data/database/policies.db       # 打开数据库
python tests/check_db_edges.py          # 检查图谱数据

# 清理
python tests/clean_duplicate_nodes.py   # 清理重复节点
rm -rf data/database/*.db               # 重置数据库
```

---

## 🤝 贡献指南

欢迎贡献！请查看 [开发者指南](Documents/04-DEVELOPER_GUIDE.md)

---

## 📞 获取帮助

- 📖 **文档** - 查看 [Documents/00-INDEX.md](Documents/00-INDEX.md)
- 🐛 **问题** - 提交 Issue 或查看 [故障排查](Documents/08-TROUBLESHOOTING.md)
- 💡 **建议** - 欢迎提交 Feature Request

---

## 📄 License

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 🤖 给AI助手的文档维护指南

> 本节专为AI助手设计，确保代码变更后文档保持同步和准确性

### 📝 文档更新原则

#### 1️⃣ 代码优先，文档跟随
```
✅ 必须遵循：代码变更 → 立即更新对应文档
❌ 禁止：先写文档再改代码，或代码改了文档不更新
```

#### 2️⃣ 文档必须准确反映实际代码
```
✅ 所有API示例必须是可运行的真实代码
✅ 所有配置项必须与config.ini一致
✅ 所有文件路径必须真实存在
❌ 禁止编造不存在的函数、参数、配置项
```

#### 3️⃣ 每次代码变更后的文档更新清单

**添加新功能时**:
- [ ] 更新 `Documents/05-API_REFERENCE.md` - 添加新API文档
- [ ] 更新 `Documents/03-USER_GUIDE.md` - 添加用户使用说明
- [ ] 更新 `Documents/technical/modules-inventory.md` - 更新模块清单
- [ ] 更新 `README.md` - 如果是重要功能，更新核心能力表格
- [ ] 更新 `Documents/00-INDEX.md` - 更新文档索引

**修改现有API时**:
- [ ] 更新 `Documents/05-API_REFERENCE.md` - 修改对应API文档
- [ ] 检查 `Documents/04-DEVELOPER_GUIDE.md` - 更新相关示例代码
- [ ] 检查 `Documents/technical/data-flow.md` - 更新数据流（如影响）

**修改配置项时**:
- [ ] 更新 `Documents/06-CONFIGURATION.md` - 配置项详解
- [ ] 更新 `config/config.ini.template` - 配置模板
- [ ] 更新 `Documents/technical/config-system.md` - 配置系统文档

**修改数据库schema时**:
- [ ] 更新 `src/database/schema.sql` - 数据库结构
- [ ] 更新 `Documents/05-API_REFERENCE.md` - DAO方法文档
- [ ] 更新 `Documents/technical/data-flow.md` - 数据流图

**重构代码时**:
- [ ] 更新 `Documents/02-ARCHITECTURE.md` - 系统架构
- [ ] 更新 `Documents/technical/code-structure.md` - 代码结构
- [ ] 更新 `Documents/technical/modules-inventory.md` - 模块清单
- [ ] 检查所有示例代码是否需要更新

### 📐 文档编写规范

#### Markdown格式规范
```markdown
# 使用中文标题和正文
# 代码块必须指定语言
```python
def example():
    pass
```

# 使用表格对比
| 项目 | 说明 |
|------|------|
| 示例 | 内容 |

# 使用emoji增强可读性
✅ 正确示例
❌ 错误示例
🔥 重要提示
⚠️ 注意事项
```

#### 代码示例规范
```python
# ✅ 好的示例：完整可运行
from src.services.ragflow_client import get_ragflow_client

client = get_ragflow_client()
docs = client.get_documents("policy_demo_kb")
print(f"获取到 {len(docs)} 个文档")

# ❌ 坏的示例：伪代码、不完整
client.get_documents()  # 缺少参数说明
result = magic_function()  # 不存在的函数
```

#### API文档模板
```markdown
### function_name()

\`\`\`python
def function_name(param1: str, param2: int = 0) -> Dict
\`\`\`

**功能**: 一句话描述功能

**参数**:
- `param1` (str): 参数说明
- `param2` (int, 可选): 参数说明，默认0

**返回值**:
\`\`\`python
{
    "key": "value",
    "status": "success"
}
\`\`\`

**示例**:
\`\`\`python
result = function_name("test", 10)
print(result['status'])
\`\`\`

**异常**:
- `ValueError`: 何时抛出
- `ConnectionError`: 何时抛出
```

### 🔍 文档质量检查清单

提交文档前，必须检查：

- [ ] **准确性** - 所有代码路径、函数名、参数与实际代码一致
- [ ] **完整性** - 所有公开API都有文档
- [ ] **可读性** - 使用清晰的标题层级和段落结构
- [ ] **示例性** - 重要功能都有可运行的代码示例
- [ ] **时效性** - 文档最后更新时间与代码变更时间接近
- [ ] **链接性** - 所有内部链接都指向正确的文档
- [ ] **索引性** - 新文档已添加到 `00-INDEX.md`

### 🚨 强制规则

1. **禁止使用"TODO"、"待完善"等占位符** - 必须完整编写
2. **禁止复制粘贴过时文档** - 必须验证当前代码
3. **禁止使用模糊表述** - 如"大约"、"可能"、"应该"，必须精确
4. **每个示例代码必须实际测试过** - 确保可运行
5. **配置项必须与config.ini.template一致** - 定期对比验证

### 📊 文档维护责任矩阵

| 文档 | 何时更新 | 负责检查的文件 |
|------|---------|--------------|
| `README.md` | 新增核心功能 | `app.py`, `src/pages/` |
| `02-ARCHITECTURE.md` | 架构变更、新增服务 | `src/services/`, `src/database/` |
| `03-USER_GUIDE.md` | 用户可见功能变更 | `src/pages/`, `src/components/` |
| `04-DEVELOPER_GUIDE.md` | 开发流程、规范变更 | 测试代码、CI配置 |
| `05-API_REFERENCE.md` | 任何API变更 | 所有 `src/` 下的Python文件 |
| `06-CONFIGURATION.md` | 配置项变更 | `config/config.ini`, `src/config/` |
| `technical/*.md` | 技术实现变更 | 对应模块代码 |

### 🎯 AI助手工作流程

每次修改代码后，遵循此流程：

```
1. 修改代码
   ↓
2. 运行测试（确保代码可用）
   ↓
3. 识别受影响的文档（使用上面的责任矩阵）
   ↓
4. 更新对应文档（使用文档编写规范）
   ↓
5. 验证文档准确性（运行示例代码）
   ↓
6. 更新文档索引（00-INDEX.md）
   ↓
7. 提交代码和文档（一起提交）
```

### 💡 提示词模板

当用户要求修改代码时，AI应该主动询问：

```
✅ 我已经完成了代码修改。是否需要我同步更新以下文档？
- Documents/05-API_REFERENCE.md（添加新API文档）
- Documents/03-USER_GUIDE.md（更新用户手册）
- README.md（如果是重要功能）

请确认是否更新，或者我直接按照文档维护规范自动更新。
```

---

