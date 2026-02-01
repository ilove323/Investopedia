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
from src.clients.ragflow_client import get_ragflow_client
from src.services.data_sync import DataSyncService
from src.config import get_config
import logging

logger = logging.getLogger(__name__)


def get_readable_status(status) -> tuple[str, str]:
    """
    将RAGFlow状态码转换为可读的中文描述

    Args:
        status: 状态码（可能是字符串或数字）

    Returns:
        (状态图标, 状态描述) 元组
    """
    # 转换为字符串以统一处理
    status_str = str(status).lower().strip()

    # 状态映射表
    status_mapping = {
        # 数字状态码
        '0': ('🔴', '失败'),
        '1': ('🟢', '已完成'),
        '2': ('🟡', '处理中'),
        '3': ('⚪', '已取消'),
        # 字符串状态码
        'failed': ('🔴', '失败'),
        'error': ('🔴', '错误'),
        'ready': ('🟢', '已完成'),
        'completed': ('🟢', '已完成'),
        'done': ('🟢', '已完成'),
        'processing': ('🟡', '处理中'),
        'running': ('🟡', '处理中'),
        'pending': ('🟡', '等待中'),
        'canceled': ('⚪', '已取消'),
        'cancelled': ('⚪', '已取消'),
    }

    # 查找匹配的状态
    if status_str in status_mapping:
        return status_mapping[status_str]

    # 未知状态
    return ('⚪', f'未知({status})')


def get_parser_name(parser_id: str) -> str:
    """
    将解析器ID转换为可读的名称

    Args:
        parser_id: 解析器ID

    Returns:
        解析器名称
    """
    parser_mapping = {
        'naive': '通用解析',
        'paper': '论文解析',
        'book': '书籍解析',
        'presentation': '演示文稿解析',
        'manual': '手动解析',
        'qa': '问答解析',
        'table': '表格解析',
        'resume': '简历解析',
        'picture': '图片解析',
        'one': '一阶解析',
        'knowledge_graph': '知识图谱解析',
        'deepdoc': '深度文档解析',
    }

    return parser_mapping.get(parser_id.lower() if parser_id else '', parser_id or 'N/A')


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
    tab_list, tab_search = st.tabs(["📋 文档列表", "🔍 文档搜索"])

    with tab_list:
        render_documents_list(ragflow_client, kb_name)

    with tab_search:
        render_document_search(ragflow_client, kb_name)


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
        # 统计各状态文档数（支持数字和字符串状态）
        ready_docs = len([d for d in documents if str(d.get('status', '')).lower() in ['1', 'ready', 'completed', 'done']])
        processing_docs = len([d for d in documents if str(d.get('status', '')).lower() in ['2', 'processing', 'running', 'pending']])
        total_chunks = sum(d.get('chunk_num', 0) for d in documents)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📄 总文档数", total_docs)
        col2.metric("✅ 已完成", ready_docs)
        col3.metric("⏳ 处理中", processing_docs)
        col4.metric("🧩 总分块数", total_chunks)

        st.divider()

        # 图谱同步区域
        st.markdown("### 🕸️ 知识图谱构建")
        col_full, col_incremental = st.columns(2)
        
        with col_full:
            if st.button("🔄 全量重建图谱", use_container_width=True, help="重新分析所有文档并构建完整知识图谱"):
                build_graph(kb_name, is_incremental=False)
        
        with col_incremental:
            if st.button("➕ 增量更新图谱", use_container_width=True, help="仅分析新增或更新的文档，合并到现有图谱"):
                build_graph(kb_name, is_incremental=True)
        
        st.divider()

        # 文档列表
        for doc in documents:
            render_document_card(doc, ragflow_client)

    except Exception as e:
        st.error(f"❌ 获取文档列表失败: {str(e)}")
        logger.error(f"获取文档列表失败: {e}")


def render_document_card(doc: Dict[str, Any], ragflow_client):
    """渲染单个文档卡片"""
    doc_id = doc.get('id', 'unknown')
    doc_name = doc.get('name', '未知文档')
    doc_size = doc.get('size', 0)
    chunk_num = doc.get('chunk_num', 0)
    token_num = doc.get('token_num', 0)
    progress = doc.get('progress', 0)
    create_time = doc.get('create_time', '')
    parser_id = doc.get('parser_id', '')

    # 获取可读状态
    status_icon, status_text = get_readable_status(doc.get('status', 'unknown'))

    with st.container(border=True):
        col_info, col_actions = st.columns([4, 1])

        with col_info:
            st.markdown(f"**📄 {doc_name}**")

            col_meta1, col_meta2 = st.columns(2)
            with col_meta1:
                st.caption(f"🆔 ID: `{doc_id}`")
                st.caption(f"📏 大小: {format_file_size(doc_size)}")
                if parser_id:
                    st.caption(f"🔧 解析: {get_parser_name(parser_id)}")

            with col_meta2:
                st.caption(f"{status_icon} 状态: {status_text}")
                st.caption(f"🧩 分块: {chunk_num} 个")
                if token_num > 0:
                    st.caption(f"🔤 Token: {token_num:,}")

            # 显示进度条（如果正在处理）
            if progress > 0 and progress < 1:
                st.progress(progress, text=f"处理进度: {progress*100:.1f}%")

            if create_time:
                st.caption(f"📅 上传: {create_time}")

        with col_actions:
            if st.button("� 查看分块", key=f"chunks_{doc_id}", use_container_width=True):
                st.session_state.selected_doc = doc_id
                st.session_state.view_mode = "chunks"  # 标记为查看分块模式

            # 下载源文件按钮
            try:
                pdf_data = ragflow_client.download_document(doc_id)
                if pdf_data:
                    st.download_button(
                        "💾 下载源文件",
                        pdf_data,
                        file_name=doc.get('name', f'document_{doc_id}.pdf'),
                        mime="application/pdf",
                        key=f"download_{doc_id}",
                        use_container_width=True
                    )
                else:
                    st.button("💾 文件不可用", disabled=True, key=f"download_disabled_{doc_id}", use_container_width=True)
            except:
                st.button("💾 下载失败", disabled=True, key=f"download_failed_{doc_id}", use_container_width=True)

        # 根据模式显示不同内容
        if st.session_state.get('selected_doc') == doc_id:
            if st.session_state.get('view_mode') == "chunks":
                render_document_detail(doc, ragflow_client)


def render_document_source(doc: Dict[str, Any], ragflow_client):
    """渲染文档源文件内容（使用SDK下载）"""
    doc_id = doc.get('id', 'unknown')
    doc_name = doc.get('name', '未知文档')

    with st.expander(f"📝 源文件内容 - {doc_name}", expanded=True):
        try:
            with st.spinner("📥 正在从RAGFlow获取源文件..."):
                # 使用SDK获取文档内容
                content = ragflow_client.get_document_content(doc_id)

            if content:
                # 显示文档信息
                col_info, col_download = st.columns([2, 1])
                with col_info:
                    st.markdown(f"**📄 文档: {doc_name}**")
                    st.caption(f"📏 {len(content):,} 字符")
                    
                    # 显示文件类型和提取方式
                    if doc_name.lower().endswith('.pdf'):
                        st.caption("🔧 使用PDF解析器提取")
                    elif doc_name.lower().endswith(('.txt', '.md')):
                        st.caption("🔧 文本文件直接读取") 
                    else:
                        st.caption("🔧 智能编码检测")

                with col_download:
                    # 提供下载按钮
                    st.download_button(
                        "💾 下载内容",
                        content,
                        file_name=f"{doc_name.replace('.pdf', '.txt')}" if doc_name != '未知文档' else f"{doc_id}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )

                st.divider()

                # 内容显示选项
                view_mode = st.radio(
                    "显示格式",
                    ["📝 纯文本", "📋 格式化", "📊 智能预览"],
                    horizontal=True,
                    key=f"view_mode_{doc_id}"
                )

                # 显示内容
                if view_mode == "📝 纯文本":
                    st.text_area(
                        "文档内容",
                        content,
                        height=600,
                        disabled=True,
                        key=f"content_text_{doc_id}"
                    )
                elif view_mode == "📋 格式化":
                    # 格式化显示
                    st.markdown("**📋 格式化内容**")
                    with st.container(height=600):
                        # 简单的段落分割和格式化
                        paragraphs = content.split('\n\n')
                        for para in paragraphs:
                            if para.strip():
                                st.markdown(para.strip())
                                st.markdown("")
                else:  # 智能预览
                    st.markdown("**📊 智能预览**")
                    
                    # 检查是否是错误信息
                    if content.startswith(('⚠️', '❌')):
                        st.warning(content)
                        
                        # 如果PDF解析失败，尝试显示分块内容
                        if '解析失败' in content:
                            st.markdown("---")
                            st.markdown("**🔄 尝试从分块内容获取文档信息**")
                            
                            try:
                                chunks = ragflow_client.get_document_chunks(doc_id)
                                if chunks:
                                    st.success(f"📊 找到 {len(chunks)} 个文档分块")
                                    
                                    # 显示前几个分块作为预览
                                    with st.expander("📖 分块内容预览", expanded=True):
                                        for i, chunk in enumerate(chunks[:3]):
                                            st.markdown(f"**分块 {i+1}:**")
                                            chunk_content = chunk.get('content', '')[:300]
                                            st.write(chunk_content + "..." if len(chunk.get('content', '')) > 300 else chunk_content)
                                            if i < 2:
                                                st.divider()
                                    
                                    if len(chunks) > 3:
                                        st.info(f"还有 {len(chunks) - 3} 个分块，可在下方查看完整分块详情")
                                else:
                                    st.error("📭 也无法获取分块内容")
                            except Exception as e:
                                st.error(f"获取分块内容失败: {str(e)}")
                    else:
                        # 正常内容的智能预览
                        content_lines = content.split('\n')
                        
                        # 显示文档摘要信息
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("总行数", len(content_lines))
                        with col2:
                            st.metric("总字符", len(content))
                        with col3:
                            non_empty_lines = len([line for line in content_lines if line.strip()])
                            st.metric("有效行数", non_empty_lines)
                        
                        # 显示内容预览
                        with st.container(height=600):
                            # 自动检测并高亮关键信息
                            if any(keyword in content.lower() for keyword in ['专项债', '政策', '条例', '管理办法']):
                                st.info("🏛️ 检测到政策文档内容")
                            
                            # 分页显示长文档
                            if len(content_lines) > 50:
                                page_size = 50
                                total_pages = (len(content_lines) + page_size - 1) // page_size
                                page_num = st.selectbox(
                                    f"选择页面 (共 {total_pages} 页)",
                                    range(1, total_pages + 1),
                                    key=f"page_select_{doc_id}"
                                )
                                
                                start_idx = (page_num - 1) * page_size
                                end_idx = min(start_idx + page_size, len(content_lines))
                                page_content = '\n'.join(content_lines[start_idx:end_idx])
                                
                                st.text_area(
                                    f"第 {page_num} 页内容",
                                    page_content,
                                    height=500,
                                    disabled=True,
                                    key=f"page_content_{doc_id}_{page_num}"
                                )
                            else:
                                # 短文档直接显示
                                st.text_area(
                                    "文档内容",
                                    content,
                                    height=500,
                                    disabled=True,
                                    key=f"smart_content_{doc_id}"
                                )

            else:
                st.warning("😔 无法获取文档内容")
                st.markdown("""
                **可能原因：**
                - 文档还在处理中，请稍后再试
                - 文档格式不支持内容提取
                - RAGFlow API暂时不可用

                **建议：**
                - 在RAGFlow Web界面检查文档状态
                - 尝试查看文档分块内容
                """)

        except Exception as e:
            st.error(f"❌ 获取源文件失败: {str(e)}")
            logger.error(f"获取文档源文件失败 (doc_id: {doc_id}): {e}")

        # 关闭按钮
        if st.button("❌ 关闭", key=f"close_source_{doc_id}"):
            st.session_state.selected_doc = None
            st.session_state.view_mode = None
            st.rerun()


def render_document_detail(doc: Dict[str, Any], ragflow_client):
    """渲染文档分块详细信息"""
    doc_id = doc.get('id', 'unknown')

    with st.expander(f"📊 分块详情 - {doc.get('name', '未知文档')}", expanded=True):
        try:
            # 显示基础信息
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**📄 基础信息**")
                st.write(f"名称: {doc.get('name', 'N/A')}")
                st.write(f"大小: {format_file_size(doc.get('size', 0))}")
                status_icon, status_text = get_readable_status(doc.get('status', 'unknown'))
                st.write(f"状态: {status_icon} {status_text}")

            with col2:
                st.markdown("**⚙️ 处理信息**")
                st.write(f"分块数: {doc.get('chunk_num', 0)} 个")
                st.write(f"Token数: {doc.get('token_num', 0):,}")
                parser_id = doc.get('parser_id', '')
                st.write(f"解析方法: {get_parser_name(parser_id)}")

                progress = doc.get('progress', 0)
                if progress > 0 and progress < 1:
                    st.write(f"处理进度: {progress*100:.1f}%")
                    st.progress(progress)
                elif progress >= 1:
                    st.write("处理进度: ✅ 100%")

            # 时间信息
            create_time = doc.get('create_time', '')
            update_time = doc.get('update_time', '')

            if create_time or update_time:
                st.markdown("**⏰ 时间信息**")
                if create_time:
                    st.write(f"创建时间: {create_time}")
                if update_time:
                    st.write(f"更新时间: {update_time}")

            # 获取并显示分块列表
            st.divider()
            st.markdown("**🧩 文档分块列表**")

            with st.spinner("获取分块信息..."):
                chunks = ragflow_client.get_document_chunks(doc_id)

            if chunks:
                for i, chunk in enumerate(chunks, 1):
                    with st.container(border=True):
                        st.markdown(f"**分块 {i}**")
                        st.caption(f"ID: `{chunk.get('id', 'N/A')}`")
                        content = chunk.get('content', '')
                        if content:
                            # 显示前200字符
                            preview = content[:200] + "..." if len(content) > 200 else content
                            st.text(preview)
                            if len(content) > 200:
                                if st.button(f"查看完整内容", key=f"chunk_full_{i}"):
                                    st.text_area("完整内容", content, height=300, key=f"chunk_content_{i}")
                        keywords = chunk.get('important_keywords', [])
                        if keywords:
                            st.caption(f"🔑 关键词: {', '.join(keywords)}")
            else:
                st.info("暂无分块信息")

        except Exception as e:
            st.error(f"获取详细信息失败: {str(e)}")
            logger.error(f"渲染文档详情失败: {e}")

        # 关闭按钮
        if st.button("❌ 关闭", key=f"close_detail_{doc_id}"):
            st.session_state.selected_doc = None
            st.session_state.view_mode = None
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


def render_document_viewer(ragflow_client):
    """简洁的文档查看器：只显示分块和下载功能"""
    st.subheader("📖 文档分块查看器")

    if not st.session_state.get('selected_doc'):
        st.info("👈 请先在左侧选择一个文档")
        return

    doc_id = st.session_state.selected_doc

    try:
        # 获取文档信息
        with st.spinner("📥 获取文档信息..."):
            documents = ragflow_client.get_documents()
            current_doc = None
            for doc in documents:
                if doc.get('id') == doc_id:
                    current_doc = doc
                    break
            
            if not current_doc:
                st.error(f"找不到文档: {doc_id}")
                return

        doc_name = current_doc.get('name', '未知文档')
        
        # 顶部：文档信息和返回按钮
        col_info, col_download, col_back = st.columns([2, 1, 1])
        
        with col_info:
            st.markdown(f"**📄 {doc_name}**")
            
        with col_download:
            # 下载源文件按钮
            try:
                with st.spinner("准备下载..."):
                    pdf_data = ragflow_client.download_document(doc_id)
                if pdf_data:
                    st.download_button(
                        "💾 下载源文件",
                        pdf_data,
                        file_name=doc_name,
                        mime="application/pdf",
                        use_container_width=True
                    )
                else:
                    st.button("💾 文件不可用", disabled=True, use_container_width=True)
            except:
                st.button("💾 下载失败", disabled=True, use_container_width=True)
                
        with col_back:
            if st.button("⬅️ 返回列表", use_container_width=True):
                st.session_state.selected_doc = None
                st.rerun()

        st.divider()

        # 主要内容：文档分块
        st.markdown("### 🧩 文档分块")
        
        try:
            with st.spinner("获取分块信息..."):
                chunks = ragflow_client.get_document_chunks(doc_id)
                
            if chunks:
                st.success(f"📊 找到 **{len(chunks)}** 个分块")
                
                # 显示每个分块
                for i, chunk in enumerate(chunks, 1):
                    with st.expander(f"📝 分块 {i} ({len(chunk.get('content', ''))} 字符)", expanded=i<=3):
                        content = chunk.get('content', '')
                        keywords = chunk.get('important_keywords', [])
                        chunk_id = chunk.get('id', f'chunk_{i}')
                        
                        if content:
                            st.text_area(
                                f"内容",
                                content,
                                height=200,
                                disabled=True,
                                label_visibility="collapsed"
                            )
                        else:
                            st.warning("分块内容为空")
                        
                        # 显示关键词和分块ID
                        col_kw, col_id = st.columns(2)
                        with col_kw:
                            if keywords:
                                st.caption(f"🔑 关键词: {', '.join(keywords)}")
                            else:
                                st.caption("🔑 无关键词")
                        with col_id:
                            st.caption(f"🔗 ID: {chunk_id}")
            else:
                st.error("❌ 未获取到分块数据")
                st.info("可能原因：文档还在处理中，或者分块功能异常")
                
        except Exception as e:
            st.error(f"❌ 获取分块失败: {e}")
            
            # 调试信息
            with st.expander("🔧 调试信息"):
                st.text(f"文档ID: {doc_id}")
                st.text(f"错误详情: {str(e)}")
                
                # 尝试直接调用API
                try:
                    st.text("尝试重新获取...")
                    chunks_debug = ragflow_client.get_document_chunks(doc_id)
                    st.text(f"调试获取结果: {len(chunks_debug)} 个分块")
                except Exception as debug_e:
                    st.text(f"调试也失败: {debug_e}")

    except Exception as e:
        st.error(f"❌ 文档查看器错误: {str(e)}")


def render_document_content(ragflow_client):
    """渲染文档内容查看（保留原功能以备后用）"""
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


def build_graph(kb_name: str, is_incremental: bool):
    """
    构建知识图谱
    
    Args:
        kb_name: 知识库名称
        is_incremental: 是否增量更新
    """
    try:
        # 创建进度容器
        progress_container = st.empty()
        status_container = st.empty()
        
        # 初始化DataSyncService
        data_sync = DataSyncService()
        
        # 进度回调函数
        def progress_callback(step: int, total: int, message: str):
            progress = step / total
            progress_container.progress(progress, text=f"进度: {step}/{total} - {message}")
            status_container.info(f"📝 {message}")
        
        # 构建图谱
        mode = "增量" if is_incremental else "全量"
        status_container.info(f"🚀 开始{mode}构建知识图谱...")
        
        result = data_sync.build_knowledge_graph(
            kb_name=kb_name,
            is_incremental=is_incremental,
            progress_callback=progress_callback
        )
        
        # 清除进度显示
        progress_container.empty()
        status_container.empty()
        
        # 显示结果
        if result.get('success'):
            st.success(f"""
✅ **{mode}图谱构建成功！**

📊 图谱统计：
- 🔵 节点数: {result.get('node_count', 0)}
- 🔗 边数: {result.get('edge_count', 0)}
- 📄 处理文档数: {result.get('doc_count', 0)}
- ⏱️ 耗时: {result.get('elapsed_time', 'N/A')}

💡 您可以前往"知识图谱"页面查看可视化结果
            """)
        else:
            error_msg = result.get('error', '未知错误')
            st.error(f"❌ {mode}图谱构建失败: {error_msg}")
            logger.error(f"图谱构建失败: {error_msg}")
            
    except Exception as e:
        st.error(f"❌ 图谱构建异常: {str(e)}")
        logger.error(f"图谱构建异常: {e}", exc_info=True)


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
