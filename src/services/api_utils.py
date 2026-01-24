"""
API工具函数 - 通用HTTP客户端库
================================
提供HTTP请求封装、响应解析、错误处理、重试机制等通用功能。
这是RAGFlow和Whisper等外部服务的基础通信层。

核心功能：
- APIClient：通用HTTP客户端
  - 支持GET/POST/PUT/DELETE等HTTP方法
  - 自动重试机制（可配置重试次数和延迟）
  - 自动超时控制
  - 响应自动解析（JSON优先）

- APIError：API调用异常类
  - 统一的异常处理
  - 便于上层捕获和处理

- retry_on_exception：重试装饰器
  - 为函数自动添加重试机制
  - 支持配置重试次数和延迟

重试机制说明：
1. 自动重试：HTTP 429/500/502/503/504 错误会自动重试
2. 延迟递增：backoff_factor 用于指数级增加延迟时间
3. 装饰器重试：@retry_on_exception 可为任意函数添加重试

依赖：
- requests - HTTP请求库
- urllib3 - URL和HTTP库（requests的依赖）

使用示例：
    from src.services.api_utils import APIClient, APIError, retry_on_exception

    # 创建客户端
    client = APIClient(
        base_url='http://localhost:9380',
        timeout=30,
        retry_times=3,
        retry_delay=1
    )

    # 发送GET请求
    try:
        data = client.get('/api/health')
        print(data)
    except APIError as e:
        print(f"请求失败: {e}")

    # 发送POST请求（JSON数据）
    response = client.post(
        '/api/upload',
        json_data={'file_name': 'policy.pdf'},
        headers={'Content-Type': 'application/json'}
    )

    # 发送POST请求（文件上传）
    with open('file.pdf', 'rb') as f:
        response = client.post(
            '/api/upload',
            files={'file': f},
            headers={'Authorization': 'Bearer token'}
        )

    # 使用装饰器为函数添加重试
    @retry_on_exception(max_retries=5, delay=2)
    def call_api():
        client = APIClient('http://api.example.com')
        return client.get('/data')

关键概念：
1. Session管理：
   - 使用requests.Session来复用连接
   - 配置HTTPAdapter以支持连接池和重试

2. 重试策略：
   - 总重试次数：total=retry_times
   - 指数级退避：backoff_factor 决定延迟时间
   - 应重试的HTTP状态码：429/500/502/503/504

3. 错误处理：
   - 将requests异常转换为APIError
   - 调用者统一捕获APIError异常

4. 响应解析：
   - 优先尝试JSON解析
   - 失败时返回文本内容

4. 上下文管理：
   - 支持 with 语句自动关闭连接
   - __enter__ 和 __exit__ 实现上下文协议
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
    """
    API调用错误异常

    说明：
    所有API相关的异常都被转换为此异常类。
    调用者可以统一捕获此异常来处理API错误。

    示例：
        try:
            client = APIClient('http://api.example.com')
            data = client.get('/data')
        except APIError as e:
            print(f"API错误: {e}")
    """
    pass


class APIClient:
    """
    通用HTTP API客户端

    说明：
    提供了一个通用的HTTP客户端，支持：
    1. 所有标准HTTP方法（GET/POST/PUT/DELETE）
    2. 自动重试机制（指数退避）
    3. 连接超时控制
    4. 自动JSON响应解析
    5. 上下文管理（with语句支持）

    属性：
        base_url (str): API基础URL，所有请求会自动拼接到这个URL之后
        timeout (int): 单次请求超时时间（秒），超过此时间会抛出超时异常
        retry_times (int): 最大重试次数，网络错误时会自动重试
        retry_delay (int): 重试延迟基数（秒），实际延迟会指数增长
        session (requests.Session): HTTP会话对象，管理连接池和重试策略

    重试策略说明：
        - 自动重试的HTTP状态码：429(Too Many Requests), 500(Internal Server Error),
          502(Bad Gateway), 503(Service Unavailable), 504(Gateway Timeout)
        - 延迟计算：第N次重试延迟 = retry_delay * (2^(N-1))
        - 例如 retry_delay=1, 那么延迟分别为: 1s, 2s, 4s, 8s...

    使用示例：
        # 基本用法
        client = APIClient(
            base_url='http://localhost:9380',
            timeout=30,
            retry_times=3,
            retry_delay=1
        )

        # GET请求
        data = client.get('/api/data', params={'id': 1})

        # POST请求（JSON）
        result = client.post(
            '/api/upload',
            json_data={'name': 'file.pdf'}
        )

        # 上下文管理（自动关闭连接）
        with APIClient('http://api.example.com') as client:
            data = client.get('/api/data')
    """

    def __init__(self, base_url: str, timeout: int = 30, retry_times: int = 3, retry_delay: int = 1):
        """
        初始化API客户端

        Args:
            base_url (str): API基础URL，例如 'http://localhost:9380'
                           所有端点都会相对于这个URL
            timeout (int, optional): 单次请求超时时间，单位秒，默认30秒
                                    如果请求在这个时间内没有收到响应，会抛出Timeout异常
            retry_times (int, optional): 最大重试次数，默认3次
                                        当服务器返回5xx错误或网络异常时会自动重试
            retry_delay (int, optional): 重试延迟基数，单位秒，默认1秒
                                        实际延迟时间会指数增长（backoff策略）

        说明：
            - 重试采用指数退避策略，避免给服务器造成压力
            - 重试仅对特定HTTP状态码进行（5xx和429）
            - 连接使用Session管理，支持连接复用

        示例：
            >>> client = APIClient('http://localhost:9380', timeout=60, retry_times=5)
            >>> health = client.check_health()
        """
        self.base_url = base_url
        self.timeout = timeout
        self.retry_times = retry_times
        self.retry_delay = retry_delay
        self.session = self._create_session()
        logger.info(f"APIClient initialized: base_url={base_url}, timeout={timeout}s, "
                   f"retry_times={retry_times}, retry_delay={retry_delay}s")

    def _create_session(self) -> requests.Session:
        """
        创建带重试机制的HTTP会话

        说明：
            这个方法配置了一个requests.Session对象，使其具有自动重试功能。

        重试策略配置：
            - total: 总重试次数
            - backoff_factor: 延迟指数基数
                延迟时间 = backoff_factor * (2 ** (重试次数 - 1))
            - status_forcelist: 哪些HTTP状态码会触发重试
                429: 请求过于频繁
                500: 服务器内部错误
                502: 网关错误
                503: 服务不可用
                504: 网关超时
            - allowed_methods: 允许重试的HTTP方法

        返回：
            requests.Session: 配置好的会话对象

        说明：
            HTTPAdapter用于管理HTTP连接。
            - mount('http://', adapter)：为所有http://请求配置适配器
            - mount('https://', adapter)：为所有https://请求配置适配器
        """
        session = requests.Session()

        # ===== 配置重试策略 =====
        # 说明：retry_strategy定义了何时重试以及如何重试
        retry_strategy = Retry(
            total=self.retry_times,  # 总共最多重试3次（原始请求 + 3次重试）
            backoff_factor=self.retry_delay,  # 指数退避的基数
            status_forcelist=[429, 500, 502, 503, 504],  # 这些HTTP状态码会触发重试
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"]  # 允许重试的HTTP方法
        )

        # ===== 创建和配置HTTP适配器 =====
        # 说明：HTTPAdapter将重试策略应用到所有HTTP连接
        adapter = HTTPAdapter(max_retries=retry_strategy)

        # 为HTTP和HTTPS请求分别配置适配器
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _build_url(self, endpoint: str) -> str:
        """
        构建完整的请求URL

        说明：
            将基础URL和端点拼接成完整的URL。
            支持两种形式的端点：
            1. 相对路径：/api/data -> http://base_url/api/data
            2. 绝对路径：http://other.com/api -> http://other.com/api（保持原样）

        Args:
            endpoint (str): API端点，可以是相对路径或绝对URL

        Returns:
            str: 完整的请求URL

        示例：
            >>> client = APIClient('http://localhost:9380')
            >>> client._build_url('/api/health')
            'http://localhost:9380/api/health'
            >>> client._build_url('http://other.com/api')
            'http://other.com/api'
        """
        # ===== 检查是否是绝对URL =====
        # 如果endpoint已经是完整的URL（以http://或https://开头），直接返回
        if endpoint.startswith(('http://', 'https://')):
            return endpoint

        # ===== 拼接相对路径 =====
        # urljoin会正确处理末尾斜杠和前导斜杠
        return urljoin(self.base_url, endpoint.lstrip('/'))

    def get(self, endpoint: str, headers: Optional[Dict[str, str]] = None,
            params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        发送GET请求

        说明：
            GET请求用于获取资源。参数通过URL查询字符串传递。

        Args:
            endpoint (str): API端点，例如 '/api/health' 或 '/api/data?id=1'
            headers (dict, optional): HTTP请求头，例如 {'Authorization': 'Bearer token'}
            params (dict, optional): URL查询参数，例如 {'id': 1, 'name': 'test'}
                                    会自动拼接到URL后面

        Returns:
            dict: 解析后的响应JSON数据

        Raises:
            APIError: 请求失败或HTTP错误时抛出

        示例：
            >>> client = APIClient('http://localhost:9380')
            >>> # 简单GET请求
            >>> data = client.get('/api/data')
            >>> # 带参数的GET请求
            >>> data = client.get('/api/search', params={'query': 'policy'})
            >>> # 带认证头的GET请求
            >>> data = client.get('/api/private', headers={'Authorization': 'Bearer token'})
        """
        url = self._build_url(endpoint)
        return self._request('GET', url, headers=headers, params=params)

    def post(self, endpoint: str, headers: Optional[Dict[str, str]] = None,
             data: Optional[Union[Dict[str, Any], str]] = None,
             json_data: Optional[Dict[str, Any]] = None,
             files: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        发送POST请求

        说明：
            POST请求用于创建或提交资源。支持多种数据格式：
            1. json_data：JSON格式（推荐用于API）
            2. data：表单数据格式
            3. files：文件上传（multipart/form-data）

        Args:
            endpoint (str): API端点
            headers (dict, optional): HTTP请求头
            data (dict or str, optional): 表单数据或字符串数据
                                        当data与json_data都为None时，body为空
            json_data (dict, optional): JSON格式的请求体
                                       优先于data参数
                                       自动设置Content-Type为application/json
            files (dict, optional): 文件上传数据
                                   格式：{'field_name': file_object}
                                   与json_data互斥

        Returns:
            dict: 解析后的响应JSON数据

        Raises:
            APIError: 请求失败或HTTP错误时抛出

        示例：
            >>> client = APIClient('http://localhost:9380')
            >>> # JSON请求
            >>> response = client.post('/api/create', json_data={'name': 'policy'})
            >>> # 文件上传
            >>> with open('file.pdf', 'rb') as f:
            ...     response = client.post('/api/upload', files={'document': f})
            >>> # 表单数据
            >>> response = client.post('/api/form', data={'username': 'admin'})
        """
        url = self._build_url(endpoint)
        return self._request('POST', url, headers=headers, data=data, json_data=json_data, files=files)

    def put(self, endpoint: str, headers: Optional[Dict[str, str]] = None,
            json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        发送PUT请求

        说明：
            PUT请求用于更新整个资源（与PATCH不同，PATCH用于部分更新）。

        Args:
            endpoint (str): API端点
            headers (dict, optional): HTTP请求头
            json_data (dict, optional): JSON格式的请求体

        Returns:
            dict: 解析后的响应JSON数据

        Raises:
            APIError: 请求失败或HTTP错误时抛出

        示例：
            >>> client = APIClient('http://localhost:9380')
            >>> response = client.put('/api/resource/1', json_data={'name': 'updated'})
        """
        url = self._build_url(endpoint)
        return self._request('PUT', url, headers=headers, json_data=json_data)

    def delete(self, endpoint: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        发送DELETE请求

        说明：
            DELETE请求用于删除资源。

        Args:
            endpoint (str): API端点，通常包含资源ID
            headers (dict, optional): HTTP请求头

        Returns:
            dict: 解析后的响应JSON数据（可能为空）

        Raises:
            APIError: 请求失败或HTTP错误时抛出

        示例：
            >>> client = APIClient('http://localhost:9380')
            >>> response = client.delete('/api/resource/1')
        """
        url = self._build_url(endpoint)
        return self._request('DELETE', url, headers=headers)

    def _request(self, method: str, url: str, headers: Optional[Dict[str, str]] = None,
                 params: Optional[Dict[str, Any]] = None,
                 data: Optional[Union[Dict[str, Any], str]] = None,
                 json_data: Optional[Dict[str, Any]] = None,
                 files: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        发送HTTP请求（内部核心方法）

        说明：
            这是所有HTTP请求的核心实现。会话已配置自动重试机制，
            所以这个方法会在遇到特定HTTP错误时自动重试。

        参数构建逻辑：
            1. 总是设置 headers 和 timeout
            2. 根据参数非None的情况，有选择地添加 params/data/json/files

        错误处理流程：
            1. HTTP 4xx/5xx 错误 → 抛出APIError
            2. 连接超时异常 → 抛出APIError
            3. 连接错误异常 → 抛出APIError
            4. 其他异常 → 转换为APIError

        Args:
            method (str): HTTP方法，例如 'GET', 'POST', 'PUT', 'DELETE'
            url (str): 完整的请求URL（不是端点，应该通过_build_url生成）
            headers (dict, optional): HTTP请求头
            params (dict, optional): URL查询参数
            data (dict or str, optional): 请求体（表单数据）
            json_data (dict, optional): 请求体（JSON格式）
            files (dict, optional): 文件上传数据

        Returns:
            dict: 解析后的响应（通常是JSON）

        Raises:
            APIError: 任何请求失败都抛出此异常

        说明：
            - 当同时指定 data 和 json_data 时，requests 会优先使用 json
            - 当指定 files 时，通常不应该同时指定 data 或 json_data
            - session.request 已配置重试机制，会自动重试5xx错误
        """
        try:
            # ===== 构建请求参数 =====
            # 说明：为了支持可选参数，我们只添加非None的参数
            kwargs = {
                'headers': headers,
                'timeout': self.timeout  # 从APIClient读取配置的超时时间
            }

            # 有选择地添加参数
            if params:
                kwargs['params'] = params  # URL查询参数
            if data:
                kwargs['data'] = data  # 表单数据
            if json_data:
                kwargs['json'] = json_data  # JSON数据（自动设置Content-Type）
            if files:
                kwargs['files'] = files  # 文件上传

            # ===== 记录请求详情 =====
            # 说明：debug级别的日志，用于调试
            logger.debug(f"{method} {url} with params: {kwargs}")

            # ===== 发送HTTP请求 =====
            # 说明：self.session 已配置重试策略，会自动重试
            response = self.session.request(method, url, **kwargs)

            # ===== 检查HTTP状态码 =====
            # 说明：状态码>=400都被认为是错误
            # 注意：重试机制只适用于5xx和429错误
            # 4xx错误（除了429）不会重试
            if response.status_code >= 400:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise APIError(error_msg)

            # ===== 解析响应 =====
            # 说明：调用_parse_response将响应转换为Python对象
            return self._parse_response(response)

        except requests.exceptions.Timeout:
            # ===== 超时异常 =====
            # 说明：请求在timeout秒内没有收到响应
            error_msg = f"请求超时 ({self.timeout}s): {url}"
            logger.error(error_msg)
            raise APIError(error_msg)

        except requests.exceptions.ConnectionError:
            # ===== 连接异常 =====
            # 说明：无法连接到服务器（网络错误、DNS错误等）
            error_msg = f"连接错误（网络不可达？）: {url}"
            logger.error(error_msg)
            raise APIError(error_msg)

        except APIError:
            # ===== APIError 直接重新抛出 =====
            # 说明：避免重复转换异常
            raise

        except Exception as e:
            # ===== 其他异常 =====
            # 说明：捕获任何其他意外异常并转换为APIError
            error_msg = f"请求异常: {str(e)}"
            logger.error(error_msg)
            raise APIError(error_msg)

    @staticmethod
    def _parse_response(response: requests.Response) -> Dict[str, Any]:
        """
        解析HTTP响应

        说明：
            尝试将响应解析为JSON。如果响应不是有效的JSON，
            则返回一个包含文本内容和状态码的字典。

        Args:
            response (requests.Response): requests库返回的Response对象

        Returns:
            dict: 解析后的数据（通常是JSON）

        解析逻辑：
            1. 尝试 response.json()
            2. 如果JSONDecodeError，返回 {'text': ..., 'status_code': ...}

        说明：
            - 大多数API都返回JSON格式
            - 但某些API可能返回纯文本或HTML
            - 这个方法会优雅地处理两种情况
        """
        # ===== 尝试JSON解析 =====
        # 说明：大多数API返回JSON
        try:
            return response.json()
        except json.JSONDecodeError:
            # ===== JSON解析失败 =====
            # 说明：返回原始文本和状态码，让调用者决定如何处理
            logger.warning(f"响应不是JSON格式，返回原始文本")
            return {"text": response.text, "status_code": response.status_code}

    def check_health(self, health_endpoint: str = "/health") -> bool:
        """
        检查服务是否正常运行

        说明：
            通过发送GET请求到健康检查端点，验证远程服务是否可达且正常响应。
            这个方法通常用于应用启动或定期监控。

        Args:
            health_endpoint (str, optional): 健康检查端点，默认为 "/health"
                                            不同服务可能使用不同的端点，例如：
                                            - RAGFlow: /api/health
                                            - Whisper: /health
                                            - 通用: /health 或 /healthz

        Returns:
            bool: True表示服务正常（返回2xx状态码），False表示异常

        说明：
            - 此方法不会抛出异常，而是返回布尔值
            - 所有APIError异常都被捕获并转换为False
            - 适合在UI中显示服务状态

        示例：
            >>> client = APIClient('http://localhost:9380')
            >>> if client.check_health():
            ...     print("服务正常")
            ... else:
            ...     print("服务离线或不可达")
        """
        try:
            response = self.get(health_endpoint)
            logger.info(f"✓ 服务健康检查成功: {self.base_url}{health_endpoint}")
            return True
        except APIError as e:
            logger.warning(f"✗ 服务健康检查失败 ({self.base_url}): {e}")
            return False

    def close(self):
        """
        关闭HTTP会话

        说明：
            释放连接池中的资源，关闭所有连接。
            当不再需要客户端时应调用此方法，或使用 with 语句自动关闭。

        示例：
            >>> client = APIClient('http://localhost:9380')
            >>> try:
            ...     data = client.get('/api/data')
            ... finally:
            ...     client.close()  # 确保关闭连接
        """
        self.session.close()
        logger.debug(f"APIClient会话已关闭")

    def __enter__(self):
        """
        上下文管理器入口

        说明：
            支持 with 语句，在进入 with 块时返回自身。

        返回：
            self: APIClient实例

        示例：
            >>> with APIClient('http://localhost:9380') as client:
            ...     data = client.get('/api/data')
            ... # 自动调用close()关闭连接
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        上下文管理器出口

        说明：
            支持 with 语句，在退出 with 块时自动关闭连接。
            即使发生异常也会执行此方法。

        参数说明：
            exc_type: 异常类型（没有异常时为None）
            exc_val: 异常值
            exc_tb: 异常的追踪栈

        返回：
            None: 不抑制异常（异常会继续传播）
        """
        self.close()


def retry_on_exception(max_retries: int = 3, delay: int = 1):
    """
    自动重试装饰器

    说明：
        为任意函数添加自动重试能力。当函数抛出APIError时，
        会自动重试直到成功或达到最大重试次数。

        这是一个装饰器工厂函数，返回实际的装饰器。

    参数说明：
        max_retries (int, optional): 最大重试次数，包括初始调用
                                    例如 max_retries=3 意味着：
                                    1次初始尝试 + 2次重试 = 最多3次调用
                                    默认值：3
        delay (int, optional): 重试延迟时间，单位秒
                              每次重试前都会等待这个时间
                              注意：这是固定延迟，不是指数退避
                              默认值：1秒

    返回：
        decorator: 一个装饰器函数，用 @retry_on_exception(...) 调用

    使用示例：
        # 基本用法
        @retry_on_exception(max_retries=5, delay=2)
        def call_api():
            client = APIClient('http://api.example.com')
            return client.get('/api/data')

        # 调用被装饰的函数
        try:
            result = call_api()  # 如果失败会自动重试5次
        except APIError:
            print("最终失败，已重试5次")

        # 与类方法一起使用
        class MyService:
            @retry_on_exception(max_retries=3, delay=1)
            def fetch_data(self):
                client = APIClient('http://localhost:9380')
                return client.get('/api/data')

    内部逻辑：
        1. for attempt in range(max_retries): 循环最多max_retries次
        2. 第一次尝试（attempt=0）到最后一次（attempt=max_retries-1）
        3. 如果成功，立即返回结果
        4. 如果抛出APIError且不是最后一次，等待delay秒后重试
        5. 如果是最后一次仍失败，抛出异常

    重试策略说明：
        - 仅重试APIError异常
        - 其他异常（如TypeError）不会被重试
        - 每次重试前固定延迟delay秒（不是指数增长）

    与Session重试的区别：
        - Session重试：在HTTP层，自动重试5xx/429错误
        - 装饰器重试：在应用层，重试任意APIError异常
        - 可以配合使用：双层重试提供更强的容错能力
    """
    def decorator(func):
        """
        实际装饰器函数

        参数：
            func: 要装饰的函数

        返回：
            wrapper: 包装后的函数
        """
        def wrapper(*args, **kwargs):
            """
            包装函数，实现重试逻辑

            参数：
                *args: 位置参数，原样传递给func
                **kwargs: 关键字参数，原样传递给func

            返回：
                func的返回值

            异常：
                如果max_retries次都失败，抛出最后的APIError
            """
            # ===== 循环重试 =====
            # 说明：总共尝试max_retries次（1次初始 + (max_retries-1)次重试）
            for attempt in range(max_retries):
                try:
                    # ===== 调用原函数 =====
                    # 说明：如果成功直接返回结果
                    return func(*args, **kwargs)

                except APIError as e:
                    # ===== 处理APIError =====
                    # 说明：检查是否还有重试机会
                    if attempt == max_retries - 1:
                        # 最后一次尝试失败，直接抛出异常
                        raise

                    # ===== 记录重试信息 =====
                    logger.warning(
                        f"API调用失败，{delay}秒后进行第 {attempt + 2}/{max_retries} 次尝试... "
                        f"(错误: {e})"
                    )

                    # ===== 等待后重试 =====
                    time.sleep(delay)

        return wrapper

    return decorator
