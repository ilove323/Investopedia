-- 政策库数据库表结构定义

-- 政策表
CREATE TABLE IF NOT EXISTS policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,                    -- 政策标题
    document_number TEXT UNIQUE,            -- 文号
    issuing_authority TEXT,                 -- 发文机关
    publish_date DATE,                      -- 发布日期
    effective_date DATE,                    -- 生效日期
    expiration_date DATE,                   -- 失效日期
    policy_type TEXT,                       -- 政策类型：special_bonds/franchise/data_assets
    region TEXT,                            -- 适用地区
    content TEXT,                           -- 政策全文
    summary TEXT,                           -- 摘要
    status TEXT DEFAULT 'active',           -- 状态：active/expired/updated
    file_path TEXT,                         -- 原始文件路径
    ragflow_doc_id TEXT UNIQUE,             -- RAGFlow文档ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建政策表索引
CREATE INDEX IF NOT EXISTS idx_policies_policy_type ON policies(policy_type);
CREATE INDEX IF NOT EXISTS idx_policies_status ON policies(status);
CREATE INDEX IF NOT EXISTS idx_policies_publish_date ON policies(publish_date);
CREATE INDEX IF NOT EXISTS idx_policies_region ON policies(region);

-- 标签表（三级标签体系）
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,              -- 标签名称
    level INTEGER,                          -- 标签级别：1/2/3
    parent_id INTEGER,                      -- 父标签ID
    policy_type TEXT,                       -- 所属政策类型：special_bonds/franchise/data_assets
    description TEXT,                       -- 标签描述
    display_order INTEGER DEFAULT 0,        -- 显示顺序
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- 创建标签表索引
CREATE INDEX IF NOT EXISTS idx_tags_level ON tags(level);
CREATE INDEX IF NOT EXISTS idx_tags_parent_id ON tags(parent_id);
CREATE INDEX IF NOT EXISTS idx_tags_policy_type ON tags(policy_type);

-- 政策-标签关联表
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

-- 创建政策-标签关联表索引
CREATE INDEX IF NOT EXISTS idx_policy_tags_policy_id ON policy_tags(policy_id);
CREATE INDEX IF NOT EXISTS idx_policy_tags_tag_id ON policy_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_policy_tags_source ON policy_tags(source);

-- 政策关系表
CREATE TABLE IF NOT EXISTS policy_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_policy_id INTEGER NOT NULL,      -- 源政策ID
    target_policy_id INTEGER NOT NULL,      -- 目标政策ID
    relation_type TEXT NOT NULL,            -- 关系类型：replaces/amends/references/relates_to/affects
    description TEXT,                       -- 关系描述
    confidence REAL DEFAULT 1.0,            -- 置信度
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_policy_id) REFERENCES policies(id) ON DELETE CASCADE,
    FOREIGN KEY (target_policy_id) REFERENCES policies(id) ON DELETE CASCADE,
    UNIQUE(source_policy_id, target_policy_id, relation_type)
);

-- 创建政策关系表索引
CREATE INDEX IF NOT EXISTS idx_policy_relations_source ON policy_relations(source_policy_id);
CREATE INDEX IF NOT EXISTS idx_policy_relations_target ON policy_relations(target_policy_id);
CREATE INDEX IF NOT EXISTS idx_policy_relations_type ON policy_relations(relation_type);

-- 处理日志表
CREATE TABLE IF NOT EXISTS processing_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_id INTEGER,                      -- 政策ID
    action TEXT NOT NULL,                   -- 操作类型：upload/extract/tag/graph/search
    status TEXT NOT NULL,                   -- 状态：success/failed/processing
    message TEXT,                           -- 处理消息
    error_detail TEXT,                      -- 错误详情
    duration_ms INTEGER,                    -- 处理耗时（毫秒）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (policy_id) REFERENCES policies(id) ON DELETE CASCADE
);

-- 创建处理日志表索引
CREATE INDEX IF NOT EXISTS idx_processing_logs_policy_id ON processing_logs(policy_id);
CREATE INDEX IF NOT EXISTS idx_processing_logs_action ON processing_logs(action);
CREATE INDEX IF NOT EXISTS idx_processing_logs_status ON processing_logs(status);
CREATE INDEX IF NOT EXISTS idx_processing_logs_created_at ON processing_logs(created_at);
