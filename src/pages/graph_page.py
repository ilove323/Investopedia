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
import networkx as nx
from src.components.graph_ui import (
    render_graph_controls,
    render_network_graph_from_data,
    render_graph_stats,
    render_graph_export
)
from src.database.graph_dao import GraphDAO
from src.config import get_config
import logging

logger = logging.getLogger(__name__)


def show():
    st.title("📊 知识图谱")

    # 数据同步侧边栏
    with st.sidebar:
        st.subheader("📊 数据管理")
        
        # 图谱统计
        try:
            config = get_config()
            db_path = config.data_dir / "database" / "policies.db"
            graph_dao = GraphDAO(str(db_path))
            graph_stats = graph_dao.get_stats()
            if graph_stats and graph_stats.get('node_count', 0) > 0:
                st.success(f"""
🕸️ **图谱信息**
- 节点数: {graph_stats.get('node_count', 0)}
- 边数: {graph_stats.get('edge_count', 0)}
- 最后更新: {graph_stats.get('last_updated', 'N/A')}
                """)
            else:
                st.warning("⚠️ 尚未构建图谱")
        except Exception as e:
            st.error(f"获取图谱统计失败: {e}")
        
        st.divider()
        
        st.info("""
💡 **如何构建图谱**

点击侧边栏切换到 **📚 文档管理** 页面，在文档列表下方有构建按钮：
- 🔄 **全量重建图谱** - 重新分析所有文档构建图谱
- ➕ **增量更新图谱** - 仅分析新增文档更新图谱

图谱由本项目自动从RAGFlow文档中提取实体和关系构建。
        """)

    # 初始化session state
    if "graph" not in st.session_state:
        st.session_state.graph = None
    if "selected_node" not in st.session_state:
        st.session_state.selected_node = None
    if "graph_layout" not in st.session_state:
        st.session_state.graph_layout = "force"

    # 从数据库加载图谱
    if st.session_state.graph is None:
        with st.spinner("正在从数据库加载知识图谱..."):
            st.session_state.graph = load_graph_from_database()

    # 分栏：控制面板 + 主视图
    col_control, col_main = st.columns([1, 4])

    with col_control:
        st.subheader("图谱控制")

        # 图谱控制 - 获取用户选择
        controls = render_graph_controls()
        st.session_state.graph_layout = controls.get('layout', '力导向')

        st.divider()

        # 导出
        st.subheader("导出")
        render_graph_export()
        
        st.divider()
        
        # 添加刷新按钮
        if st.button("🔄 重新加载图谱", use_container_width=True):
            st.session_state.graph = None
            st.rerun()

    with col_main:
        # 图谱统计
        if st.session_state.graph:
            node_count = len(st.session_state.graph.get('nodes', []))
            edge_count = len(st.session_state.graph.get('edges', []))
            
            if node_count > 0:
                # 显示基本统计
                stats = {
                    'node_count': node_count,
                    'edge_count': edge_count,
                    'density': 0,
                    'number_of_connected_components': 0,
                    'diameter': None
                }
                render_graph_stats(stats)
        else:
            st.info("📊 图谱统计信息将在添加数据后显示")

        st.divider()

        # 主图谱显示
        if st.session_state.graph and len(st.session_state.graph.get('nodes', [])) > 0:
            # 直接使用Pyvis渲染原始图谱数据，并传递控制参数
            render_network_graph_from_data(
                st.session_state.graph,
                layout=controls.get('layout', '力导向'),
                physics_enabled=controls.get('physics', True)
            )
        else:
            st.warning("🔍 图谱为空或尚未构建")
            st.info("""
            💡 **如何构建知识图谱**：
            
            1. 点击左侧边栏切换到 **📚 文档管理** 页面
            2. 确保已上传政策文档到RAGFlow（文档列表会显示）
            3. 在文档统计下方找到 **🕸️ 知识图谱构建** 区域
            4. 点击按钮：
               - 🔄 **全量重建图谱** - 重新分析所有文档
               - ➕ **增量更新图谱** - 仅分析新增文档
            5. 等待进度条完成后返回本页面查看
            
            ⚠️ **说明**：图谱由本项目自动构建，无需去RAGFlow操作
            """)

        st.divider()

        # 关系浏览（基于图谱数据）
        if st.session_state.graph and len(st.session_state.graph.get('nodes', [])) > 0:
            st.divider()
            st.subheader("🔗 关系浏览")
            render_edge_browser_from_graph(st.session_state.graph)


def load_graph_from_database():
    """从数据库加载知识图谱（直接使用Pyvis格式）"""
    try:
        config = get_config()
        db_path = config.data_dir / "database" / "policies.db"
        graph_dao = GraphDAO(str(db_path))
        graph_data = graph_dao.load_graph()
        
        if not graph_data:
            logger.info("数据库中没有图谱数据")
            return None
        
        logger.info(f"从数据库加载Pyvis格式图谱: {len(graph_data.get('nodes', []))}个节点, {len(graph_data.get('edges', []))}条边")
        
        # 直接返回原始的Pyvis格式数据，不转换为PolicyGraph
        # 因为数据已经是可视化格式（包含title, size, color等属性）
        return graph_data
        
    except Exception as e:
        logger.error(f"从数据库加载图谱失败: {e}")
        return None


def render_edge_browser_from_graph(graph_data: dict):
    """
    基于图谱数据显示关系浏览器
    
    Args:
        graph_data: 图谱数据字典 {'nodes': [...], 'edges': [...]}
    """
    try:
        nodes = graph_data.get('nodes', [])
        edges = graph_data.get('edges', [])
        
        if not nodes:
            st.info("图谱中没有节点数据")
            return
        
        # 创建节点ID到节点的映射，并去重
        node_map = {}
        unique_nodes = []
        seen_labels = set()
        
        for node in nodes:
            node_id = node.get('id')
            label = node.get('label', node_id)
            
            # 去重：如果label已经见过，跳过
            if label in seen_labels:
                continue
            
            seen_labels.add(label)
            node_map[node_id] = node
            unique_nodes.append(node)
        
        if not unique_nodes:
            st.info("图谱中没有有效节点")
            return
        
        # 选择源节点
        col1, col2 = st.columns([1, 1])
        
        with col1:
            selected_node = st.selectbox(
                "选择节点查看关系",
                options=unique_nodes,
                format_func=lambda n: f"{n.get('label', 'Unknown')} ({n.get('type', 'Unknown')})",
                key="selected_source_node"
            )
        
        if not selected_node:
            return
        
        selected_id = selected_node.get('id')
        
        # 查找与该节点相关的所有边
        related_edges = []
        for edge in edges:
            if edge.get('from') == selected_id or edge.get('to') == selected_id:
                related_edges.append(edge)
        
        with col2:
            st.metric("关系数量", len(related_edges))
        
        # 显示关系列表
        if related_edges:
            st.markdown("**关系列表：**")
            for idx, edge in enumerate(related_edges, 1):
                from_id = edge.get('from')
                to_id = edge.get('to')
                edge_type = edge.get('type', edge.get('label', '未知关系'))
                
                # 获取源节点和目标节点
                from_node = node_map.get(from_id, {})
                to_node = node_map.get(to_id, {})
                
                from_label = from_node.get('label', from_id)
                to_label = to_node.get('label', to_id)
                
                # 显示关系
                with st.expander(f"#{idx} {from_label} → {to_label}", expanded=False):
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        st.write("**源节点:**")
                        st.caption(f"标签: {from_label}")
                        st.caption(f"类型: {from_node.get('type', 'Unknown')}")
                        st.caption(f"ID: `{from_id}`")
                    
                    with col_b:
                        st.write("**目标节点:**")
                        st.caption(f"标签: {to_label}")
                        st.caption(f"类型: {to_node.get('type', 'Unknown')}")
                        st.caption(f"ID: `{to_id}`")
                    
                    st.divider()
                    st.write(f"**关系类型:** {edge_type}")
                    
                    if edge.get('label'):
                        st.write(f"**标签:** {edge.get('label')}")
        else:
            st.info(f"节点 **{selected_node.get('label')}** 没有关联的关系")
    
    except Exception as e:
        st.error(f"加载关系浏览器失败: {str(e)}")
        import traceback
        st.error(traceback.format_exc())