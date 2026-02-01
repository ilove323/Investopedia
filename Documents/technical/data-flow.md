# 🕸️ 数据流详解

> 详细解释系统中的3条核心数据流  
> 阅读时间: 20分钟

---

## 📋 核心数据流

系统有3条核心数据流：
1. **文档上传与同步流** - RAGFlow → SQLite
2. **知识图谱构建流** - RAGFlow + Qwen → SQLite
3. **智能问答流** - RAGFlow Chat Assistant → 用户

---

## 1️⃣ 文档上传与同步流

### 完整流程图

```
┌─────────────┐
│   用户      │
└──────┬──────┘
       │ ① 上传PDF/DOCX
       ↓
┌─────────────────┐
│ RAGFlow Web界面 │
└──────┬──────────┘
       │ ② 自动处理
       ├─ 文本提取
       ├─ 分块 (chunking)
       ├─ 向量化 (embedding)
       └─ 存储到向量数据库
       ↓
┌─────────────────┐
│ RAGFlow知识库   │
│ - documents     │
│ - chunks        │
│ - vectors       │
└──────┬──────────┘
       │ ③ DocumentsPage触发同步
       ↓
┌─────────────────────────┐
│ DataSyncService         │
│ sync_documents_to_database() │
└──────┬──────────────────┘
       │ ④ 调用RAGFlow API
       ↓
┌─────────────────┐
│ RAGFlowClient   │
│ get_documents() │
└──────┬──────────┘
       │ ⑤ 返回文档元数据
       ↓
┌─────────────────┐
│ PolicyDAO       │
│ create_policy() │
│ update_policy() │
└──────┬──────────┘
       │ ⑥ 存储到SQLite
       ↓
┌─────────────────┐
│ SQLite policies │
│ - id            │
│ - ragflow_id    │
│ - title         │
│ - policy_type   │
│ - region        │
│ - ...           │
└─────────────────┘
```

---

### 详细步骤

#### 步骤①: 用户上传文档
```bash
# 访问RAGFlow Web界面
http://localhost:9380

# 登录后进入知识库管理
# 选择知识库: policy_demo_kb
# 点击"上传文档"
# 选择文件: 科技创新政策.pdf
# 点击"确定"
```

---

#### 步骤②: RAGFlow自动处理
```python
# RAGFlow内部流程（自动）
1. 文本提取
   - PDF → 纯文本
   - 保留格式（标题、段落、表格等）

2. 智能分块 (Chunking)
   - 根据语义边界切分
   - 块大小: 512 tokens (可配置)
   - 块重叠: 50 tokens
   - 生成chunk_id

3. 向量化 (Embedding)
   - 调用嵌入模型（如BGE、OpenAI Ada-002）
   - 生成768维向量（根据模型）
   - 存储到向量数据库

4. 元数据提取
   - 文件名、大小、上传时间
   - chunk数量、token数量
   - 文档状态（processing → completed）
```

---

#### 步骤③: 触发同步
```python
# src/pages/documents_page.py
def show():
    st.title("📄 文档管理")
    
    if st.button("🔄 同步文档到本地数据库"):
        with st.spinner("正在同步..."):
            sync_service = DataSyncService()
            result = sync_service.sync_documents_to_database("policy_demo_kb")
            
            st.success(f"同步完成！新增/更新: {result['synced_count']} 个文档")
```

---

#### 步骤④: 调用RAGFlow API
```python
# src/services/data_sync.py
def sync_documents_to_database(self, kb_name: str) -> Dict:
    # 1. 获取RAGFlow文档列表
    ragflow_client = get_ragflow_client()
    documents = ragflow_client.get_documents(kb_name)
    
    # 2. 遍历每个文档
    synced_count = 0
    skipped_count = 0
    
    for doc in documents:
        doc_id = doc['id']
        
        # 3. 检查本地是否已存在
        policy_dao = get_policy_dao()
        existing_policy = policy_dao.get_policy_by_ragflow_id(doc_id)
        
        # 4. 提取元数据
        metadata = {
            'ragflow_id': doc_id,
            'title': doc['name'].replace('.pdf', ''),
            'size': doc.get('size', 0),
            'chunk_count': doc.get('chunk_count', 0),
            'token_count': doc.get('token_count', 0),
            'created_at': doc.get('created_at'),
            # ...更多字段从MetadataExtractor提取
        }
        
        # 5. 创建或更新
        if existing_policy is None:
            policy_dao.create_policy(metadata)
            synced_count += 1
        else:
            policy_dao.update_policy(existing_policy.id, metadata)
            synced_count += 1
    
    return {
        'synced_count': synced_count,
        'skipped_count': skipped_count
    }
```

---

#### 步骤⑤: 元数据提取（可选）
```python
# src/business/metadata_extractor.py
class MetadataExtractor:
    def extract_all(self, content: str) -> Dict:
        """从政策文本提取元数据"""
        return {
            'policy_type': self._extract_policy_type(content),
            'issuing_authority': self._extract_authority(content),
            'region': self._extract_region(content),
            'document_number': self._extract_doc_number(content),
            'effective_date': self._extract_effective_date(content)
        }
    
    def _extract_authority(self, content: str) -> str:
        """提取发文机关"""
        # 正则匹配: "XX省XX厅", "国务院", "XX市政府"等
        patterns = [
            r'([\u4e00-\u9fa5]+省[\u4e00-\u9fa5]+厅)',
            r'([\u4e00-\u9fa5]+市[\u4e00-\u9fa5]+局)',
            r'(国务院|发改委|财政部)',
        ]
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        return "未知"
```

---

#### 步骤⑥: 存储到SQLite
```python
# src/database/policy_dao.py
def create_policy(self, metadata: Dict) -> int:
    conn = self.db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO policies (
            ragflow_id, title, policy_type, region,
            issuing_authority, document_number,
            effective_date, expiry_date, status,
            content, summary, chunk_count, token_count,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        metadata['ragflow_id'],
        metadata['title'],
        metadata.get('policy_type', ''),
        metadata.get('region', ''),
        metadata.get('issuing_authority', ''),
        metadata.get('document_number', ''),
        metadata.get('effective_date'),
        metadata.get('expiry_date'),
        metadata.get('status', '有效'),
        metadata.get('content', ''),
        metadata.get('summary', ''),
        metadata.get('chunk_count', 0),
        metadata.get('token_count', 0),
        datetime.now(),
        datetime.now()
    ))
    
    conn.commit()
    return cursor.lastrowid
```

---

### 数据对比

| 数据 | RAGFlow | SQLite |
|-----|---------|--------|
| 文档完整内容 | ✅ Chunks拼接 | ❌ 不存储（节省空间） |
| 向量嵌入 | ✅ 768维向量 | ❌ 不存储 |
| 元数据 | ✅ 基础元数据 | ✅ 增强元数据 |
| 政策类型 | ❌ | ✅ 自动提取 |
| 发文机关 | ❌ | ✅ 自动提取 |
| 时效性分析 | ❌ | ✅ 有效/过期 |
| 标签体系 | ❌ | ✅ tags表 |

**设计思路**: RAGFlow负责向量检索，SQLite负责结构化查询和分析

---

## 2️⃣ 知识图谱构建流

### 完整流程图

```
┌──────────────┐
│ GraphPage    │ 用户点击"构建图谱"
└──────┬───────┘
       │
       ↓
┌──────────────────────────┐
│ DataSyncService          │
│ build_knowledge_graph()  │
└──────┬───────────────────┘
       │
       ├─────────────────────────────┐
       │                             │
       ↓                             ↓
┌──────────────┐            ┌──────────────┐
│RAGFlowClient │            │ GraphDAO     │
│get_documents()│            │load_graph()  │ (如果增量构建)
└──────┬───────┘            └──────┬───────┘
       │                             │
       ↓                             ↓
  遍历每个文档                   已处理文档列表
       │
       ├─ get_document_content(doc_id)  # 获取完整内容
       │  └─ 拼接所有chunks
       │
       ├─ QwenClient.extract_entities_and_relations(content)
       │  ├─ 加载提示词模板
       │  ├─ 调用Qwen API
       │  ├─ 解析JSON返回
       │  └─ 返回 {entities: [...], relations: [...]}
       │
       ├─ 构建GraphNode对象
       │  └─ 去重（节点ID、文档名去.pdf后缀）
       │
       ├─ 构建GraphEdge对象
       │  └─ 验证source/target存在
       │
       └─ 累积到graph_data
              │
              ↓
       ┌──────────────┐
       │ GraphDAO     │
       │ save_graph() │
       └──────┬───────┘
              │
              ↓
       ┌──────────────────┐
       │ SQLite           │
       │ knowledge_graph  │
       │ - graph_data (JSON) │
       │ - node_count     │
       │ - edge_count     │
       └──────────────────┘
```

---

### 详细步骤

#### 步骤1: 用户触发
```python
# src/pages/graph_page.py
def show():
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔨 全量构建"):
            sync_service = DataSyncService()
            result = sync_service.build_knowledge_graph(
                kb_name="policy_demo_kb",
                is_incremental=False  # 全量
            )
            st.success(f"构建完成！节点: {result['node_count']}, 边: {result['edge_count']}")
    
    with col2:
        if st.button("⚡ 增量构建"):
            result = sync_service.build_knowledge_graph(
                kb_name="policy_demo_kb",
                is_incremental=True  # 增量
            )
```

---

#### 步骤2: 获取文档列表
```python
# src/services/data_sync.py
def build_knowledge_graph(self, kb_name: str, is_incremental: bool = False):
    ragflow_client = get_ragflow_client()
    qwen_client = get_qwen_client()
    graph_dao = get_graph_dao()
    
    # 1. 获取文档列表
    documents = ragflow_client.get_documents(kb_name)
    print(f"获取到 {len(documents)} 个文档")
    
    # 2. 如果是增量构建，加载已有图谱
    seen_doc_names = set()
    if is_incremental:
        existing_graph = graph_dao.load_graph()
        if existing_graph:
            # 提取已处理的文档名
            for node in existing_graph['nodes']:
                if node['type'] == 'POLICY':
                    seen_doc_names.add(node['label'])
    
    # 3. 初始化图谱数据结构
    all_nodes = []
    all_edges = []
    seen_node_ids = set()
```

---

#### 步骤3: 遍历文档并调用Qwen
```python
    # 4. 遍历每个文档
    for idx, doc in enumerate(documents):
        doc_id = doc['id']
        doc_name = doc['name'].replace('.pdf', '').replace('.docx', '')
        
        # 增量构建：跳过已处理文档
        if is_incremental and doc_name in seen_doc_names:
            continue
        
        print(f"[{idx+1}/{len(documents)}] 处理文档: {doc_name}")
        
        try:
            # 5. 获取文档完整内容
            content = ragflow_client.get_document_content(doc_id, kb_name)
            
            # 限制长度（避免Qwen超出token限制）
            if len(content) > 10000:
                content = content[:10000]
            
            # 6. 调用Qwen抽取实体和关系
            extraction = qwen_client.extract_entities_and_relations(
                text=content,
                doc_title=doc_name
            )
            
            # 7. 构建节点
            for entity in extraction['entities']:
                node_id = f"{entity['type']}_{entity['text']}"
                
                # 去重
                if node_id in seen_node_ids:
                    continue
                
                seen_node_ids.add(node_id)
                
                all_nodes.append({
                    'id': node_id,
                    'label': entity['text'],
                    'type': entity['type'],
                    'description': entity.get('description', ''),
                    'source_doc': doc_name
                })
            
            # 8. 构建边
            for relation in extraction['relations']:
                source_id = f"UNKNOWN_{relation['source']}"
                target_id = f"UNKNOWN_{relation['target']}"
                
                # 查找实际的节点ID
                for node in all_nodes:
                    if node['label'] == relation['source']:
                        source_id = node['id']
                    if node['label'] == relation['target']:
                        target_id = node['id']
                
                # 验证节点存在
                if source_id.startswith('UNKNOWN') or target_id.startswith('UNKNOWN'):
                    continue
                
                all_edges.append({
                    'from': source_id,
                    'to': target_id,
                    'type': relation['type'],
                    'source_doc': doc_name
                })
        
        except Exception as e:
            print(f"处理文档 {doc_name} 失败: {e}")
            continue
```

---

#### 步骤4: Qwen提示词工程
```
# config/prompts/entity_extraction.txt

你是一个专业的政策文本分析专家。请从以下政策文本中提取实体和关系。

文档标题: {doc_title}

政策文本:
{text}

请严格按照以下JSON格式返回结果:

{{
  "entities": [
    {{
      "text": "实体名称",
      "type": "POLICY | AUTHORITY | REGION | CONCEPT | PROJECT",
      "description": "简短描述"
    }}
  ],
  "relations": [
    {{
      "source": "源实体名称（必须是entities中的text）",
      "target": "目标实体名称（必须是entities中的text）",
      "type": "ISSUED_BY | APPLIES_TO | REFERENCES | AFFECTS | BELONGS_TO"
    }}
  ]
}}

注意事项:
1. 实体类型:
   - POLICY: 政策文档本身
   - AUTHORITY: 发布机构（如"广东省科技厅"）
   - REGION: 地区（如"广东省"、"深圳市"）
   - CONCEPT: 抽象概念（如"高新技术企业"、"研发费用加计扣除"）
   - PROJECT: 具体项目或计划

2. 关系类型:
   - ISSUED_BY: 发布关系（政策 → 机构）
   - APPLIES_TO: 适用关系（政策 → 对象）
   - REFERENCES: 引用关系（政策 → 政策）
   - AFFECTS: 影响关系（政策 → 概念/项目）
   - BELONGS_TO: 从属关系（机构 → 地区）

3. relations中的source和target必须是entities中出现的text，完全匹配

4. 只返回JSON，不要任何其他文字
```

---

#### 步骤5: Qwen返回示例
```json
{
  "entities": [
    {
      "text": "科技创新政策",
      "type": "POLICY",
      "description": "广东省科技创新相关政策文件"
    },
    {
      "text": "广东省科技厅",
      "type": "AUTHORITY",
      "description": "政策发布机构"
    },
    {
      "text": "广东省",
      "type": "REGION",
      "description": "政策适用地区"
    },
    {
      "text": "高新技术企业",
      "type": "CONCEPT",
      "description": "政策扶持对象"
    },
    {
      "text": "研发费用加计扣除",
      "type": "CONCEPT",
      "description": "税收优惠措施"
    }
  ],
  "relations": [
    {
      "source": "科技创新政策",
      "target": "广东省科技厅",
      "type": "ISSUED_BY"
    },
    {
      "source": "科技创新政策",
      "target": "高新技术企业",
      "type": "APPLIES_TO"
    },
    {
      "source": "科技创新政策",
      "target": "研发费用加计扣除",
      "type": "AFFECTS"
    },
    {
      "source": "广东省科技厅",
      "target": "广东省",
      "type": "BELONGS_TO"
    }
  ]
}
```

---

#### 步骤6: 保存图谱
```python
    # 9. 保存到数据库
    graph_data = {
        'nodes': all_nodes,
        'edges': all_edges
    }
    
    graph_dao.save_graph(graph_data, is_incremental=is_incremental)
    
    # 10. 返回统计结果
    return {
        'node_count': len(all_nodes),
        'edge_count': len(all_edges),
        'document_count': len(documents),
        'elapsed_time': time.time() - start_time
    }
```

---

### 性能数据

| 指标 | 全量构建 (40文档) | 增量构建 (5新文档) |
|------|----------------|------------------|
| 总耗时 | ~145秒 (2.4分钟) | ~18秒 |
| 单文档耗时 | ~3.6秒 | ~3.6秒 |
| Qwen调用次数 | 40次 | 5次 |
| Token消耗 | ~120K tokens | ~15K tokens |
| 成本 (qwen-plus) | ~￥0.48 | ~￥0.06 |
| 生成节点数 | 40个 | 8个 |
| 生成边数 | 73条 | 12条 |

**优化建议**:
1. 使用qwen-turbo替代qwen-plus（降低50%成本，速度提升30%）
2. 限制文档长度（截取前5000字）
3. 批量调用（如果Qwen支持）
4. 缓存已处理文档的结果

---

## 3️⃣ 智能问答流

### 完整流程图

```
┌──────────────┐
│   ChatPage   │ 用户输入问题
└──────┬───────┘
       │
       ↓
┌──────────────────┐
│ ChatService      │
│ chat(question,   │
│      session_id, │
│      stream=True)│
└──────┬───────────┘
       │
       ↓
┌────────────────────────┐
│ RAGFlow Chat Assistant │
│ POST /v1/chat          │
│ {                      │
│   "question": "...",   │
│   "session_id": "...", │
│   "stream": true       │
│ }                      │
└──────┬─────────────────┘
       │
       ├─ ① 向量检索 (Retrieve)
       │  └─ 查询向量数据库
       │     └─ 返回Top-5相关chunks
       │
       ├─ ② 重排序 (Rerank)
       │  └─ 根据相似度重新排序
       │
       ├─ ③ 生成答案 (Generate)
       │  ├─ 构建Prompt
       │  │  ├─ 系统提示词
       │  │  ├─ 检索到的文档上下文
       │  │  └─ 用户问题
       │  │
       │  └─ 调用大模型 (如Qwen)
       │     └─ 流式返回答案
       │
       └─ ④ 返回结果
          ├─ answer (完整答案)
          └─ references (参考文档列表)
              └─ [{doc_id, doc_name, chunk_id, similarity}]
```

---

### 详细步骤

#### 步骤1: 用户输入
```python
# src/pages/chat_page.py
def show():
    st.title("💬 智能问答")
    
    # 初始化session_state
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    
    if 'current_session_id' not in st.session_state:
        chat_service = get_chat_service()
        st.session_state.current_session_id = chat_service.create_session()
    
    # 聊天输入
    if prompt := st.chat_input("请输入问题"):
        # 添加用户消息
        st.session_state.chat_messages.append({
            "role": "user",
            "content": prompt
        })
        
        # 调用Chat Service（流式）
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            references = []
            
            for chunk in chat_service.chat(
                question=prompt,
                session_id=st.session_state.current_session_id,
                stream=True
            ):
                if 'delta' in chunk:
                    # 增量文本
                    full_response += chunk['delta']
                    message_placeholder.markdown(full_response + "▌")
                elif 'answer' in chunk:
                    # 最后一个chunk，包含完整答案和参考
                    full_response = chunk['answer']
                    references = chunk.get('references', [])
            
            message_placeholder.markdown(full_response)
            
            # 显示参考文档
            if references:
                with st.expander("📚 参考文档"):
                    for i, ref in enumerate(references):
                        st.write(f"[{i+1}] {ref['doc_name']} (相似度: {ref['similarity']:.2f})")
        
        # 保存助手消息
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": full_response,
            "references": references
        })
```

---

#### 步骤2: ChatService调用
```python
# src/services/chat_service.py
def chat(self, question: str, session_id: str = None, stream: bool = False):
    """
    发送问题到RAGFlow Chat Assistant
    """
    if session_id is None:
        session_id = self.create_session()
    
    # 调用RAGFlow Chat API
    response = requests.post(
        f"{self.api_url}/v1/chat",
        headers={
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        },
        json={
            "question": question,
            "session_id": session_id,
            "stream": stream
        },
        stream=stream  # 启用流式响应
    )
    
    if stream:
        # 流式返回（生成器）
        for line in response.iter_lines():
            if line:
                data = json.loads(line.decode('utf-8'))
                
                if 'delta' in data:
                    # 增量文本
                    yield {"delta": data['delta']}
                elif 'answer' in data:
                    # 完整答案（最后一个chunk）
                    yield {
                        "answer": data['answer'],
                        "references": data.get('references', [])
                    }
    else:
        # 非流式返回
        result = response.json()
        return {
            "answer": result['answer'],
            "references": result.get('references', []),
            "session_id": session_id
        }
```

---

#### 步骤3: RAGFlow内部处理

##### 3.1 向量检索
```python
# RAGFlow内部（不可见，仅说明原理）

# 1. 将问题向量化
question_embedding = embedding_model.encode(question)
# 返回: [0.123, -0.456, 0.789, ...] (768维向量)

# 2. 向量相似度搜索
results = vector_db.search(
    query_vector=question_embedding,
    top_k=10,  # 初步检索10个候选
    filters={
        "kb_name": "policy_demo_kb"
    }
)

# 3. 返回候选chunks
# [
#   {"chunk_id": "chunk_123", "doc_id": "doc_1", "similarity": 0.92, "content": "..."},
#   {"chunk_id": "chunk_456", "doc_id": "doc_2", "similarity": 0.87, "content": "..."},
#   ...
# ]
```

##### 3.2 重排序（可选）
```python
# 使用重排序模型（如BGE Reranker）进一步优化结果
reranked_results = reranker.rank(
    query=question,
    documents=[r['content'] for r in results]
)

# 取Top-5作为最终上下文
final_docs = reranked_results[:5]
```

##### 3.3 构建Prompt
```python
# 系统提示词
system_prompt = """
你是一个专业的政策咨询助手。请根据以下参考文档回答用户的问题。
如果参考文档中没有相关信息，请明确告知用户。
回答要准确、全面、易懂。
"""

# 拼接参考文档
context = ""
for i, doc in enumerate(final_docs):
    context += f"\n[参考文档{i+1}] {doc['doc_name']}\n{doc['content']}\n"

# 完整Prompt
full_prompt = f"""
{system_prompt}

{context}

用户问题: {question}

请回答:
"""
```

##### 3.4 调用大模型（流式）
```python
# 调用Qwen或其他大模型
for chunk in llm.generate_stream(full_prompt):
    yield {
        "delta": chunk.text,  # 增量文本
        "finish_reason": chunk.finish_reason
    }

# 最后一个chunk返回完整答案和参考
yield {
    "answer": full_answer,
    "references": [
        {
            "doc_id": doc['doc_id'],
            "doc_name": doc['doc_name'],
            "chunk_id": doc['chunk_id'],
            "similarity": doc['similarity']
        }
        for doc in final_docs
    ]
}
```

---

### 示例对话

**用户问题**: 高新技术企业有哪些税收优惠？

**检索结果**:
```python
[
    {
        "doc_name": "高新技术企业税收政策.pdf",
        "chunk_id": "chunk_12",
        "content": "高新技术企业减按15%的税率征收企业所得税...",
        "similarity": 0.94
    },
    {
        "doc_name": "研发费用加计扣除指南.pdf",
        "chunk_id": "chunk_7",
        "content": "高新技术企业研发费用加计扣除比例为100%...",
        "similarity": 0.89
    }
]
```

**生成答案**:
```
根据相关政策，高新技术企业可享受以下税收优惠：

1. **企业所得税优惠**
   - 减按15%的税率征收企业所得税（一般企业为25%）
   - 预计减税幅度约40%

2. **研发费用加计扣除**
   - 研发费用加计扣除比例为100%
   - 即实际发生100万元研发费用，可在税前扣除200万元

3. **其他优惠**
   - 技术转让所得免征、减征企业所得税
   - 符合条件的软件企业"两免三减半"

📚 参考文档:
[1] 高新技术企业税收政策.pdf
[2] 研发费用加计扣除指南.pdf
```

---

### 去重参考文档

```python
# src/pages/chat_page.py
def deduplicate_references(references: List[Dict]) -> List[Dict]:
    """
    去除重复的参考文档
    
    去重规则:
    1. 相同doc_id只保留第一个
    2. 按相似度降序排列
    """
    seen_doc_ids = set()
    unique_refs = []
    
    # 先按相似度降序排序
    sorted_refs = sorted(references, key=lambda x: x.get('similarity', 0), reverse=True)
    
    for ref in sorted_refs:
        doc_id = ref.get('doc_id')
        if doc_id not in seen_doc_ids:
            seen_doc_ids.add(doc_id)
            unique_refs.append(ref)
    
    return unique_refs

# 使用
references = deduplicate_references(raw_references)
```

---

## 🔗 相关文档

- [02-ARCHITECTURE.md](../02-ARCHITECTURE.md) - 系统架构
- [modules-inventory.md](modules-inventory.md) - 模块清单
- [05-API_REFERENCE.md](../05-API_REFERENCE.md) - API参考

---

**Last Updated**: 2026-02-01
