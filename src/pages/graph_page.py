"""
知识图谱页面
==========
提供政策关系的可视化展示、查询、分析等功能。

核心功能：
- 图谱可视化：全局图谱、子图、时间线三种视图
- 布局切换：力导向、圆形、层次三种布局
- 节点/边查询：点击查看详情
- 路径查询：查找两个节点之间的路径
- 图表统计：显示节点数、边数、密度等
- 导出功能：支持HTML、JSON、SVG、PNG格式

使用示例：
    import streamlit as st
    from src.pages import graph_page
    graph_page.show()
"""
import streamlit as st
from src.components.graph_ui import (
    render_graph_controls,
    render_network_graph,
    render_graph_stats,
    render_node_details,
    render_edge_details,
    render_graph_export,
    render_graph_search,
    render_graph_filter_by_type,
    render_graph_path_finder
)
from src.database.policy_dao import PolicyDAO
from src.models.graph import PolicyGraph, NodeType, RelationType


def show():
    st.title("📊 知识图谱")

    # 初始化session state
    if "graph" not in st.session_state:
        st.session_state.graph = None
    if "selected_node" not in st.session_state:
        st.session_state.selected_node = None
    if "graph_layout" not in st.session_state:
        st.session_state.graph_layout = "force"

    # 构建图谱
    if st.session_state.graph is None:
        with st.spinner("正在加载知识图谱..."):
            st.session_state.graph = build_policy_graph()

    # 分栏：控制面板 + 主视图
    col_control, col_main = st.columns([1, 4])

    with col_control:
        st.subheader("图谱控制")

        # 图谱控制
        render_graph_controls()

        st.divider()

        # 节点类型筛选
        st.subheader("节点筛选")
        render_graph_filter_by_type()

        st.divider()

        # 搜索
        st.subheader("搜索")
        render_graph_search()

        st.divider()

        # 路径查询
        st.subheader("路径查询")
        render_graph_path_finder()

        st.divider()

        # 导出
        st.subheader("导出")
        render_graph_export()

    with col_main:
        # 图谱统计
        if st.session_state.graph:
            render_graph_stats(st.session_state.graph)

        st.divider()

        # 主图谱显示
        if st.session_state.graph:
            render_network_graph(st.session_state.graph)

        st.divider()

        # 节点详情
        if st.session_state.selected_node:
            st.subheader("节点详情")
            node = st.session_state.graph.get_node(st.session_state.selected_node)
            if node:
                render_node_details(node)

        # 边详情
        st.subheader("关系详情")
        render_edge_details_section()


def build_policy_graph():
    """构建政策知识图谱"""
    try:
        dao = PolicyDAO()
        policies = dao.get_policies()

        # 创建图谱
        graph = PolicyGraph()

        # 添加政策节点
        for policy in policies:
            graph.add_node(
                node_id=f"policy_{policy.id}",
                label=policy.metadata.title,
                node_type=NodeType.POLICY,
                attributes={
                    "policy_type": policy.policy_type,
                    "region": policy.metadata.region,
                    "status": policy.status
                }
            )

        # 添加发行机关节点
        authorities = set()
        for policy in policies:
            if policy.metadata.issuing_authority:
                authorities.add(policy.metadata.issuing_authority)

        for authority in authorities:
            graph.add_node(
                node_id=f"authority_{authority}",
                label=authority,
                node_type=NodeType.AUTHORITY
            )

            # 连接政策到发行机关
            for policy in policies:
                if policy.metadata.issuing_authority == authority:
                    graph.add_edge(
                        source_id=f"policy_{policy.id}",
                        target_id=f"authority_{authority}",
                        relation_type=RelationType.ISSUED_BY,
                        label="由...发布"
                    )

        # 添加地区节点
        regions = set()
        for policy in policies:
            if policy.metadata.region:
                regions.add(policy.metadata.region)

        for region in regions:
            graph.add_node(
                node_id=f"region_{region}",
                label=region,
                node_type=NodeType.REGION
            )

            # 连接政策到地区
            for policy in policies:
                if policy.metadata.region == region:
                    graph.add_edge(
                        source_id=f"policy_{policy.id}",
                        target_id=f"region_{region}",
                        relation_type=RelationType.APPLIES_TO,
                        label="适用于"
                    )

        # 添加政策关系
        for policy in policies:
            for relation in policy.relations:
                graph.add_edge(
                    source_id=f"policy_{policy.id}",
                    target_id=f"policy_{relation.target_policy_id}",
                    relation_type=relation.relation_type,
                    label=relation.relation_type,
                    attributes={"confidence": relation.confidence}
                )

        return graph

    except Exception as e:
        st.error(f"构建图谱失败：{str(e)}")
        return PolicyGraph()


def render_edge_details_section():
    """显示边（关系）详情"""
    try:
        dao = PolicyDAO()

        col1, col2 = st.columns(2)

        with col1:
            source_policy = st.selectbox(
                "源政策",
                options=dao.get_policies(),
                format_func=lambda p: p.metadata.title,
                key="source_policy"
            )

        with col2:
            if source_policy:
                relations = dao.get_policy_relations(source_policy.id, as_source=True)
                if relations:
                    target_policy = st.selectbox(
                        "目标政策",
                        options=relations,
                        format_func=lambda r: f"关系: {r.relation_type}",
                        key="target_relation"
                    )

                    with st.expander(f"📍 关系详情：{source_policy.metadata.title}", expanded=True):
                        render_edge_details(target_policy)
                else:
                    st.info("此政策没有关系链接")

    except Exception as e:
        st.error(f"加载关系详情失败：{str(e)}")
