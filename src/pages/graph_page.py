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
    render_network_graph,
    render_network_graph_from_data,
    render_graph_stats,
    render_node_details,
    render_edge_details,
    render_graph_export,
    render_graph_search,
    render_graph_filter_by_type,
    render_graph_path_finder
)
from src.database.policy_dao import PolicyDAO
from src.database.graph_dao import GraphDAO
from src.models.graph import PolicyGraph, NodeType, RelationType, GraphNode, GraphEdge
from src.services.data_sync import DataSyncService
from src.config import get_config
import logging

logger = logging.getLogger(__name__)


def show():
    st.title("📊 知识图谱")

    # 数据同步侧边栏
    with st.sidebar:
        st.subheader("📊 数据管理")
        
        # 显示数据状态
        dao = PolicyDAO()
        policies_count = len(dao.get_policies())
        st.info(f"📋 本地数据库: {policies_count} 个政策")
        
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
        
        # 同步按钮（只同步文档到数据库，不构建图谱）
        if st.button("🔄 同步RAGFlow数据", help="将RAGFlow中的文档同步到本地数据库（不构建图谱）"):
            with st.spinner("正在同步数据..."):
                try:
                    sync_service = DataSyncService()
                    
                    sync_results = sync_service.sync_documents_to_database()
                    
                    st.success(f"""
                    📊 同步完成！
                    - 新增政策: {sync_results['new_policies']}个
                    - 更新政策: {sync_results['updated_policies']}个
                    - 总文档数: {sync_results['total_documents']}个
                    
                    ⚠️ 注意：需要在文档页面手动构建图谱
                    """)
                    
                    if sync_results['errors']:
                        with st.expander("⚠️ 同步错误", expanded=False):
                            for error in sync_results['errors']:
                                st.error(error)
                    
                except Exception as e:
                    st.error(f"同步失败: {str(e)}")
        
        # 同步状态检查
        if st.button("🔍 检查同步状态", help="检查数据库和RAGFlow的同步状态"):
            try:
                sync_service = DataSyncService()
                status = sync_service.get_sync_status()
                
                if 'error' in status:
                    st.error(f"状态检查失败: {status['error']}")
                else:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("本地政策", status['database_policies'])
                    with col2:
                        st.metric("RAGFlow文档", status['ragflow_documents'])
                    
                    # 连接状态
                    if status['ragflow_status'] == 'connected':
                        st.success("✅ RAGFlow连接正常")
                    else:
                        st.error("❌ RAGFlow连接失败")
            except Exception as e:
                st.error(f"状态检查失败: {str(e)}")

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

        # 节点类型筛选 - 获取筛选配置
        st.subheader("节点筛选")
        node_filter = render_graph_filter_by_type()

        st.divider()

        # 搜索 - 获取搜索关键词
        st.subheader("搜索")
        search_query = render_graph_search()

        st.divider()

        # 路径查询 - 获取路径查询参数
        st.subheader("路径查询")
        path_params = render_graph_path_finder()

        st.divider()

        # 导出
        st.subheader("导出")
        render_graph_export()

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
            # 直接使用Pyvis渲染原始图谱数据
            render_network_graph_from_data(st.session_state.graph)
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

        # 节点详情 - 暂时禁用，因为需要重构
        # if st.session_state.selected_node:
        #     st.subheader("节点详情")
        #     node = st.session_state.graph.get_node(st.session_state.selected_node)
        #     if node:
        #         render_node_details(node)

        # 边详情
        st.subheader("关系详情")
        render_edge_details_section()


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


def render_edge_details_section():
    """显示边（关系）详情"""
    try:
        dao = PolicyDAO()

        col1, col2 = st.columns(2)

        with col1:
            policies = dao.get_policies()
            source_policy = st.selectbox(
                "源政策",
                options=policies,
                format_func=lambda p: p.get('title', '无标题'),
                key="source_policy"
            )

        with col2:
            if source_policy:
                relations = dao.get_policy_relations(source_policy['id'], as_source=True)
                if relations:
                    target_policy = st.selectbox(
                        "目标政策",
                        options=relations,
                        format_func=lambda r: f"关系: {r.get('relation_type', '未知')}",
                        key="target_relation"
                    )

                    with st.expander(f"📍 关系详情：{source_policy.get('title', '无标题')}", expanded=True):
                        render_edge_details(target_policy)
                else:
                    st.info("此政策没有关系链接")

    except Exception as e:
        st.error(f"加载关系详情失败：{str(e)}")

def apply_filters_and_search(graph, node_filter, search_query, node_types, edge_types):
    """
    应用节点过滤和搜索
    
    Args:
        graph: PolicyGraph对象
        node_filter: 节点类型过滤字典
        search_query: 搜索关键词
        node_types: 控制面板选中的节点类型列表
        edge_types: 控制面板选中的边类型列表
    
    Returns:
        过滤后的PolicyGraph对象
    """
    if not graph or graph.get_node_count() == 0:
        return graph
    
    # 创建新图谱用于过滤结果
    filtered_graph = PolicyGraph()
    
    # 节点类型映射
    type_mapping = {
        '政策': NodeType.POLICY,
        '机构': NodeType.AUTHORITY,
        '地区': NodeType.REGION,
        '概念': NodeType.CONCEPT,
        '项目': NodeType.PROJECT
    }
    
    # 获取允许的节点类型
    allowed_types = set()
    for type_name in node_types:
        if type_name in type_mapping:
            allowed_types.add(type_mapping[type_name])
    
    # 如果没有选择任何类型，显示所有类型
    if not allowed_types:
        allowed_types = set(type_mapping.values())
    
    # 过滤节点
    for node in graph.nodes.values():
        # 类型过滤
        if node.node_type not in allowed_types:
            continue
        
        # 搜索过滤
        if search_query:
            query_lower = search_query.lower()
            if (query_lower not in node.label.lower() and 
                query_lower not in node.node_id.lower()):
                continue
        
        # 添加符合条件的节点
        filtered_graph.add_node(node)
    
    # 添加边（只添加两端节点都存在的边）
    for edge in graph.edges:
        if (edge.source_id in filtered_graph.nodes and 
            edge.target_id in filtered_graph.nodes):
            filtered_graph.add_edge(edge)
    
    return filtered_graph


def display_shortest_path(graph, source_id, target_id):
    """
    显示两个节点之间的最短路径
    
    Args:
        graph: PolicyGraph对象
        source_id: 源节点ID
        target_id: 目标节点ID
    """
    if not graph or graph.get_node_count() == 0:
        st.warning("图谱为空，无法查询路径")
        return
    
    try:
        nx_graph = graph.get_nx_graph()
        
        # 查找路径
        if nx.has_path(nx_graph, source_id, target_id):
            path = nx.shortest_path(nx_graph, source_id, target_id)
            
            st.success(f"✅ 找到路径！长度: {len(path) - 1}")
            
            # 显示路径
            st.write("**路径:**")
            for i, node_id in enumerate(path):
                node = graph.get_node(node_id)
                if node:
                    st.write(f"{i + 1}. {node.label} ({node.node_type.value})")
                else:
                    st.write(f"{i + 1}. {node_id}")
            
            # 高亮显示路径图
            path_graph = PolicyGraph()
            for node_id in path:
                node = graph.get_node(node_id)
                if node:
                    path_graph.add_node(node)
            
            for i in range(len(path) - 1):
                for edge in graph.edges:
                    if ((edge.source_id == path[i] and edge.target_id == path[i + 1]) or
                        (edge.source_id == path[i + 1] and edge.target_id == path[i])):
                        path_graph.add_edge(edge)
                        break
            
            st.subheader("路径图谱")
            render_network_graph(path_graph.get_nx_graph(), title="最短路径")
            
        else:
            st.warning(f"❌ 未找到从 {source_id} 到 {target_id} 的路径")
            
    except nx.NodeNotFound as e:
        st.error(f"节点不存在: {str(e)}")
    except Exception as e:
        st.error(f"路径查询失败: {str(e)}")