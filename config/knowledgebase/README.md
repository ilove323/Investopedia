# RAGFlow知识库配置说明

## 配置文件结构

`config/knowledgebase/policy_demo_kb.ini` 仅包含RAGFlow API实际支持的配置参数。

## RAGFlow支持的配置参数

### 1. 知识库基本信息 [KNOWLEDGE_BASE]
- `name`: 知识库名称
- `description`: 知识库描述

### 2. 分块配置 [CHUNKING]
- `chunk_method`: 分块方法（naive, qa, manual, table, paper, book, laws, presentation, picture, one, email）
- `chunk_size`: 分块大小（token数）
- `child_chunk_enabled`: 是否启用子分块（RAPTOR技术）
- `child_chunk_size`: 子分块大小

### 3. 文档处理 [DOCUMENT_PROCESSING]
- `layout_recognize`: 版面识别方法（deepdoc）

### 4. 检索配置 [RETRIEVAL]
用于RAGFlow Chat Assistant的检索参数：
- `similarity_threshold`: 相似度阈值（默认0.2）
- `vector_similarity_weight`: 向量相似度权重（默认0.3，关键词权重为1-此值）
- `top_k`: 参与向量计算的chunk数（默认1024）
- `top_n`: 返回给LLM的chunk数（默认8）
- `rerank_model`: 重排序模型（可选）

### 5. 问答配置 [QA]
用于RAGFlow Chat Assistant的LLM设置：
- `qa_model`: LLM模型名称
- `temperature`: 生成温度（0-1）
- `top_p`: 核采样参数
- `max_tokens`: 最大生成token数
- `system_prompt_file`: 系统提示词文件名

## 需要在RAGFlow Web界面手动配置的项

以下配置**无法通过API设置**，需要在RAGFlow Web界面手动配置：

### Embedding Model（嵌入模型）
- 位置：Knowledge Base > Settings > Embedding model
- 建议：`BAAI/bge-large-zh-v1.5`
- ⚠️ 一旦知识库有chunks，就无法更改embedding model

### Permission（权限）
- `me`: 仅自己可管理
- `team`: 团队成员可管理

### Indexing Model
- RAGFlow没有单独的indexing model配置
- 使用与embedding model相同的模型

## 不支持的配置（已从配置文件删除）

以下配置在之前版本中存在，但**RAGFlow API不支持**，已删除：

- ❌ TOC增强配置（目录提取）
- ❌ 元数据自动提取配置
- ❌ 关键词提取配置（包括LLM关键词模型）
- ❌ 知识图谱配置（实体/关系提取）
- ❌ 社区检测与报告配置
- ❌ chunk重叠百分比配置

如需这些功能，需要：
1. 在应用层自己实现
2. 或等待RAGFlow未来版本支持
3. 或直接在RAGFlow Web界面配置（部分功能可能在UI中可用）

## 配置同步流程

1. 编辑 `config/knowledgebase/policy_demo_kb.ini`
2. 启动应用时自动调用 `src/services/config_sync.py`
3. 配置通过RAGFlow Python SDK同步到知识库
4. 检查日志确认同步结果

## 测试配置

运行测试验证配置正确性：

```bash
source venv/bin/activate
python -m pytest tests/test_config_sync.py -v
```

## 参考文档

- [RAGFlow Python API Reference](https://ragflow.io/docs/python_api_reference#create-dataset)
- [RAGFlow Configure Knowledge Base](https://ragflow.io/docs/configure_knowledge_base)
