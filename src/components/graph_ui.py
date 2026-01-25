"""
知识图谱UI组件
=============
提供知识图谱页面的各种UI组件，包括图谱渲染、控制面板、统计、搜索、导出等。

核心组件：
- render_graph_controls：图谱控制面板（视图类型、布局算法、节点/边过滤）
- render_network_graph：网络图渲染（Pyvis）
- render_graph_stats：图谱统计（节点数、边数、密度、连通分量、直径）
- render_node_details：节点详情（ID、标签、类型、属性、度数）
- render_edge_details：边详情（源、目标、关系类型、描述）
- render_graph_export：导出选项（HTML、JSON、SVG、PNG）
- render_graph_search：图谱搜索框
- render_graph_filter_by_type：按节点类型过滤
- render_graph_path_finder：最短路径查询

使用示例：
    from src.components.graph_ui import render_network_graph, render_graph_controls

    controls = render_graph_controls()
    render_network_graph(nx_graph)
"""
import streamlit as st
from typing import Optional, Dict, Any
import networkx as nx
from pyvis.network import Network
import tempfile
from pathlib import Path


def render_graph_controls() -> Dict[str, Any]:
    """
    渲染图谱控制面板

    Returns:
        控制选项字典
    """
    with st.expander("🎮 图谱控制", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            view = st.selectbox(
                "视图类型",
                ["全局视图", "子图视图", "时间线视图"],
                index=0
            )

        with col2:
            layout = st.selectbox(
                "布局算法",
                ["力导向", "圆形", "层级"],
                index=0
            )

        with col3:
            physics = st.checkbox("物理引擎", value=True)

        # 节点和边的过滤
        col4, col5 = st.columns(2)

        with col4:
            show_node_types = st.multiselect(
                "节点类型",
                ["政策", "机构", "地区", "概念", "项目"],
                default=["政策", "机构"]
            )

        with col5:
            show_edges = st.multiselect(
                "关系类型",
                ["发布", "适用", "引用", "影响", "替代"],
                default=["发布", "影响"]
            )

        return {
            'view': view,
            'layout': layout,
            'physics': physics,
            'node_types': show_node_types,
            'edge_types': show_edges
        }


def render_network_graph(graph: nx.Graph, title: str = "知识图谱") -> None:
    """
    使用Pyvis渲染网络图

    Args:
        graph: NetworkX图对象
        title: 图谱标题
    """
    try:
        # 检查图是否为空
        if graph.number_of_nodes() == 0:
            st.warning("🔍 图谱为空，请先添加政策数据或调整筛选条件")
            st.info("""
            可能的原因：
            - 数据库中没有政策数据
            - 筛选条件过于严格
            - 数据加载失败
            
            建议：
            1. 检查是否有政策数据
            2. 调整节点类型和关系类型筛选
            3. 查看错误日志
            """)
            return

        # 创建Pyvis网络
        net = Network(
            height="600px",
            width="100%",
            directed=False,
            physics=True
        )

        # 添加节点和边
        net.from_nx(graph)

        # 配置物理引擎
        net.physics = True
        net.show_physics = True

        # 保存为HTML
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            net.show(f.name)
            temp_path = f.name

        # 在Streamlit中显示
        with open(temp_path, 'r', encoding='utf-8') as f:
            html_string = f.read()
        st.components.v1.html(html_string, height=650)

        # 清理临时文件
        Path(temp_path).unlink()

    except Exception as e:
        st.error(f"图谱渲染失败: {str(e)}")


def render_graph_stats(stats: Dict[str, Any]) -> None:
    """
    渲染图谱统计信息

    Args:
        stats: 统计数据
    """
    with st.expander("📊 图谱统计", expanded=False):
        # 检查是否有错误
        if 'error' in stats:
            st.error(f"统计计算错误: {stats['error']}")
        
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("节点数", stats.get('node_count', 0))

        with col2:
            st.metric("边数", stats.get('edge_count', 0))

        with col3:
            density = stats.get('density', 0)
            if isinstance(density, (int, float)):
                st.metric("密度", f"{density:.3f}")
            else:
                st.metric("密度", "N/A")

        with col4:
            components = stats.get('number_of_connected_components', 1)
            st.metric("连通分量", components)

        # 直径
        diameter = stats.get('diameter')
        if diameter is not None:
            st.write(f"**直径**: {diameter}")
        elif stats.get('node_count', 0) > 1:
            st.write("**直径**: 图不连通或计算失败")
        else:
            st.write("**直径**: N/A (节点数不足)")
            
        # 显示图谱健康状况
        node_count = stats.get('node_count', 0)
        edge_count = stats.get('edge_count', 0)
        
        if node_count == 0:
            st.warning("⚠️ 图谱为空")
        elif edge_count == 0:
            st.warning("⚠️ 没有关系连接")
        else:
            st.success("✅ 图谱正常")


def render_node_details(node: Dict[str, Any]) -> None:
    """
    渲染节点详情

    Args:
        node: 节点数据
    """
    with st.expander(f"📍 节点详情: {node.get('label', 'N/A')}", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**ID**: {node.get('id')}")
            st.write(f"**标签**: {node.get('label')}")
            st.write(f"**类型**: {node.get('type', '未知')}")

        with col2:
            st.write(f"**度数**: {node.get('degree', 'N/A')}")

            # 显示其他属性
            attributes = node.get('attributes', {})
            if attributes:
                st.write("**属性**:")
                for key, value in attributes.items():
                    st.caption(f"  {key}: {value}")


def render_edge_details(edge: Dict[str, Any]) -> None:
    """
    渲染边详情

    Args:
        edge: 边数据
    """
    with st.expander(f"🔗 关系详情: {edge.get('label', 'N/A')}", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**源**: {edge.get('source')}")
            st.write(f"**目标**: {edge.get('target')}")

        with col2:
            st.write(f"**关系**: {edge.get('relation_type', '未知')}")
            st.write(f"**标签**: {edge.get('label', '')}")

        # 关系描述
        if edge.get('description'):
            st.write(f"**描述**: {edge['description']}")


def render_graph_export() -> None:
    """渲染图谱导出选项"""
    with st.expander("💾 导出选项", expanded=False):
        export_format = st.selectbox(
            "导出格式",
            ["HTML", "JSON", "SVG", "PNG"]
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("导出为 " + export_format, use_container_width=True):
                st.info(f"导出为 {export_format} 的功能正在开发中...")

        with col2:
            if st.button("下载图谱数据", use_container_width=True):
                st.info("下载功能正在开发中...")


def render_graph_search() -> str:
    """
    渲染图谱搜索框

    Returns:
        搜索查询
    """
    search_query = st.text_input(
        "🔍 在图谱中搜索",
        placeholder="输入节点名称或ID..."
    )
    return search_query


def render_graph_filter_by_type() -> Dict[str, bool]:
    """
    按类型过滤图谱节点

    Returns:
        节点类型的可见性字典
    """
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        show_policy = st.checkbox("政策", value=True, key="show_policy")

    with col2:
        show_authority = st.checkbox("机构", value=True, key="show_authority")

    with col3:
        show_region = st.checkbox("地区", value=True, key="show_region")

    with col4:
        show_concept = st.checkbox("概念", value=True, key="show_concept")

    with col5:
        show_project = st.checkbox("项目", value=True, key="show_project")

    return {
        'policy': show_policy,
        'authority': show_authority,
        'region': show_region,
        'concept': show_concept,
        'project': show_project
    }


def render_graph_path_finder() -> Dict[str, Any]:
    """
    渲染最短路径查询工具

    Returns:
        查询参数
    """
    with st.expander("🛣️ 路径查询", expanded=False):
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            source = st.text_input("源节点", placeholder="输入源节点ID...")

        with col2:
            target = st.text_input("目标节点", placeholder="输入目标节点ID...")

        with col3:
            find_path = st.button("查询路径", use_container_width=True)

        return {
            'source': source,
            'target': target,
            'find_path': find_path
        }
