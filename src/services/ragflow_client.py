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
from typing import Optional, Dict, List, Any

# ===== 导入新的配置系统 =====
from src.config import get_config
from src.services.api_utils import APIClient, APIError

# ===== 获取RAGFlow配置 =====
config = get_config()

RAGFLOW_BASE_URL = config.ragflow_base_url  # RAGFlow服务URL（http://host:port）
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
    'qa': '/api/qa'
}

# RAGFlow API请求头
RAGFLOW_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

logger = logging.getLogger(__name__)


class RAGFlowError(APIError):
    """RAGFlow API错误"""
    pass


class RAGFlowClient:
    """RAGFlow客户端"""

    def __init__(self):
        """初始化RAGFlow客户端"""
        self.client = APIClient(
            base_url=RAGFLOW_BASE_URL,
            timeout=RAGFLOW_TIMEOUT,
            retry_times=RAGFLOW_RETRY_TIMES
        )
        self.headers = RAGFLOW_HEADERS
        self._check_connection()

    def _check_connection(self):
        """检查与RAGFlow的连接"""
        try:
            health_endpoint = RAGFLOW_ENDPOINTS['health']
            is_healthy = self.client.check_health(health_endpoint)
            if is_healthy:
                logger.info("RAGFlow服务连接成功")
            else:
                logger.warning("RAGFlow服务可能不可用")
        except Exception as e:
            logger.warning(f"RAGFlow服务连接检查失败: {e}")

    def check_health(self) -> bool:
        """检查RAGFlow服务健康状态"""
        try:
            endpoint = RAGFLOW_ENDPOINTS['health']
            self.client.get(endpoint, headers=self.headers)
            return True
        except APIError:
            return False

    def upload_document(self, file_path: str, file_name: str,
                       knowledge_base_name: str = "policy_demo_kb") -> Optional[str]:
        """
        上传文档到RAGFlow

        Args:
            file_path: 本地文件路径
            file_name: 文件名
            knowledge_base_name: 知识库名称

        Returns:
            文档ID，失败返回None
        """
        try:
            with open(file_path, 'rb') as f:
                files = {
                    'file': (file_name, f, self._get_file_mimetype(file_name))
                }

                params = {
                    'knowledge_base': knowledge_base_name
                }

                endpoint = RAGFLOW_ENDPOINTS['upload']
                response = self.client.post(
                    endpoint,
                    headers=self.headers,
                    files=files,
                    params=params
                )

                # 解析响应获取文档ID
                if 'doc_id' in response:
                    logger.info(f"文档上传成功: {file_name} -> {response['doc_id']}")
                    return response['doc_id']
                elif 'id' in response:
                    logger.info(f"文档上传成功: {file_name} -> {response['id']}")
                    return response['id']
                else:
                    logger.warning(f"文档上传响应格式异常: {response}")
                    return None

        except APIError as e:
            logger.error(f"上传文档失败: {e}")
            return None
        except Exception as e:
            logger.error(f"上传文档异常: {e}")
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
            endpoint = RAGFLOW_ENDPOINTS['documents']
            params = {'knowledge_base': knowledge_base_name}
            response = self.client.get(endpoint, headers=self.headers, params=params)

            documents = response.get('documents', []) or response.get('data', [])
            logger.info(f"获取文档列表成功: {len(documents)} 个文档")
            return documents

        except APIError as e:
            logger.error(f"获取文档列表失败: {e}")
            return []
        except Exception as e:
            logger.error(f"获取文档列表异常: {e}")
            return []

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
