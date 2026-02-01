"""
数据统计页面
==========
提供文档统计和图谱分析功能。

核心功能：
- 文档统计：显示RAGFlow中的文档数量和状态
- 图谱统计：显示知识图谱的节点和边统计
- 快速链接：跳转到其他功能页面
"""
import streamlit as st
import pandas as pd
from src.clients.ragflow_client import get_ragflow_client
from src.database.graph_dao import GraphDAO
from src.config import get_config


def show():
    st.title("📈 数据统计")

    tab_overview, tab_docs, tab_graph = st.tabs(["📊 总览", "📚 文档统计", "🕸️ 图谱统计"])

    with tab_overview:
        render_overview()

    with tab_docs:
        render_document_stats()

    with tab_graph:
        render_graph_stats()


def render_overview():
    """总览"""
    st.subheader("系统数据概览")
    
    try:
        config = get_config()
        kb_name = getattr(config, 'ragflow_kb_name', 'policy_demo_kb')
        ragflow_client = get_ragflow_client()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if ragflow_client.check_health():
                docs = ragflow_client.get_documents(kb_name)
                st.metric("📄 RAGFlow文档", len(docs))
            else:
                st.metric("📄 RAGFlow文档", "N/A", help="RAGFlow服务不可用")
        
        with col2:
            try:
                db_path = config.data_dir / "database" / "policies.db"
                graph_dao = GraphDAO(str(db_path))
                graph_stats = graph_dao.get_stats()
                if graph_stats:
                    st.metric("🕸️ 图谱节点", graph_stats.get('node_count', 0))
                else:
                    st.metric("🕸️ 图谱节点", 0, help="尚未构建图谱")
            except Exception:
                st.metric("🕸️ 图谱节点", "N/A", help="图谱数据获取失败")
        
        with col3:
            try:
                if graph_stats:
                    st.metric("🔗 图谱关系", graph_stats.get('edge_count', 0))
                else:
                    st.metric("🔗 图谱关系", 0)
            except:
                st.metric("🔗 图谱关系", "N/A")
        
        st.divider()
        st.subheader("快速操作")
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            if st.button("📚 查看文档", use_container_width=True):
                st.switch_page("pages/3_📚_文档管理.py")
        
        with col_b:
            if st.button("🕸️ 查看图谱", use_container_width=True):
                st.switch_page("pages/2_📊_知识图谱.py")
        
        with col_c:
            if st.button("💬 AI问答", use_container_width=True):
                st.switch_page("pages/4_💬_智能问答.py")
        
    except Exception as e:
        st.error(f"获取统计数据失败: {e}")


def render_document_stats():
    """文档统计"""
    st.subheader("RAGFlow 文档统计")
    
    try:
        config = get_config()
        kb_name = getattr(config, 'ragflow_kb_name', 'policy_demo_kb')
        ragflow_client = get_ragflow_client()
        
        if not ragflow_client.check_health():
            st.error("RAGFlow服务不可用，请检查配置")
            return
        
        with st.spinner("获取文档数据..."):
            docs = ragflow_client.get_documents(kb_name)
        
        if not docs:
            st.info("知识库中暂无文档")
            return
        
        total_docs = len(docs)
        ready_docs = len([d for d in docs if str(d.get('status', '')).lower() in ['1', 'ready', 'completed', 'done']])
        processing_docs = len([d for d in docs if str(d.get('status', '')).lower() in ['2', 'processing', 'running', 'pending']])
        total_chunks = sum(d.get('chunk_num', 0) for d in docs)
        total_tokens = sum(d.get('token_num', 0) for d in docs)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("📄 文档总数", total_docs)
        col2.metric("✅ 已完成", ready_docs)
        col3.metric("⏳ 处理中", processing_docs)
        
        col4, col5, col6 = st.columns(3)
        col4.metric("🧩 总分块数", total_chunks)
        col5.metric("🔤 总Token数", f"{total_tokens:,}")
        col6.metric("📊 平均分块", f"{total_chunks/total_docs:.1f}" if total_docs > 0 else "0")
        
        st.divider()
        st.subheader("文档列表")
        doc_data = []
        for doc in docs:
            status_icon, status_text = get_readable_status(doc.get('status'))
            doc_data.append({
                "文档名": doc.get('name', 'Unknown'),
                "状态": f"{status_icon} {status_text}",
                "分块数": doc.get('chunk_num', 0),
                "Token数": doc.get('token_num', 0)
            })
        
        df = pd.DataFrame(doc_data)
        st.dataframe(df, use_container_width=True)
        
    except Exception as e:
        st.error(f"获取文档统计失败: {e}")


def render_graph_stats():
    """图谱统计"""
    st.subheader("知识图谱统计")
    
    try:
        config = get_config()
        db_path = config.data_dir / "database" / "policies.db"
        graph_dao = GraphDAO(str(db_path))
        graph_data = graph_dao.load_graph()
        
        if not graph_data:
            st.warning("尚未构建知识图谱")
            st.info("请前往「📚 文档管理」页面构建知识图谱")
            return
        
        nodes = graph_data.get('nodes', [])
        edges = graph_data.get('edges', [])
        
        col1, col2, col3 = st.columns(3)
        col1.metric("🔵 节点数", len(nodes))
        col2.metric("🔗 关系数", len(edges))
        col3.metric("📊 平均连接", f"{len(edges)/len(nodes):.2f}" if len(nodes) > 0 else "0")
        
        st.divider()
        st.subheader("节点类型分布")
        node_types = {}
        for node in nodes:
            node_type = node.get('type', 'unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        type_df = pd.DataFrame(list(node_types.items()), columns=['类型', '数量'])
        type_df = type_df.sort_values('数量', ascending=False)
        
        col_chart, col_table = st.columns([2, 1])
        with col_chart:
            st.bar_chart(type_df.set_index('类型'))
        with col_table:
            st.dataframe(type_df, use_container_width=True, hide_index=True)
        
        st.divider()
        st.subheader("关系类型分布")
        edge_types = {}
        for edge in edges:
            edge_type = edge.get('type') or edge.get('label', 'unknown')
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
        
        edge_df = pd.DataFrame(list(edge_types.items()), columns=['关系类型', '数量'])
        edge_df = edge_df.sort_values('数量', ascending=False)
        
        col_chart2, col_table2 = st.columns([2, 1])
        with col_chart2:
            st.bar_chart(edge_df.set_index('关系类型'))
        with col_table2:
            st.dataframe(edge_df, use_container_width=True, hide_index=True)
        
    except Exception as e:
        st.error(f"获取图谱统计失败: {e}")


def get_readable_status(status) -> tuple[str, str]:
    """将状态码转换为可读描述"""
    status_str = str(status).lower().strip()
    status_mapping = {
        '0': ('🔴', '失败'), '1': ('🟢', '已完成'), '2': ('🟡', '处理中'), '3': ('⚪', '已取消'),
        'failed': ('🔴', '失败'), 'error': ('🔴', '错误'),
        'ready': ('🟢', '已完成'), 'completed': ('🟢', '已完成'), 'done': ('🟢', '已完成'),
        'processing': ('🟡', '处理中'), 'running': ('🟡', '处理中'), 'pending': ('🟡', '等待中'),
        'canceled': ('⚪', '已取消'), 'cancelled': ('⚪', '已取消'),
    }
    return status_mapping.get(status_str, ('⚪', f'未知({status})'))
