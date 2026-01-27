# 知识图谱SQLite存储实施报告

## 📋 任务概述

实现知识图谱的SQLite数据库持久化存储，替换之前的session state内存存储方案。用户要求：
1. ✅ 添加进度显示
2. ✅ 如果RAGFlow同步失败，不构建图谱
3. ✅ 提供全量重建和增量更新两个按钮

## 🎯 实施内容

### 1. 创建GraphDAO数据访问层

**文件**: `src/database/graph_dao.py` (新建, 206行)

**核心功能**:
- `save_graph(graph_data, is_incremental)` - 保存图谱，支持全量/增量
- `load_graph()` - 从数据库加载最新图谱
- `get_stats()` - 获取图谱统计信息（节点数、边数、更新时间）
- `_merge_graphs(existing, new)` - 合并图谱（用于增量更新）
- `clear_graph()` - 清空图谱数据

**数据库表结构**:
```sql
CREATE TABLE knowledge_graph (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    graph_data TEXT NOT NULL,           -- JSON格式存储
    node_count INTEGER DEFAULT 0,       -- 节点数统计
    edge_count INTEGER DEFAULT 0,       -- 边数统计
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**数据格式**:
```json
{
  "nodes": [
    {"id": "node1", "label": "节点1", "type": "POLICY", "attributes": {...}},
    ...
  ],
  "edges": [
    {"from": "node1", "to": "node2", "label": "关系", "attributes": {...}},
    ...
  ]
}
```

### 2. 修改DataSyncService添加图谱构建

**文件**: `src/services/data_sync.py` (修改)

**新增方法**:
- `build_knowledge_graph(kb_name, is_incremental, progress_callback)` - 构建图谱主方法
- `_init_graph_dao()` - 延迟初始化GraphDAO
- `_extract_entities_simple(content, doc_name)` - 简单实体提取
- `_extract_relations_simple(content, entities)` - 简单关系提取

**构建流程** (5步):
1. 获取RAGFlow文档列表
2. 分析文档内容，提取实体和关系
3. 构建图谱数据结构
4. 保存到SQLite数据库
5. 返回构建结果

**返回格式**:
```python
{
    'success': True/False,
    'node_count': 10,
    'edge_count': 15,
    'doc_count': 5,
    'elapsed_time': '2.34秒',
    'timestamp': '2024-01-01T12:00:00',
    'error': '错误信息'  # 仅失败时
}
```

### 3. 文档页面添加图谱构建按钮

**文件**: `src/pages/documents_page.py` (修改)

**新增功能**:
- 在文档列表统计信息后添加图谱构建区域
- 🔄 **全量重建图谱** 按钮 - 重新分析所有文档
- ➕ **增量更新图谱** 按钮 - 仅分析新增/更新文档
- `build_graph(kb_name, is_incremental)` 辅助函数

**用户体验**:
- ✅ 进度条显示构建进度 (1/5, 2/5, ...)
- ✅ 实时状态消息更新
- ✅ 成功提示包含详细统计（节点数、边数、文档数、耗时）
- ✅ 失败提示显示错误信息

### 4. 图谱页面改为只读模式

**文件**: `src/pages/graph_page.py` (重构)

**主要变更**:
- ❌ 删除 `build_policy_graph()` 函数（旧的自动构建逻辑）
- ✅ 新增 `load_graph_from_database()` 函数（仅读取）
- ✅ 侧边栏显示图谱统计信息（节点数、边数、最后更新时间）
- ✅ 友好提示如何构建图谱（引导用户去文档页面）
- ✅ 移除"同步后自动重建图谱"的行为

**用户提示**:
```
💡 如何构建知识图谱：

1. 前往 📚 RAGFlow文档查看器 页面
2. 确保已上传政策文档到RAGFlow
3. 点击以下按钮之一：
   - 🔄 全量重建图谱 - 重新分析所有文档
   - ➕ 增量更新图谱 - 仅分析新增文档
4. 等待构建完成后返回此页面查看

⚠️ 注意：图谱不会自动生成，必须手动点击构建按钮
```

## 🧪 测试验证

**测试文件**: `tests/test_graph_storage.py` (新建, 161行)

**测试用例**:
1. ✅ **GraphDAO基本功能** - 初始化、保存、加载、统计
2. ✅ **增量更新功能** - 合并现有图谱和新图谱，去重更新
3. ✅ **图谱数据格式** - 验证nodes/edges结构正确性

**测试结果**: 🎉 全部通过

```
============================================================
🎉 所有测试通过！
============================================================
```

## 📁 文件变更清单

### 新建文件 (2个)
- ✅ `src/database/graph_dao.py` - GraphDAO类，206行
- ✅ `tests/test_graph_storage.py` - 测试脚本，161行

### 修改文件 (3个)
- ✅ `src/services/data_sync.py` - 添加build_knowledge_graph方法及相关辅助方法
- ✅ `src/pages/documents_page.py` - 添加图谱构建按钮和build_graph函数
- ✅ `src/pages/graph_page.py` - 重构为只读模式，添加load_graph_from_database

## 🔑 关键技术决策

### 1. 为什么选择SQLite + JSON？
- ✅ 无需额外依赖，Python内置支持
- ✅ JSON格式灵活，易于扩展
- ✅ 适合中小规模图谱 (<10k节点)
- ✅ 支持事务，保证数据一致性

### 2. 增量更新策略
- 基于节点ID去重合并
- 基于边的(from, to)组合去重
- 新数据覆盖旧数据（允许更新）

### 3. 用户控制构建时机
- ❌ 不再自动构建图谱
- ✅ 必须手动点击按钮
- ✅ 避免意外的高CPU占用
- ✅ 让用户明确知道何时构建

## 🚀 使用指南

### 构建全量图谱
1. 前往"📚 RAGFlow文档查看器"页面
2. 确保文档已上传并处理完成
3. 点击"🔄 全量重建图谱"按钮
4. 等待进度条完成（通常几秒到几十秒）
5. 查看成功提示中的统计信息
6. 前往"📊 知识图谱"页面查看可视化

### 增量更新图谱
1. 上传新文档到RAGFlow
2. 前往"📚 RAGFlow文档查看器"页面
3. 点击"➕ 增量更新图谱"按钮
4. 新实体和关系会合并到现有图谱

### 查看图谱
1. 前往"📊 知识图谱"页面
2. 侧边栏显示图谱统计信息
3. 如果图谱为空，会显示友好提示

## ⚠️ 注意事项

1. **实体提取算法简化**：当前使用基于关键词的简单提取，可后续升级为NLP模型
2. **关系提取逻辑**：当前为相邻实体连接，可优化为语义关系抽取
3. **数据库位置**：`data/database/policies.db`，与政策数据共用
4. **图谱格式兼容**：需要PolicyGraph能够解析{nodes, edges}格式

## 🔮 后续优化建议

1. **NLP集成**：使用jieba/spaCy进行实体识别
2. **关系抽取**：基于依存句法或知识图谱补全
3. **图谱压缩**：对大规模图谱启用压缩存储
4. **版本控制**：保留历史版本，支持回滚
5. **性能优化**：对大文档集合使用批处理和并行

## ✅ 验证清单

- [x] GraphDAO初始化正常
- [x] 全量保存和加载图谱
- [x] 增量更新正确合并
- [x] 图谱统计准确
- [x] 文档页面按钮显示正常
- [x] 进度显示功能正常
- [x] 错误处理友好提示
- [x] 图谱页面只读模式
- [x] 测试全部通过
- [x] 无语法错误

## 📊 代码统计

- 新增代码: ~500行
- 修改代码: ~300行
- 测试代码: ~160行
- 总计影响: ~960行

---

**实施日期**: 2024年
**实施者**: GitHub Copilot
**状态**: ✅ 完成并测试通过
