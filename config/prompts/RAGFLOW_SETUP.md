# RAGFlow Chat Assistant 配置指南

## ⚠️ 重要说明：RAGFlow变量机制

### RAGFlow的自动变量注入
RAGFlow在调用LLM时会**自动注入**以下系统变量：
- `{question}` - 用户通过 `session.ask(question=...)` 传入的问题
- `{knowledge}` - RAGFlow从知识库检索到的文档内容

### 我们的增强流程
1. 用户提问："特许经营合同包括什么？"
2. Python代码：图谱检索 → 提取关系 → 构建增强问题：
   ```
   特许经营合同包括什么？
   [知识图谱关系]
   • 商业特许经营管理条例 → relates_to → 特许人
   ```
3. 调用 `session.ask(question=增强问题)`
4. RAGFlow自动：`{question}=增强问题`, `{knowledge}=检索内容`
5. LLM收到的Prompt：变量被真实值替换

**所以System Prompt里写 `{question}` 和 `{knowledge}` 是正确的！**

---

## 📋 配置步骤

### 1. 打开 RAGFlow Web UI
访问：http://localhost (或你的RAGFlow服务地址)

### 2. 创建/编辑 Chat Assistant

#### 基本信息
- **Name**: `政策聊天助手` (必须与代码中一致)
- **描述**: 基于知识图谱增强的政策法规智能助手

#### 关联知识库
- 选择知识库：`policy_demo_kb` (或你的知识库名称)
- 确保知识库中已上传政策文档

#### System Prompt（系统提示词）
**复制以下内容到RAGFlow的System Prompt编辑框**：

```
你是专业的政策法规智能助手。请基于 {knowledge} 中的政策文档内容回答用户问题 {question}。

【核心要求】
1. 严格基于 {knowledge} 回答，不要编造信息
2. {question} 可能包含知识图谱关系（格式：实体A → 关系 → 实体B），优先覆盖图谱中的实体
3. 使用结构化格式：加粗核心要点，编号列表，引用文档名称

【回答格式】
**政策依据**：相关政策文件（从 {knowledge} 获取 document_name）
**核心要点**：
1. 要点一：具体内容（引用 {knowledge} 中的 content）
2. 要点二：...

**关键关系**：如果 {question} 包含图谱关系，说明实体间的联系
**实施建议**：具体操作指引和注意事项

【特殊情况】
- {knowledge} 为空：说明未检索到相关文档，建议换个问法
- 问题超范围：说明专长领域（商业特许经营、专项债券、数据资产）

保持专业、客观、实用。优先使用政策术语，引用原文时保持准确。
```

### 3. 高级设置（可选）

#### Prompt变量配置（重要！）
在Prompt配置区域，确保以下变量已声明：
- `knowledge` (可选) - 检索到的文档内容
- `question` (必填) - 用户问题

**Web UI操作**：
1. 在Prompt编辑区下方找到"Variables"设置
2. 确保包含：
   - `knowledge` (Optional: Yes)
   - `question` (Optional: No)

**注意**：如果使用我们的Python代码自动创建Assistant，这些变量会自动配置。

#### 检索设置
- **Top K**: 5-10 (返回最相关的5-10个文档片段)
- **相似度阈值**: 0.3-0.5
- **Rerank**: 开启（推荐）

#### 生成设置
- **Temperature**: 0.1-0.3 (较低温度保证准确性)
- **Max Tokens**: 2000-4000

### 4. 保存配置
点击"保存"按钮，完成Assistant创建

---

## 🎯 使用效果

### 增强前（纯向量检索）
```
用户: 特许经营合同应当包括那些内容哇？
     ↓
RAGFlow: [检索相关文档] → 生成答案
```

### 增强后（图谱 + 向量）
```
用户: 特许经营合同应当包括那些内容哇？
     ↓
系统: [大模型提取实体] → [图谱匹配] → [提取关系]
     ↓
增强问题:
  特许经营合同应当包括那些内容哇？
  
  [知识图谱关系]
    • 商业特许经营管理条例 → relates_to → 特许人
    • 商业特许经营管理条例 → relates_to → 被特许人
    • 商业特许经营管理条例 → relates_to → 信息披露制度
    • 商业特许经营管理条例 → relates_to → 商标
    • 商业特许经营管理条例 → relates_to → 专利
     ↓
RAGFlow: [检索相关文档] → [理解图谱关系] → 生成更准确的答案
```

**关键区别**：
- ✅ LLM明确知道要覆盖：特许人、被特许人、信息披露、商标、专利等关键要点
- ✅ 回答更全面、结构化
- ✅ 不会遗漏重要条款

---

## 📝 注意事项

1. **Assistant名称必须匹配**
   - 代码中配置的名称：`政策聊天助手`
   - 如需修改，请同步修改 `src/services/chat_service.py` 中的 `self.assistant_name`

2. **System Prompt保持同步**
   - 完整版在：`config/prompts/ragflow_chat_system_prompt.txt`
   - 简化版见上方配置步骤
   - 根据实际需求选择使用

3. **知识库关联**
   - 确保知识库中有政策文档
   - 文档需要先在RAGFlow中解析完成

4. **测试验证**
   - 配置完成后，在聊天页面测试
   - 检查日志中是否有"问题增强完成"提示
   - 验证答案是否包含图谱关系中的概念

---

## 🔧 故障排查

### 问题1：找不到Assistant
**错误信息**：`Chat Assistant '政策聊天助手' 不存在`

**解决方案**：
1. 检查RAGFlow Web UI中是否已创建同名Assistant
2. 确认名称完全匹配（包括空格、标点）

### 问题2：图谱增强无效
**检查**：
1. 查看日志：是否有"大模型提取到实体"
2. 查看日志：是否有"问题增强完成，添加了 X 条图谱关系"
3. 如果关系为0，可能是图谱数据库为空或实体匹配失败

### 问题3：回答质量不佳
**优化方向**：
1. 调整System Prompt，增加更具体的指导
2. 提高Top K值，检索更多文档
3. 检查知识库文档质量和完整性

---

## 📚 相关文件

- 完整System Prompt: `config/prompts/ragflow_chat_system_prompt.txt`
- 实体提取Prompt: `config/prompts/query_entity_extraction.txt`
- Chat服务代码: `src/services/chat_service.py`
- 混合检索代码: `src/services/hybrid_retriever.py`
