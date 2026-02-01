# 数据库设计详解

> **阅读时间**: 15分钟  
> **难度**: ⭐⭐⭐  
> **前置知识**: SQL基础、数据库设计原理

---

## 📖 目录

- [概述](#概述)
- [数据库架构](#数据库架构)
- [表结构详解](#表结构详解)
- [索引策略](#索引策略)
- [数据完整性](#数据完整性)
- [查询优化](#查询优化)
- [数据迁移](#数据迁移)
- [最佳实践](#最佳实践)

---

## 概述

### 技术选型

**SQLite**

| 优势 | 说明 |
|------|------|
| **零配置** | 无需独立服务，嵌入式数据库 |
| **轻量级** | 单文件存储，易于备份和迁移 |
| **高性能** | 对于中小规模数据（<10万条）性能优异 |
| **事务支持** | 完整的ACID事务保证 |
| **跨平台** | 支持Windows/macOS/Linux |

**适用场景**:
- ✅ 单机应用
- ✅ 数据量 < 100万条
- ✅ 读多写少
- ✅ 快速原型开发

**不适用场景**:
- ❌ 高并发写入（>1000 TPS）
- ❌ 分布式部署
- ❌ 需要复杂权限控制

### 数据库文件

**路径**: `data/database/policies.db`

```bash
# 查看数据库信息
sqlite3 data/database/policies.db ".schema"

# 查看数据统计
sqlite3 data/database/policies.db "SELECT COUNT(*) FROM policies;"
```

---

## 数据库架构

### ER图（实体关系图）

```
┌─────────────────┐
│    policies     │  政策主表
│  - id (PK)      │
│  - title        │
│  - content      │
│  - ragflow_doc_id
└────────┬────────┘
         │
         │ 1:N
         │
┌────────▼────────┐
│  policy_tags    │  政策-标签关联表
│  - policy_id (FK)
│  - tag_id (FK)  │
│  - confidence   │
└────────┬────────┘
         │
         │ N:1
         │
┌────────▼────────┐
│      tags       │  标签表
│  - id (PK)      │
│  - name         │
│  - level (1/2/3)│
│  - parent_id (FK)
└─────────────────┘

┌─────────────────┐
│ policy_relations│  政策关系表
│  - source_policy_id (FK)
│  - target_policy_id (FK)
│  - relation_type │
└─────────────────┘

┌─────────────────┐
│ graph_nodes     │  图谱节点表
│  - id (PK)      │
│  - label        │
│  - type         │
└────────┬────────┘
         │
         │ 1:N
         │
┌────────▼────────┐
│  graph_edges    │  图谱边表
│  - source_id (FK)│
│  - target_id (FK)│
│  - relation     │
└─────────────────┘
```

---

## 表结构详解

### 1. policies（政策表）

**文件**: [src/database/schema.sql](../../src/database/schema.sql#L19)

```sql
CREATE TABLE IF NOT EXISTS policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,                    -- 政策标题
    document_number TEXT UNIQUE,            -- 文号
    issuing_authority TEXT,                 -- 发文机关
    publish_date DATE,                      -- 发布日期
    effective_date DATE,                    -- 生效日期
    expiration_date DATE,                   -- 失效日期
    policy_type TEXT,                       -- 政策类型
    region TEXT,                            -- 适用地区
    content TEXT,                           -- 政策全文
    summary TEXT,                           -- 摘要
    status TEXT DEFAULT 'active',           -- 状态
    file_path TEXT,                         -- 原始文件路径
    ragflow_doc_id TEXT UNIQUE,             -- RAGFlow文档ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**字段说明**:

| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| `id` | INTEGER | 主键 | PK, AUTO_INCREMENT |
| `title` | TEXT | 政策标题 | NOT NULL |
| `document_number` | TEXT | 文号（如"财综〔2024〕10号"） | UNIQUE |
| `ragflow_doc_id` | TEXT | RAGFlow文档ID（用于关联） | UNIQUE |
| `policy_type` | TEXT | 政策类型（special_bonds/franchise/data_assets） | - |
| `status` | TEXT | 状态（active/expired/updated） | DEFAULT 'active' |
| `content` | TEXT | 政策全文（可能很长） | - |

**索引**:
```sql
CREATE INDEX idx_policies_policy_type ON policies(policy_type);
CREATE INDEX idx_policies_status ON policies(status);
CREATE INDEX idx_policies_publish_date ON policies(publish_date);
CREATE INDEX idx_policies_region ON policies(region);
```

**示例数据**:
```sql
INSERT INTO policies (title, document_number, issuing_authority, policy_type, ragflow_doc_id) 
VALUES (
    '地方政府专项债券管理办法',
    '财预〔2024〕15号',
    '财政部',
    'special_bonds',
    'doc_123456'
);
```

### 2. tags（标签表）

**三级标签体系**:

```
Level 1 (政策类型)
├─ Level 2 (分类)
│  ├─ Level 3 (具体标签)
│  └─ Level 3 (具体标签)
└─ Level 2 (分类)
   └─ Level 3 (具体标签)
```

**表结构**:
```sql
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,              -- 标签名称
    level INTEGER,                          -- 标签级别：1/2/3
    parent_id INTEGER,                      -- 父标签ID
    policy_type TEXT,                       -- 所属政策类型
    description TEXT,                       -- 标签描述
    display_order INTEGER DEFAULT 0,        -- 显示顺序
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES tags(id) ON DELETE CASCADE
);
```

**示例数据**:
```sql
-- Level 1: 政策类型
INSERT INTO tags (name, level, policy_type) VALUES ('专项债券', 1, 'special_bonds');

-- Level 2: 分类
INSERT INTO tags (name, level, parent_id, policy_type) 
VALUES ('发行管理', 2, 1, 'special_bonds');

-- Level 3: 具体标签
INSERT INTO tags (name, level, parent_id, policy_type) 
VALUES ('发行条件', 3, 2, 'special_bonds');
```

**索引**:
```sql
CREATE INDEX idx_tags_level ON tags(level);
CREATE INDEX idx_tags_parent_id ON tags(parent_id);
CREATE INDEX idx_tags_policy_type ON tags(policy_type);
```

### 3. policy_tags（政策-标签关联表）

**多对多关系**:

```sql
CREATE TABLE IF NOT EXISTS policy_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    confidence REAL DEFAULT 1.0,            -- 标签置信度（0-1）
    source TEXT DEFAULT 'auto',             -- 标签来源：auto/manual
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (policy_id) REFERENCES policies(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
    UNIQUE(policy_id, tag_id)
);
```

**字段说明**:
- `confidence` - 标签置信度，AI自动打标时使用
- `source` - 区分自动打标（auto）和人工标注（manual）

**查询示例**:
```sql
-- 获取政策的所有标签
SELECT t.name, pt.confidence 
FROM policy_tags pt
JOIN tags t ON pt.tag_id = t.id
WHERE pt.policy_id = 1;

-- 获取某标签的所有政策
SELECT p.title 
FROM policies p
JOIN policy_tags pt ON p.id = pt.policy_id
WHERE pt.tag_id = 5;
```

### 4. policy_relations（政策关系表）

**政策间关系**:

```sql
CREATE TABLE IF NOT EXISTS policy_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_policy_id INTEGER NOT NULL,      -- 源政策ID
    target_policy_id INTEGER NOT NULL,      -- 目标政策ID
    relation_type TEXT NOT NULL,            -- 关系类型
    description TEXT,                       -- 关系描述
    confidence REAL DEFAULT 1.0,            -- 置信度
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_policy_id) REFERENCES policies(id) ON DELETE CASCADE,
    FOREIGN KEY (target_policy_id) REFERENCES policies(id) ON DELETE CASCADE,
    UNIQUE(source_policy_id, target_policy_id, relation_type)
);
```

**关系类型**:
- `replaces` - 替代（新政策废止旧政策）
- `amends` - 修订
- `references` - 引用
- `relates_to` - 相关
- `affects` - 影响

**示例**:
```sql
-- 政策A替代政策B
INSERT INTO policy_relations (source_policy_id, target_policy_id, relation_type)
VALUES (1, 2, 'replaces');
```

### 5. graph_nodes（图谱节点表）

**知识图谱节点**:

```sql
CREATE TABLE IF NOT EXISTS graph_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL,                    -- 节点标签（显示名称）
    type TEXT NOT NULL,                     -- 节点类型
    properties TEXT,                        -- JSON格式的属性
    ragflow_doc_id TEXT,                    -- 关联的RAGFlow文档ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(label, type)
);
```

**节点类型** (对应Qwen抽取的实体类型):
- `POLICY` - 政策名称
- `ORGANIZATION` - 发文机关
- `LAW` - 法律法规
- `REGION` - 地区
- `INDUSTRY` - 行业
- `PROJECT` - 项目类型
- `DATE` - 日期
- `CONCEPT` - 概念术语

**示例**:
```sql
INSERT INTO graph_nodes (label, type, properties, ragflow_doc_id)
VALUES (
    '财政部',
    'ORGANIZATION',
    '{"full_name": "中华人民共和国财政部", "level": "国家级"}',
    'doc_123'
);
```

### 6. graph_edges（图谱边表）

**知识图谱边（关系）**:

```sql
CREATE TABLE IF NOT EXISTS graph_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,             -- 源节点ID
    target_id INTEGER NOT NULL,             -- 目标节点ID
    relation TEXT NOT NULL,                 -- 关系类型
    properties TEXT,                        -- JSON格式的属性
    ragflow_doc_id TEXT,                    -- 关联的RAGFlow文档ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES graph_nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES graph_nodes(id) ON DELETE CASCADE,
    UNIQUE(source_id, target_id, relation)
);
```

**关系类型** (对应Qwen抽取的关系类型):
- `ISSUED_BY` - 发布
- `BASED_ON` - 依据
- `APPLIES_TO` - 适用于
- `REPLACES` - 替代
- `AMENDS` - 修订
- `REFERENCES` - 引用

**查询示例**:
```sql
-- 获取某文档的完整图谱
SELECT 
    sn.label AS source,
    e.relation,
    tn.label AS target
FROM graph_edges e
JOIN graph_nodes sn ON e.source_id = sn.id
JOIN graph_nodes tn ON e.target_id = tn.id
WHERE e.ragflow_doc_id = 'doc_123';
```

---

## 索引策略

### 索引设计原则

1. **查询频率优先** - 为高频查询字段建索引
2. **选择性高** - 索引字段值多样性高
3. **避免过度索引** - 影响写入性能

### 当前索引

```sql
-- policies表
CREATE INDEX idx_policies_policy_type ON policies(policy_type);
CREATE INDEX idx_policies_status ON policies(status);
CREATE INDEX idx_policies_publish_date ON policies(publish_date);
CREATE INDEX idx_policies_region ON policies(region);

-- tags表
CREATE INDEX idx_tags_level ON tags(level);
CREATE INDEX idx_tags_parent_id ON tags(parent_id);
CREATE INDEX idx_tags_policy_type ON tags(policy_type);

-- policy_tags表
CREATE INDEX idx_policy_tags_policy_id ON policy_tags(policy_id);
CREATE INDEX idx_policy_tags_tag_id ON policy_tags(tag_id);

-- graph_nodes表
CREATE INDEX idx_graph_nodes_type ON graph_nodes(type);
CREATE INDEX idx_graph_nodes_ragflow_doc_id ON graph_nodes(ragflow_doc_id);

-- graph_edges表
CREATE INDEX idx_graph_edges_source_id ON graph_edges(source_id);
CREATE INDEX idx_graph_edges_target_id ON graph_edges(target_id);
CREATE INDEX idx_graph_edges_ragflow_doc_id ON graph_edges(ragflow_doc_id);
```

### 索引使用分析

```sql
-- 查看查询是否使用索引
EXPLAIN QUERY PLAN 
SELECT * FROM policies WHERE policy_type = 'special_bonds';

-- 结果示例：
-- SEARCH TABLE policies USING INDEX idx_policies_policy_type (policy_type=?)
```

---

## 数据完整性

### 外键约束

**级联删除** (ON DELETE CASCADE):

```sql
-- 删除政策时，自动删除关联的标签和关系
FOREIGN KEY (policy_id) REFERENCES policies(id) ON DELETE CASCADE
```

**示例**:
```sql
-- 删除政策
DELETE FROM policies WHERE id = 1;

-- 自动级联删除：
-- - policy_tags中policy_id=1的记录
-- - policy_relations中source_policy_id=1或target_policy_id=1的记录
```

### 唯一约束

```sql
-- 防止重复数据
UNIQUE(policy_id, tag_id)           -- policy_tags表
UNIQUE(label, type)                 -- graph_nodes表
UNIQUE(source_id, target_id, relation)  -- graph_edges表
```

### 非空约束

```sql
title TEXT NOT NULL,                -- 政策标题不能为空
source_id INTEGER NOT NULL,         -- 边的源节点必须存在
```

---

## 查询优化

### 常见查询优化

#### 1. 使用JOIN代替子查询

**❌ 低效**:
```sql
SELECT * FROM policies 
WHERE id IN (
    SELECT policy_id FROM policy_tags WHERE tag_id = 5
);
```

**✅ 高效**:
```sql
SELECT DISTINCT p.* 
FROM policies p
JOIN policy_tags pt ON p.id = pt.policy_id
WHERE pt.tag_id = 5;
```

#### 2. 限制返回结果

```sql
-- 分页查询
SELECT * FROM policies 
ORDER BY created_at DESC 
LIMIT 20 OFFSET 0;
```

#### 3. 避免SELECT *

```sql
-- 只查询需要的字段
SELECT id, title, policy_type 
FROM policies 
WHERE status = 'active';
```

#### 4. 使用EXPLAIN分析

```sql
EXPLAIN QUERY PLAN 
SELECT * FROM policies WHERE policy_type = 'special_bonds';
```

---

## 数据迁移

### 版本管理

**迁移脚本命名**: `migrations/V{version}_{description}.sql`

```
migrations/
├── V001_initial_schema.sql
├── V002_add_graph_tables.sql
└── V003_add_ragflow_doc_id.sql
```

### 迁移示例

**V002_add_graph_tables.sql**:
```sql
-- 添加图谱表
CREATE TABLE IF NOT EXISTS graph_nodes (...);
CREATE TABLE IF NOT EXISTS graph_edges (...);

-- 创建索引
CREATE INDEX idx_graph_nodes_type ON graph_nodes(type);
```

### 数据备份

```bash
# 备份数据库
sqlite3 data/database/policies.db ".backup data/database/policies_backup.db"

# 导出SQL
sqlite3 data/database/policies.db ".dump" > backup.sql

# 恢复
sqlite3 data/database/policies.db < backup.sql
```

---

## 最佳实践

### 1. 事务使用

```python
import sqlite3

conn = sqlite3.connect('data/database/policies.db')
try:
    conn.execute('BEGIN TRANSACTION')
    
    # 多个操作
    conn.execute('INSERT INTO policies (...) VALUES (...)')
    conn.execute('INSERT INTO policy_tags (...) VALUES (...)')
    
    conn.execute('COMMIT')
except Exception as e:
    conn.execute('ROLLBACK')
    raise e
finally:
    conn.close()
```

### 2. 参数化查询

**❌ SQL注入风险**:
```python
query = f"SELECT * FROM policies WHERE title = '{user_input}'"
```

**✅ 安全**:
```python
query = "SELECT * FROM policies WHERE title = ?"
cursor.execute(query, (user_input,))
```

### 3. 连接池

```python
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    conn = sqlite3.connect('data/database/policies.db')
    try:
        yield conn
    finally:
        conn.close()

# 使用
with get_db_connection() as conn:
    cursor = conn.execute('SELECT * FROM policies')
    results = cursor.fetchall()
```

### 4. 定期维护

```sql
-- 清理碎片
VACUUM;

-- 更新统计信息
ANALYZE;

-- 检查完整性
PRAGMA integrity_check;
```

---

## 相关文档

- [数据流详解](data-flow.md) - 了解数据如何流入数据库
- [API参考](../05-API_REFERENCE.md#policydao) - 数据库访问API
- [开发者指南](../04-DEVELOPER_GUIDE.md) - 数据库操作示例

---

**最后更新**: 2026-02-01  
**维护者**: AI Assistant
