# 系统工作流程指南

> 本文档说明系统的实际工作流程（非开发历史），帮助理解各模块的交互逻辑

**更新日期:** 2026年1月24日

---

## 🎯 核心工作流程

### 1. 文档上传与处理

```
用户上传文件 (PDF/DOCX/TXT)
        ↓
[render_upload_section @ documents_page.py]
        ↓
_extract_file_content(uploaded_file)
    ├─ 识别文件类型 (扩展名)
    ├─ PDF: pdfplumber.open(BytesIO) 
    │       → for page in pdf.pages: page.extract_text()
    ├─ DOCX: Document(BytesIO)
    │        → for para in doc.paragraphs: para.text
    └─ TXT: decode('utf-8') 或 decode('gbk')
        ↓
得到纯文本内容
        ↓
generate_summary(content) [src/utils/summarizer.py]
    ├─ _summarize_with_deepseek(text) [优先级1]
    │  └─ DeepSeek API + prompts/summarize_policy.txt
    │     输出5部分: 政策目的/核心内容/适用范围/关键时间/主要影响
    │     参数: temperature=0.3, max_tokens=1200, top_p=0.9
    │
    ├─ _summarize_with_ragflow(text) [优先级2] 
    │  └─ RAGFlow API (http://127.0.0.1:7890/api/llm_chat)
    │
    └─ text[:max_length] [回退]
        ↓
PolicyDAO.create_policy(policy_data)
    ├─ 验证document_number唯一性
    ├─ 插入 policies 表
    ├─ 返回 policy_id
    └─ 成功提示显示摘要内容
        ↓
数据库保存成功
```

**关键代码片段:**

```python
# documents_page.py - 上传处理流程
if uploaded_file:
    # 1. 提取文本
    content = _extract_file_content(uploaded_file)  # ← 智能提取
    
    # 2. 生成摘要
    summary = generate_summary(content)  # ← 使用默认max_length=1500
    
    # 3. 保存到数据库
    dao = PolicyDAO()
    if document_number and not dao.get_policy_by_document_number(...):
        policy_data = {
            'title': title,
            'content': content,
            'summary': summary,
            'document_number': document_number,
            ...
        }
        policy_id = dao.create_policy(policy_data)
        st.success(f"✅ 文档已上传")
```

---

### 2. 知识图谱构建与展示

```
页面加载 [graph_page.py @ show()]
        ↓
session_state.graph 为空?
    ├─ 是: build_policy_graph()
    └─ 否: 使用缓存
        ↓
build_policy_graph() [核心函数]
    ├─ dao = PolicyDAO()
    ├─ policies = dao.get_policies()  # ← 返回 List[Dict]!
    │
    ├─ 第1步: 添加政策节点
    │  for policy in policies:
    │      node = GraphNode(
    │          node_id=f"policy_{policy['id']}",  # ← 字典访问!
    │          label=policy.get('title'),
    │          node_type=NodeType.POLICY
    │      )
    │      graph.add_node(node)  # ← 对象参数，非关键字参数!
    │
    ├─ 第2步: 添加机关节点 + 边
    │  authorities = {p['issuing_authority'] for p in policies}
    │  for auth in authorities:
    │      node = GraphNode(node_id=f"authority_{auth}", ...)
    │      graph.add_node(node)
    │      
    │      for policy in policies:
    │          if policy['issuing_authority'] == auth:
    │              edge = GraphEdge(
    │                  source_id=f"policy_{policy['id']}",
    │                  target_id=f"authority_{auth}",
    │                  relation_type=RelationType.ISSUED_BY
    │              )
    │              graph.add_edge(edge)
    │
    ├─ 第3步: 添加地区节点 + 边
    │  (同上，关系类型为 APPLIES_TO)
    │
    └─ 第4步: 添加政策间关系
       for policy in policies:
           relations = dao.get_policy_relations(policy['id'])  # ← List[Dict]!
           for rel in relations:
               edge = GraphEdge(
                   source_id=f"policy_{policy['id']}",
                   target_id=f"policy_{rel['target_policy_id']}",  # ← 字典访问!
                   relation_type=rel.get('relation_type')
               )
               graph.add_edge(edge)
        ↓
返回 PolicyGraph (NetworkX图)
        ↓
[col_main] 显示图谱
    ├─ render_graph_stats(graph)  → 节点数、边数、密度
    ├─ render_network_graph(graph) → Pyvis可视化
    └─ render_node_details(node)  → 点击节点显示详情
```

**⚠️ 常见错误:**

```python
# ❌ 错误1: 对象属性访问 (policies是Dict[]，不是Policy[])
for policy in policies:
    policy.id              # AttributeError!
    policy.metadata.title  # AttributeError!

# ✅ 正确: 字典访问
for policy in policies:
    policy['id']
    policy.get('title')

# ❌ 错误2: 使用关键字参数
graph.add_node(
    node_id=f"policy_{policy['id']}",  # ✗ 不支持
    label=policy.get('title')
)

# ✅ 正确: 创建对象后传入
node = GraphNode(
    node_id=f"policy_{policy['id']}",
    label=policy.get('title')
)
graph.add_node(node)  # ← 对象参数
```

---

### 3. 搜索流程

```
用户输入关键词
        ↓
[render_search_panel @ search_page.py]
    ├─ 快速搜索框
    ├─ 高级筛选:
    │  ├─ policy_type (政策类型)
    │  ├─ region (地区)
    │  ├─ date_from / date_to (时间范围)
    │  └─ status (状态)
    └─ 搜索按钮点击
        ↓
dao.get_policies(filters={...})  [PolicyDAO]
    ├─ 构建SQL WHERE条件
    ├─ 执行查询
    └─ 返回 List[Dict[str, Any]]
        ↓
render_search_results(policies)  [search_ui.py]
    ├─ 遍历结果列表
    ├─ 显示卡片:
    │  ├─ 标题、文号
    │  ├─ 摘要、标签
    │  └─ 操作按钮
    └─ 支持点击展开详情
        ↓
用户查看政策详情
```

**SQL示例:**
```sql
SELECT * FROM policies 
WHERE 1=1
  AND policy_type = ?  -- 如果指定
  AND region = ?       -- 如果指定
  AND publish_date >= ? -- 如果指定起始日期
  AND publish_date <= ? -- 如果指定结束日期
  AND status = ?       -- 如果指定状态
ORDER BY publish_date DESC 
LIMIT ? OFFSET ?
```

---

## 📊 数据流转

### 类型系统

```
文件输入
  │
  ├─→ PDF → pdfplumber → 文本
  ├─→ DOCX → python-docx → 文本
  └─→ TXT → 解码 → 文本
            ↓
          字符串 (str)
            ↓
    generate_summary(text: str)
            ↓
    返回字符串 (str)
            ↓
  PolicyDAO.create_policy(Dict)
            ↓
          int (policy_id)
            ↓
   数据库查询
            ↓
  List[Dict[str, Any]]  ← ⚠️ 关键：这是字典，不是对象！
            ↓
   遍历policies
            ↓
  policy['id']          ← 字典键访问
  policy.get('title')   ← 字典get方法
```

### 对象模型

```
GraphNode
  ├─ node_id: str
  ├─ label: str
  ├─ node_type: NodeType (enum)
  └─ attributes: Dict[str, Any]

GraphEdge
  ├─ source_id: str
  ├─ target_id: str
  ├─ relation_type: RelationType (enum)
  ├─ label: str
  └─ attributes: Dict[str, Any]

PolicyGraph (基于NetworkX)
  ├─ add_node(node: GraphNode)
  ├─ add_edge(edge: GraphEdge)
  ├─ get_node_count() → int
  └─ get_edge_count() → int
```

---

## 🔧 配置管理

### 配置加载流程

```
app.py 启动
    ↓
from src.config import get_config
    ↓
get_config() [单例模式]
    ├─ 第1次调用: ConfigLoader初始化
    │  ├─ 读取 config/config.ini
    │  ├─ 验证必需字段
    │  └─ 初始化数据库
    │
    └─ 后续调用: 返回同一实例
        ↓
config 对象
  ├─ config.data_dir → Path
  ├─ config.deepseek_api_key → str
  ├─ config.ragflow_base_url → str
  └─ 其他配置项
```

### 关键配置项

| 项目 | 文件 | 默认值 | 说明 |
|------|------|--------|------|
| DEEPSEEK_API_KEY | config.ini | - | 必需，用于摘要/问答 |
| RAGFLOW_BASE_URL | config.ini | http://127.0.0.1:7890 | RAGFlow服务地址 |
| WHISPER_BASE_URL | config.ini | http://127.0.0.1:9000 | Whisper服务地址 |
| DATABASE_PATH | config.ini | data/database | SQLite数据库目录 |

---

## 📈 性能优化

### 缓存策略

```python
# graph_page.py
if "graph" not in st.session_state:
    with st.spinner("正在加载知识图谱..."):
        st.session_state.graph = build_policy_graph()

# 后续加载直接使用缓存
# 仅在新文档上传时清空缓存
if new_document_uploaded:
    st.session_state.documents_list = []  # 清空缓存
```

### 数据库索引

```sql
-- 建议添加的索引 (提高搜索性能)
CREATE INDEX idx_document_number ON policies(document_number);
CREATE INDEX idx_policy_type ON policies(policy_type);
CREATE INDEX idx_region ON policies(region);
CREATE INDEX idx_publish_date ON policies(publish_date);
CREATE INDEX idx_title ON policies(title);
```

---

## 🚨 常见问题排查

### Q1: 摘要缺少部分内容
**原因:** DeepSeek Prompt未强制所有部分  
**检查:**
1. prompts/summarize_policy.txt 是否存在
2. Prompt中是否有"缺一不可"的要求
3. max_tokens是否足够 (建议≥1000)

**修复:**
```python
# summarizer.py
max_tokens = 1200  # 足够空间
# Prompt中明确声明
"你的任务是按照要求严格输出5个部分的摘要，缺一不可。"
```

### Q2: 图谱节点显示为空
**原因:** 数据库为空或数据访问错误  
**检查:**
1. `PolicyDAO.get_policies()` 是否返回数据
2. 是否正确使用字典访问 (`policy['id']` 而非 `policy.id`)
3. 节点label是否为空

**修复:**
```python
# graph_page.py
node = GraphNode(
    node_id=f"policy_{policy['id']}",
    label=policy.get('title', '无标题'),  # ← 提供默认值
)
```

### Q3: PDF上传失败
**原因:** PDF提取库未安装或PDF格式问题  
**检查:**
1. `pip list | grep pdfplumber` → 是否已安装
2. 查看日志输出
3. 尝试其他PDF文件

**修复:**
```bash
pip install pdfplumber==0.10.3
```

---

## 📚 相关文档

- [QUICK_START.md](QUICK_START.md) - 快速开始指南
- [README.md](README.md) - 项目说明
- [config/config.ini.template](config/config.ini.template) - 配置模板

---

**文档由实际测试验证，2026年1月24日最后更新**
