"""
聊天服务 - 封装RAGFlow Chat Assistant + 知识图谱增强
=======================================================

核心功能：
1. 查找RAGFlow中的Chat Assistant（不自动创建）
2. 混合检索（本地图谱粗筛 + RAGFlow向量精排）
3. 构建增强prompt（注入图谱关系）
4. 流式返回对话结果
"""
import logging
from typing import Optional, Dict, Any, Iterator

from src.clients.ragflow_client import get_ragflow_client
from src.services.hybrid_retriever import get_hybrid_retriever
from src.config import get_config

logger = logging.getLogger(__name__)


class ChatService:
    """聊天服务：RAGFlow Chat API + 知识图谱增强"""
    
    def __init__(self):
        self.ragflow = get_ragflow_client()
        self.retriever = get_hybrid_retriever()
        self.config = get_config()
        self.assistant = None
        # Assistant名称必须与config/chat_assistant_config.ini中的name一致
        self.assistant_name = "政策聊天助手"
    
    def _get_or_find_assistant(self):
        """
        查找已存在的Chat Assistant
        
        ⚠️ 注意：不会自动创建！
        用户必须先在RAGFlow Web UI中手动创建Assistant
        参考：config/chat_assistant_config.ini
        
        Returns:
            Chat Assistant对象
        
        Raises:
            ValueError: 如果找不到指定名称的Assistant
        """
        if self.assistant:
            return self.assistant
        
        try:
            # 查找现有的Chat Assistant
            logger.info(f"正在查找Chat Assistant: {self.assistant_name}")
            
            # RAGFlow SDK的list_chats()方法获取所有assistants
            assistants = self.ragflow.rag.list_chats()
            
            # 按名称过滤
            matching_assistants = [
                a for a in assistants 
                if hasattr(a, 'name') and a.name == self.assistant_name
            ]
            
            if not matching_assistants:
                raise ValueError(
                    f"\n{'='*60}\n"
                    f"❌ Chat Assistant '{self.assistant_name}' 不存在！\n"
                    f"{'='*60}\n\n"
                    f"请按照以下步骤手动创建：\n\n"
                    f"1️⃣  打开 RAGFlow Web UI:\n"
                    f"   {self.config.ragflow_base_url}\n\n"
                    f"2️⃣  进入 'Chat' 或 'Assistant' 页面\n\n"
                    f"3️⃣  点击 'Create Assistant' 按钮\n\n"
                    f"4️⃣  参考配置文件填写参数:\n"
                    f"   config/chat_assistant_config.ini\n\n"
                    f"5️⃣  确保设置：\n"
                    f"   - Name = '{self.assistant_name}'（必须严格匹配）\n"
                    f"   - 关联知识库 = '{self.config.default_kb_name}'\n"
                    f"   - 复制System Prompt到提示词编辑框\n\n"
                    f"6️⃣  保存后重新运行本页面\n\n"
                    f"{'='*60}\n"
                )
            
            self.assistant = matching_assistants[0]
            logger.info(f"✅ 找到Chat Assistant: {self.assistant.id}")
            return self.assistant
        
        except Exception as e:
            logger.error(f"查找Chat Assistant失败: {e}")
            raise
    
    def chat(self, 
             question: str, 
             session_id: Optional[str] = None,
             stream: bool = True) -> Iterator[Dict[str, Any]]:
        """
        智能对话（流式返回）
        
        工作流程：
        1. 查找/获取Chat Assistant
        2. 混合检索（图谱粗筛 + 向量精排）
        3. 构建增强question（注入图谱关系）
        4. 调用RAGFlow Chat API
        5. 流式返回答案chunks + 参考文档 + 图谱上下文
        
        Args:
            question: 用户问题
            session_id: 会话ID（None则创建新会话）
            stream: 是否流式返回（建议True以获得更好的用户体验）
        
        Yields:
            {'type': 'chunk', 'content': '...'}     # 文本chunk
            {'type': 'reference', 'docs': [...]}    # 参考文档
            {'type': 'graph', 'context': {...}}     # 图谱上下文
            {'type': 'error', 'message': '...'}     # 错误信息
        """
        try:
            # 1. 获取Assistant
            assistant = self._get_or_find_assistant()
            
            # 2. 混合检索（图谱 + 向量）
            logger.info(f"开始混合检索: {question[:50]}...")
            graph_context = self.retriever.retrieve(question, max_nodes=30)
            logger.info(f"图谱检索完成: {len(graph_context.get('document_ids', []))} 个相关文档")
            
            # 3. 构建增强问题（注入图谱关系）
            enhanced_question = self._build_enhanced_question(question, graph_context)
            
            # 4. 获取/创建Session
            if session_id:
                try:
                    # 尝试获取已有session
                    session = assistant.get_session(session_id)
                    logger.info(f"使用已有session: {session_id}")
                except:
                    # Session失效，创建新的
                    logger.warning(f"Session {session_id} 失效，创建新session")
                    session = assistant.create_session(name="Policy Chat")
            else:
                # 创建新session
                session = assistant.create_session(name="Policy Chat")
                logger.info(f"创建新session: {session.id}")
            
            # 5. 调用RAGFlow Chat API（流式）
            logger.info("调用RAGFlow Chat API...")
            response = session.ask(
                question=enhanced_question,
                stream=stream,
                quote=True  # 返回参考文档
            )
            
            # 6. 流式返回
            for chunk in response:
                # 文本chunk
                if hasattr(chunk, 'content') and chunk.content:
                    yield {
                        'type': 'chunk',
                        'content': chunk.content
                    }
                
                # 参考文档
                if hasattr(chunk, 'reference') and chunk.reference:
                    yield {
                        'type': 'reference',
                        'docs': self._format_references(chunk.reference)
                    }
            
            # 7. 最后返回图谱上下文（用于可视化）
            yield {
                'type': 'graph',
                'context': graph_context,
                'session_id': session.id
            }
            
            logger.info("对话完成")
        
        except ValueError as e:
            # 配置错误（如Assistant不存在）
            logger.error(f"配置错误: {e}")
            yield {
                'type': 'error',
                'message': str(e)
            }
        
        except ConnectionError as e:
            # 网络连接错误
            logger.error(f"连接错误: {e}")
            yield {
                'type': 'error',
                'message': f'无法连接到RAGFlow服务，请检查:\n1. RAGFlow服务是否运行\n2. 网络连接是否正常\n3. 配置的URL是否正确: {self.config.ragflow_base_url}'
            }
        
        except Exception as e:
            # 其他未知错误
            logger.error(f"对话失败: {e}", exc_info=True)
            yield {
                'type': 'error',
                'message': f'系统错误: {str(e)}'
            }
    
    def _build_enhanced_question(self, question: str, graph_context: Dict) -> str:
        """
        构建增强问题（注入图谱关系）
        
        策略：在question中附加图谱关系，而非修改System Prompt
        原因：
        1. 灵活性高，不需要修改RAGFlow中的Assistant配置
        2. 每次对话可以根据实际检索结果动态调整
        3. 避免图谱关系累积导致prompt过长
        
        Args:
            question: 原始用户问题
            graph_context: 混合检索返回的图谱上下文
        
        Returns:
            增强后的问题文本
        """
        if not graph_context or not graph_context.get('relations'):
            logger.info("无图谱关系，使用原始问题")
            return question
        
        # 提取关系三元组
        relations = graph_context['relations'][:10]  # 限制数量，避免超长
        
        if not relations:
            return question
        
        # 格式化关系
        relations_text = "\n".join([
            f"  • {r['source']} → {r['relation']} → {r['target']}"
            for r in relations
        ])
        
        # 构建增强问题
        enhanced = f"""{question}

[知识图谱关系]
{relations_text}
"""
        
        logger.info(f"问题增强完成，添加了 {len(relations)} 条图谱关系")
        return enhanced
    
    def _format_references(self, references: list) -> list:
        """
        格式化参考文档（去重）
        
        Args:
            references: RAGFlow返回的reference字典列表
        
        Returns:
            格式化后的文档信息列表（已去重）
        """
        formatted = []
        seen_chunks = set()  # 用于去重
        
        for idx, ref in enumerate(references):
            # references是字典列表，使用.get()访问
            chunk_id = ref.get('chunk_id') or ref.get('id')
            
            # 如果已经见过这个chunk，跳过
            if chunk_id and chunk_id in seen_chunks:
                continue
            
            # 提取文档名称（尝试多个可能的key）
            doc_name = (
                ref.get('document_name') or 
                ref.get('doc_name') or
                ref.get('title') or
                ref.get('name') or
                '未知文档'
            )
            
            # 提取内容
            content = ref.get('content') or ref.get('text') or ''
            
            # 只添加有内容的文档
            if content.strip():
                formatted.append({
                    'content': content,
                    'document_name': doc_name,
                    'document_id': ref.get('document_id') or ref.get('doc_id') or '',
                    'chunk_id': chunk_id or '',
                    'similarity': float(ref.get('similarity') or ref.get('score') or 0.0)
                })
                
                if chunk_id:
                    seen_chunks.add(chunk_id)
        
        return formatted
    
    def clear_session(self, session_id: str):
        """
        清除会话
        
        Args:
            session_id: 要清除的会话ID
        """
        try:
            assistant = self._get_or_find_assistant()
            assistant.delete_session(session_id)
            logger.info(f"✅ 会话已清除: {session_id}")
        except Exception as e:
            logger.error(f"清除会话失败: {e}")
            # 不抛出异常，避免影响用户体验


# ===== 单例模式 =====
_chat_service_instance = None

def get_chat_service() -> ChatService:
    """获取ChatService单例"""
    global _chat_service_instance
    if _chat_service_instance is None:
        _chat_service_instance = ChatService()
    return _chat_service_instance
