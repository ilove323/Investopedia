# 详细实现计划和代码模板

> 这个文档为开发者提供详细的实现指导和代码参考

---

## 第一部分：配置和修复阶段

### 任务1.1：修复 app.py 配置导入

**问题诊断：**
```python
# ❌ 当前错误的导入（config目录中已删除Python文件）
from config.app_config import (
    APP_NAME,
    APP_DESCRIPTION,
    APP_ICON,
    APP_LAYOUT,
    PAGES,
    DATA_DIR,
    LOGS_DIR
)
```

**解决方案：**
修改 `app.py` 的导入部分，改用新的ConfigLoader系统。

**具体步骤：**

1. **替换导入语句（第17-25行）**

旧代码：
```python
from config.app_config import (
    APP_NAME,
    APP_DESCRIPTION,
    APP_ICON,
    APP_LAYOUT,
    PAGES,
    DATA_DIR,
    LOGS_DIR
)
```

新代码：
```python
from src.config import get_config
from pathlib import Path

# 获取配置对象
config = get_config()

# 从config中读取应用配置
APP_NAME = config.app_name
APP_DESCRIPTION = config.app_description
APP_ICON = config.app_icon
APP_LAYOUT = config.app_layout
DATA_DIR = config.data_dir
LOGS_DIR = config.logs_dir

# 定义页面列表（这个之前可能是从config.PAGES读取的，现在改为硬编码）
PAGES = {
    "🏠 欢迎": "home",
    "🔍 搜索": "search",
    "📊 图谱": "graph",
    "🎤 语音": "voice",
    "📄 文档": "documents",
    "📈 分析": "analysis"
}
```

2. **修改日志初始化（第32行）**

旧代码：
```python
logger = setup_logger(log_file=LOGS_DIR / "app.log")
```

新代码：
```python
logger = setup_logger(
    log_file=str(config.logs_dir_path / "app.log"),
    log_level=config.log_level
)
```

3. **修改初始化目录部分（第34-36行）**

旧代码：
```python
# 初始化数据目录
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
```

新代码：
```python
# 初始化数据目录（ConfigLoader已经在__init__中做过了，这里可以保留或删除）
config.data_dir.mkdir(parents=True, exist_ok=True)
config.logs_dir.mkdir(parents=True, exist_ok=True)
```

4. **在 setup_page_config() 中使用新变量**

函数内容保持不变，因为 `APP_NAME`, `APP_ICON`, `APP_LAYOUT` 都已经赋值了。

5. **验证所有使用了 APP_* 的地方都能正常工作**

搜索文件中所有引用这些变量的地方，确保都能正常访问。

**测试方法：**
```bash
cd /Users/laurant/Documents/github/Investopedia
streamlit run app.py
```

如果应用能正常启动并显示标题和图标，说明修复成功。

---

### 任务1.2：验证和修复数据库模块兼容性

**检查清单：**

1. **检查 src/database/db_manager.py**

打开文件，搜索以下内容：
- 是否有 `from config.` 或 `import config` 的导入
- 是否有 `CONFIG.` 或 `app_config.` 的引用

如果有，需要替换为：
```python
from src.config import get_config

# 在需要的地方
config = get_config()
db_path = config.sqlite_path
db_config = config.sqlite_config
```

2. **检查 src/database/policy_dao.py**

同样检查导入和引用。

3. **如果有修改，运行测试**

```python
# 快速测试脚本，可以临时在app.py中或独立运行
from src.config import get_config
from src.database.db_manager import get_db_manager

try:
    config = get_config()
    print(f"✓ 配置加载成功: {config.app_name}")

    db = get_db_manager()
    print(f"✓ 数据库连接成功: {config.sqlite_path}")

except Exception as e:
    print(f"✗ 错误: {e}")
    import traceback
    traceback.print_exc()
```

---

## 第二部分：代码注释完善指南

### 通用注释标准

#### 文件头部注释（必须）

```python
"""
模块名称 - 简短说明
====================
详细说明这个模块的作用，包括：
- 主要功能
- 核心类和函数
- 外部依赖

功能清单：
---------
1. 功能A（FunctionA）：用于...的操作
2. 功能B（ClassB）：用于...的逻辑

使用示例：
--------
```python
from src.xxx import xxx_function
result = xxx_function(param1, param2)
print(result)
```

依赖说明：
--------
- requests：调用HTTP API
- configparser：读取INI配置文件
- sqlalchemy：数据库ORM框架

作者注：
-------
[可选] 一些设计决策或重要注意事项

更新历史：
--------
- 2026-01-24：初版实现
"""
```

#### 函数/方法注释（必须）

```python
def process_data(input_data: dict, timeout: int = 30) -> dict:
    """处理数据的主函数

    这个函数负责：
    1. 验证输入数据的格式
    2. 调用外部API进行处理
    3. 解析返回结果
    4. 返回结果

    Args:
        input_data (dict): 输入数据，必须包含以下字段：
            - "id" (int): 数据ID
            - "content" (str): 内容
            - "type" (str): 类型，可选值为 "A", "B", "C"
        timeout (int, optional): API调用超时时间，单位秒. 默认为 30.

    Returns:
        dict: 处理结果，包含以下字段：
            - "success" (bool): 是否成功
            - "data" (dict): 结果数据
            - "error" (str): 错误信息（如果失败）

    Raises:
        ValueError: 当input_data格式不正确时
        TimeoutError: 当API调用超时时

    Example:
        >>> data = {"id": 1, "content": "测试", "type": "A"}
        >>> result = process_data(data)
        >>> if result["success"]:
        ...     print(result["data"])
    """
    # 函数体
    pass
```

#### 关键逻辑注释（必须）

```python
def extract_policy_info(content: str) -> dict:
    """从政策文本中提取关键信息

    返回值字段说明：
    - "number": 文号
    - "authority": 发文机关
    - "date": 发布日期
    - "type": 政策类型
    - "region": 适用地区
    """
    info = {}

    # 第1步：提取文号
    # 文号通常形式为："财预[年份]号" 或 "财库[年份]号"
    # 使用正则表达式匹配，避免false positive
    import re
    number_match = re.search(r'(财预|财库)〔\d{4}〕\d+号', content)
    info['number'] = number_match.group(0) if number_match else None

    # 第2步：提取发文机关
    # 关键词法：寻找"财政部"、"发改委"等常见机构名称
    # 优先级：精确匹配 > 模糊匹配
    authorities = ['财政部', '国家发改委', '证监会', '银监会']
    info['authority'] = None
    for auth in authorities:
        if auth in content:
            info['authority'] = auth
            break  # 找到第一个就返回

    # 第3步：提取发布日期
    # 日期通常在"发布日期："或"批复"后面
    # 格式可能为：年-月-日 或 年年年年年年年年
    date_pattern = r'(\d{4}年\d{1,2}月\d{1,2}日|\d{8})'
    date_match = re.search(date_pattern, content)
    info['date'] = date_match.group(0) if date_match else None

    # 第4步：确定政策类型
    # 根据关键词在content中的出现来分类
    # 权重：文号 > 标题 > 内容
    if '专项债' in content or '专项' in content:
        info['type'] = '专项债'
    elif '特许经营' in content or 'PPP' in content:
        info['type'] = '特许经营'
    elif '数据资产' in content or '数据' in content:
        info['type'] = '数据资产'
    else:
        info['type'] = '其他'

    # 第5步：提取适用地区
    # 地区通常在"适用范围"或"实施对象"后面
    # 按优先级：明确地名 > 全国 > 特定省市
    regions = ['全国', '北京', '上海', '深圳']  # 示例，实际应更完整
    info['region'] = '全国'  # 默认值
    for region in regions:
        if region in content:
            info['region'] = region
            break

    return info
```

#### 复杂逻辑块的注释

```python
def build_knowledge_graph(policies: list) -> nx.Graph:
    """构建政策知识图谱

    图构建流程：
    1. 创建NetworkX无向图对象
    2. 添加政策节点（node）
    3. 添加政策间的关系边（edge）
    4. 计算节点权重（影响力）
    5. 返回图对象
    """
    G = nx.Graph()

    # ============ 第1步：添加政策节点 ============
    # 每个政策成为一个节点
    # 节点属性包括：标题、类型、发布日期、状态
    # 节点颜色按类型设置，便于可视化
    for policy in policies:
        node_color = {
            '专项债': '#FF6B6B',
            '特许经营': '#4ECDC4',
            '数据资产': '#95E1D3'
        }.get(policy.type, '#95A5A6')  # 默认灰色

        G.add_node(
            policy.id,
            label=policy.title,
            title=policy.title,  # Pyvis hover时显示
            type=policy.type,
            color=node_color,
            date=str(policy.publish_date),
            size=20  # 节点大小
        )

    # ============ 第2步：添加政策关系边 ============
    # 三种关系类型：
    # - 'references': 引用关系（A引用B）
    # - 'replaces': 替代关系（A替代B）
    # - 'amends': 修正关系（A修正B）
    #
    # 这里使用简化逻辑：同类型政策之间有关系
    # 实际应该从数据库的 policy_relations 表查询
    for i, policy_a in enumerate(policies):
        for policy_b in policies[i+1:]:
            # 相同类型的政策建立"同类"关系
            if policy_a.type == policy_b.type:
                G.add_edge(
                    policy_a.id,
                    policy_b.id,
                    relation='related',
                    weight=1
                )

            # 如果发文机关相同，也建立关系
            if policy_a.authority == policy_b.authority:
                G.add_edge(
                    policy_a.id,
                    policy_b.id,
                    relation='same_authority',
                    weight=2  # 权重更高
                )

    # ============ 第3步：计算节点权重 ============
    # 权重代表节点的重要性
    # 计算方式：节点的度数（关联的边数）越多，权重越高
    # 这影响Pyvis中节点的大小显示
    for node in G.nodes():
        degree = G.degree(node)
        # 度数映射到大小：2-30之间
        size = min(30, 10 + degree * 2)
        G.nodes[node]['size'] = size

    return G
```

---

## 第三部分：页面实现参考

### 参考页面框架：搜索页面

```python
"""
政策搜索页面
============
核心功能：
- 快速和高级政策搜索
- 多维度过滤（类型、机构、时间、地区、状态）
- 搜索结果展示和分页
- 政策详情查看

页面流程：
1. 显示搜索面板（快速搜索 + 高级过滤）
2. 处理用户搜索请求
3. 调用RAGFlow进行语义搜索
4. 展示搜索结果（分页）
5. 处理用户点击详情请求

关键组件：
- search_ui.SearchComponent：搜索UI组件
- ragflow_client.RAGFlowClient：RAGFlow服务客户端
- PolicyCard：政策卡片组件

外部服务依赖：
- RAGFlow：提供语义搜索和问答能力
- SQLite数据库：存储政策元数据
"""

import streamlit as st
from datetime import datetime
from typing import List, Dict, Optional
from src.config import get_config
from src.services.ragflow_client import get_ragflow_client
from src.database.policy_dao import get_policy_dao
from src.components.search_ui import SearchComponent
from src.components.policy_card import PolicyCard
from src.utils.logger import get_logger

# 初始化日志
logger = get_logger(__name__)

# 常量定义
POLICY_TYPES = ["专项债", "特许经营", "数据资产"]  # 三大政策类型
POLICY_STATUS = ["有效", "即将过期", "已过期", "已更新"]  # 政策状态
RESULTS_PER_PAGE = 10  # 每页显示结果数
MAX_RESULTS = 100  # 最多返回100条结果


def show():
    """显示搜索页面

    这是搜索页面的主入口函数，由app.py调用。
    页面结构：
    1. 初始化会话状态
    2. 显示搜索面板
    3. 处理用户搜索
    4. 显示搜索结果

    会话状态变量说明：
    - search_results: 搜索结果列表
    - current_page: 当前分页页码
    - selected_policy: 选中的政策详情
    - search_params: 用户输入的搜索参数
    """
    st.title("🔍 政策搜索")
    st.write("快速搜索和检索政策文档，支持多维度筛选")

    # ========== 第1步：初始化会话状态 ==========
    # 说明：会话状态跨越多次用户交互，保持数据不丢失
    _init_session_state()

    # ========== 第2步：构建搜索面板 ==========
    # 说明：用户在这个区域输入搜索条件
    search_params = _build_search_panel()

    # ========== 第3步：处理搜索请求 ==========
    # 说明：当用户点击搜索按钮时，执行搜索逻辑
    if search_params:
        st.session_state.search_params = search_params
        st.session_state.current_page = 0  # 重置分页
        _perform_search(search_params)

    # ========== 第4步：显示搜索结果 ==========
    # 说明：根据搜索结果的多少，采用不同的显示策略
    if st.session_state.search_results:
        _display_results()
    elif st.session_state.search_params:
        # 用户搜索过，但没有结果
        st.info("未找到匹配的政策，请修改搜索条件")


def _init_session_state():
    """初始化页面会话状态

    会话状态在用户整个使用过程中保持，每刷新一次就重新初始化一次。
    这里定义的变量可以在整个页面中使用：st.session_state.variable_name

    初始化的变量说明：
    - search_results：搜索得到的政策列表，初始为空
    - current_page：当前查看第几页，初始为0
    - selected_policy：用户选中查看详情的政策ID，初始为None
    - search_params：最后一次搜索的参数，初始为None
    """
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []

    if 'current_page' not in st.session_state:
        st.session_state.current_page = 0

    if 'selected_policy' not in st.session_state:
        st.session_state.selected_policy = None

    if 'search_params' not in st.session_state:
        st.session_state.search_params = None


def _build_search_panel() -> Optional[Dict]:
    """构建搜索面板

    功能：
    1. 显示快速搜索框（关键词）
    2. 显示可折叠的高级过滤选项
    3. 返回用户输入的搜索参数

    搜索维度：
    - 关键词（政策标题、内容）
    - 政策类型（专项债/特许经营/数据资产）
    - 发文机构
    - 发布日期范围
    - 适用地区
    - 政策状态（有效/过期等）

    返回：
    - None：用户未点击搜索
    - Dict：用户的搜索参数
    """
    # ========== 快速搜索框 ==========
    # 这是页面最醒目的部分，用户一眼就能看到
    search_query = st.text_input(
        "输入关键词搜索",
        placeholder="例如：专项债、风险防范、转贷...",
        key="quick_search"
    )

    # ========== 高级过滤选项（可折叠） ==========
    # 使用expandable section来组织复杂的过滤选项，避免占用过多空间
    with st.expander("🔧 高级过滤选项", expanded=False):
        col1, col2 = st.columns(2)

        # 左列：政策类型 + 发文机关
        with col1:
            policy_type = st.multiselect(
                "政策类型",
                options=POLICY_TYPES,
                default=[],
                key="policy_type_filter",
                help="可多选，为空则表示全部类型"
            )

            authority = st.text_input(
                "发文机关",
                placeholder="例如：财政部、发改委...",
                key="authority_filter",
                help="支持模糊匹配，可为空"
            )

        # 右列：时间范围 + 状态
        with col2:
            date_range = st.date_input(
                "发布日期范围",
                value=(None, None),
                key="date_range_filter"
            )

            status = st.multiselect(
                "政策状态",
                options=POLICY_STATUS,
                default=[],
                key="status_filter",
                help="可多选，为空则表示全部状态"
            )

        # 适用地区（单独一行）
        region = st.text_input(
            "适用地区",
            placeholder="例如：全国、北京、上海...",
            key="region_filter"
        )

    # ========== 搜索按钮和清空按钮 ==========
    # 使用列布局把两个按钮并排放置
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        search_button = st.button(
            "🔍 搜索",
            use_container_width=True,
            type="primary",  # 蓝色高亮按钮
            help="点击执行搜索"
        )

    with col2:
        clear_button = st.button(
            "清空",
            use_container_width=True,
            help="清除搜索条件"
        )

    with col3:
        st.empty()  # 占位符，保持对齐

    # ========== 处理按钮点击事件 ==========
    if clear_button:
        # 清空所有搜索条件
        st.session_state.search_results = []
        st.session_state.search_params = None
        st.rerun()

    if search_button:
        # 用户点击搜索按钮，返回搜索参数
        search_params = {
            'query': search_query,
            'type': policy_type if policy_type else None,
            'authority': authority if authority else None,
            'date_from': date_range[0] if len(date_range) > 0 and date_range[0] else None,
            'date_to': date_range[1] if len(date_range) > 1 and date_range[1] else None,
            'status': status if status else None,
            'region': region if region else None
        }
        return search_params

    return None


def _perform_search(search_params: Dict):
    """执行搜索请求

    流程：
    1. 验证搜索参数（至少有一个非空条件）
    2. 调用RAGFlow进行语义搜索
    3. 从数据库查询元数据和过滤
    4. 合并结果
    5. 保存到session_state

    参数说明：
    - search_params：包含所有搜索条件的字典

    异常处理：
    - RAGFlow服务不可用：捕获异常，显示错误提示
    - 数据库查询失败：捕获异常，记录日志
    """
    # ========== 第1步：验证搜索参数 ==========
    # 确保用户至少输入了一个搜索条件
    if not search_params['query'] and not any([
        search_params['type'],
        search_params['authority'],
        search_params['region']
    ]):
        st.error("请至少输入一个搜索条件")
        return

    with st.spinner("⏳ 正在搜索..."):
        try:
            # ========== 第2步：调用RAGFlow进行语义搜索 ==========
            # 说明：RAGFlow提供语义搜索能力，可以理解用户的查询意图
            ragflow_client = get_ragflow_client()

            # 构建搜索query
            search_query = search_params['query'] if search_params['query'] else "政策"

            # 调用RAGFlow的搜索接口
            # 返回结果包括：文档ID、相关性分数、摘要等
            ragflow_results = ragflow_client.search(
                query=search_query,
                top_k=MAX_RESULTS,
                threshold=0.5  # 相关性阈值
            )

            logger.info(f"RAGFlow搜索返回 {len(ragflow_results)} 条结果")

            # ========== 第3步：从数据库查询完整信息 ==========
            # 说明：RAGFlow返回的是向量相似度匹配，需要从数据库取完整信息
            dao = get_policy_dao()
            results = []

            for ragflow_result in ragflow_results:
                # 从RAGFlow结果中获取document_id
                doc_id = ragflow_result.get('doc_id')

                # 从数据库查询完整的政策信息
                policy = dao.get_policy_by_ragflow_doc_id(doc_id)

                if policy is None:
                    continue  # 如果数据库中找不到，跳过

                # ========== 第4步：应用本地过滤条件 ==========
                # 说明：根据用户选择的过滤条件进行本地过滤
                # （也可以在SQL查询时直接过滤，这里为了简化示例）

                # 过滤政策类型
                if search_params['type'] and policy.policy_type not in search_params['type']:
                    continue

                # 过滤发文机关
                if search_params['authority'] and search_params['authority'] not in policy.issuing_authority:
                    continue

                # 过滤日期
                if search_params['date_from'] and policy.publish_date < search_params['date_from']:
                    continue
                if search_params['date_to'] and policy.publish_date > search_params['date_to']:
                    continue

                # 过滤地区
                if search_params['region'] and search_params['region'] not in policy.region:
                    continue

                # 所有过滤条件都满足，加入结果
                results.append({
                    'policy': policy,
                    'score': ragflow_result.get('score', 0)  # RAGFlow的相似度分数
                })

            # ========== 第5步：保存结果到会话状态 ==========
            # 说明：这样即使用户切换分页，数据也能保持
            st.session_state.search_results = results
            st.session_state.current_page = 0

            # 显示搜索统计信息
            st.success(f"✓ 找到 {len(results)} 条相关政策")
            logger.info(f"搜索完成，返回 {len(results)} 条结果")

        except Exception as e:
            # ========== 异常处理 ==========
            # 说明：捕获可能发生的各种异常，给用户友好的提示
            logger.error(f"搜索失败: {str(e)}", exc_info=True)
            st.error(f"搜索失败：{str(e)}")
            st.info("💡 建议：检查RAGFlow服务是否正常运行")


def _display_results():
    """显示搜索结果

    功能：
    1. 计算分页信息
    2. 显示当前页的搜索结果
    3. 处理政策卡片的交互（查看详情）
    4. 显示分页导航

    分页逻辑：
    - 每页显示RESULTS_PER_PAGE条结果
    - 显示当前分页和总数
    - 支持上一页、下一页、跳转
    """
    results = st.session_state.search_results
    total_results = len(results)
    total_pages = (total_results + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE
    current_page = st.session_state.current_page

    # ========== 显示搜索统计 ==========
    st.subheader(f"搜索结果（共 {total_results} 条）")

    # ========== 计算当前页的结果范围 ==========
    # 说明：分页计算，start_idx是第一条的索引，end_idx是最后一条+1
    start_idx = current_page * RESULTS_PER_PAGE
    end_idx = min(start_idx + RESULTS_PER_PAGE, total_results)
    page_results = results[start_idx:end_idx]

    # ========== 显示当前页的政策卡片 ==========
    # 说明：每个政策用一张卡片展示
    for idx, result in enumerate(page_results):
        policy = result['policy']
        score = result['score']

        # 使用columns和expandable来组织卡片
        col1, col2 = st.columns([0.9, 0.1])

        with col1:
            # 显示政策标题（带链接）
            st.subheader(f"{policy.title} ({policy.policy_type})")

            # 显示关键信息
            col_info1, col_info2, col_info3 = st.columns(3)
            with col_info1:
                st.caption(f"📅 发布: {policy.publish_date}")
            with col_info2:
                st.caption(f"🏛️ {policy.issuing_authority}")
            with col_info3:
                # 显示相关性分数，用进度条可视化
                st.caption(f"🎯 匹配度: {score:.1%}")

            # 显示摘要
            st.write(policy.summary or policy.content[:200] + "...")

            # 显示标签
            if hasattr(policy, 'tags') and policy.tags:
                tags_html = " ".join([f'<span style="background: #E8F5E9; padding: 2px 8px; border-radius: 3px; margin-right: 4px;">{tag}</span>' for tag in policy.tags])
                st.markdown(f"**标签：** {tags_html}", unsafe_allow_html=True)

        with col2:
            # 查看详情按钮
            if st.button("详情", key=f"detail_{idx}_{policy.id}"):
                st.session_state.selected_policy = policy.id

        st.divider()

    # ========== 显示分页导航 ==========
    # 说明：允许用户在不同页之间切换
    st.write("")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        if st.button("⬅️ 上一页", disabled=(current_page == 0)):
            st.session_state.current_page -= 1
            st.rerun()

    with col2:
        st.write("")

    with col3:
        st.write(f"第 {current_page + 1} / {total_pages} 页")

    with col4:
        st.write("")

    with col5:
        if st.button("下一页 ➡️", disabled=(current_page == total_pages - 1)):
            st.session_state.current_page += 1
            st.rerun()


# ===== 辅助函数 =====

def _format_date(date_obj) -> str:
    """格式化日期对象为字符串

    参数：
    - date_obj：datetime或date对象

    返回：
    - str：格式化后的日期字符串，格式为 YYYY-MM-DD
    """
    if date_obj is None:
        return "未知"
    return date_obj.strftime("%Y-%m-%d")
```

---

## 第四部分：重要概念和最佳实践

### ConfigLoader的使用模式

```python
# ✅ 正确的使用方式

# 方式1：在模块顶部导入（推荐）
from src.config import get_config
config = get_config()

# 方式2：在函数内导入（如果需要在多个函数中使用不同的配置）
def some_function():
    from src.config import get_config
    config = get_config()
    value = config.some_property
    return value

# ✅ 环境变量会自动覆盖INI配置
# 如果设置了环境变量：RAGFLOW_HOST=192.168.1.100
# 那么 config.ragflow_host 会返回 192.168.1.100
# 即使 config.ini 中写的是 localhost

# ✅ 访问各种配置
config = get_config()

# 访问APP配置
app_name = config.app_name
app_debug = config.app_debug

# 访问RAGFlow配置
ragflow_host = config.ragflow_host
ragflow_port = config.ragflow_port
ragflow_base_url = config.ragflow_base_url

# 访问数据库配置
db_path = config.sqlite_path
db_config = config.sqlite_config

# 访问路径
data_dir = config.data_dir
logs_dir = config.logs_dir

# ✅ 列表配置（逗号分隔）
supported_langs = config.supported_languages  # 返回 ['zh', 'en']

# ✅ 复杂配置（返回字典）
ragflow_search_config = config.ragflow_search_config
# 返回 {'top_k': 10, 'score_threshold': 0.5, 'search_type': 'hybrid'}
```

### 数据库操作模式

```python
"""
数据库操作的标准模式

所有数据库操作应该通过 DAO (Data Access Object) 进行。
DAO层负责：
1. SQL语句的构建和执行
2. 数据的转换和映射
3. 错误处理和日志
"""

# ✅ 正确的做法：使用DAO
from src.database.policy_dao import get_policy_dao

dao = get_policy_dao()

# 查询单个政策
policy = dao.get_policy_by_id(policy_id=123)

# 查询多个政策
policies = dao.query_policies(
    policy_type='专项债',
    authority='财政部',
    limit=10
)

# 添加政策
dao.add_policy(policy_obj)

# 更新政策
dao.update_policy(policy_obj)

# ❌ 错误的做法：直接执行SQL
# from sqlalchemy import text
# session = get_session()
# session.execute(text("SELECT * FROM policies"))
# （避免这种做法，应该通过DAO封装）
```

### 日志使用模式

```python
"""
日志记录的标准模式

每个模块都应该有一个logger，用于记录该模块的信息。
"""

from src.utils.logger import get_logger

# 在模块顶部创建logger实例
logger = get_logger(__name__)

# 不同级别的日志
logger.debug("调试信息：这个变量的值是 %s", variable_value)
logger.info("信息：处理完成，返回 %d 条结果", result_count)
logger.warning("警告：服务响应缓慢，耗时 %.2f 秒", elapsed_time)
logger.error("错误：无法连接到服务", exc_info=True)

# 在异常处理中记录详细信息
try:
    do_something()
except Exception as e:
    logger.error(f"处理失败：{str(e)}", exc_info=True)
    # exc_info=True 会记录完整的堆栈跟踪，便于debug
```

### Streamlit最佳实践

```python
"""
Streamlit应用的最佳实践
"""

import streamlit as st

# ✅ 使用缓存避免重复计算（如果数据不经常变化）
@st.cache_data
def load_policies():
    """加载所有政策（缓存）

    这个函数的结果会被缓存，除非输入参数改变或代码改变。
    这样可以显著提升性能。
    """
    from src.database.policy_dao import get_policy_dao
    dao = get_policy_dao()
    return dao.get_all_policies()

# ❌ 不要把所有代码都放在一个函数里
# 应该拆分为多个小函数，每个函数做一件事

# ✅ 使用 st.session_state 跨越多次交互保持状态
if 'counter' not in st.session_state:
    st.session_state.counter = 0

if st.button("增加"):
    st.session_state.counter += 1

st.write(f"计数器：{st.session_state.counter}")

# ✅ 使用 st.columns 进行布局
col1, col2, col3 = st.columns(3)

with col1:
    st.write("左边")
with col2:
    st.write("中间")
with col3:
    st.write("右边")

# ✅ 使用 st.expander 折叠不常用的内容
with st.expander("详细选项"):
    # 这个区域默认是折叠的，减少视觉混乱
    st.write("详细内容在这里")

# ✅ 使用 st.spinner 显示进度
with st.spinner("正在处理..."):
    # 这个代码块执行时，会显示一个"正在处理..."的加载动画
    time.sleep(3)

# ✅ 使用 st.tabs 组织内容
tab1, tab2, tab3 = st.tabs(["选项卡1", "选项卡2", "选项卡3"])

with tab1:
    st.write("第一个选项卡的内容")
with tab2:
    st.write("第二个选项卡的内容")
```

---

**这个文档提供了实现过程中的具体指导。在实现每个功能时，参考相应的代码模板和最佳实践。**
