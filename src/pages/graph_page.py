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
    render_graph_stats,
    render_node_details,
    render_edge_details,
    render_graph_export,
    render_graph_search,
    render_graph_filter_by_type,
    render_graph_path_finder
)
from src.database.policy_dao import PolicyDAO
from src.models.graph import PolicyGraph, NodeType, RelationType, GraphNode, GraphEdge
from src.services.data_sync import DataSyncService


def show():
    st.title("📊 知识图谱")

    # 数据同步侧边栏
    with st.sidebar:
        st.subheader("📊 数据管理")
        
        # 显示数据状态
        dao = PolicyDAO()
        policies_count = len(dao.get_policies())
        st.info(f"📋 本地数据库: {policies_count} 个政策")
        
        # 同步按钮
        if st.button("🔄 同步RAGFlow数据", help="将RAGFlow中的文档同步到本地数据库"):
            with st.spinner("正在同步数据..."):
                try:
                    sync_service = DataSyncService()
                    
                    sync_results = sync_service.sync_documents_to_database()
                    
                    st.success(f"""
                    📊 同步完成！
                    - 新增政策: {sync_results['new_policies']}个
                    - 更新政策: {sync_results['updated_policies']}个
                    - 总文档数: {sync_results['total_documents']}个
                    """)
                    
                    if sync_results['errors']:
                        with st.expander("⚠️ 同步错误", expanded=False):
                            for error in sync_results['errors']:
                                st.error(error)
                    
                    # 清空图谱缓存，强制重新构建
                    st.session_state.graph = None
                    st.rerun()
                    
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

    # 构建图谱
    if st.session_state.graph is None:
        with st.spinner("正在加载知识图谱..."):
            st.session_state.graph = build_policy_graph()

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
        if st.session_state.graph and st.session_state.graph.get_node_count() > 0:
            render_graph_stats(st.session_state.graph.get_stats())
        else:
            st.info("📊 图谱统计信息将在添加数据后显示")

        st.divider()

        # 应用过滤和搜索
        filtered_graph = apply_filters_and_search(
            st.session_state.graph,
            node_filter,
            search_query,
            controls.get('node_types', []),
            controls.get('edge_types', [])
        )

        # 处理路径查询
        if path_params.get('find_path') and path_params.get('source') and path_params.get('target'):
            display_shortest_path(filtered_graph, path_params['source'], path_params['target'])

        # 主图谱显示
        if filtered_graph and filtered_graph.get_node_count() > 0:
            render_network_graph(filtered_graph.get_nx_graph())
        else:
            st.warning("🔍 图谱为空，无法显示")
            st.info("""
            💡 **提示**：
            - 请先在"文档管理"页面上传政策文档
            - 等待文档处理完成后返回此页面
            - 或检查数据库连接是否正常
            - 或调整节点类型筛选条件
            """)

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

        # 检查是否有数据
        if not policies:
            st.warning("📝 数据库中没有政策数据")
            st.info("""
            请先添加政策数据：
            1. 访问"文档管理"页面
            2. 上传政策文档
            3. 等待处理完成
            4. 返回图谱页面查看
            """)
            return PolicyGraph()

        # 创建图谱
        graph = PolicyGraph()
        
        # 记录添加的节点数
        added_nodes = 0
        added_edges = 0

        # 添加政策节点
        for policy in policies:
            node = GraphNode(
                node_id=f"policy_{policy['id']}",
                label=policy.get('title', '无标题'),
                node_type=NodeType.POLICY,
                attributes={
                    'document_id': str(policy['id']),  # 用于混合检索关联RAGFlow文档
                    "policy_type": policy.get('policy_type'),
                    "region": policy.get('region'),
                    "status": policy.get('status')
                }
            )
            if graph.add_node(node):
                added_nodes += 1

        # 添加发行机关节点
        authorities = set()
        for policy in policies:
            if policy.get('issuing_authority'):
                authorities.add(policy['issuing_authority'])

        for authority in authorities:
            node = GraphNode(
                node_id=f"authority_{authority}",
                label=authority,
                node_type=NodeType.AUTHORITY
            )
            if graph.add_node(node):
                added_nodes += 1

            # 连接政策到发行机关
            for policy in policies:
                if policy.get('issuing_authority') == authority:
                    edge = GraphEdge(
                        source_id=f"policy_{policy['id']}",
                        target_id=f"authority_{authority}",
                        relation_type=RelationType.ISSUED_BY,
                        label="由...发布"
                    )
                    if graph.add_edge(edge):
                        added_edges += 1
        # 添加地区节点
        regions = set()
        for policy in policies:
            if policy.get('region'):
                regions.add(policy['region'])

        for region in regions:
            node = GraphNode(
                node_id=f"region_{region}",
                label=region,
                node_type=NodeType.REGION
            )
            if graph.add_node(node):
                added_nodes += 1

            # 连接政策到地区
            for policy in policies:
                if policy.get('region') == region:
                    edge = GraphEdge(
                        source_id=f"policy_{policy['id']}",
                        target_id=f"region_{region}",
                        relation_type=RelationType.APPLIES_TO,
                        label="适用于"
                    )
                    if graph.add_edge(edge):
                        added_edges += 1

        # 添加政策间关系
        for policy in policies:
            relations = dao.get_policy_relations(policy['id'], as_source=True)
            for relation in relations:
                edge = GraphEdge(
                    source_id=f"policy_{policy['id']}",
                    target_id=f"policy_{relation.get('target_policy_id')}",
                    relation_type=relation.get('relation_type'),
                    label=relation.get('relation_type'),
                    attributes={"confidence": relation.get('confidence')}
                )
                if graph.add_edge(edge):
                    added_edges += 1

        # 记录构建结果
        st.success(f"🎯 图谱构建完成: 添加了 {added_nodes} 个节点, {added_edges} 条边")
        
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