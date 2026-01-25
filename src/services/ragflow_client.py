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
- 错误处理和重试机制

依赖：
- src.config.ConfigLoader - RAGFlow服务配置
- src.services.api_utils - HTTP请求工具

配置项（来自config.ini的[RAGFLOW]部分）：
- host: RAGFlow服务主机地址
- port: RAGFlow服务端口
- timeout: API调用超时时间
- retry_times: 重试次数
- retry_delay: 重试延迟

使用示例：
    from src.services.ragflow_client import get_ragflow_client

    client = get_ragflow_client()

    # 检查连接
    if client.check_health():
        print("RAGFlow服务正常")

    # 上传文档
    doc_id = client.upload_document("policy.pdf", content)

    # 搜索
    results = client.search("政策内容", top_k=10)
"""
import logging
import requests
from typing import Optional, Dict, List, Any

# ===== 导入新的配置系统 =====
from src.config import get_config
from src.services.api_utils import APIClient, APIError

# ===== 获取RAGFlow配置 =====
config = get_config()

RAGFLOW_BASE_URL = config.ragflow_base_url  # RAGFlow服务URL（http://host:port）
RAGFLOW_API_KEY = config.ragflow_api_key  # RAGFlow API密钥（如果需要认证）
RAGFLOW_TIMEOUT = config.ragflow_timeout  # API调用超时时间（秒）
RAGFLOW_RETRY_TIMES = config.ragflow_retry_times  # 失败重试次数
RAGFLOW_RETRY_DELAY = config.ragflow_retry_delay  # 重试延迟（秒）
RAGFLOW_SEARCH_CONFIG = config.ragflow_search_config  # 搜索配置（top_k, threshold等）
RAGFLOW_QA_CONFIG = config.ragflow_qa_config  # 问答配置（max_tokens, temperature等）

# RAGFlow API端点定义
RAGFLOW_ENDPOINTS = {
    'health': '/api/health',
    'upload': '/api/upload',
    'delete': '/api/delete',
    'search': '/api/search',
    'qa': '/api/qa',
    'documents': '/api/v1/datasets/{dataset_id}/documents',  # 文档列表 - 正确的端点
    'datasets': '/api/v1/datasets',  # 知识库列表 - 正确的端点
    'retrieval': '/api/v1/retrieval'  # 检索端点 - 正确的端点
}

# RAGFlow API请求头（包含认证信息）
def _get_ragflow_headers() -> dict:
    """
    生成RAGFlow请求头，包含API Key认证信息

    如果配置了RAGFLOW_API_KEY，将通过Authorization头发送
    格式：Authorization: Bearer {api_key}
    """
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    # 如果配置了API Key，添加认证信息
    if RAGFLOW_API_KEY:
        headers['Authorization'] = f'Bearer {RAGFLOW_API_KEY}'

    return headers

logger = logging.getLogger(__name__)


class RAGFlowError(APIError):
    """RAGFlow API错误"""
    pass


class RAGFlowClient:
    """RAGFlow客户端"""

    def __init__(self, auto_configure: bool = True):
        """初始化RAGFlow客户端
        
        Args:
            auto_configure: 是否在初始化时自动应用配置参数
        """
        self.client = APIClient(
            base_url=RAGFLOW_BASE_URL,
            timeout=RAGFLOW_TIMEOUT,
            retry_times=RAGFLOW_RETRY_TIMES
        )
        # 生成包含认证信息的请求头
        self.headers = _get_ragflow_headers()

        # 如果配置了API Key，记录日志
        if RAGFLOW_API_KEY:
            logger.info("RAGFlow客户端: 使用API Key认证")

        self._check_connection()
        
        # 自动应用配置参数
        if auto_configure:
            self._apply_configuration()

    def _check_connection(self):
        """检查与RAGFlow的连接"""
        try:
            # 尝试连接到基础 URL，检查服务是否在线
            # 注：不同版本的 RAGFlow 可能有不同的 API 路径
            response = requests.get(RAGFLOW_BASE_URL, timeout=5)
            # 只要能连接上服务，就认为可用（即使返回 404）
            logger.info(f"RAGFlow服务连接成功 (HTTP {response.status_code})")
        except requests.exceptions.ConnectionError:
            logger.warning(f"RAGFlow服务离线或地址错误: {RAGFLOW_BASE_URL}")
        except requests.exceptions.Timeout:
            logger.warning(f"RAGFlow服务连接超时")
        except Exception as e:
            logger.warning(f"RAGFlow服务连接检查失败: {e}")

    def _apply_configuration(self):
        """应用配置文件中的RAGFlow参数"""
        try:
            from src.config import get_config
            
            config = get_config()
            
            # 获取默认知识库配置
            kb_name = config.default_kb_name
            kb_config = config.get_kb_config(kb_name)
            
            if not kb_config:
                logger.warning(f"⚠️ 无法加载知识库 '{kb_name}' 的配置")
                return
            
            logger.info(f"开始应用知识库 '{kb_name}' 的配置...")
            
            # 1. 首先检查知识库是否存在
            if not self._check_knowledge_base_exists(kb_config['kb_name']):
                logger.warning(f"⚠️ 知识库 '{kb_config['kb_name']}' 不存在")
                logger.info(f"💡 请在RAGFlow Web界面 ({RAGFLOW_BASE_URL}) 中创建知识库")
                logger.warning("RAGFlow配置可能未完全生效")
                return
            
            logger.info(f"📋 应用配置: {len(kb_config)} 个参数")
            
            # 2. 应用知识库配置
            success = self._update_knowledge_base_config(kb_config['kb_name'], kb_config)
            
            if success:
                logger.info("✅ 知识库配置应用成功")
                logger.info(f"🏛️ 配置详情: 分块大小={kb_config.get('chunk_size')}, "
                          f"相似度阈值={kb_config.get('similarity_threshold')}, "
                          f"图谱检索={kb_config.get('graph_retrieval')}")
            else:
                logger.warning("⚠️ 知识库配置可能未完全生效")
                
        except Exception as e:
            logger.warning(f"自动配置失败: {e}")
            logger.warning("RAGFlow配置可能未完全生效")

    def _check_knowledge_base_exists(self, kb_name: str) -> bool:
        """
        检查知识库是否存在
        
        Args:
            kb_name: 知识库名称
            
        Returns:
            bool: 知识库是否存在
        """
        try:
            # 使用正确的API端点获取知识库列表
            endpoint = "/api/v1/datasets"
            
            response = self.client.get(endpoint, headers=self.headers)
            
            if isinstance(response, dict) and response.get('code') == 0:
                datasets = response.get('data', [])
                if isinstance(datasets, list):
                    # 检查知识库名称匹配
                    kb_names = []
                    kb_ids = []
                    
                    for dataset in datasets:
                        name = dataset.get('name', '')
                        id_val = dataset.get('id', '')
                        kb_names.append(name)
                        kb_ids.append(id_val)
                        
                        # 检查名称匹配（支持名称或ID匹配）
                        if name == kb_name or id_val == kb_name:
                            logger.info(f"✅ 知识库 '{kb_name}' 存在")
                            logger.debug(f"知识库详情: {dataset}")
                            return True
                    
                    logger.info(f"📋 可用知识库: {kb_names}")
                    logger.warning(f"❌ 知识库 '{kb_name}' 不存在")
                    return False
                    
            logger.warning(f"❌ 获取知识库列表失败: {response}")
            return False
            
        except Exception as e:
            logger.warning(f"知识库存在性检查失败: {e}")
            return False
            logger.warning("RAGFlow配置可能未完全生效")
    
    def _update_knowledge_base_config(self, kb_name: str, config_params: dict) -> bool:
        """更新知识库配置
        
        Args:
            kb_name: 知识库名称
            config_params: 配置参数字典
            
        Returns:
            更新是否成功
        """
        try:
            logger.debug(f"开始更新知识库 '{kb_name}' 的配置...")
            
            # 首先获取知识库ID
            kb_id = self._get_knowledge_base_id(kb_name)
            if not kb_id:
                logger.error(f"无法获取知识库 '{kb_name}' 的ID")
                return False
            
            # 根据官方API文档构建正确的更新请求
            endpoint = f"/api/v1/datasets/{kb_id}"
            
            # 构建符合API文档的配置数据
            update_data = self._build_dataset_update_payload(config_params)
            
            logger.debug(f"更新数据: {update_data}")
            logger.info(f"向端点 {endpoint} 发送配置更新...")
            
            # 使用PUT方法更新数据集配置
            response = self.client.put(
                endpoint,
                headers=self.headers,
                json_data=update_data
            )
            
            # 检查响应
            if isinstance(response, dict):
                if response.get('code') == 0:
                    logger.info(f"✅ 知识库配置更新成功: {kb_name}")
                    return True
                elif response.get('code') == 101:
                    logger.error(f"❌ 配置参数错误: {response.get('message')}")
                    return False
                else:
                    logger.warning(f"⚠️ 更新响应: {response}")
                    return False
            else:
                logger.warning(f"⚠️ 意外的响应格式: {response}")
                return False
                
        except Exception as e:
            logger.error(f"知识库配置更新异常: {e}")
            return False
            
    def _get_knowledge_base_id(self, kb_name: str) -> str:
        """获取知识库ID
        
        Args:
            kb_name: 知识库名称
            
        Returns:
            知识库ID，如果未找到返回None
        """
        try:
            response = self.client.get("/api/v1/datasets", headers=self.headers)
            
            if isinstance(response, dict) and response.get('code') == 0:
                for dataset in response.get('data', []):
                    if dataset.get('name') == kb_name:
                        return dataset.get('id')
            
            return None
        except Exception as e:
            logger.error(f"获取知识库ID失败: {e}")
            return None
            
    def _build_dataset_update_payload(self, config_params: dict) -> dict:
        """根据API文档构建数据集更新载荷
        
        Args:
            config_params: 配置参数
            
        Returns:
            符合API文档格式的更新数据
        """
        # 基础更新数据
        update_data = {}
        
        # 设置分块方法
        chunk_method = "naive"  # 默认使用General方法
        if config_params.get("pdf_parser") == "deepdoc":
            chunk_method = "naive"  # deepdoc对应General
        elif config_params.get("pdf_parser") == "laws":
            chunk_method = "laws"
            
        update_data["chunk_method"] = chunk_method
        
        # 构建parser_config根据chunk_method
        parser_config = {}
        
        if chunk_method == "naive":
            # General方法的parser_config
            parser_config = {
                "chunk_token_num": config_params.get("chunk_size", 800),
                "auto_keywords": 1 if config_params.get("auto_keywords", True) else 0,
                "auto_questions": 0,  # 不启用自动问题生成
                "delimiter": "\\n",
                "html4excel": False,
                "layout_recognize": "deepdoc",  # 使用deepdoc布局识别
                "task_page_size": 12,
                "raptor": {
                    "use_raptor": config_params.get("graph_retrieval", True),
                    "max_cluster": config_params.get("max_clusters", 50),
                    "max_token": config_params.get("max_tokens", 256),
                    "threshold": config_params.get("similarity_threshold", 0.3),
                    "random_seed": config_params.get("random_seed", 42)
                },
                "graphrag": {
                    "use_graphrag": config_params.get("graph_retrieval", True),
                    "entity_types": ["organization", "person", "geo", "event", "category"],
                    "method": config_params.get("retrieval_mode", "general"),
                    "resolution": config_params.get("entity_normalization", True)
                }
            }
            
        elif chunk_method == "laws":
            # Laws方法的parser_config (只有raptor配置)
            parser_config = {
                "raptor": {
                    "use_raptor": config_params.get("graph_retrieval", True),
                    "max_cluster": config_params.get("max_clusters", 50), 
                    "max_token": config_params.get("max_tokens", 256),
                    "threshold": config_params.get("similarity_threshold", 0.3),
                    "random_seed": config_params.get("random_seed", 42)
                }
            }
        
        update_data["parser_config"] = parser_config
        
        return update_data

    def check_health(self) -> bool:
        """
        检查RAGFlow服务健康状态

        只要能连接到服务就认为健康（某些RAGFlow版本的API路径可能不同）
        """
        try:
            response = requests.get(RAGFLOW_BASE_URL, timeout=5)
            # 服务在线即为健康（HTTP 连接成功）
            return True
        except Exception as e:
            logger.debug(f"RAGFlow 健康检查失败: {e}")
            return False

    def upload_document(self, file_path: str, file_name: str,
                       knowledge_base_name: Optional[str] = None) -> Optional[str]:
        """
        上传文档到RAGFlow

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
            
            with open(file_path, 'rb') as f:
                files = {
                    'file': (file_name, f, self._get_file_mimetype(file_name))
                }

                # 构建查询字符串参数
                endpoint = f"{RAGFLOW_ENDPOINTS['upload']}?knowledge_base={knowledge_base_name}"
                
                logger.info(f"上传文档到知识库 '{knowledge_base_name}': {file_name}")

                response = self.client.post(
                    endpoint,
                    headers=self.headers,
                    files=files
                )
                
                logger.debug(f"上传响应: {response}")

                # 解析响应获取文档ID
                if isinstance(response, dict):
                    # 尝试多种可能的响应格式
                    if 'doc_id' in response:
                        logger.info(f"✅ 文档上传成功: {file_name} -> {response['doc_id']}")
                        return response['doc_id']
                    elif 'id' in response:
                        logger.info(f"✅ 文档上传成功: {file_name} -> {response['id']}")
                        return response['id']
                    elif 'data' in response and isinstance(response['data'], dict):
                        data = response['data']
                        if 'doc_id' in data:
                            logger.info(f"✅ 文档上传成功: {file_name} -> {data['doc_id']}")
                            return data['doc_id']
                        elif 'id' in data:
                            logger.info(f"✅ 文档上传成功: {file_name} -> {data['id']}")
                            return data['id']
                
                logger.warning(f"文档上传响应格式异常: {response}")
                return None

        except APIError as e:
            logger.error(f"上传文档失败 (APIError): {e}")
            return None
        except FileNotFoundError as e:
            logger.error(f"文件不存在: {file_path}")
            return None
        except Exception as e:
            logger.error(f"上传文档异常: {type(e).__name__}: {e}")
            return None

    def delete_document(self, doc_id: str) -> bool:
        """
        删除RAGFlow中的文档

        Args:
            doc_id: 文档ID

        Returns:
            True表示删除成功
        """
        try:
            endpoint = RAGFLOW_ENDPOINTS['delete'].replace('{id}', doc_id)
            response = self.client.delete(endpoint, headers=self.headers)
            logger.info(f"文档删除成功: {doc_id}")
            return True
        except APIError as e:
            logger.error(f"删除文档失败: {e}")
            return False

    def search(self, query: str, knowledge_base_name: str = "policy_demo_kb",
               top_k: Optional[int] = None, score_threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        在RAGFlow中进行语义搜索

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
            score_threshold = score_threshold or RAGFLOW_SEARCH_CONFIG['score_threshold']

            endpoint = RAGFLOW_ENDPOINTS['search']
            data = {
                'query': query,
                'knowledge_base': knowledge_base_name,
                'top_k': top_k,
                'score_threshold': score_threshold,
                'search_type': RAGFLOW_SEARCH_CONFIG['search_type']
            }

            response = self.client.post(endpoint, headers=self.headers, json_data=data)

            # 处理响应
            results = response.get('results', []) or response.get('data', [])
            logger.info(f"搜索完成: '{query}' 返回 {len(results)} 结果")
            return results

        except APIError as e:
            logger.error(f"搜索失败: {e}")
            return []
        except Exception as e:
            logger.error(f"搜索异常: {e}")
            return []

    def ask(self, query: str, knowledge_base_name: str = "policy_demo_kb",
            context_limit: int = 5) -> Optional[Dict[str, Any]]:
        """
        在RAGFlow中进行问答

        Args:
            query: 问题
            knowledge_base_name: 知识库名称
            context_limit: 上下文限制

        Returns:
            问答结果
        """
        try:
            endpoint = RAGFLOW_ENDPOINTS['ask']
            data = {
                'question': query,
                'knowledge_base': knowledge_base_name,
                'context_limit': context_limit,
                'max_tokens': RAGFLOW_QA_CONFIG['max_tokens'],
                'temperature': RAGFLOW_QA_CONFIG['temperature']
            }

            response = self.client.post(endpoint, headers=self.headers, json_data=data)
            logger.info(f"问答完成: '{query}'")
            return response

        except APIError as e:
            logger.error(f"问答失败: {e}")
            return None
        except Exception as e:
            logger.error(f"问答异常: {e}")
            return None

    def get_documents(self, knowledge_base_name: str = "policy_demo_kb") -> List[Dict[str, Any]]:
        """
        获取知识库中的文档列表

        Args:
            knowledge_base_name: 知识库名称

        Returns:
            文档列表
        """
        try:
            # 首先获取知识库ID
            dataset_id = self._get_knowledge_base_id(knowledge_base_name)
            if not dataset_id:
                logger.error(f"未找到知识库: {knowledge_base_name}")
                return []
            
            # 使用正确的API endpoint格式
            endpoint = RAGFLOW_ENDPOINTS['documents'].format(dataset_id=dataset_id)
            
            # 添加分页参数
            params = {
                'page': 1,
                'page_size': 30,
                'orderby': 'create_time',
                'desc': True
            }
            
            logger.debug(f"请求文档列表: {endpoint} 参数: {params}")
            response = self.client.get(endpoint, headers=self.headers, params=params)

            if isinstance(response, dict):
                if response.get('code') == 0:
                    # 根据API文档，文档在data.docs中
                    documents = response.get('data', {}).get('docs', [])
                    logger.info(f"获取文档列表成功: {len(documents)} 个文档")
                    return documents
                else:
                    logger.error(f"API错误: {response.get('message', 'Unknown error')}")
                    return []
            else:
                logger.error(f"意外的响应格式: {response}")
                return []

        except APIError as e:
            logger.error(f"获取文档列表失败: {e}")
            return []
        except Exception as e:
            logger.error(f"获取文档列表异常: {e}")
            return []

    def get_document_content(self, doc_id: str) -> Optional[str]:
        """
        获取文档的完整内容

        Args:
            doc_id: 文档ID

        Returns:
            文档内容，失败返回None
        """
        try:
            # RAGFlow可能的文档内容端点
            possible_endpoints = [
                f"/api/v1/documents/{doc_id}/content",
                f"/api/v1/documents/{doc_id}",
                f"/api/documents/{doc_id}/content",
                f"/v1/documents/{doc_id}/content",
            ]
            
            for endpoint in possible_endpoints:
                try:
                    response = self.client.get(endpoint, headers=self.headers)
                    
                    if isinstance(response, dict):
                        # 尝试从不同的响应字段获取内容
                        content = (response.get('content') or 
                                 response.get('data', {}).get('content') or
                                 response.get('text'))
                        
                        if content:
                            logger.info(f"成功获取文档内容 (doc_id: {doc_id})")
                            return content
                            
                except APIError as e:
                    if "404" not in str(e):
                        logger.debug(f"端点 {endpoint} 失败: {e}")
                    continue
            
            # 如果所有直接端点都失败，尝试通过搜索获取内容
            logger.info(f"尝试通过搜索获取文档内容: {doc_id}")
            search_results = self.search(f"doc_id:{doc_id}", top_k=50)
            
            if search_results:
                # 合并搜索结果的内容
                content_parts = []
                for result in search_results:
                    if result.get('content'):
                        content_parts.append(result['content'])
                
                if content_parts:
                    return "\n\n".join(content_parts)
            
            logger.warning(f"无法获取文档内容: {doc_id}")
            return None

        except Exception as e:
            logger.error(f"获取文档内容失败 (doc_id: {doc_id}): {e}")
            return None

    def get_document_chunks(self, doc_id: str) -> List[Dict[str, Any]]:
        """
        获取文档的分块信息

        Args:
            doc_id: 文档ID

        Returns:
            分块信息列表
        """
        try:
            # RAGFlow可能的分块端点
            possible_endpoints = [
                f"/api/v1/documents/{doc_id}/chunks",
                f"/api/v1/documents/{doc_id}/segments",
                f"/api/documents/{doc_id}/chunks",
                f"/v1/documents/{doc_id}/chunks",
            ]
            
            for endpoint in possible_endpoints:
                try:
                    response = self.client.get(endpoint, headers=self.headers)
                    
                    if isinstance(response, dict):
                        chunks = (response.get('chunks') or 
                                response.get('segments') or
                                response.get('data', []))
                        
                        if chunks:
                            logger.info(f"成功获取文档分块 (doc_id: {doc_id}): {len(chunks)} 块")
                            return chunks
                            
                except APIError as e:
                    if "404" not in str(e):
                        logger.debug(f"端点 {endpoint} 失败: {e}")
                    continue
            
            logger.warning(f"无法获取文档分块: {doc_id}")
            return []

        except Exception as e:
            logger.error(f"获取文档分块失败 (doc_id: {doc_id}): {e}")
            return []

    def configure_knowledge_base(self, kb_name: str = None) -> bool:
        """手动配置知识库
        
        Args:
            kb_name: 知识库名称，默认使用配置文件中的值
            
        Returns:
            配置是否成功
        """
        try:
            from src.config import get_config
            
            config = get_config()
            
            if kb_name is None:
                kb_name = config.default_kb_name
            
            # 获取配置参数
            kb_config = config.ragflow_document_config
            advanced_config = config.ragflow_advanced_config
            full_config = {**kb_config, **advanced_config}
            
            logger.info(f"手动配置知识库: {kb_name}")
            
            return self._update_knowledge_base_config(kb_name, full_config)
            
        except Exception as e:
            logger.error(f"手动配置知识库失败: {e}")
            return False

    def get_knowledge_base_config(self, kb_name: str = None) -> dict:
        """获取知识库当前配置
        
        Args:
            kb_name: 知识库名称
            
        Returns:
            知识库配置字典
        """
        try:
            if kb_name is None:
                from src.config import get_config
                config = get_config()
                kb_name = config.default_kb_name
            
            # 使用正确的API端点获取知识库列表，然后找到对应的知识库
            endpoint = "/api/v1/datasets"
            
            response = self.client.get(endpoint, headers=self.headers)
            
            if isinstance(response, dict) and response.get('code') == 0:
                datasets = response.get('data', [])
                
                for dataset in datasets:
                    if dataset.get('name') == kb_name:
                        # 提取关键配置信息
                        config_info = {
                            "知识库基本信息": {
                                "名称": dataset.get('name'),
                                "ID": dataset.get('id'),
                                "状态": dataset.get('status'),
                                "语言": dataset.get('language'),
                                "分块方法": dataset.get('chunk_method'),
                                "相似度阈值": dataset.get('similarity_threshold'),
                                "向量权重": dataset.get('vector_similarity_weight'),
                                "嵌入模型": dataset.get('embedding_model'),
                                "文档数量": dataset.get('document_count'),
                                "分块数量": dataset.get('chunk_count')
                            }
                        }
                        
                        # 提取解析器配置
                        parser_config = dataset.get('parser_config', {})
                        if parser_config:
                            config_info["解析器配置"] = {
                                "分块Token数": parser_config.get('chunk_token_num'),
                                "重叠百分比": parser_config.get('overlapped_percent'),
                                "自动关键词": parser_config.get('auto_keywords'),
                                "启用元数据": parser_config.get('enable_metadata'),
                                "布局识别": parser_config.get('layout_recognize'),
                                "表格解析": parser_config.get('mineru_table_enable'),
                                "公式解析": parser_config.get('mineru_formula_enable'),
                                "TOC提取": parser_config.get('toc_extraction')
                            }
                            
                            # 提取图谱配置
                            graphrag = parser_config.get('graphrag', {})
                            if graphrag:
                                config_info["图谱配置"] = {
                                    "使用图谱": graphrag.get('use_graphrag'),
                                    "方法": graphrag.get('method'),
                                    "实体归一化": graphrag.get('resolution'),
                                    "实体类型": graphrag.get('entity_types')
                                }
                        
                        return config_info
                
                logger.warning(f"在知识库列表中未找到 '{kb_name}'")
                return {}
                
            logger.warning(f"获取知识库列表失败: {response}")
            return {}
                
        except Exception as e:
            logger.warning(f"获取知识库配置异常: {e}")
            return {}

    @staticmethod
    def _get_file_mimetype(file_name: str) -> str:
        """根据文件名获取MIME类型"""
        mime_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel',
            '.txt': 'text/plain',
            '.md': 'text/markdown'
        }

        # 获取文件扩展名
        ext = '.' + file_name.split('.')[-1].lower()
        return mime_types.get(ext, 'application/octet-stream')

    def close(self):
        """关闭客户端"""
        self.client.close()

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


# 全局客户端实例
_ragflow_client: Optional[RAGFlowClient] = None


def get_ragflow_client() -> RAGFlowClient:
    """获取全局RAGFlow客户端实例"""
    global _ragflow_client
    if _ragflow_client is None:
        _ragflow_client = RAGFlowClient()
    return _ragflow_client
