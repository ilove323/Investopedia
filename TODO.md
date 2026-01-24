# 📋 详细任务列表和执行计划

> 最后更新：2026-01-24
> 当前阶段：BUG修复和测试验证阶段

---

## 🎯 任务总览

| 阶段 | 优先级 | 任务数 | 工作量 | 状态 |
|------|--------|--------|--------|------|
| **阶段0：关键修复** | 🔴 最高 | 2 | 1-2h | ✅ 完成 |
| **阶段0.1：BUG修复** | 🔴 最高 | 1 | 1h | ✅ 完成 |
| **阶段1：代码注释** | 🔴 最高 | 8 | 3-4h | ⏳ 待开始 |
| **阶段2：页面实现** | 🟠 高 | 5 | 8-10h | ✅ 完成 |
| **阶段3：UI组件** | 🟠 高 | 3 | 2-3h | ✅ 完成 |
| **阶段4：测试验证** | 🟡 中 | 2 | 1-2h | 🔄 进行中 |
| **阶段5：文档完善** | 🟡 中 | 3 | 1-2h | 🔄 进行中 |
| **总计** | — | 24 | 17-24h | 🟢 42% 完成 |

---

## 🟢 阶段0.1：BUG修复（关键）

**目标：修复文档上传时的UNIQUE约束错误**
**预计工作量：1小时**
**关键性：必须修复，否则上传功能无法使用**

### 任务0.1.1：修复 documents_page.py 文档上传验证
<details open>
<summary><strong>✅ 已完成</strong></summary>

**任务号：BUG-FIX-001**
**优先级：🔴 紧急**
**工作量：30分钟**
**所属文件：** `src/pages/documents_page.py`
**修改行数：约35行**

**问题诊断：**
上传文档后出现错误：`UNIQUE constraint failed: policies.document_number`

原因分析：
1. document_number字段允许NULL值，SQLite中多个NULL会导致约束冲突
2. 当用户未填文号时，空字符串转NULL会导致多个NULL值
3. 没有在上传前检查文号是否已存在

**解决方案：**
1. 前端表单验证 - 检查document_number唯一性和规范化输入
2. 后端验证 - DAO层也进行重复检查（防线）
3. 错误处理 - 给出清晰的中文错误提示

**修改内容：**
```python
# 新增验证逻辑（第62-75行）
if not title or title.strip() == '':
    st.error("❌ 政策名称不能为空")
    return

# 检查文号唯一性
dao = PolicyDAO()
if document_number and document_number.strip() != '':
    existing_policy = dao.get_policy_by_document_number(document_number.strip())
    if existing_policy:
        st.error(f"❌ 文号 '{document_number}' 已存在，请修改或联系管理员")
        return
    document_number = document_number.strip()
else:
    st.warning("⚠️ 建议填写文号以便管理和搜索")
    document_number = None

# 改进错误处理（第109-115行）
except ValueError as e:
    st.error(f"❌ {str(e)}")
except Exception as e:
    if "UNIQUE constraint failed" in str(e):
        st.error("❌ 文号已存在，请检查或修改文号后重试")
    else:
        st.error(f"❌ 上传失败：{str(e)}")
```

**验收标准：**
- ✅ 上传相同文号 -> 显示"文号已存在"错误
- ✅ 上传空文号 -> 显示警告但允许继续
- ✅ 上传新文号 -> 成功上传
- ✅ 不出现数据库约束异常

</details>

### 任务0.1.2：修复 policy_dao.py create_policy方法
<details open>
<summary><strong>✅ 已完成</strong></summary>

**任务号：BUG-FIX-001**
**优先级：🔴 紧急**
**工作量：30分钟**
**所属文件：** `src/database/policy_dao.py`
**修改行数：约50行**

**问题诊断：**
create_policy方法缺少数据验证，导致重复文号和NULL值处理不当。

**解决方案：**
在DAO层添加验证逻辑，作为数据层防线。

**修改内容：**
```python
# 第67-100行：完善函数文档
"""创建政策记录
    
Args:
    policy_data: 政策数据字典，包含以下字段：
        - title: 政策标题（必填）
        - document_number: 文号（可选，但如果提供必须唯一）
        ...
        
Returns:
    int: 创建的政策ID
    
Raises:
    ValueError: 当document_number重复时
    Exception: 其他数据库错误
"""

# 第101-115行：数据验证逻辑
document_number = policy_data.get('document_number')
if document_number and document_number.strip() != '':
    document_number = document_number.strip()
    existing = self.get_policy_by_document_number(document_number)
    if existing:
        error_msg = f"文号 '{document_number}' 已存在，无法创建重复的政策"
        logger.warning(f"创建政策失败 - {error_msg}")
        raise ValueError(error_msg)
else:
    # 将空字符串转换为None，避免UNIQUE约束冲突
    document_number = None
```

**编码规范遵循：**
- ✅ 函数文档包含Args、Returns、Raises
- ✅ 错误消息清晰的中文
- ✅ 异常类型准确（ValueError for业务错误）
- ✅ 日志信息详细

**验收标准：**
- ✅ 重复文号时抛出ValueError
- ✅ 空文号转为None不报错
- ✅ 新文号成功插入
- ✅ 日志记录完整

</details>

---
<details open>
<summary><strong>✅ 已完成</strong></summary>

**任务号：TASK-0.1**
**优先级：🔴 紧急**
**工作量：30-40分钟**
**所属文件：** `app.py`
**修改行数：约30行**

**任务说明：**
app.py还在尝试从已删除的`config.app_config`模块导入配置。需要改为使用新的`src.config.get_config()`系统。

**需要修改的地方：**

1. **第17-25行** - 替换导入语句
   ```python
   # ❌ 旧代码（会报错：ModuleNotFoundError）
   from config.app_config import (
       APP_NAME,
       APP_DESCRIPTION,
       APP_ICON,
       APP_LAYOUT,
       PAGES,
       DATA_DIR,
       LOGS_DIR
   )

   # ✅ 新代码
   from src.config import get_config
   from pathlib import Path

   config = get_config()

   APP_NAME = config.app_name
   APP_DESCRIPTION = config.app_description
   APP_ICON = config.app_icon
   APP_LAYOUT = config.app_layout
   DATA_DIR = config.data_dir
   LOGS_DIR = config.logs_dir

   PAGES = {
       "🏠 欢迎": "home",
       "🔍 搜索": "search",
       "📊 图谱": "graph",
       "🎤 语音": "voice",
       "📄 文档": "documents",
       "📈 分析": "analysis"
   }
   ```

2. **第32行** - 更新日志初始化
   ```python
   # 修改这一行
   logger = setup_logger(
       log_file=str(config.logs_dir_path / "app.log"),
       log_level=config.log_level
   )
   ```

3. **验证测试** - 运行应用检查是否正常启动
   ```bash
   cd /Users/laurant/Documents/github/Investopedia
   streamlit run app.py
   ```

**验收标准：**
- [ ] 应用能正常启动，不报ImportError
- [ ] Streamlit页面显示应用标题和icon
- [ ] 侧边栏显示所有5个页面选项
- [ ] 服务状态检查能正常执行

**相关文档：**
- 详细实现指南：见 `IMPLEMENTATION_PLAN.md` 第一部分 - 任务1.1
- 新的配置系统说明：见 `README.md` 配置说明章节

</details>

### 任务0.2：验证数据库模块兼容性
<details open>
<summary><strong>✅ 已完成</strong></summary>

**任务号：TASK-0.2**
**优先级：🔴 紧急**
**工作量：20-30分钟**
**所属文件：** `src/database/db_manager.py`, `src/database/policy_dao.py`
**修改行数：约10-20行**

**任务说明：**
验证这两个文件是否有使用旧的配置系统，如果有则更新为新的ConfigLoader。

**检查清单：**

1. **检查 src/database/db_manager.py**
   - [ ] 搜索文件中是否有 `from config` 或 `import config` 的导入
   - [ ] 搜索是否有 `CONFIG.` 或 `app_config.` 的引用
   - [ ] 如果有，按照模板替换：
     ```python
     # ❌ 旧方式
     from config.database_config import DB_PATH, DB_CONFIG

     # ✅ 新方式
     from src.config import get_config
     config = get_config()
     db_path = config.sqlite_path
     db_config = config.sqlite_config
     ```

2. **检查 src/database/policy_dao.py**
   - [ ] 同样检查导入和引用
   - [ ] 更新所有配置相关的导入

3. **验证数据库连接**
   ```python
   # 可以在app.py的main()函数中临时添加这段代码测试
   try:
       from src.config import get_config
       from src.database.db_manager import get_db_manager

       config = get_config()
       print(f"✓ 配置加载成功")

       db = get_db_manager()
       print(f"✓ 数据库连接成功: {config.sqlite_path}")

   except Exception as e:
       print(f"✗ 错误: {e}")
       import traceback
       traceback.print_exc()
   ```

**验收标准：**
- [ ] 两个文件中没有对旧配置系统的引用
- [ ] app.py能成功调用get_db_manager()
- [ ] 数据库文件路径正确（data/database/policy.db）
- [ ] 没有SQL异常或连接错误

**相关文档：**
- ConfigLoader使用方式：见 `IMPLEMENTATION_PLAN.md` 第四部分

</details>

---

## 🔴 阶段1：代码注释和优化（最高优先级）

**目标：为所有已完成的实现文件添加详细的中文注释**
**预计工作量：3-4小时**
**重要性：便于后续维护和理解，为继续开发奠定基础**

### 任务1.1：给 src/config/ 模块添加注释
<details>
<summary><strong>点击展开详细任务描述</strong></summary>

**任务号：TASK-1.1**
**优先级：🔴 最高**
**工作量：40-50分钟**
**所属文件：** `src/config/config_loader.py`, `src/config/__init__.py`

**需要添加的注释：**

1. **文件头部注释** - 解释ConfigLoader的作用和工作原理
   ```
   - ConfigLoader的职责
   - 读取config.ini文件的过程
   - 环境变量覆盖机制
   - 支持的配置类型（INT, FLOAT, BOOL, STRING, LIST）
   ```

2. **关键方法注释** - 每个public方法和property都需要详细注释
   ```
   - get()：如何从INI文件读取字符串值
   - get_int()、get_float()、get_bool()：类型转换逻辑
   - get_list()：如何解析逗号分隔的列表
   - 各个@property：参数覆盖优先级说明
   ```

3. **复杂逻辑注释** - 特别是环境变量覆盖部分
   ```
   示例：
   @property
   def ragflow_host(self) -> str:
       # 优先级：环境变量 > config.ini > 默认值
       # 1. 先检查环境变量RAGFLOW_HOST（用于容器部署）
       # 2. 如果环境变量未设置，读取config.ini中的值
       # 3. 如果config.ini中也没有，使用默认值localhost
   ```

**验收标准：**
- [ ] 文件顶部有详细的模块说明
- [ ] 每个public方法都有完整的docstring（参数、返回值、异常）
- [ ] 关键逻辑行都有中文注释
- [ ] 没有自相矛盾的注释

</details>

### 任务1.2：给 src/services/ 模块添加注释
<details>
<summary><strong>点击展开详细任务描述</strong></summary>

**任务号：TASK-1.2**
**优先级：🔴 最高**
**工作量：50-60分钟**
**所属文件：** `src/services/ragflow_client.py`, `src/services/whisper_client.py`, `src/services/api_utils.py`

**需要添加的注释：**

对于 **ragflow_client.py**：
- [ ] 说明RAGFlow是什么、提供什么功能
- [ ] API端点说明（健康检查、上传、搜索、问答）
- [ ] 重试机制和超时控制的设计
- [ ] 错误处理策略

对于 **whisper_client.py**：
- [ ] 说明Whisper是什么、怎样进行语音识别
- [ ] 支持的音频格式和参数
- [ ] 音频预处理流程（降噪、格式转换等）
- [ ] 超时和文件大小限制

对于 **api_utils.py**：
- [ ] HTTP请求工具函数的作用
- [ ] 响应解析的流程
- [ ] 错误处理的规则

**验收标准：**
- [ ] 文件顶部有详细说明
- [ ] 每个函数都有docstring
- [ ] 关键的API调用都有注释
- [ ] 异常处理的目的都已说明

</details>

### 任务1.3：给 src/business/ 模块添加注释
<details>
<summary><strong>点击展开详细任务描述</strong></summary>

**任务号：TASK-1.3**
**优先级：🔴 最高**
**工作量：60分钟**
**所属文件：**
- `src/business/metadata_extractor.py` - 元数据提取规则
- `src/business/tag_generator.py` - 标签生成算法
- `src/business/validity_checker.py` - 时效性检查逻辑
- `src/business/impact_analyzer.py` - 影响分析逻辑

**需要添加的注释详情：**

对于 **metadata_extractor.py**：
- 每种提取操作的正则表达式说明
- 提取顺序和优先级说明
- 处理异常情况的方式

对于 **tag_generator.py**：
- 三级标签体系的设计
- 关键词匹配的规则
- 置信度计算的算法

对于 **validity_checker.py**：
- 失效检查的各种情况
- 政策替代关系的判断标准
- 预警机制的工作流程

对于 **impact_analyzer.py**：
- 影响范围分析的维度
- 程度评估的等级划分
- 建议生成的逻辑

**验收标准：**
- [ ] 每个业务逻辑都有清晰的中文说明
- [ ] 算法或规则都有设计思路的注释
- [ ] 异常边界情况都有说明

</details>

### 任务1.4：给 src/models/ 模块添加注释
<details>
<summary><strong>点击展开详细任务描述</strong></summary>

**任务号：TASK-1.4**
**优先级：🔴 最高**
**工作量：40分钟**
**所属文件：** `src/models/policy.py`, `src/models/tag.py`, `src/models/graph.py`

**需要添加的注释：**

对于 **policy.py**：
- Policy类的各个属性的含义和类型
- 数据验证规则
- 序列化/反序列化的流程

对于 **tag.py**：
- Tag类和三级标签体系
- 标签之间的层级关系
- 置信度的含义

对于 **graph.py**：
- NetworkX图的操作方法
- 节点和边的属性说明
- 图遍历和查询的方法

**验收标准：**
- [ ] 数据模型的各个字段都有说明
- [ ] 复杂的操作都有过程说明
- [ ] 类型转换和验证都有说明

</details>

### 任务1.5：给 src/database/ 模块添加注释
<details>
<summary><strong>点击展开详细任务描述</strong></summary>

**任务号：TASK-1.5**
**优先级：🔴 最高**
**工作量：50分钟**
**所属文件：** `src/database/db_manager.py`, `src/database/policy_dao.py`, `src/database/schema.sql`

**需要添加的注释：**

对于 **schema.sql**：
- 每个表的用途说明
- 每个字段的含义和约束
- 表之间的外键关系

对于 **db_manager.py**：
- 数据库连接的初始化
- 连接池的配置
- 事务管理的说明

对于 **policy_dao.py**：
- 每个SQL查询的目的
- 参数的含义
- 返回值的结构

**验收标准：**
- [ ] SQL中文注释完整
- [ ] 数据库操作都有说明
- [ ] DAO方法的职责清晰

</details>

### 任务1.6：给 src/utils/ 模块添加注释
<details>
<summary><strong>点击展开详细任务描述</strong></summary>

**任务号：TASK-1.6**
**优先级：🔴 最高**
**工作量：40分钟**
**所属文件：** `src/utils/logger.py`, `src/utils/file_utils.py`, `src/utils/text_utils.py`

**需要添加的注释：**

对于 **logger.py**：
- 日志级别的含义
- 日志输出的地方（控制台/文件）
- 轮转日志的配置

对于 **file_utils.py**：
- 文件处理的各个步骤
- 文件类型验证的规则
- 文件大小限制的说明

对于 **text_utils.py**：
- 文本处理的各个工具函数
- 正则表达式的含义
- 处理逻辑的说明

**验收标准：**
- [ ] 每个工具函数都有明确的用途说明
- [ ] 使用方式有示例
- [ ] 返回值结构清晰

</details>

### 任务1.7：给 src/components/ 模块添加注释
<details>
<summary><strong>点击展开详细任务描述</strong></summary>

**任务号：TASK-1.7**
**优先级：🔴 最高**
**工作量：30分钟**
**所属文件：** `src/components/search_ui.py`, `src/components/graph_ui.py`（其他两个还未实现）

**需要添加的注释：**

对于 **search_ui.py**：
- UI组件的功能说明
- 搜索框和过滤条件的设计
- 用户交互的处理

对于 **graph_ui.py**：
- 图谱渲染的过程
- Pyvis的配置
- 交互功能的说明

**验收标准：**
- [ ] 组件的职责明确
- [ ] 参数和返回值有说明
- [ ] Streamlit特定的API有注释

</details>

### 任务1.8：修复 app.py 的注释
<details>
<summary><strong>点击展开详细任务描述</strong></summary>

**任务号：TASK-1.8**
**优先级：🔴 最高**
**工作量：30分钟**
**所属文件：** `app.py`

**需要修改的注释：**

1. **更新导入部分的注释** - 说明新的配置系统
2. **函数注释** - 确保所有函数都有docstring
3. **会话状态说明** - initialize_session_state()中详细说明每个变量

**验收标准：**
- [ ] 文件头部注释正确
- [ ] 所有函数都有明确的说明
- [ ] 会话变量的用途都清楚

</details>

---

## 🟠 阶段2：页面实现（高优先级）

**目标：实现5个页面模块的核心功能**
**预计工作量：8-10小时**
**重要性：应用的主要用户界面，直接影响用户体验**

### 任务2.1：实现搜索页面 (search_page.py)
<details>
<summary><strong>✅ 已完成</strong></summary>

**任务号：TASK-2.1**
**优先级：🟠 高**
**工作量：150-180分钟** ✅
**所属文件：** `src/pages/search_page.py`
**预期代码行数：150-200行** ✅

**功能需求：**

1. **搜索UI布局**
   - [ ] 快速搜索框（顶部，显眼）
   - [ ] 可折叠的高级过滤面板
   - [ ] 搜索按钮 + 清空按钮

2. **过滤维度**
   - [ ] 关键词搜索（支持政策标题、内容）
   - [ ] 政策类型（专项债/特许经营/数据资产，多选）
   - [ ] 发文机关（文本输入，模糊匹配）
   - [ ] 发布日期范围（日期选择器）
   - [ ] 适用地区（文本输入）
   - [ ] 政策状态（有效/即将过期/已过期/已更新，多选）

3. **搜索处理**
   - [ ] 调用RAGFlow进行语义搜索
   - [ ] 基于过滤条件的本地过滤
   - [ ] 结果去重和排序
   - [ ] 错误处理和用户提示

4. **结果展示**
   - [ ] 结果列表（分页，每页10条）
   - [ ] 每条结果使用政策卡片展示
   - [ ] 显示相关性分数
   - [ ] 分页导航（上一页、下一页、当前页码）

5. **详情交互**
   - [ ] 点击"详情"按钮展开/折叠详细信息
   - [ ] 显示政策的完整信息和相关政策

**实现参考：**
详见 `IMPLEMENTATION_PLAN.md` 第三部分 - 搜索页面参考实现

**验收标准：**
- [ ] 快速搜索和高级过滤都能正常工作
- [ ] RAGFlow搜索能返回结果
- [ ] 过滤条件能正确应用
- [ ] 分页导航正常
- [ ] 没有Python错误或异常
- [ ] 代码有详细的中文注释

</details>

### 任务2.2：实现文档管理页面 (documents_page.py)
<details>
<summary><strong>✅ 已完成</strong></summary>

**任务号：TASK-2.2**
**优先级：🟠 高**
**工作量：180-210分钟** ✅
**所属文件：** `src/pages/documents_page.py`
**预期代码行数：200-250行** ✅

**功能需求：**

1. **文档上传**
   - [ ] 拖拽上传区域
   - [ ] 文件选择对话框
   - [ ] 格式验证（PDF/DOCX/XLSX/TXT）
   - [ ] 大小验证（≤50MB）
   - [ ] 上传进度显示

2. **文档处理流程**
   - [ ] 保存上传的文件到 data/uploads/
   - [ ] 调用 metadata_extractor 提取元数据
   - [ ] 调用 RAGFlow 进行向量化处理
   - [ ] 调用 tag_generator 自动生成标签
   - [ ] 保存政策信息到SQLite数据库
   - [ ] 更新知识图谱
   - [ ] 记录处理日志

3. **文档列表**
   - [ ] 表格显示：标题、发文机关、发布日期、类型、状态
   - [ ] 搜索和过滤
   - [ ] 排序（按日期、标题等）
   - [ ] 分页

4. **操作功能**
   - [ ] 查看详情：显示完整的元数据
   - [ ] 编辑元数据：修改自动提取的错误信息
   - [ ] 删除：从数据库和RAGFlow中删除
   - [ ] 批量操作：批量删除、批量重新处理

5. **处理日志**
   - [ ] 显示最近处理的文档
   - [ ] 显示处理状态（成功/失败/处理中）
   - [ ] 显示处理消息和错误信息
   - [ ] 支持重新处理失败的文档

**关键设计点：**

处理流程编排：
```
上传 → 验证 → 保存 → 元数据提取 → RAGFlow向量化 → 标签生成 → DB存储 → 图谱更新 → 日志记录
```

每一步都需要：
- 成功/失败的反馈
- 详细的日志记录
- 异常处理和重试机制

**验收标准：**
- [ ] 文件上传和处理完整
- [ ] 所有处理步骤都有日志
- [ ] 错误能被正确捕获和显示
- [ ] UI清晰易用
- [ ] 代码有详细注释

</details>

### 任务2.3：实现知识图谱页面 (graph_page.py)
<details>
<summary><strong>✅ 已完成</strong></summary>

**任务号：TASK-2.3**
**优先级：🟠 高**
**工作量：150-180分钟** ✅
**所属文件：** `src/pages/graph_page.py`
**预期代码行数：180-220行** ✅

**功能需求：**

1. **图数据加载**
   - [ ] 从SQLite数据库加载所有政策
   - [ ] 加载政策关系（policy_relations表）
   - [ ] 限制节点数量（默认200个，避免过载）
   - [ ] 过滤选项（按类型、机构等）

2. **NetworkX图构建**
   - [ ] 创建无向图（is_directed=False）
   - [ ] 添加政策节点（id, title, type等属性）
   - [ ] 添加关系边（relation, weight等属性）
   - [ ] 计算节点权重（度数）

3. **Pyvis可视化**
   - [ ] 配置布局（Force-Directed）
   - [ ] 设置节点样式
     - 颜色按类型：专项债(红) / 特许经营(绿) / 数据资产(蓝)
     - 大小按权重：度数越高越大
     - 标签显示政策标题（缩短显示）
   - [ ] 设置边样式
     - 颜色和粗细按关系类型
   - [ ] 启用物理引擎（自动布局）
   - [ ] 生成HTML并在Streamlit中显示

4. **交互功能**
   - [ ] 图谱控制面板
     - [ ] 选择视图（全局/按类型/按机构）
     - [ ] 布局算法选择（Force-Directed/Hierarchical等）
     - [ ] 节点大小调整滑块
     - [ ] 物理引擎开关
   - [ ] 节点点击事件
     - [ ] 显示政策详情（右侧面板）
     - [ ] 显示相关政策（同类型、同机构等）
     - [ ] 支持跳转到搜索页查看该政策

5. **导出功能**
   - [ ] 导出为HTML（保存可视化结果）
   - [ ] 导出为JSON（导出图数据）
   - [ ] 导出为SVG（导出图片）

**关键设计点：**

节点颜色映射：
```python
color_map = {
    '专项债': '#FF6B6B',
    '特许经营': '#4ECDC4',
    '数据资产': '#95E1D3',
    '其他': '#95A5A6'
}
```

节点大小计算：
```
size = min(30, 10 + degree * 2)
# 度数为0: 10, 度数为1: 12, 度数为5: 20, 度数为10: 30
```

**验收标准：**
- [ ] 图能正确渲染和显示
- [ ] 交互功能正常工作
- [ ] 导出功能能生成正确的文件
- [ ] 代码注释清晰

</details>

### 任务2.4：实现语音问答页面 (voice_page.py)
<details>
<summary><strong>✅ 已完成</strong></summary>

**任务号：TASK-2.4**
**优先级：🟠 高**
**工作量：140-170分钟** ✅
**所属文件：** `src/pages/voice_page.py`
**预期代码行数：160-200行** ✅

**功能需求：**

1. **语音输入方式**
   - [ ] 录音按钮（点击开始/停止）
   - [ ] 音频文件上传（选择本地文件）
   - [ ] 音频波形可视化（显示波形或进度条）
   - [ ] 录音时间显示

2. **音频处理**
   - [ ] 音频格式验证（.wav, .mp3, .m4a, .flac, .ogg）
   - [ ] 文件大小验证（≤50MB）
   - [ ] 调用Whisper服务进行转写
   - [ ] 文本后处理（标点符号、数字标准化）
   - [ ] 显示转写结果（文本）

3. **问答逻辑**
   - [ ] 问题解析（从转写的文本中提取问题）
   - [ ] 意图识别（是提问、查询、反馈）
   - [ ] 调用RAGFlow进行政策检索
   - [ ] 获取相关政策片段
   - [ ] 答案生成和格式化
   - [ ] 显示答案和相关政策

4. **历史记录**
   - [ ] 显示过往的问答记录
   - [ ] 显示时间、问题、答案
   - [ ] 支持点击重新查看详情
   - [ ] 支持删除记录
   - [ ] 支持点击快速重新提问

5. **错误处理**
   - [ ] Whisper服务不可用的提示
   - [ ] RAGFlow服务不可用的提示
   - [ ] 音频格式不支持的提示
   - [ ] 文件过大的提示

**工作流程：**
```
录音/上传 → 音频验证 → Whisper转写 → 文本展示 → RAGFlow检索 → 答案展示 → 记录保存
```

**验收标准：**
- [ ] 音频输入方式都能工作
- [ ] Whisper转写能正确执行
- [ ] RAGFlow检索能返回相关政策
- [ ] 答案展示清晰
- [ ] 历史记录管理正常
- [ ] 代码有详细注释

</details>

### 任务2.5：实现政策分析页面 (analysis_page.py)
<details>
<summary><strong>✅ 已完成</strong></summary>

**任务号：TASK-2.5**
**优先级：🟠 高**
**工作量：130-160分钟** ✅
**所属文件：** `src/pages/analysis_page.py`
**预期代码行数：150-200行** ✅

**功能需求：**

1. **时效性分析**
   - [ ] 使用 validity_checker 检查所有政策
   - [ ] 显示即将过期的政策（30天内）
   - [ ] 显示已过期的政策
   - [ ] 显示最近更新的政策
   - [ ] 过期预警列表（优先级排序）
   - [ ] 支持批量操作（标记为已处理、设置提醒等）

2. **影响分析**
   - [ ] 使用 impact_analyzer 分析各政策的影响
   - [ ] 按地区统计：各地区受影响的政策数量
   - [ ] 按行业统计：各行业受影响的政策数量
   - [ ] 按对象统计：各对象类型受影响的政策数量
   - [ ] 影响程度分级：高/中/低
   - [ ] 柱状图或饼图展示统计结果

3. **趋势统计**
   - [ ] 按年份统计发布的政策数量
   - [ ] 线性图显示发布趋势
   - [ ] 按类型分布统计（饼图）
   - [ ] 时间序列分析
   - [ ] 增长率计算

4. **详细数据表**
   - [ ] 显示所有政策的详细数据
   - [ ] 支持搜索和过滤
   - [ ] 按多列排序
   - [ ] 导出功能（CSV/Excel）
   - [ ] 详情查看

5. **仪表板设计**
   - [ ] KPI指标卡
     - 总政策数
     - 有效政策数
     - 即将过期数
     - 已过期数
   - [ ] 各分析模块用Tab组织
   - [ ] 清晰的可视化图表

**关键数据计算：**

时效性分析逻辑：
```python
# 即将过期：失效日期在30天内且还未失效
# 已过期：失效日期在今天之前
# 活跃：失效日期在30天之后或还未定义
```

影响分析逻辑：
```python
# 遍历所有政策和它们的标签/地区/行业
# 统计受影响的对象数量
# 计算各维度的分布
```

**验收标准：**
- [ ] 所有数据统计正确
- [ ] 图表清晰易读
- [ ] 数据表功能完整
- [ ] 导出功能可用
- [ ] 代码注释充分
- [ ] 没有数据重复或遗漏

</details>

---

## 🟠 阶段3：UI组件完整实现（高优先级）

**目标：完整实现剩余的UI组件，增强页面的交互能力** ✅
**预计工作量：2-3小时** ✅
**重要性：页面框架完整，用户体验提升** ✅

### 任务3.1：完整实现 voice_ui.py
<details>
<summary><strong>✅ 已完成</strong></summary>

**任务号：TASK-3.1**
**优先级：🟠 高**
**工作量：60分钟** ✅
**所属文件：** `src/components/voice_ui.py`
**预期代码行数：80-120行** ✅

**组件功能：**
- 录音控制按钮（开始/停止/重新录制） ✅
- 波形可视化 ✅
- 文件上传组件 ✅
- 设置面板（采样率、声道、格式等） ✅

**职责：**
负责所有与语音输入相关的UI，voice_page.py调用这个组件来处理用户的语音输入。

</details>

### 任务3.2：完整实现 policy_card.py
<details>
<summary><strong>✅ 已完成</strong></summary>

**任务号：TASK-3.2**
**优先级：🟠 高**
**工作量：50-60分钟** ✅
**所属文件：** `src/components/policy_card.py`
**预期代码行数：60-100行** ✅

**组件功能：**
- 政策信息展示（标题、发文机关、日期等） ✅
- 标签展示（多个标签的布局） ✅
- 状态指示（有效/过期/更新） ✅
- 操作按钮（查看详情、编辑、删除） ✅
- 可选的展开/折叠详情 ✅

**职责：**
政策卡片是可复用组件，在搜索结果、文档列表、图谱详情等多个地方使用。

</details>

### 任务3.3：增强 search_ui.py 和 graph_ui.py
<details>
<summary><strong>✅ 已完成</strong></summary>

**任务号：TASK-3.3**
**优先级：🟠 高**
**工作量：60-90分钟** ✅
**所属文件：** `src/components/search_ui.py`, `src/components/graph_ui.py`

**search_ui.py 增强：**
- 高级搜索面板组件 ✅
- 搜索建议（自动完成） ✅
- 搜索历史 ✅
- 保存的搜索 ✅

**graph_ui.py 增强：**
- 图谱控制面板 ✅
- 布局选择 ✅
- 节点过滤 ✅
- 性能优化（限制节点数量） ✅

</details>

---

## 🟡 阶段4：测试验证（中优先级）

**目标：验证所有功能正常工作**
**预计工作量：1-2小时**

### 任务4.1：手工测试所有页面
<details>
<summary><strong>点击展开详细任务描述</strong></summary>

**任务号：TASK-4.1**
**优先级：🟡 中**
**工作量：60-90分钟**

**测试清单：**

- [ ] 搜索页面
  - [ ] 快速搜索能返回结果
  - [ ] 高级过滤选项能正常应用
  - [ ] 分页导航正常
  - [ ] 详情页能打开

- [ ] 文档管理页面
  - [ ] 能上传文档
  - [ ] 处理流程正常完成
  - [ ] 文档列表显示
  - [ ] 操作按钮能用

- [ ] 知识图谱页面
  - [ ] 图能正确渲染
  - [ ] 节点能点击
  - [ ] 控制面板能用
  - [ ] 导出功能能用

- [ ] 语音问答页面
  - [ ] 能上传音频
  - [ ] 转写能工作
  - [ ] 问答能返回结果
  - [ ] 历史记录能保存

- [ ] 分析页面
  - [ ] 数据统计正确
  - [ ] 图表显示正常
  - [ ] 表格功能完整
  - [ ] 导出能用

</details>

### 任务4.2：验证外部服务集成
<details>
<summary><strong>点击展开详细任务描述</strong></summary>

**任务号：TASK-4.2**
**优先级：🟡 中**
**工作量：30-60分钟**

**验证清单：**

- [ ] RAGFlow
  - [ ] 服务健康检查通过
  - [ ] 文档上传功能工作
  - [ ] 搜索功能工作
  - [ ] 问答功能工作

- [ ] Whisper
  - [ ] 服务健康检查通过
  - [ ] 音频转写工作
  - [ ] 返回结果正确

- [ ] SQLite数据库
  - [ ] 数据库文件正确创建
  - [ ] 表结构正确
  - [ ] 数据CRUD操作正常

</details>

---

## 🟡 阶段5：文档完善（中优先级）

**目标：完善项目文档**
**预计工作量：1-2小时**

### 任务5.1：更新 README.md
<details>
<summary><strong>点击展开详细任务描述</strong></summary>

**任务号：TASK-5.1**
**优先级：🟡 中**
**工作量：40-50分钟**

**需要更新的部分：**
- [ ] 功能说明更新（添加5个页面的详细说明）
- [ ] 使用示例（每个功能的使用流程）
- [ ] 故障排除（常见问题和解决方案）
- [ ] 性能优化建议

</details>

### 任务5.2：创建 API 文档
<details>
<summary><strong>点击展开详细任务描述</strong></summary>

**任务号：TASK-5.2**
**优先级：🟡 中**
**工作量：40-50分钟**

**需要创建的文档：**
- [ ] `docs/API.md` - 各服务的API文档
  - RAGFlow API说明
  - Whisper API说明
  - 数据库API说明
- [ ] `docs/DATA_MODELS.md` - 数据模型说明
- [ ] `docs/USAGE_EXAMPLES.md` - 使用示例

</details>

### 任务5.3：创建 DEVELOPMENT.md
<details>
<summary><strong>点击展开详细任务描述</strong></summary>

**任务号：TASK-5.3**
**优先级：🟡 中**
**工作量：30-40分钟**

**需要创建的文档：**
- [ ] `DEVELOPMENT.md` - 开发指南
  - 开发环境设置
  - 代码结构说明
  - 扩展指南
  - 贡献指南

</details>

---

## 📊 任务优先级和依赖关系

```
优先级 1（必须先做）：
├─ TASK-0.1：修复app.py配置导入
└─ TASK-0.2：验证db_manager兼容性
    ↓
优先级 2（依赖优先级1）：
├─ TASK-1.1～1.8：代码注释（可并行）
    ↓
优先级 3（依赖优先级2）：
├─ TASK-2.1～2.5：页面实现（可并行）
│   └─ TASK-3.1～3.3：UI组件（在页面实现中使用）
    ↓
优先级 4（依赖优先级3）：
├─ TASK-4.1～4.2：测试验证
    ↓
优先级 5（最后）：
└─ TASK-5.1～5.3：文档完善
```

---

## ✅ 完成标准

一个任务完成的标准：
1. ✅ 代码实现完整，功能正常工作
2. ✅ 代码有详细的中文注释
3. ✅ 没有Python语法错误
4. ✅ 没有逻辑错误或异常
5. ✅ 通过手工测试（如果有UI）
6. ✅ 集成到应用中能正常运行

---

## 📈 进度跟踪

建议按照以下顺序完成任务：

**第1天（优先级1）：** 配置和修复
- TASK-0.1 - 30分钟
- TASK-0.2 - 20分钟
- 测试应用启动 - 10分钟

**第2天（优先级2）：** 代码注释
- TASK-1.1～1.8 - 3-4小时

**第3-4天（优先级3）：** 页面实现
- TASK-2.1（搜索） - 3小时
- TASK-2.2（文档） - 3.5小时
- TASK-2.3（图谱） - 2.5小时
- TASK-2.4（语音） - 2.5小时
- TASK-2.5（分析） - 2.5小时

**第5天（优先级3）：** UI组件
- TASK-3.1～3.3 - 2-3小时

**第6天（优先级4）：** 测试
- TASK-4.1～4.2 - 1-2小时

**第7天（优先级5）：** 文档
- TASK-5.1～5.3 - 1-2小时

**总计时间：** 约16-23小时

---

**最后更新：2026-01-24**
**下一步：从TASK-0.1开始！**
