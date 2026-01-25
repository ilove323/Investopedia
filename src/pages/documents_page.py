"""
RAGFlow文档查看器页面
===================
提供RAGFlow知识库中文档的查看、搜索和管理功能。

核心功能：
- 文档列表：显示RAGFlow知识库中的所有文档
- 文档详情：查看文档元数据和处理状态
- 文档内容：获取并显示文档原文内容
- 文档搜索：在知识库中搜索相关文档内容

注意：
- 文档上传请在RAGFlow Web界面进行
- 本页面专注于文档查看和搜索功能
- 需要确保RAGFlow服务正在运行并配置正确

使用示例：
    import streamlit as st
    from src.pages import documents_page
    documents_page.show()
"""
import streamlit as st
from typing import List, Dict, Any, Optional
from src.services.ragflow_client import get_ragflow_client
from src.config import get_config
import logging

logger = logging.getLogger(__name__)


def show():
    """主要显示函数"""
    st.title("📚 RAGFlow 文档查看器")
    
    # 检查RAGFlow服务状态
    ragflow_client = get_ragflow_client()
    config = get_config()
    kb_name = getattr(config, 'ragflow_kb_name', 'policy_demo_kb')

    if not ragflow_client.check_health():
        st.error(f"""
🔴 **RAGFlow服务不可用**

请检查以下配置：
1. RAGFlow服务是否已启动
2. 配置文件中的host/port是否正确  
3. 知识库 `{kb_name}` 是否存在

💡 **上传文档**: 请访问 RAGFlow Web界面进行文档上传
        """)
        return

    # 初始化session state
    if "selected_doc" not in st.session_state:
        st.session_state.selected_doc = None
    if "search_results" not in st.session_state:
        st.session_state.search_results = []

    # 显示知识库信息
    col_info, col_upload = st.columns([2, 1])
    with col_info:
        st.info(f"📂 当前知识库: **{kb_name}**")
    with col_upload:
        ragflow_url = config.ragflow_web_url
        st.markdown(f"[📤 上传文档到RAGFlow]({ragflow_url})")

    # 标签页
    tab_list, tab_search, tab_content = st.tabs(["📋 文档列表", "🔍 文档搜索", "📖 文档内容"])

    with tab_list:
        render_documents_list(ragflow_client, kb_name)

    with tab_search:
        render_document_search(ragflow_client, kb_name)

    with tab_content:
        render_document_content(ragflow_client)


def render_documents_list(ragflow_client, kb_name: str):
    """渲染文档列表"""
    st.subheader("📋 知识库文档")
    
    col_refresh, col_info = st.columns([1, 3])
    with col_refresh:
        if st.button("🔄 刷新列表", use_container_width=True):
            st.rerun()
    
    with col_info:
        st.caption("💡 文档上传请在RAGFlow Web界面操作")

    try:
        with st.spinner("📥 获取文档列表..."):
            documents = ragflow_client.get_documents(kb_name)

        if not documents:
            st.info("📭 知识库中暂无文档")
            st.markdown(f"""
            **如何上传文档：**
            1. 访问 RAGFlow Web界面
            2. 确保知识库 `{kb_name}` 已创建
            3. 上传您的政策文档（PDF、DOCX、TXT等）
            4. 等待文档处理完成后回到此页面查看
            """)
            return

        # 显示文档统计
        total_docs = len(documents)
        ready_docs = len([d for d in documents if d.get('status') in ['ready', 'completed', 'done']])
        processing_docs = len([d for d in documents if d.get('status') in ['processing', 'running']])
        
        col1, col2, col3 = st.columns(3)
        col1.metric("📄 总文档数", total_docs)
        col2.metric("✅ 已完成", ready_docs)  
        col3.metric("⏳ 处理中", processing_docs)

        st.divider()

        # 文档列表
        for doc in documents:
            render_document_card(doc, ragflow_client)

    except Exception as e:
        st.error(f"❌ 获取文档列表失败: {str(e)}")
        logger.error(f"获取文档列表失败: {e}")


def render_document_card(doc: Dict[str, Any], ragflow_client):
    """渲染单个文档卡片"""
    doc_id = doc.get('id') or doc.get('doc_id') or doc.get('document_id', 'unknown')
    doc_name = doc.get('name') or doc.get('filename') or doc.get('title', '未知文档')
    doc_status = doc.get('status', 'unknown')
    doc_size = doc.get('size', 0)
    doc_type = doc.get('type') or doc.get('file_type', '未知')
    chunk_count = doc.get('chunk_count') or doc.get('chunks') or doc.get('chunk_num', 0)
    upload_time = doc.get('upload_time') or doc.get('created_at') or doc.get('create_time', '')

    # 状态颜色映射
    status_colors = {
        'ready': '🟢',
        'completed': '🟢', 
        'done': '🟢',
        'processing': '🟡',
        'running': '🟡',
        'failed': '🔴',
        'error': '🔴'
    }
    status_icon = status_colors.get(doc_status, '⚪')

    with st.container(border=True):
        col_info, col_actions = st.columns([4, 1])
        
        with col_info:
            st.markdown(f"**📄 {doc_name}**")
            
            col_meta1, col_meta2 = st.columns(2)
            with col_meta1:
                st.caption(f"🆔 ID: `{doc_id}`")
                st.caption(f"📏 大小: {format_file_size(doc_size)}")
                
            with col_meta2:
                st.caption(f"{status_icon} 状态: {doc_status}")
                st.caption(f"🧩 分块: {chunk_count} 个")
                
            if upload_time:
                st.caption(f"📅 上传: {upload_time}")

        with col_actions:
            if st.button("📖 查看详情", key=f"detail_{doc_id}"):
                st.session_state.selected_doc = doc_id
                
            if st.button("📝 查看内容", key=f"content_{doc_id}"):
                st.session_state.selected_doc = doc_id

        # 显示文档详情
        if st.session_state.get('selected_doc') == doc_id:
            render_document_detail(doc, ragflow_client)


def render_document_detail(doc: Dict[str, Any], ragflow_client):
    """渲染文档详细信息"""
    doc_id = doc.get('id') or doc.get('doc_id') or doc.get('document_id')
    
    with st.expander(f"📖 详细信息 - {doc.get('name', '未知文档')}", expanded=True):
        try:
            # 显示基础信息
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📄 基础信息**")
                st.write(f"名称: {doc.get('name', 'N/A')}")
                st.write(f"类型: {doc.get('type', 'N/A')}")
                st.write(f"大小: {format_file_size(doc.get('size', 0))}")
                st.write(f"状态: {doc.get('status', 'N/A')}")
                
            with col2:
                st.markdown("**⚙️ 处理信息**")
                st.write(f"分块数: {doc.get('chunk_count', 0)} 个")
                st.write(f"Token数: {doc.get('token_count', 0)}")
                st.write(f"解析方法: {doc.get('parser_method', 'N/A')}")
                
                progress = doc.get('progress')
                if progress is not None:
                    st.write(f"处理进度: {progress}%")
                    st.progress(progress / 100)

            # 时间信息
            upload_time = doc.get('upload_time') or doc.get('created_at')
            update_time = doc.get('update_time') or doc.get('updated_at')
            
            if upload_time or update_time:
                st.markdown("**⏰ 时间信息**")
                if upload_time:
                    st.write(f"上传时间: {upload_time}")
                if update_time:
                    st.write(f"更新时间: {update_time}")

        except Exception as e:
            st.error(f"获取详细信息失败: {str(e)}")

        # 关闭按钮
        if st.button("❌ 关闭详情", key=f"close_detail_{doc_id}"):
            st.session_state.selected_doc = None
            st.rerun()


def render_document_search(ragflow_client, kb_name: str):
    """渲染文档搜索功能"""
    st.subheader("🔍 文档搜索")
    
    # 搜索表单
    col_query, col_params = st.columns([3, 1])
    
    with col_query:
        search_query = st.text_input("🔎 输入搜索关键词", placeholder="例如：特别国债管理办法")
        
    with col_params:
        top_k = st.number_input("返回结果数", min_value=1, max_value=50, value=10)
        score_threshold = st.slider("相似度阈值", 0.0, 1.0, 0.3, 0.1)

    if st.button("🚀 开始搜索", use_container_width=True) and search_query:
        try:
            with st.spinner("🔍 搜索中..."):
                results = ragflow_client.search(
                    query=search_query,
                    knowledge_base_name=kb_name,
                    top_k=top_k,
                    score_threshold=score_threshold
                )
                
            st.session_state.search_results = results
            
            if results:
                st.success(f"🎯 找到 {len(results)} 个相关结果")
            else:
                st.warning("😔 未找到相关内容，请尝试其他关键词")
                
        except Exception as e:
            st.error(f"❌ 搜索失败: {str(e)}")
            logger.error(f"搜索失败: {e}")

    # 显示搜索结果
    if st.session_state.search_results:
        st.divider()
        st.markdown("### 🎯 搜索结果")
        
        for i, result in enumerate(st.session_state.search_results, 1):
            render_search_result(result, i)


def render_search_result(result: Dict[str, Any], index: int):
    """渲染单个搜索结果"""
    doc_id = result.get('doc_id')
    doc_name = result.get('doc_name', '未知文档')
    content = result.get('content', '')
    score = result.get('score', 0)
    
    with st.container(border=True):
        col_header, col_score = st.columns([4, 1])
        
        with col_header:
            st.markdown(f"**{index}. 📄 {doc_name}**")
            
        with col_score:
            st.metric("相似度", f"{score:.2%}" if score else "N/A")

        # 显示内容片段
        if content:
            # 限制显示长度
            display_content = content[:500] + "..." if len(content) > 500 else content
            st.markdown(f"**内容片段：**")
            st.markdown(f"> {display_content}")
        
        # 操作按钮
        col_view, col_full = st.columns(2)
        
        with col_view:
            if st.button(f"📖 查看完整文档", key=f"view_full_{doc_id}_{index}"):
                st.session_state.selected_doc = doc_id
                
        with col_full:
            if st.button(f"📄 查看此片段", key=f"view_chunk_{doc_id}_{index}"):
                st.markdown("**完整片段内容：**")
                st.text_area("", content, height=200, key=f"content_{doc_id}_{index}")


def render_document_content(ragflow_client):
    """渲染文档内容查看"""
    st.subheader("📖 文档内容查看")

    if not st.session_state.get('selected_doc'):
        st.info("👈 请先在左侧选择一个文档")
        return

    doc_id = st.session_state.selected_doc

    try:
        with st.spinner("📥 获取文档内容..."):
            content = ragflow_client.get_document_content(doc_id)

        if content:
            # 显示文档信息
            st.markdown(f"**📄 文档ID: {doc_id}**")
            st.caption(f"📏 {len(content)} 字符")

            st.divider()

            # 内容显示选项
            col_format, col_actions = st.columns([2, 2])
            
            with col_format:
                view_mode = st.radio(
                    "显示格式",
                    ["📝 纯文本", "📋 格式化"],
                    horizontal=True
                )
                
            with col_actions:
                st.download_button(
                    "💾 下载完整内容",
                    content,
                    file_name=f"{doc_id}.txt",
                    mime="text/plain"
                )

            # 显示内容
            if view_mode == "📝 纯文本":
                st.text_area(
                    "文档内容",
                    content,
                    height=600,
                    disabled=True
                )
            else:
                st.markdown("**📋 格式化内容**")
                # 简单的段落分割和格式化
                paragraphs = content.split('\n\n')
                for para in paragraphs:
                    if para.strip():
                        st.markdown(para.strip())
                        st.markdown("")

        else:
            st.warning("😔 无法获取文档内容，可能原因：")
            st.markdown("""
            - 文档还在处理中
            - 文档类型不支持内容提取  
            - RAGFlow API端点配置问题
            """)

    except Exception as e:
        st.error(f"❌ 获取文档内容失败: {str(e)}")
        logger.error(f"获取文档内容失败: {e}")

    # 返回按钮
    if st.button("⬅️ 返回文档列表"):
        st.session_state.selected_doc = None
        st.rerun()


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小显示"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"
