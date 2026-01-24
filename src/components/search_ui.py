"""
搜索UI组件
==========
提供搜索页面的各种UI组件，包括搜索栏、高级搜索面板、结果展示、过滤器、统计等。

核心组件：
- render_search_bar：搜索栏（输入框 + 搜索按钮）
- render_advanced_search_panel：高级搜索面板（政策类型、地区、状态、日期、排序）
- render_search_results：搜索结果展示（分页、卡片列表）
- render_search_filters_sidebar：侧边栏过滤器（政策类型、地区、状态、日期）
- render_search_stats：搜索统计（总数、各类型政策数等）

使用示例：
    from src.components.search_ui import render_search_bar, render_search_results

    query = render_search_bar()
    if query:
        results = search_policies(query)
        total_pages, current_page = render_search_results(results, total=100)
"""
import streamlit as st
from typing import Optional, Dict, Any, List, Tuple


def render_search_bar(placeholder: str = "搜索政策关键词...") -> str:
    """
    渲染搜索栏

    Args:
        placeholder: 占位符文本

    Returns:
        搜索查询字符串
    """
    cols = st.columns([4, 1])

    with cols[0]:
        query = st.text_input("🔍", placeholder=placeholder, label_visibility="collapsed")

    with cols[1]:
        search_button = st.button("搜索", use_container_width=True)

    return query if search_button else ""


def render_advanced_search_panel() -> Dict[str, Any]:
    """
    渲染高级搜索面板

    Returns:
        搜索过滤条件字典
    """
    with st.expander("🔧 高级搜索", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            policy_type = st.multiselect(
                "政策类型",
                ["special_bonds", "franchise", "data_assets"],
                default=[]
            )

            region = st.multiselect(
                "适用地区",
                ["全国", "北京", "上海", "广东", "浙江", "江苏", "四川", "湖北"],
                default=[]
            )

        with col2:
            status = st.multiselect(
                "政策状态",
                ["active", "expired", "expiring_soon", "updated"],
                default=["active"]
            )

            use_date_range = st.checkbox("使用日期范围筛选", value=False)
            date_from = None
            date_to = None

            if use_date_range:
                try:
                    date_range = st.date_input(
                        "发布日期范围",
                        value=[],
                        label_visibility="visible"
                    )
                    if isinstance(date_range, (list, tuple)) and len(date_range) >= 2:
                        date_from = date_range[0]
                        date_to = date_range[1]
                except Exception:
                    pass

        # 排序选项
        sort_by = st.selectbox(
            "排序方式",
            ["最新发布", "标题（A-Z）", "相关度最高"],
            index=0
        )

        return {
            'policy_type': policy_type[0] if policy_type else None,
            'region': region[0] if region else None,
            'status': status[0] if status else None,
            'date_from': date_from,
            'date_to': date_to,
            'sort_by': sort_by
        }


def render_search_results(results: List[Dict[str, Any]], total: int,
                         page: int = 1, page_size: int = 10) -> Tuple[int, int]:
    """
    渲染搜索结果

    Args:
        results: 搜索结果列表
        total: 总数
        page: 当前页码
        page_size: 每页数量

    Returns:
        (总页数, 当前页码)
    """
    if not results:
        st.info("未找到匹配的政策")
        return 1, 1

    # 显示结果统计
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.write(f"找到 **{total}** 个结果")
    with col2:
        st.write(f"第 **{page}** 页")
    with col3:
        total_pages = (total + page_size - 1) // page_size
        st.write(f"共 **{total_pages}** 页")

    st.divider()

    # 显示结果
    for idx, result in enumerate(results, start=1):
        with st.container():
            col1, col2 = st.columns([5, 1])

            with col1:
                st.subheader(f"{idx}. {result.get('title', '未知标题')}")

                # 摘要和元数据
                meta_info = []
                if result.get('document_number'):
                    meta_info.append(f"📄 {result['document_number']}")
                if result.get('issuing_authority'):
                    meta_info.append(f"🏛️ {result['issuing_authority']}")
                if result.get('publish_date'):
                    meta_info.append(f"📅 {result['publish_date']}")

                st.caption(" | ".join(meta_info))

                # 摘要
                summary = result.get('summary', result.get('content', ''))
                if isinstance(summary, str):
                    summary = summary[:200] + '...' if len(summary) > 200 else summary
                st.write(summary)

                # 标签
                if result.get('tags'):
                    tag_str = " ".join([f"🔹 {tag.get('name', 'Tag')}" for tag in result['tags'][:3]])
                    st.caption(tag_str)

            with col2:
                # 相关度分数（如果有）
                if result.get('score'):
                    st.metric("相关度", f"{result['score']:.1%}")

                # 查看按钮
                if st.button("查看", key=f"view_{result['id']}", use_container_width=True):
                    st.session_state.selected_policy = result['id']

        st.divider()

    # 分页控制
    col1, col2, col3, col4, col5 = st.columns(5)
    total_pages = (total + page_size - 1) // page_size

    with col1:
        if st.button("⬅️ 首页"):
            return total_pages, 1

    with col2:
        if st.button("⬅️ 上一页"):
            return total_pages, max(1, page - 1)

    with col3:
        current_page = st.number_input("页码", min_value=1, max_value=total_pages, value=page)

    with col4:
        if st.button("下一页 ➡️"):
            return total_pages, min(total_pages, page + 1)

    with col5:
        if st.button("末页 ➡️"):
            return total_pages, total_pages

    return total_pages, current_page


def render_search_filters_sidebar() -> Dict[str, Any]:
    """
    在侧边栏渲染搜索过滤器

    Returns:
        过滤条件字典
    """
    with st.sidebar:
        st.subheader("📊 搜索过滤")

        filters = {}

        # 政策类型
        st.write("**政策类型**")
        type_filter = st.checkbox("专项债", key="type_special_bonds")
        if type_filter:
            filters['special_bonds'] = True

        type_filter = st.checkbox("特许经营", key="type_franchise")
        if type_filter:
            filters['franchise'] = True

        type_filter = st.checkbox("数据资产", key="type_data_assets")
        if type_filter:
            filters['data_assets'] = True

        st.divider()

        # 地区过滤
        st.write("**地区**")
        regions = st.multiselect(
            "选择地区",
            ["全国", "北京", "上海", "广东", "浙江"],
            key="region_filter"
        )
        if regions:
            filters['regions'] = regions

        st.divider()

        # 状态过滤
        st.write("**状态**")
        status_active = st.checkbox("有效", value=True, key="status_active")
        status_expired = st.checkbox("失效", key="status_expired")
        status_expiring = st.checkbox("即将失效", key="status_expiring")

        statuses = []
        if status_active:
            statuses.append('active')
        if status_expired:
            statuses.append('expired')
        if status_expiring:
            statuses.append('expiring_soon')

        if statuses:
            filters['statuses'] = statuses

        st.divider()

        # 日期范围
        st.write("**发布日期**")
        date_from = st.date_input("从", key="date_from")
        date_to = st.date_input("到", key="date_to")

        if date_from or date_to:
            filters['date_from'] = date_from
            filters['date_to'] = date_to

        return filters


def render_search_stats(stats: Dict[str, Any]) -> None:
    """
    渲染搜索统计

    Args:
        stats: 统计数据
    """
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("总政策数", stats.get('total', 0))

    with col2:
        by_type = stats.get('by_type', {})
        special_bonds = by_type.get('special_bonds', 0)
        st.metric("专项债", special_bonds)

    with col3:
        franchise = by_type.get('franchise', 0)
        st.metric("特许经营", franchise)

    with col4:
        data_assets = by_type.get('data_assets', 0)
        st.metric("数据资产", data_assets)
