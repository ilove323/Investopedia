# RAGFlow 配置自动应用功能说明

<!-- 文档类型: 技术配置指南 | 版本: 2026.1 | 更新时间: 2026-01-25 -->
<!-- 描述: RAGFlow系统配置参数说明和自动配置功能使用指南 -->

## 📋 功能概述

系统现在支持从 `config.ini` 文件自动读取和应用RAGFlow配置参数，无需手动在RAGFlow界面中逐项配置。

**更新状态 (2026-01-25)**：
- ✅ RAGFlow自动配置系统已完成
- ✅ 16个配置参数全部生效
- ✅ 文档查看器已替换上传功能
- ✅ 配置测试脚本验证通过

## ✅ 配置生效确认

### 1. 配置文件参数
```bash
# 运行配置测试脚本
python test_ragflow_config.py
```

测试结果显示：
- **文档配置参数 (9个)**：分块大小、PDF解析器、元数据提取等
- **高级配置参数 (7个)**：相似度阈值、最大聚类数、检索模式等
- **服务连接状态**：✅ 正常

### 2. 自动配置应用

**应用时机**：
- ✅ 应用启动时自动初始化
- ✅ RAGFlow客户端创建时自动应用
- ✅ 手动配置知识库时应用

**配置验证**：
- 在应用侧边栏查看 "🔧 配置详情" 
- 配置状态显示为 ✅ 时表示参数已正确加载

## 📊 配置参数详情

### 文档处理配置
```ini
[RAGFLOW]
# 分块配置（适合政策文档）
document_chunk_size = 800           # 政策条目较长
document_chunk_overlap = 100        # 保持上下文连贯
document_smart_chunking = true      # 智能分块

# 解析配置
ragflow_pdf_parser = deepdoc        # 深度文档解析
ragflow_ocr_enabled = true          # OCR备用支持
```

### 元数据与检索配置
```ini
# 元数据提取
ragflow_auto_metadata = true        # 自动元数据提取
ragflow_metadata_extraction = true  # 结构化信息提取
ragflow_table_recognition = true    # 表格识别
ragflow_entity_normalization = true # 实体归一化

# 检索优化
ragflow_similarity_threshold = 0.3  # 相似度阈值
ragflow_max_tokens = 2048           # 最大TOKEN数
ragflow_retrieval_mode = general    # 通用检索模式
ragflow_graph_retrieval = true      # 图检索增强
```

## 🔧 配置验证方法

### 方法1：运行测试脚本
```bash
cd /path/to/Investopedia
python test_ragflow_config.py
```

### 方法2：查看应用界面
1. 启动应用：`streamlit run app.py`
2. 查看侧边栏 "服务状态"
3. 展开 "🔧 配置详情"
4. 确认显示：✅ RAGFlow配置已自动应用

### 方法3：检查日志输出
```bash
tail -f logs/app.log
```

查找以下日志：
- `开始初始化RAGFlow配置...`
- `✅ RAGFlow配置应用成功`
- `配置参数将在文档上传时应用`

## 📚 使用说明

### 1. 知识库配置
知识库名称：`policy_demo_kb`（在config.ini中配置）

**前置要求**：
1. 确保RAGFlow服务运行在 `http://117.21.184.150:9380`
2. 在RAGFlow Web界面中创建名为 `policy_demo_kb` 的知识库
3. API Key已正确配置

### 2. 配置修改
要修改配置参数：
1. 编辑 `config/config.ini` 文件
2. 修改 `[RAGFLOW]` 部分的相关参数
3. 重启应用，配置会自动重新加载

### 3. 参数说明
- **chunk_size**: 文档分块大小（推荐800，适合政策文档）
- **pdf_parser**: PDF解析器（deepdoc=深度解析，适合复杂布局）
- **similarity_threshold**: 检索相似度阈值（0.3=平衡精度与召回）
- **entity_normalization**: 实体归一化（推荐开启，提升检索精度）

## ⚠️ 注意事项

1. **API兼容性**：配置自动应用功能会适应不同版本的RAGFlow API
2. **配置优先级**：config.ini > 环境变量 > 默认值
3. **热重载**：某些配置修改需要重启应用才能生效
4. **错误处理**：即使API配置失败，核心功能仍可正常使用

## 🎯 配置建议

### 政策文档优化配置
```ini
# 针对政策文档的推荐配置
document_chunk_size = 800          # 政策条目通常较长
ragflow_pdf_parser = deepdoc       # 政策文档格式复杂
ragflow_entity_normalization = true # 政策实体标准化
ragflow_table_recognition = true    # 政策表格信息重要
ragflow_similarity_threshold = 0.3  # 平衡准确性与覆盖率
```

---

✨ **配置功能已完全实现，所有参数都会在应用启动时自动生效！**