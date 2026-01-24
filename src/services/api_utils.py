"""
API工具函数
提供HTTP请求封装、响应解析、错误处理等通用功能
"""
import logging
import json
import time
from typing import Optional, Dict, Any, Union
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class APIError(Exception):
    """API错误异常"""
    pass


class APIClient:
    """通用API客户端"""

    def __init__(self, base_url: str, timeout: int = 30, retry_times: int = 3, retry_delay: int = 1):
        """
        初始化API客户端

        Args:
            base_url: API基础URL
            timeout: 请求超时时间（秒）
            retry_times: 重试次数
            retry_delay: 重试延迟（秒）
        """
        self.base_url = base_url
        self.timeout = timeout
        self.retry_times = retry_times
        self.retry_delay = retry_delay
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """创建带重试机制的Session"""
        session = requests.Session()

        # 配置重试策略
        retry_strategy = Retry(
            total=self.retry_times,
            backoff_factor=self.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _build_url(self, endpoint: str) -> str:
        """构建完整URL"""
        if endpoint.startswith(('http://', 'https://')):
            return endpoint
        return urljoin(self.base_url, endpoint.lstrip('/'))

    def get(self, endpoint: str, headers: Optional[Dict[str, str]] = None,
            params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        GET请求

        Args:
            endpoint: API端点
            headers: 请求头
            params: 查询参数

        Returns:
            响应JSON数据
        """
        url = self._build_url(endpoint)
        return self._request('GET', url, headers=headers, params=params)

    def post(self, endpoint: str, headers: Optional[Dict[str, str]] = None,
             data: Optional[Union[Dict[str, Any], str]] = None,
             json_data: Optional[Dict[str, Any]] = None,
             files: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        POST请求

        Args:
            endpoint: API端点
            headers: 请求头
            data: 表单数据
            json_data: JSON数据
            files: 文件数据

        Returns:
            响应JSON数据
        """
        url = self._build_url(endpoint)
        return self._request('POST', url, headers=headers, data=data, json_data=json_data, files=files)

    def put(self, endpoint: str, headers: Optional[Dict[str, str]] = None,
            json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """PUT请求"""
        url = self._build_url(endpoint)
        return self._request('PUT', url, headers=headers, json_data=json_data)

    def delete(self, endpoint: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """DELETE请求"""
        url = self._build_url(endpoint)
        return self._request('DELETE', url, headers=headers)

    def _request(self, method: str, url: str, headers: Optional[Dict[str, str]] = None,
                 params: Optional[Dict[str, Any]] = None,
                 data: Optional[Union[Dict[str, Any], str]] = None,
                 json_data: Optional[Dict[str, Any]] = None,
                 files: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        发送HTTP请求

        Args:
            method: HTTP方法
            url: 完整URL
            headers: 请求头
            params: 查询参数
            data: 表单数据
            json_data: JSON数据
            files: 文件数据

        Returns:
            响应JSON数据

        Raises:
            APIError: API调用失败
        """
        try:
            kwargs = {
                'headers': headers,
                'timeout': self.timeout
            }

            if params:
                kwargs['params'] = params
            if data:
                kwargs['data'] = data
            if json_data:
                kwargs['json'] = json_data
            if files:
                kwargs['files'] = files

            logger.debug(f"{method} {url} with {kwargs}")
            response = self.session.request(method, url, **kwargs)

            # 检查HTTP状态码
            if response.status_code >= 400:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise APIError(error_msg)

            # 解析响应
            return self._parse_response(response)

        except requests.exceptions.Timeout:
            error_msg = f"请求超时: {url}"
            logger.error(error_msg)
            raise APIError(error_msg)
        except requests.exceptions.ConnectionError:
            error_msg = f"连接错误: {url}"
            logger.error(error_msg)
            raise APIError(error_msg)
        except APIError:
            raise
        except Exception as e:
            error_msg = f"请求失败: {str(e)}"
            logger.error(error_msg)
            raise APIError(error_msg)

    @staticmethod
    def _parse_response(response: requests.Response) -> Dict[str, Any]:
        """解析响应"""
        # 尝试解析JSON
        try:
            return response.json()
        except json.JSONDecodeError:
            # 如果不是JSON，返回文本
            return {"text": response.text, "status_code": response.status_code}

    def check_health(self, health_endpoint: str = "/health") -> bool:
        """
        检查服务健康状态

        Args:
            health_endpoint: 健康检查端点

        Returns:
            True表示服务正常，False表示异常
        """
        try:
            response = self.get(health_endpoint)
            logger.info(f"服务健康检查成功: {self.base_url}")
            return True
        except APIError as e:
            logger.warning(f"服务健康检查失败: {e}")
            return False

    def close(self):
        """关闭会话"""
        self.session.close()

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


def retry_on_exception(max_retries: int = 3, delay: int = 1):
    """
    重试装饰器

    Args:
        max_retries: 最大重试次数
        delay: 重试延迟（秒）
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except APIError as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(f"调用失败，{delay}秒后重试... (尝试 {attempt + 1}/{max_retries})")
                    time.sleep(delay)
        return wrapper
    return decorator
