"""
政策搜索页面
==========
提供政策关键词搜索、高级筛选、结果展示等功能。

核心功能：
- 搜索栏：支持关键词输入
- 高级筛选：按政策类型、地区、状态、日期范围筛选
- 结果展示：分页显示搜索结果
- 过滤器：侧边栏快速筛选

使用示例：
    import streamlit as st
    from src.pages import search_page
    search_page.show()
"""
import streamlit as st
from src.components.search_ui import (
    render_search_bar,
    render_advanced_search_panel,
    render_search_results,
    render_search_filters_sidebar,
    render_search_stats
)
from src.database.policy_dao import PolicyDAO


def show():
    st.title("🔍 政策搜索")

    # 初始化session state
    if "search_query" not in st.session_state:
        st.session_state.search_query = ""
    if "search_results" not in st.session_state:
        st.session_state.search_results = []
    if "current_page" not in st.session_state:
        st.session_state.current_page = 0
    if "search_filters" not in st.session_state:
        st.session_state.search_filters = {
            "policy_type": None,
            "region": None,
            "status": None,
            "date_from": None,
            "date_to": None
        }

    # 分栏布局：侧边栏过滤器 + 主要内容
    col_sidebar, col_main = st.columns([1, 4])

    with col_sidebar:
        st.subheader("过滤条件")
        filters = render_search_filters_sidebar()
        st.session_state.search_filters = filters

    with col_main:
        # 搜索栏
        col_search, col_advanced = st.columns([3, 1])
        with col_search:
            st.session_state.search_query = st.text_input(
                "输入关键词搜索政策",
                value=st.session_state.search_query,
                placeholder="例：特别国债、基础设施、数据资产..."
            )

        with col_advanced:
            if st.button("🔧 高级筛选"):
                st.session_state.show_advanced = not st.session_state.get("show_advanced", False)

        # 高级筛选面板
        if st.session_state.get("show_advanced", False):
            render_advanced_search_panel()

        # 执行搜索
        if st.button("🔍 搜索", use_container_width=True):
            if st.session_state.search_query or any(st.session_state.search_filters.values()):
                perform_search()
            else:
                st.warning("请输入搜索关键词或选择筛选条件")

        # 显示统计信息
        if st.session_state.search_results:
            render_search_stats(len(st.session_state.search_results))

        # 显示搜索结果
        if st.session_state.search_results:
            render_search_results(st.session_state.search_results, st.session_state.current_page)


def perform_search():
    """执行搜索并更新结果"""
    try:
        dao = PolicyDAO()
        query = st.session_state.search_query
        filters = st.session_state.search_filters

        # 获取所有政策
        results = dao.get_policies()

        # 应用过滤条件
        if filters.get("policy_type"):
            results = [p for p in results if p.get('policy_type') == filters.get("policy_type")]

        if filters.get("status"):
            results = [p for p in results if p.get('status') == filters.get("status")]

        if filters.get("region"):
            results = [p for p in results if p.get('region') == filters.get("region")]

        # 关键词过滤
        if query:
            results = [
                p for p in results
                if query.lower() in p.get('title', '').lower()
                or query.lower() in p.get('summary', '').lower()
                or query.lower() in p.get('content', '').lower()
            ]

        st.session_state.search_results = results
        st.session_state.current_page = 0
        st.success(f"找到 {len(results)} 条结果")

    except Exception as e:
        st.error(f"搜索失败: {str(e)}")
        st.session_state.search_results = []
