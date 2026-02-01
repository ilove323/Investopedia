# Qwen 集成详解

> **阅读时间**: 25分钟  
> **难度**: ⭐⭐⭐⭐  
> **前置知识**: 了解大模型API、Prompt工程、JSON解析

---

## 📖 目录

- [概述](#概述)
- [架构设计](#架构设计)
- [QwenClient实现](#qwenclient实现)
- [实体抽取详解](#实体抽取详解)
- [Prompt工程](#prompt工程)
- [结果解析](#结果解析)
- [错误处理](#错误处理)
- [性能优化](#性能优化)
- [最佳实践](#最佳实践)

---

## 概述

### 什么是Qwen？

Qwen（通义千问）是阿里云推出的大语言模型，通过DashScope API提供服务。本系统使用Qwen实现：
- **实体抽取** - 识别政策文档中的8种实体类型
- **关系抽取** - 识别实体间的6种关系类型
- **结构化输出** - 返回标准JSON格式结果

### 为什么选择Qwen？

| 对比项 | Qwen | GPT-4 | 本地模型 |
|--------|------|-------|---------|
| **中文理解** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **API稳定性** | 高 | 高 | N/A |
| **成本** | 低 | 高 | 免费 |
| **部署难度** | 简单 | 简单 | 复杂 |
| **政策领域** | 优秀 | 良好 | 一般 |

### 在本系统中的作用

```
RAGFlow文档分块
        ↓
    提取文本内容
        ↓
    Qwen实体抽取 ←─── Prompt模板
        ↓
    JSON结果解析
        ↓
    存入数据库
        ↓
    构建知识图谱
```

---

## 架构设计

### 调用流程

```
┌─────────────────────────────────────────┐
│   GraphService (图谱构建服务)            │
│   - build_graph_for_document()          │
└───────────────┬─────────────────────────┘
                │
                │ 1. 获取文档chunks
                ▼
┌─────────────────────────────────────────┐
│   QwenClient (Qwen客户端)               │
│   - extract_entities_and_relations()    │
└───────────────┬─────────────────────────┘
                │
                │ 2. 构建Prompt
                ▼
┌─────────────────────────────────────────┐
│   DashScope API (阿里云)                │
│   - Generation.call()                   │
│   - Model: qwen-plus                    │
└───────────────┬─────────────────────────┘
                │
                │ 3. 返回JSON
                ▼
┌─────────────────────────────────────────┐
│   结果解析和验证                          │
│   - _parse_extraction_result()          │
│   - 格式验证                             │
└───────────────┬─────────────────────────┘
                │
                │ 4. 存入数据库
                ▼
┌─────────────────────────────────────────┐
│   GraphDAO (图谱数据访问)                │
│   - add_node() / add_edge()             │
└─────────────────────────────────────────┘
```

---

## QwenClient实现

### 初始化

**文件**: [src/services/qwen_client.py](../../src/services/qwen_client.py)

```python
class QwenClient:
    """Qwen大模型客户端"""
    
    def __init__(
        self, 
        api_key: str, 
        model: str = "qwen-plus", 
        temperature: float = 0.1,
        max_tokens: int = 2000,
        prompt_file: str = "config/prompts/entity_extraction.txt"
    ):
        """
        初始化Qwen客户端
        
        Args:
            api_key: DashScope API密钥
            model: 模型名称 (qwen-plus, qwen-turbo, qwen-max)
            temperature: 温度参数 (0-1, 越低越确定)
            max_tokens: 最大生成token数
            prompt_file: 提示词文件路径
        """
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.prompt_file = Path(prompt_file)
        
        dashscope.api_key = api_key
        
        # 加载提示词模板
        self.system_prompt = self._load_prompt_template()
```

**关键参数说明**:

| 参数 | 默认值 | 说明 | 调优建议 |
|------|--------|------|---------|
| `model` | qwen-plus | 模型版本 | qwen-plus平衡性能和成本 |
| `temperature` | 0.1 | 随机性 | 实体抽取用低温度（0.1）确保稳定 |
| `max_tokens` | 2000 | 最大输出长度 | 根据文档复杂度调整 |
| `prompt_file` | entity_extraction.txt | 提示词模板 | 按领域定制 |

### Prompt模板加载

```python
def _load_prompt_template(self) -> str:
    """加载提示词模板"""
    try:
        if self.prompt_file.exists():
            with open(self.prompt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"成功加载提示词模板: {self.prompt_file}")
            return content
        else:
            logger.warning(f"提示词文件不存在: {self.prompt_file}，使用默认提示词")
            return self._get_default_prompt()
    except Exception as e:
        logger.error(f"加载提示词文件失败: {e}，使用默认提示词")
        return self._get_default_prompt()
```

**优势**:
- ✅ 支持外部文件管理Prompt
- ✅ Prompt变更无需修改代码
- ✅ 支持不同领域定制（专项债、特许经营等）

---

## 实体抽取详解

### 核心方法

```python
def extract_entities_and_relations(self, text: str, doc_title: str) -> Dict:
    """
    从政策文本中提取实体和关系
    
    Args:
        text: 政策文本内容
        doc_title: 文档标题
        
    Returns:
        {
            "entities": [
                {"name": "实体名称", "type": "实体类型"},
                ...
            ],
            "relations": [
                {"source": "源实体", "target": "目标实体", "type": "关系类型"},
                ...
            ]
        }
    """
    user_prompt = self._build_user_prompt(text, doc_title)
    
    try:
        logger.info(f"开始调用Qwen API提取实体: {doc_title[:50]}...")
        
        response = Generation.call(
            model=self.model,
            messages=[
                {'role': 'system', 'content': self.system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            result_format='message'
        )
        
        if response.status_code == 200:
            content = response.output.choices[0].message.content
            result = self._parse_extraction_result(content)
            
            entity_count = len(result.get('entities', []))
            relation_count = len(result.get('relations', []))
            logger.info(f"实体抽取成功: {entity_count}个实体, {relation_count}个关系")
            
            return result
        else:
            logger.error(f"Qwen API调用失败: {response.code} - {response.message}")
            return {'entities': [], 'relations': []}
            
    except Exception as e:
        logger.error(f"实体抽取异常: {e}", exc_info=True)
        return {'entities': [], 'relations': []}
```

### 支持的实体类型

**实体类型定义** (8种):

| 类型 | 中文名 | 示例 | 说明 |
|------|--------|------|------|
| `POLICY` | 政策名称 | 《专项债券管理办法》 | 政策文件标题 |
| `ORGANIZATION` | 发文机关 | 财政部、发改委 | 发布政策的机构 |
| `LAW` | 法律法规 | 《预算法》 | 被引用的法律 |
| `REGION` | 地区 | 北京市、长三角 | 适用地区 |
| `INDUSTRY` | 行业 | 交通、水利 | 适用行业 |
| `PROJECT` | 项目类型 | 基础设施、保障性住房 | 项目分类 |
| `DATE` | 日期 | 2024年1月1日 | 时间信息 |
| `CONCEPT` | 概念术语 | 风险防控、收益平衡 | 关键概念 |

### 支持的关系类型

**关系类型定义** (6种):

| 类型 | 中文名 | 示例 | 说明 |
|------|--------|------|------|
| `ISSUED_BY` | 发布 | 政策 ←发布← 发文机关 | 发布关系 |
| `BASED_ON` | 依据 | 政策A ←依据← 法律B | 法律依据 |
| `APPLIES_TO` | 适用于 | 政策 ←适用于← 地区/行业 | 适用范围 |
| `REPLACES` | 替代 | 新政策 ←替代← 旧政策 | 废止关系 |
| `AMENDS` | 修订 | 政策A ←修订← 政策B | 修订关系 |
| `REFERENCES` | 引用 | 政策A ←引用← 政策B | 引用关系 |

---

## Prompt工程

### Prompt结构

完整Prompt由两部分组成：

#### 1. System Prompt（系统提示词）

**文件**: [config/prompts/policy_demo_kb.txt](../../config/prompts/policy_demo_kb.txt)

```
你是一个专业的政策文件分析助手，擅长从政策法规文本中抽取实体和关系。

【任务要求】
从给定的政策文本中提取以下信息：

1. 实体类型（8种）:
   - POLICY: 政策名称
   - ORGANIZATION: 发文机关
   - LAW: 法律法规
   - REGION: 地区
   - INDUSTRY: 行业
   - PROJECT: 项目类型
   - DATE: 日期
   - CONCEPT: 概念术语

2. 关系类型（6种）:
   - ISSUED_BY: 发布（政策 ← 机关）
   - BASED_ON: 依据（政策 ← 法律）
   - APPLIES_TO: 适用于（政策 ← 地区/行业）
   - REPLACES: 替代
   - AMENDS: 修订
   - REFERENCES: 引用

【输出格式】
严格返回JSON格式，不要添加任何解释：
{
  "entities": [
    {"name": "实体名称", "type": "实体类型"}
  ],
  "relations": [
    {"source": "源实体", "target": "目标实体", "type": "关系类型"}
  ]
}

【注意事项】
1. 实体名称要准确完整，不要简写
2. 关系要有明确的文本依据
3. 日期统一格式为 YYYY-MM-DD
4. 去除重复实体和关系
```

#### 2. User Prompt（用户提示词）

```python
def _build_user_prompt(self, text: str, doc_title: str) -> str:
    """构建用户提示词"""
    # 截断过长文本
    max_length = 3000
    if len(text) > max_length:
        text = text[:max_length] + "\n...[文本过长，已截断]"
    
    user_prompt = f"""
**文档标题**: {doc_title}

**文档内容**:
{text}

---

请按照要求提取实体和关系，直接返回JSON格式结果。
"""
    return user_prompt
```

**设计要点**:
- ✅ 包含文档标题（提供上下文）
- ✅ 限制文本长度（避免超token）
- ✅ 明确指令（"直接返回JSON"）

### Prompt优化技巧

#### 1. Few-Shot示例

在System Prompt中添加示例：

```
【示例】
文本：根据《预算法》，财政部发布《专项债券管理办法》，适用于全国范围。

输出：
{
  "entities": [
    {"name": "专项债券管理办法", "type": "POLICY"},
    {"name": "财政部", "type": "ORGANIZATION"},
    {"name": "预算法", "type": "LAW"},
    {"name": "全国", "type": "REGION"}
  ],
  "relations": [
    {"source": "专项债券管理办法", "target": "财政部", "type": "ISSUED_BY"},
    {"source": "专项债券管理办法", "target": "预算法", "type": "BASED_ON"},
    {"source": "专项债券管理办法", "target": "全国", "type": "APPLIES_TO"}
  ]
}
```

#### 2. 明确约束

```
【约束条件】
1. 每个实体必须在文本中明确出现
2. 禁止推测或补充文本中没有的信息
3. 同一实体只保留一次
4. 关系的source和target必须都在entities中
```

#### 3. 格式强调

```
【重要】输出必须是有效的JSON格式，不要包含：
- 解释性文字
- Markdown代码块标记（如 ```json）
- 注释
```

---

## 结果解析

### 解析流程

```python
def _parse_extraction_result(self, content: str) -> Dict:
    """解析Qwen返回的实体抽取结果"""
    try:
        # 1. 清理内容
        content = content.strip()
        
        # 2. 提取JSON（处理Markdown代码块）
        if '```json' in content:
            start = content.find('```json') + 7
            end = content.find('```', start)
            content = content[start:end].strip()
        elif '```' in content:
            start = content.find('```') + 3
            end = content.find('```', start)
            content = content[start:end].strip()
        
        # 3. 解析JSON
        result = json.loads(content)
        
        # 4. 验证格式
        if 'entities' not in result or 'relations' not in result:
            logger.error("JSON格式错误：缺少entities或relations字段")
            return {'entities': [], 'relations': []}
        
        # 5. 验证数据类型
        if not isinstance(result['entities'], list) or not isinstance(result['relations'], list):
            logger.error("JSON格式错误：entities和relations必须是数组")
            return {'entities': [], 'relations': []}
        
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}\n原始内容: {content[:200]}...")
        return {'entities': [], 'relations': []}
    except Exception as e:
        logger.error(f"结果解析异常: {e}")
        return {'entities': [], 'relations': []}
```

### 常见解析问题

#### 问题1: Markdown代码块

**输入**:
```
```json
{"entities": [...]}
```
```

**解决**:
```python
# 移除代码块标记
if '```json' in content:
    start = content.find('```json') + 7
    end = content.find('```', start)
    content = content[start:end].strip()
```

#### 问题2: 多余的解释文字

**输入**:
```
好的，我已经提取了实体和关系：
{"entities": [...]}
```

**解决**:
```python
# 查找第一个 { 和最后一个 }
start = content.find('{')
end = content.rfind('}') + 1
if start != -1 and end > start:
    content = content[start:end]
```

#### 问题3: 字段缺失

**输入**:
```json
{"entities": [...]}  // 缺少 relations
```

**解决**:
```python
# 验证必需字段
if 'entities' not in result:
    result['entities'] = []
if 'relations' not in result:
    result['relations'] = []
```

---

## 错误处理

### API错误

```python
if response.status_code == 200:
    # 成功
    content = response.output.choices[0].message.content
    result = self._parse_extraction_result(content)
else:
    # 失败
    logger.error(f"Qwen API调用失败: {response.code} - {response.message}")
    
    # 根据错误码处理
    if response.code == 'InvalidApiKey':
        raise ValueError("API密钥无效，请检查配置")
    elif response.code == 'Throttling.RateQuota':
        raise RuntimeError("API调用频率超限，请稍后重试")
    else:
        return {'entities': [], 'relations': []}
```

### 超时处理

```python
import signal

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("API调用超时")

# 设置超时
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(30)  # 30秒超时

try:
    result = qwen_client.extract_entities_and_relations(text, title)
finally:
    signal.alarm(0)  # 取消超时
```

### 重试机制

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def extract_with_retry(text: str, title: str):
    """带重试的实体抽取"""
    return qwen_client.extract_entities_and_relations(text, title)
```

---

## 性能优化

### 1. 文本截断

```python
# 限制输入长度，避免超token
max_length = 3000
if len(text) > max_length:
    text = text[:max_length] + "\n...[文本过长，已截断]"
```

**效果**:
- 降低API成本（按token计费）
- 加快响应速度
- 避免超长文本导致质量下降

### 2. 批量处理

```python
def batch_extract(chunks: List[str], doc_title: str) -> Dict:
    """批量提取多个chunk的实体"""
    all_entities = []
    all_relations = []
    
    for chunk in chunks:
        result = qwen_client.extract_entities_and_relations(chunk, doc_title)
        all_entities.extend(result['entities'])
        all_relations.extend(result['relations'])
    
    # 去重
    unique_entities = remove_duplicate_entities(all_entities)
    unique_relations = remove_duplicate_relations(all_relations)
    
    return {
        'entities': unique_entities,
        'relations': unique_relations
    }
```

### 3. 缓存结果

```python
import hashlib
import json
from functools import lru_cache

@lru_cache(maxsize=100)
def extract_cached(text_hash: str, doc_title: str):
    """缓存提取结果"""
    # 从缓存获取或调用API
    pass

# 使用
text_hash = hashlib.md5(text.encode()).hexdigest()
result = extract_cached(text_hash, doc_title)
```

### 4. 异步调用

```python
import asyncio
from typing import List

async def async_extract(text: str, title: str):
    """异步实体抽取"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, 
        qwen_client.extract_entities_and_relations, 
        text, 
        title
    )

async def batch_extract_async(chunks: List[str], title: str):
    """并发处理多个chunk"""
    tasks = [async_extract(chunk, title) for chunk in chunks]
    results = await asyncio.gather(*tasks)
    return merge_results(results)
```

---

## 最佳实践

### 1. 合理设置参数

```python
# 实体抽取：低温度，确保稳定
qwen_client = QwenClient(
    api_key=api_key,
    model="qwen-plus",
    temperature=0.1,      # 低温度
    max_tokens=2000
)

# 文本生成：高温度，增加多样性
qwen_summary = QwenClient(
    api_key=api_key,
    model="qwen-turbo",
    temperature=0.7,      # 高温度
    max_tokens=500
)
```

### 2. 验证输出质量

```python
def validate_extraction_result(result: Dict) -> bool:
    """验证提取结果质量"""
    # 1. 检查必需字段
    if 'entities' not in result or 'relations' not in result:
        return False
    
    # 2. 检查实体格式
    for entity in result['entities']:
        if 'name' not in entity or 'type' not in entity:
            logger.warning(f"实体格式错误: {entity}")
            return False
        if entity['type'] not in VALID_ENTITY_TYPES:
            logger.warning(f"无效实体类型: {entity['type']}")
            return False
    
    # 3. 检查关系格式
    entity_names = {e['name'] for e in result['entities']}
    for relation in result['relations']:
        if relation['source'] not in entity_names:
            logger.warning(f"关系源实体不存在: {relation['source']}")
            return False
        if relation['target'] not in entity_names:
            logger.warning(f"关系目标实体不存在: {relation['target']}")
            return False
    
    return True
```

### 3. 监控API使用

```python
import time

class QwenClientWithMetrics(QwenClient):
    """带监控的Qwen客户端"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.total_calls = 0
        self.total_tokens = 0
        self.total_time = 0
    
    def extract_entities_and_relations(self, text: str, doc_title: str) -> Dict:
        start_time = time.time()
        result = super().extract_entities_and_relations(text, doc_title)
        elapsed = time.time() - start_time
        
        self.total_calls += 1
        self.total_time += elapsed
        
        logger.info(f"API调用统计: 总次数={self.total_calls}, 平均耗时={self.total_time/self.total_calls:.2f}秒")
        
        return result
```

### 4. 错误恢复

```python
def safe_extract(text: str, title: str, fallback: bool = True) -> Dict:
    """安全的实体抽取（带降级策略）"""
    try:
        result = qwen_client.extract_entities_and_relations(text, title)
        
        # 验证结果
        if validate_extraction_result(result):
            return result
        else:
            logger.warning("提取结果验证失败")
            if fallback:
                return fallback_extraction(text, title)
            return {'entities': [], 'relations': []}
            
    except Exception as e:
        logger.error(f"实体抽取失败: {e}")
        if fallback:
            return fallback_extraction(text, title)
        return {'entities': [], 'relations': []}

def fallback_extraction(text: str, title: str) -> Dict:
    """降级策略：使用规则提取"""
    # 使用正则表达式提取基本实体
    import re
    
    entities = []
    # 提取组织机构（简单示例）
    orgs = re.findall(r'([\u4e00-\u9fa5]{2,10}(?:部|委|局|厅|办))', text)
    for org in set(orgs):
        entities.append({'name': org, 'type': 'ORGANIZATION'})
    
    return {'entities': entities, 'relations': []}
```

---

## 相关文档

- [数据流详解](data-flow.md) - 了解Qwen在图谱构建流程中的位置
- [RAGFlow集成详解](ragflow-integration.md) - 了解文档分块和内容提取
- [图谱算法详解](graph-algorithms.md) - 了解提取结果如何构建图谱
- [API参考](../05-API_REFERENCE.md#qwenclient) - QwenClient完整API文档

---

**最后更新**: 2026-02-01  
**维护者**: AI Assistant
