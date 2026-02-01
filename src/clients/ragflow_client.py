"""
RAGFlow服务客户端
=================
负责与RAGFlow服务的API交互。

核心功能：
- 健康检查（验证服务连接）
- 文档上传（向RAGFlow上传政策文档）
- 文档删除（从RAGFlow删除文档）
- 语义搜索（基于向量相似度搜索）
- 问答功能（调用RAGFlow的问答API）
- 知识库配置管理

本模块使用官方RAGFlow SDK实现所有功能，不再使用自定义HTTP客户端。

🔗 RAGFlow API文档：
- Python API参考: https://ragflow.com.cn/docs/python_api_reference
- HTTP API参考: https://ragflow.com.cn/docs/http_api_reference

📦 API类型说明：
本模块**完全使用Python SDK API**，所有方法都基于ragflow-sdk包。
SDK内部会自动处理HTTP请求，开发者无需关心底层HTTP通信细节。

依赖：
- ragflow_sdk - RAGFlow官方Python SDK
- src.config.ConfigLoader - RAGFlow服务配置

配置项（来自config.ini的[RAGFLOW]部分）：
- host: RAGFlow服务主机地址
- port: RAGFlow服务端口
- api_key: RAGFlow API密钥

使用示例：
    from src.clients.ragflow_client import get_ragflow_client

    client = get_ragflow_client()

    # 检查连接
    if client.check_health():
        print("RAGFlow服务正常")

    # 上传文档
    doc_id = client.upload_document("policy.pdf", "policy.pdf")

    # 搜索
    results = client.search("政策内容", top_k=10)
"""
import logging
from typing import Optional, Dict, List, Any

# ===== 导入官方RAGFlow SDK =====
try:
    from ragflow_sdk import RAGFlow
except ImportError:
    RAGFlow = None
    print("Warning: ragflow-sdk not installed. Please run: pip install ragflow-sdk")

# ===== 导入配置系统 =====
from src.config import get_config

# ===== 获取RAGFlow配置 =====
config = get_config()

RAGFLOW_BASE_URL = config.ragflow_base_url  # RAGFlow服务URL（http://host:port）
RAGFLOW_API_KEY = config.ragflow_api_key  # RAGFlow API密钥（如果需要认证）
RAGFLOW_TIMEOUT = config.ragflow_timeout  # API调用超时时间（秒）
RAGFLOW_RETRY_TIMES = config.ragflow_retry_times  # 失败重试次数
RAGFLOW_RETRY_DELAY = config.ragflow_retry_delay  # 重试延迟（秒）
RAGFLOW_SEARCH_CONFIG = config.ragflow_search_config  # 搜索配置（top_k, threshold等）
RAGFLOW_QA_CONFIG = config.ragflow_qa_config  # 问答配置（max_tokens, temperature等）

logger = logging.getLogger(__name__)


class RAGFlowClient:
    """RAGFlow客户端 - 使用官方SDK"""

    def __init__(self):
        """初始化RAGFlow客户端"""
        if RAGFlow is None:
            raise ImportError("RAGFlow SDK not available. Please install: pip install ragflow-sdk")

        # 初始化官方SDK客户端
        self.rag = RAGFlow(
            api_key=RAGFLOW_API_KEY,
            base_url=RAGFLOW_BASE_URL
        )

        # 存储知识库和聊天助手的缓存
        self._dataset_cache = {}
        self._chat_cache = {}

        logger.info(f"RAGFlow SDK initialized: {RAGFLOW_BASE_URL}")



    def _get_or_create_dataset(self, kb_name: str):
        """获取或缓存数据集对象
        
        📦 API: Python SDK - RAGFlow.list_datasets()
        参考: https://ragflow.com.cn/docs/python_api_reference#list-datasets

        Args:
            kb_name: 知识库名称

        Returns:
            数据集对象，如果未找到返回None
        """
        # 检查缓存
        if kb_name in self._dataset_cache:
            return self._dataset_cache[kb_name]

        try:
            # 使用SDK列出数据集
            datasets = self.rag.list_datasets(name=kb_name)
            if datasets:
                dataset = datasets[0]
                self._dataset_cache[kb_name] = dataset
                logger.debug(f"Dataset cached: {kb_name} (ID: {dataset.id})")
                return dataset

            logger.error(f"Dataset '{kb_name}' not found")
            return None
        except Exception as e:
            logger.error(f"Failed to get dataset '{kb_name}': {e}")
            return None

    def _check_knowledge_base_exists(self, kb_name: str) -> bool:
        """
        检查知识库是否存在
        
        📦 API: Python SDK - RAGFlow.list_datasets()
        参考: https://ragflow.com.cn/docs/python_api_reference#list-datasets

        Args:
            kb_name: 知识库名称

        Returns:
            bool: 知识库是否存在
        """
        try:
            datasets = self.rag.list_datasets(name=kb_name)
            if datasets:
                logger.info(f"✅ 知识库 '{kb_name}' 存在")
                return True
            logger.warning(f"❌ 知识库 '{kb_name}' 不存在")
            return False
        except Exception as e:
            logger.warning(f"知识库存在性检查失败: {e}")
            return False



    def _get_knowledge_base_id(self, kb_name: str) -> Optional[str]:
        """获取知识库ID

        Args:
            kb_name: 知识库名称

        Returns:
            知识库ID，如果未找到返回None
        """
        try:
            dataset = self._get_or_create_dataset(kb_name)
            return dataset.id if dataset else None
        except Exception as e:
            logger.error(f"获取知识库ID失败: {e}")
            return None

    def _get_or_create_chat_assistant(self, knowledge_base_name: str):
        """获取或创建聊天助手
        
        📦 API: Python SDK - RAGFlow.list_chats() / create_chat()
        参考: https://ragflow.com.cn/docs/python_api_reference#chat-assistant-management

        Args:
            knowledge_base_name: 知识库名称

        Returns:
            聊天助手对象
        """
        try:
            # 检查缓存
            if knowledge_base_name in self._chat_cache:
                return self._chat_cache[knowledge_base_name]

            # 获取知识库
            datasets = self.rag.list_datasets(name=knowledge_base_name)
            if not datasets:
                logger.error(f"知识库 '{knowledge_base_name}' 不存在")
                return None

            dataset = datasets[0]
            dataset_id = dataset.id

            # 获取系统提示词配置
            from src.config import get_config
            config = get_config()
            kb_config = config.get_kb_config(knowledge_base_name)
            system_prompt = ""

            if kb_config and 'system_prompt' in kb_config:
                system_prompt = kb_config['system_prompt']
                logger.info(f"使用自定义系统提示词 (长度: {len(system_prompt)})")

            # 查找现有的聊天助手
            chat_name = f"PolicyChat_{knowledge_base_name}"
            existing_chats = self.rag.list_chats(name=chat_name)

            if existing_chats:
                chat_assistant = existing_chats[0]
                logger.info(f"找到现有聊天助手: {chat_name}")

                # 如果有新的系统提示词，更新聊天助手
                if system_prompt and system_prompt.strip():
                    chat_assistant.update({
                        "prompt": {
                            "prompt": system_prompt,
                            "top_n": 8,
                            "similarity_threshold": 0.2,
                            "variables": [
                                {"key": "knowledge", "optional": True},
                                {"key": "question", "optional": False}
                            ]
                        }
                    })
                    logger.info("更新聊天助手的系统提示词")
            else:
                # 创建新的聊天助手
                logger.info(f"创建新聊天助手: {chat_name}")

                # 构建提示词配置
                prompt_config = None
                if system_prompt and system_prompt.strip():
                    from ragflow_sdk import Chat
                    prompt_config = Chat.Prompt(
                        prompt=system_prompt,
                        top_n=8,
                        similarity_threshold=0.2,
                        keywords_similarity_weight=0.7,
                        variables=[
                            {"key": "knowledge", "optional": True},
                            {"key": "question", "optional": False}
                        ]
                    )

                chat_assistant = self.rag.create_chat(
                    name=chat_name,
                    dataset_ids=[dataset_id],
                    prompt=prompt_config
                )
                logger.info(f"聊天助手创建成功: {chat_assistant.id}")

            # 缓存聊天助手
            self._chat_cache[knowledge_base_name] = chat_assistant
            return chat_assistant

        except Exception as e:
            logger.error(f"获取或创建聊天助手失败: {e}")
            return None

    def _get_or_create_session(self, chat_assistant):
        """获取或创建会话
        
        📦 API: Python SDK - Chat.list_sessions() / create_session()
        参考: https://ragflow.com.cn/docs/python_api_reference#session-management

        Args:
            chat_assistant: 聊天助手对象

        Returns:
            会话对象
        """
        try:
            # 获取现有会话
            sessions = chat_assistant.list_sessions(page_size=1)

            if sessions:
                session = sessions[0]
                logger.debug(f"使用现有会话: {session.id}")
            else:
                # 创建新会话
                session = chat_assistant.create_session("Policy Assistant Session")
                logger.debug(f"创建新会话: {session.id}")

            return session

        except Exception as e:
            logger.error(f"获取或创建会话失败: {e}")
            return None



    def check_health(self) -> bool:
        """
        检查RAGFlow服务健康状态
        
        📦 API: Python SDK - RAGFlow.list_datasets()
        参考: https://ragflow.com.cn/docs/python_api_reference#list-datasets

        通过尝试列出数据集来验证SDK连接
        """
        try:
            # 尝试列出数据集以验证连接
            self.rag.list_datasets(page=1, page_size=1)
            return True
        except Exception as e:
            logger.debug(f"RAGFlow health check failed: {e}")
            return False

    def upload_document(self, file_path: str, file_name: str,
                       knowledge_base_name: Optional[str] = None) -> Optional[str]:
        """
        上传文档到RAGFlow
        
        📦 API: Python SDK - DataSet.upload_documents()
        参考: https://ragflow.com.cn/docs/python_api_reference#upload-documents

        Args:
            file_path: 本地文件路径
            file_name: 文件名
            knowledge_base_name: 知识库名称（如不指定则从config.ini读取）

        Returns:
            文档ID，失败返回None
        """
        try:
            # 如果未指定知识库名称，从配置读取
            if knowledge_base_name is None:
                knowledge_base_name = config.default_kb_name

            # 获取数据集
            dataset = self._get_or_create_dataset(knowledge_base_name)
            if not dataset:
                logger.error(f"Knowledge base '{knowledge_base_name}' not found")
                return None

            # 读取文件内容
            with open(file_path, 'rb') as f:
                file_content = f.read()

            logger.info(f"上传文档到知识库 '{knowledge_base_name}': {file_name}")

            # 使用SDK上传文档
            documents = dataset.upload_documents([{
                "display_name": file_name,
                "blob": file_content
            }])

            if documents:
                doc_id = documents[0].id
                logger.info(f"✅ 文档上传成功: {file_name} -> {doc_id}")
                return doc_id

            logger.warning(f"文档上传未返回文档ID")
            return None

        except FileNotFoundError:
            logger.error(f"文件不存在: {file_path}")
            return None
        except Exception as e:
            logger.error(f"上传文档失败: {type(e).__name__}: {e}")
            return None

    def delete_document(self, doc_id: str, kb_name: Optional[str] = None) -> bool:
        """
        删除RAGFlow中的文档
        
        📦 API: Python SDK - DataSet.delete_documents()
        参考: https://ragflow.com.cn/docs/python_api_reference#delete-documents

        Args:
            doc_id: 文档ID
            kb_name: 知识库名称（可选）

        Returns:
            True表示删除成功
        """
        try:
            kb_name = kb_name or config.default_kb_name
            dataset = self._get_or_create_dataset(kb_name)
            if not dataset:
                return False

            # 使用SDK删除文档
            dataset.delete_documents(ids=[doc_id])
            logger.info(f"文档删除成功: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False

    def search(self, query: str, knowledge_base_name: str = "policy_demo_kb",
               top_k: Optional[int] = None, score_threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        在RAGFlow中进行语义搜索
        
        📦 API: Python SDK - DataSet.retrieve()
        参考: https://ragflow.com.cn/docs/python_api_reference#retrieve

        Args:
            query: 搜索查询
            knowledge_base_name: 知识库名称
            top_k: 返回结果数
            score_threshold: 相似度阈值

        Returns:
            搜索结果列表
        """
        try:
            top_k = top_k or RAGFLOW_SEARCH_CONFIG['top_k']

            dataset = self._get_or_create_dataset(knowledge_base_name)
            if not dataset:
                return []

            # 使用SDK检索方法
            chunks = dataset.retrieve(
                question=query,
                limit=top_k
            )

            # 转换为预期格式
            results = []
            for chunk in chunks:
                results.append({
                    'content': chunk.content,
                    'document_name': getattr(chunk, 'document_name', ''),
                    'similarity': getattr(chunk, 'similarity', 0.0),
                    'chunk_id': chunk.id
                })

            logger.info(f"搜索完成: '{query}' 返回 {len(results)} 结果")
            return results

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []

    def ask(self, query: str, knowledge_base_name: str = "policy_demo_kb",
            context_limit: int = 5) -> Optional[Dict[str, Any]]:
        """
        在RAGFlow中进行问答
        
        📦 API: Python SDK - Session.ask()
        参考: https://ragflow.com.cn/docs/python_api_reference#ask-question

        Args:
            query: 问题
            knowledge_base_name: 知识库名称
            context_limit: 上下文限制

        Returns:
            问答结果
        """
        try:
            # 获取或创建聊天助手
            chat_assistant = self._get_or_create_chat_assistant(knowledge_base_name)
            if not chat_assistant:
                logger.error(f"无法获取知识库 '{knowledge_base_name}' 的聊天助手")
                return None

            # 获取或创建会话
            session = self._get_or_create_session(chat_assistant)
            if not session:
                logger.error(f"无法创建聊天会话")
                return None

            # 进行问答
            logger.debug(f"向聊天助手提问: {query}")
            message = session.ask(question=query, stream=False)

            if message:
                result = {
                    'answer': message.content,
                    'message_id': message.id,
                    'references': []
                }

                # 处理引用文档
                if hasattr(message, 'reference') and message.reference:
                    for ref in message.reference:
                        if hasattr(ref, 'content'):
                            result['references'].append({
                                'content': ref.content,
                                'document_name': getattr(ref, 'document_name', ''),
                                'similarity': getattr(ref, 'similarity', 0.0)
                            })

                logger.info(f"问答完成: '{query}' -> {len(result['answer'])} 字符")
                return result
            else:
                logger.error("聊天助手返回空响应")
                return None

        except Exception as e:
            logger.error(f"问答异常: {e}")
            return None

    def get_documents(self, knowledge_base_name: str = "policy_demo_kb") -> List[Dict[str, Any]]:
        """
        获取知识库中的文档列表
        
        📦 API: Python SDK - DataSet.list_documents()
        参考: https://ragflow.com.cn/docs/python_api_reference#list-documents

        Args:
            knowledge_base_name: 知识库名称

        Returns:
            文档列表，包含完整的文档元数据
        """
        try:
            dataset = self._get_or_create_dataset(knowledge_base_name)
            if not dataset:
                return []

            # 使用SDK列出文档
            docs = dataset.list_documents(page=1, page_size=100)

            # 转换为预期格式，提取所有可用字段
            documents = []
            for doc in docs:
                doc_info = {
                    'id': doc.id,
                    'name': doc.name,
                    'size': getattr(doc, 'size', 0),
                    'status': getattr(doc, 'status', ''),
                    'create_time': getattr(doc, 'create_time', ''),
                    'update_time': getattr(doc, 'update_time', ''),
                    # 分块和token信息 - 使用正确的属性名
                    'chunk_num': getattr(doc, 'chunk_count', 0),  # SDK用chunk_count
                    'token_num': getattr(doc, 'token_count', 0),  # SDK用token_count
                    # 解析器信息
                    'parser_id': getattr(doc, 'parser_id', ''),
                    'parser_config': getattr(doc, 'parser_config', {}),
                    # 处理进度
                    'progress': getattr(doc, 'progress', 0),
                    'progress_msg': getattr(doc, 'progress_msg', ''),
                    # 其他元数据
                    'type': getattr(doc, 'type', ''),
                    'location': getattr(doc, 'location', ''),
                }
                documents.append(doc_info)

            logger.info(f"获取文档列表成功: {len(documents)} 个文档")
            return documents

        except Exception as e:
            logger.error(f"获取文档列表失败: {e}")
            return []

    def get_document_content(self, doc_id: str, kb_name: Optional[str] = None) -> Optional[str]:
        """
        获取文档的完整内容
        
        📦 API: Python SDK - Document.download() / Document.list_chunks()
        参考: https://ragflow.com.cn/docs/python_api_reference#download-a-document

        Args:
            doc_id: 文档ID
            kb_name: 知识库名称

        Returns:
            文档内容，失败返回None
        """
        try:
            kb_name = kb_name or config.default_kb_name
            dataset = self._get_or_create_dataset(kb_name)
            if not dataset:
                return None

            # 获取文档
            docs = dataset.list_documents(id=doc_id)
            if not docs:
                logger.warning(f"Document not found: {doc_id}")
                return None

            doc = docs[0]
            doc_name = getattr(doc, 'name', '') or ''

            # 尝试下载文档内容并解析
            try:
                content_bytes = doc.download()
                if content_bytes:
                    # 根据文件类型进行不同的处理
                    if doc_name.lower().endswith('.pdf'):
                        # PDF文件处理
                        return self._extract_pdf_content(content_bytes, doc_name)
                    elif doc_name.lower().endswith(('.txt', '.md', '.json', '.xml', '.csv')):
                        # 文本文件处理
                        return self._extract_text_content(content_bytes)
                    else:
                        # 其他文件类型，尝试文本提取
                        return self._extract_text_content(content_bytes)
            except Exception as e:
                logger.warning(f"文档下载或解析失败 (doc_id: {doc_id}): {e}")

            # 回退：聚合块内容
            chunks = doc.list_chunks()
            if chunks:
                content = "\n\n".join([chunk.content for chunk in chunks])
                logger.info(f"Retrieved document content from chunks: {doc_id}")
                return content

            return None
        except Exception as e:
            logger.error(f"获取文档内容失败 (doc_id: {doc_id}): {e}")
            return None

    def _extract_pdf_content(self, content_bytes: bytes, doc_name: str) -> str:
        """
        从PDF字节内容提取文本
        
        Args:
            content_bytes: PDF文件的二进制内容
            doc_name: 文档名称（用于日志）
            
        Returns:
            提取的文本内容
        """
        import warnings
        import logging
        
        # 抑制PDF解析警告
        warnings.filterwarnings('ignore', message='.*FontBBox.*')
        warnings.filterwarnings('ignore', message='.*cannot be parsed.*')
        
        # 抑制PDF库的日志输出
        logging.getLogger('pdfplumber').setLevel(logging.ERROR)
        logging.getLogger('pdfminer').setLevel(logging.ERROR)
        logging.getLogger('pdfminer.layout').setLevel(logging.ERROR)
        logging.getLogger('pdfminer.converter').setLevel(logging.ERROR)
        
        try:
            import io
            
            # 尝试使用pdfplumber（推荐，对表格和布局支持更好）
            try:
                import pdfplumber
                with pdfplumber.open(io.BytesIO(content_bytes)) as pdf:
                    text_parts = []
                    for page_num, page in enumerate(pdf.pages, 1):
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(f"第{page_num}页:\n{page_text}")
                    
                    if text_parts:
                        logger.info(f"PDF内容提取成功 (pdfplumber): {doc_name}, {len(text_parts)}页")
                        return "\n\n".join(text_parts)
                        
            except ImportError:
                logger.warning("pdfplumber未安装，尝试pypdf")
            except Exception as e:
                logger.warning(f"pdfplumber提取失败: {e}，尝试pypdf")
            
            # 回退到pypdf
            try:
                import pypdf
                pdf_reader = pypdf.PdfReader(io.BytesIO(content_bytes))
                text_parts = []
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text_parts.append(f"第{page_num}页:\n{page_text}")
                
                if text_parts:
                    logger.info(f"PDF内容提取成功 (pypdf): {doc_name}, {len(text_parts)}页")
                    return "\n\n".join(text_parts)
                    
            except ImportError:
                logger.error("PDF处理库未安装，请安装：pip install pdfplumber pypdf")
            except Exception as e:
                logger.error(f"pypdf提取失败: {e}")
            
            # 如果都失败了，返回提示信息
            return f"⚠️ PDF文件解析失败 ({doc_name})\n\n这可能是因为：\n1. PDF文件是扫描版（图片），需要OCR识别\n2. PDF文件有密码保护\n3. PDF文件格式不兼容\n\n建议：在RAGFlow Web界面查看解析后的分块内容"
                
        except Exception as e:
            logger.error(f"PDF内容提取异常: {e}")
            return f"❌ PDF文件处理异常: {str(e)}"

    def _extract_text_content(self, content_bytes: bytes) -> str:
        """
        从文本文件字节内容提取文本
        
        Args:
            content_bytes: 文件的二进制内容
            
        Returns:
            提取的文本内容
        """
        try:
            # 尝试检测编码
            import chardet
            detected = chardet.detect(content_bytes)
            encoding = detected.get('encoding', 'utf-8')
            confidence = detected.get('confidence', 0)
            
            logger.debug(f"检测到编码: {encoding} (置信度: {confidence:.2f})")
            
            # 按优先级尝试不同编码
            encodings_to_try = [
                encoding,  # 检测到的编码
                'utf-8',
                'utf-8-sig',  # UTF-8 with BOM
                'gbk',
                'gb2312', 
                'big5',
                'iso-8859-1',
                'cp1252'
            ]
            
            for enc in encodings_to_try:
                if not enc:
                    continue
                try:
                    text = content_bytes.decode(enc)
                    logger.info(f"文本内容提取成功，使用编码: {enc}")
                    return text
                except (UnicodeDecodeError, LookupError):
                    continue
            
            # 最后尝试忽略错误
            text = content_bytes.decode('utf-8', errors='ignore')
            logger.warning("使用UTF-8编码忽略错误模式")
            return text
                
        except Exception as e:
            logger.error(f"文本内容提取异常: {e}")
            return f"❌ 文件内容提取失败: {str(e)}"

    def download_document(self, doc_id: str, kb_name: Optional[str] = None) -> Optional[bytes]:
        """
        下载文档的原始二进制数据（用于PDF预览等）
        
        📦 API: Python SDK - Document.download()
        参考: https://ragflow.com.cn/docs/python_api_reference#download-a-document

        Args:
            doc_id: 文档ID
            kb_name: 知识库名称

        Returns:
            文档的二进制数据，如果失败返回None
        """
        try:
            kb_name = kb_name or config.default_kb_name
            dataset = self._get_or_create_dataset(kb_name)
            if not dataset:
                logger.warning(f"知识库 '{kb_name}' 不存在")
                return None

            # 获取文档信息
            docs = dataset.list_documents(id=doc_id)
            if not docs:
                logger.warning(f"文档 '{doc_id}' 不存在")
                return None

            doc = docs[0]
            
            # 使用SDK下载文档
            try:
                # 尝试获取文档的二进制数据
                binary_data = doc.download()
                if binary_data:
                    logger.info(f"成功下载文档 {doc_id}，大小: {len(binary_data)} 字节")
                    return binary_data
            except Exception as e:
                logger.warning(f"SDK下载失败: {e}")
            
            # 如果SDK方法失败，尝试其他方法
            logger.warning(f"无法下载文档 {doc_id} 的原始二进制数据")
            return None

        except Exception as e:
            logger.error(f"下载文档异常 {doc_id}: {e}")
            return None

    def get_document_chunks(self, doc_id: str, kb_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取文档的分块信息
        
        📦 API: Python SDK - Document.list_chunks()
        参考: https://ragflow.com.cn/docs/python_api_reference#list-chunks

        Args:
            doc_id: 文档ID
            kb_name: 知识库名称

        Returns:
            分块信息列表
        """
        try:
            kb_name = kb_name or config.default_kb_name
            dataset = self._get_or_create_dataset(kb_name)
            if not dataset:
                return []

            docs = dataset.list_documents(id=doc_id)
            if not docs:
                return []

            doc = docs[0]
            chunks = doc.list_chunks()

            # 转换为预期格式
            chunk_list = []
            for chunk in chunks:
                chunk_list.append({
                    'id': chunk.id,
                    'content': chunk.content,
                    'important_keywords': getattr(chunk, 'important_keywords', []),
                    'available': getattr(chunk, 'available', True)
                })

            logger.info(f"Retrieved {len(chunk_list)} chunks for document {doc_id}")
            return chunk_list
        except Exception as e:
            logger.error(f"获取文档分块失败 (doc_id: {doc_id}): {e}")
            return []





    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        # SDK不需要显式关闭
        pass


# 全局客户端实例
_ragflow_client: Optional[RAGFlowClient] = None


def get_ragflow_client() -> RAGFlowClient:
    """获取全局RAGFlow客户端实例"""
    global _ragflow_client
    if _ragflow_client is None:
        _ragflow_client = RAGFlowClient()
    return _ragflow_client
