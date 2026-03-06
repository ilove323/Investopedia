"""
智能问答页面
===========

基于RAGFlow Chat Assistant + 知识图谱的智能对话界面

功能特性：
- 流式打字效果
- 参考文档展示（去重）
- 可点击的引用编号
- 知识图谱可视化
- 多轮对话支持
- 会话管理
- 语音输入（实时录音）
"""
import streamlit as st
import logging
import re
import hashlib
import tempfile
from pathlib import Path

try:
    from audio_recorder_streamlit import audio_recorder
    AUDIO_RECORDER_AVAILABLE = True
except ImportError:
    AUDIO_RECORDER_AVAILABLE = False
    logging.warning("audio_recorder_streamlit未安装，语音功能不可用")

from src.services.chat_service import get_chat_service
from src.components.graph_ui import render_network_graph
from src.clients.whisper_client import get_whisper_client

logger = logging.getLogger(__name__)


def format_references_with_anchors(text: str, references: list) -> str:
    """
    将[ID:x]标记转换为可点击的引用编号
    
    Args:
        text: 原始文本（包含[ID:x]标记）
        references: 参考文档列表
    
    Returns:
        格式化后的HTML文本
    """
    if not text or not references:
        return text
    
    # 先去重references，构建ID映射
    id_to_index = {}
    seen_chunks = set()
    current_index = 1
    
    for idx, ref in enumerate(references):
        chunk_id = ref.get('chunk_id', '')
        content = ref.get('content', '')
        
        # 生成唯一标识
        unique_id = chunk_id or hashlib.md5(content.encode()).hexdigest()[:16]
        
        if unique_id not in seen_chunks:
            seen_chunks.add(unique_id)
            # 原始ID就是索引idx
            id_to_index[str(idx)] = current_index
            current_index += 1
    
    # 替换[ID:x]为可点击的引用编号
    def replace_id(match):
        id_str = match.group(1)
        display_index = id_to_index.get(id_str, int(id_str) + 1)  # 如果没找到，默认使用原ID+1
        return f'<a href="#ref-{display_index}" style="color: #1f77b4; text-decoration: none; font-size: 0.9em; vertical-align: super;">[{display_index}]</a>'
    
    # 找到所有[ID:x]标记并替换
    formatted_text = re.sub(r'\[ID:(\d+)\]', replace_id, text)
    
    return formatted_text


def deduplicate_references(references: list) -> list:
    """
    去重参考文档（按文档名去重）
    
    Args:
        references: 原始参考文档列表
    
    Returns:
        去重后的参考文档列表（保留原始ID）
    """
    seen_docs = set()
    deduplicated = []
    
    for idx, ref in enumerate(references):
        doc_name = ref.get('document_name', '未知文档')
        
        # 按文档名去重
        if doc_name not in seen_docs:
            seen_docs.add(doc_name)
            # 保留原始ID用于映射
            ref['original_id'] = idx
            deduplicated.append(ref)
    
    return deduplicated


def show():
    """渲染聊天页面"""
    
    st.title("💬 智能问答")
    st.caption("基于RAGFlow向量检索 + 知识图谱的政策智能咨询")
    
    # ===== 初始化Session State =====
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'chat_session_id' not in st.session_state:
        st.session_state.chat_session_id = None
    if 'last_audio_bytes' not in st.session_state:
        st.session_state.last_audio_bytes = None
    if 'pending_voice_input' not in st.session_state:
        st.session_state.pending_voice_input = False
    
    # ===== 顶部控制栏 =====
    col1, col2, col3 = st.columns([8, 1, 1])
    
    with col2:
        if st.button("🗑️ 清除", help="清除聊天历史和会话", use_container_width=True):
            # 清除后端session
            if st.session_state.chat_session_id:
                try:
                    chat_service = get_chat_service()
                    chat_service.clear_session(st.session_state.chat_session_id)
                except Exception as e:
                    logger.warning(f"清除会话失败: {e}")
            
            # 清除前端状态
            st.session_state.chat_history = []
            st.session_state.chat_session_id = None
            st.rerun()
    
    with col3:
        # 显示会话状态
        if st.session_state.chat_session_id:
            st.caption(f"🟢 会话中")
        else:
            st.caption("🔴 新会话")
    
    # ===== 分隔线 =====
    st.divider()
    
    # ===== 处理待处理的语音输入 =====
    user_input = None
    if st.session_state.pending_voice_input:
        st.session_state.pending_voice_input = False
        
        with st.spinner("正在识别语音..."):
            try:
                # 保存音频到临时文件
                audio_bytes = st.session_state.last_audio_bytes
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                    tmp_file.write(audio_bytes)
                    tmp_path = tmp_file.name
                
                # 调用Whisper转写
                whisper_client = get_whisper_client()
                result = whisper_client.transcribe(
                    tmp_path,
                    task='transcribe',
                    language='zh'
                )
                
                # 清理临时文件
                Path(tmp_path).unlink()
                
                # 提取文本（只要text字段的纯文本）
                recognized_text = None
                if result:
                    if isinstance(result, dict):
                        # 从JSON中提取text字段
                        recognized_text = result.get('text', '')
                    elif isinstance(result, str):
                        # 如果是字符串，尝试解析JSON
                        try:
                            import json
                            data = json.loads(result)
                            recognized_text = data.get('text', result)
                        except:
                            # 如果不是JSON，直接使用字符串
                            recognized_text = result
                    
                    # 清理空白字符
                    if recognized_text:
                        recognized_text = recognized_text.strip()
                
                if recognized_text:
                    # 只显示纯文本内容
                    st.success(f"✅ 识别结果: {recognized_text}")
                    # 将语音识别结果直接添加到聊天历史
                    st.session_state.chat_history.append({
                        'role': 'user',
                        'content': recognized_text
                    })
                    # 触发重新运行以显示对话
                    st.rerun()
                else:
                    st.warning("未识别到有效文本")
            
            except Exception as e:
                logger.error(f"语音识别失败: {e}")
                st.error(f"语音识别失败: {str(e)}")
    
    # ===== 显示聊天历史 =====
    for idx, msg in enumerate(st.session_state.chat_history):
        with st.chat_message(msg['role']):
            # 显示消息内容（带引用编号）
            if msg['role'] == 'assistant' and msg.get('references'):
                # 格式化答案，将[ID:x]转换为可点击的引用
                formatted_content = format_references_with_anchors(
                    msg['content'], 
                    msg['references']
                )
                st.markdown(formatted_content, unsafe_allow_html=True)
            else:
                st.markdown(msg['content'])
            
            # 显示参考文档（RAGFlow原生风格）
            if msg.get('references') and len(msg['references']) > 0:
                references = msg['references']
                
                # 按文档分组统计
                doc_groups = {}
                for ref in references:
                    doc_name = ref.get('document_name', 'Unknown')
                    if doc_name not in doc_groups:
                        doc_groups[doc_name] = {
                            'count': 0,
                            'chunks': [],
                            'doc_id': ref.get('document_id', ''),
                            'dataset_id': ref.get('dataset_id', '')
                        }
                    doc_groups[doc_name]['count'] += 1
                    doc_groups[doc_name]['chunks'].append(ref)
                
                with st.expander(
                    f"📚 参考文档 ({len(doc_groups)}个文档, {len(references)}个引用片段)", 
                    expanded=False
                ):
                    # 显示每个chunk（类似RAGFlow）
                    for i, ref in enumerate(references, 1):
                        doc_name = ref.get('document_name', 'Unknown')
                        doc_id = ref.get('document_id', '')
                        dataset_id = ref.get('dataset_id', '')
                        similarity = ref.get('similarity', 0)
                        chunk_id = ref.get('id', '')
                        image_id = ref.get('image_id', '')
                        
                        col1, col2 = st.columns([5, 1])
                        with col1:
                            st.markdown(f"**引用 #{i}: {doc_name}**")
                            st.caption(f"相似度: {similarity:.2%} | ID: {chunk_id[:12]}...")
                        
                        with col2:
                            # 下载按钮（获取完整文档）
                            if st.button("📥", key=f"download_doc_{idx}_{chunk_id}", 
                                       help="下载完整文档"):
                                try:
                                    from src.clients.ragflow_client import RAGFlowClient
                                    ragflow = RAGFlowClient()
                                    
                                    # 通过dataset查找文档并下载
                                    datasets = ragflow.rag.list_datasets(id=dataset_id)
                                    if datasets:
                                        docs = datasets[0].list_documents(id=doc_id)
                                        if docs:
                                            content = docs[0].download()
                                            st.download_button(
                                                label="💾 保存",
                                                data=content,
                                                file_name=doc_name,
                                                mime="application/octet-stream",
                                                key=f"save_{idx}_{chunk_id}"
                                            )
                                        else:
                                            st.error("文档未找到")
                                    else:
                                        st.error("知识库未找到")
                                except Exception as e:
                                    st.error(f"下载失败: {str(e)}")
                        
                        # 显示chunk内容（可折叠）
                        with st.expander("查看引用内容", expanded=False):
                            st.markdown(ref.get('content', ''))
                            
                            # 如果有图片截图
                            if image_id:
                                st.caption(f"📸 包含图片截图 (ID: {image_id})")
                        
                        if i < len(references):
                            st.divider()
            
            # 显示知识图谱（折叠）
            if msg.get('graph_context'):
                graph_context = msg['graph_context']
                subgraph = graph_context.get('subgraph')
                
                if subgraph and subgraph.get_node_count() > 0:
                    relations = graph_context.get('relations', [])
                    node_count = subgraph.get_node_count()
                    
                    with st.expander(
                        f"🔗 知识图谱 ({node_count}个节点, {len(relations)}条关系)", 
                        expanded=False
                    ):
                        # 显示关系列表
                        if relations:
                            st.caption("**相关关系**:")
                            for r in relations[:8]:  # 只显示前8条
                                st.markdown(
                                    f"• {r['source']} → *{r['relation']}* → {r['target']}"
                                )
                            
                            if len(relations) > 8:
                                st.caption(f"...还有 {len(relations) - 8} 条关系")
                            
                            st.divider()
                        
                        # 可视化图谱
                        st.caption("**图谱可视化**:")
                        try:
                            nx_graph = subgraph.get_nx_graph()
                            render_network_graph(nx_graph)
                        except Exception as e:
                            st.error(f"图谱可视化失败: {e}")
    
    # ===== 检查是否有待回答的用户消息 =====
    if (len(st.session_state.chat_history) > 0 and 
        st.session_state.chat_history[-1]['role'] == 'user'):
        
        # 获取最后一条用户消息
        prompt = st.session_state.chat_history[-1]['content']
        
        # ===== 调用ChatService，流式显示回答 =====
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            references = []
            graph_context = None
            session_id = st.session_state.chat_session_id
            
            try:
                chat_service = get_chat_service()
                
                # 流式处理响应
                for chunk in chat_service.chat(
                    question=prompt, 
                    session_id=session_id, 
                    stream=True
                ):
                    if chunk['type'] == 'chunk':
                        # 文本chunk - 增量累积
                        full_response += chunk['content']
                        message_placeholder.markdown(full_response + "▌")
                    
                    elif chunk['type'] == 'reference':
                        # 参考文档
                        references = chunk['docs']
                    
                    elif chunk['type'] == 'graph':
                        # 图谱上下文
                        graph_context = chunk['context']
                        session_id = chunk.get('session_id')
                        
                        # 更新session_id
                        if session_id:
                            st.session_state.chat_session_id = session_id
                    
                    elif chunk['type'] == 'error':
                        # 错误信息
                        st.error(f"⚠️ {chunk['message']}")
                        full_response = f"抱歉，出现错误：{chunk['message']}"
                        break
                
                # 完成打字效果，显示带引用的最终答案
                if references:
                    formatted_response = format_references_with_anchors(full_response, references)
                    message_placeholder.markdown(formatted_response, unsafe_allow_html=True)
                else:
                    message_placeholder.markdown(full_response)
                
                # ===== 显示参考文档（去重） =====
                if references and len(references) > 0:
                    dedup_refs = deduplicate_references(references)
                    
                    with st.expander(f"📚 参考文档 ({len(dedup_refs)}个)", expanded=False):
                        for i, ref in enumerate(dedup_refs, 1):
                            # 添加锚点供引用编号跳转
                            st.markdown(f'<div id="ref-{i}"></div>', unsafe_allow_html=True)
                            
                            st.markdown(f"**[{i}] {ref['document_name']}**")
                            st.caption(f"相似度: {ref['similarity']:.2%}")
                            
                            content = ref['content']
                            if len(content) > 300:
                                st.text(content[:300] + "...")
                            else:
                                st.text(content)
                            
                            if i < len(dedup_refs):
                                st.divider()
                
                # ===== 显示知识图谱 =====
                if graph_context and graph_context.get('subgraph'):
                    subgraph = graph_context['subgraph']
                    
                    if subgraph and subgraph.get_node_count() > 0:
                        relations = graph_context.get('relations', [])
                        node_count = subgraph.get_node_count()
                        
                        with st.expander(
                            f"🔗 知识图谱 ({node_count}个节点, {len(relations)}条关系)", 
                            expanded=False
                        ):
                            # 显示关系列表
                            if relations:
                                st.caption("**相关关系**:")
                                for r in relations[:8]:
                                    st.markdown(
                                        f"• {r['source']} → *{r['relation']}* → {r['target']}"
                                    )
                                
                                if len(relations) > 8:
                                    st.caption(f"...还有 {len(relations) - 8} 条关系")
                                
                                st.divider()
                            
                            # 可视化图谱
                            st.caption("**图谱可视化**:")
                            try:
                                nx_graph = subgraph.get_nx_graph()
                                render_network_graph(nx_graph)
                            except Exception as e:
                                st.error(f"图谱可视化失败: {e}")
            
            except Exception as e:
                st.error(f"⚠️ 对话失败: {str(e)}")
                logger.error(f"对话失败: {e}", exc_info=True)
                full_response = "抱歉，系统出现错误，请稍后重试。"
        
        # ===== 保存助手消息到历史 =====
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': full_response,
            'references': references,
            'graph_context': graph_context
        })
    
    # ===== 输入区（页面底部） =====
    st.divider()
    
    col_input, col_voice = st.columns([5, 1])
    
    with col_input:
        text_input = st.chat_input("请输入您的问题...", key="chat_input")
    
    with col_voice:
        if AUDIO_RECORDER_AVAILABLE:
            st.caption("🎤 语音")
            audio_bytes = audio_recorder(
                text="",
                recording_color="#e74c3c",
                neutral_color="#6aa36f",
                icon_size="2x",
                key="voice_input"
            )
            
            if audio_bytes and audio_bytes != st.session_state.get('last_audio_bytes'):
                st.session_state.last_audio_bytes = audio_bytes
                st.session_state.pending_voice_input = True
                st.rerun()
        else:
            st.caption("⚠️ 语音不可用")
    
    # 处理文字输入
    if text_input and not user_input:
        st.session_state.chat_history.append({
            'role': 'user',
            'content': text_input
        })
        st.rerun()
    
    # ===== 页面底部提示 =====
    if len(st.session_state.chat_history) == 0:
        st.info(
            "💡 **使用提示**\n\n"
            "• 输入政策相关问题，或点击🎤录音提问\n"
            "• 答案中的蓝色数字 [1,2] 可点击跳转到对应参考文档\n"
            "• 点击折叠面板可查看参考文档和知识图谱\n"
            "• 支持多轮对话，上下文会自动保持\n"
            "• 点击「清除」按钮可开始新对话"
        )


if __name__ == "__main__":
    show()
