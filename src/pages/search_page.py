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
    
    # 初始化完整图谱缓存
    if "full_graph" not in st.session_state:
        st.session_state.full_graph = None

    # 分栏布局：侧边栏过滤器 + 主要内容
    col_sidebar, col_main = st.columns([1, 4])

    with col_sidebar:
        st.subheader("过滤条件")
        filters = render_search_filters_sidebar()
        st.session_state.search_filters = filters
        
        st.divider()
        
        # 图谱缓存管理
        st.subheader("图谱缓存")
        if st.button("🔄 刷新图谱缓存", use_container_width=True):
            st.session_state.full_graph = None
            with st.spinner("正在构建图谱..."):
                from src.pages.graph_page import build_policy_graph
                st.session_state.full_graph = build_policy_graph()
            st.success("图谱缓存已刷新")
        
        if st.session_state.full_graph:
            st.caption(f"✅ 图谱已加载: {st.session_state.full_graph.get_node_count()} 个节点")
        else:
            st.caption("⚠️ 图谱未加载")

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
                # 自动加载图谱（如果还未加载）
                if st.session_state.full_graph is None:
                    with st.spinner("正在加载图谱..."):
                        from src.pages.graph_page import build_policy_graph
                        st.session_state.full_graph = build_policy_graph()
            else:
                st.warning("请输入搜索关键词或选择筛选条件")

        # 显示统计信息
        if st.session_state.search_results:
            render_search_stats(st.session_state.search_results)

        # 显示搜索结果（传递完整图谱）
        if st.session_state.search_results:
            total_results = len(st.session_state.search_results)
            current_page = st.session_state.get("current_page", 0) + 1
            render_search_results(
                st.session_state.search_results, 
                total_results, 
                current_page,
                full_graph=st.session_state.full_graph  # 传递完整图谱
            )


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
