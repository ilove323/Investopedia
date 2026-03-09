"""
OpenAI 兼容接口客户端
====================
纯API客户端，负责与任意兼容 OpenAI 协议的服务通信。

核心功能：
- 调用 Chat Completions 生成API
- 流式响应支持
- 错误处理和重试
- 健康检查

依赖：
- openai - OpenAI 官方 Python SDK
- src.config.ConfigLoader - OpenAI 服务配置

配置项（来自config.ini的[OPENAI]部分）：
- base_url: 接口地址（支持 OpenAI 官方 / 阿里云 / Ollama 等兼容服务）
- api_key: API 密钥
- model: 模型名称（gpt-4o-mini, qwen-turbo 等）
- temperature: 温度参数
- max_tokens: 最大生成token数

使用示例：
    from src.clients.openai_client import get_openai_client

    client = get_openai_client()

    # 单轮对话
    response = client.generate(
        messages=[{"role": "user", "content": "你好"}]
    )
    print(response)

    # 多轮对话
    response = client.generate(
        messages=[
            {"role": "system", "content": "你是一个助手"},
            {"role": "user", "content": "今天天气怎么样？"}
        ],
        temperature=0.7
    )
"""
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class OpenAIError(Exception):
    """OpenAI API错误"""
    pass


class OpenAIClient:
    """OpenAI 兼容接口客户端 - 纯通信层"""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.1,
        max_tokens: int = 4000
    ):
        """
        初始化 OpenAI 兼容客户端

        Args:
            base_url: 接口地址，例如 https://api.openai.com/v1
                      或阿里云 https://dashscope.aliyuncs.com/compatible-mode/v1
            api_key: API 密钥
            model: 模型名称
            temperature: 默认温度参数
            max_tokens: 默认最大生成token数
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("请安装 openai 包: pip install openai")

        from openai import OpenAI
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model = model
        self.default_temperature = temperature
        self.default_max_tokens = max_tokens
        logger.info(f"OpenAI客户端初始化成功: model={model}, base_url={base_url}")

    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stream: bool = False
    ) -> Optional[str]:
        """
        调用 Chat Completions 生成API

        Args:
            messages: 消息列表，格式：[{"role": "user", "content": "..."}]
            temperature: 温度参数，不指定则使用默认值
            max_tokens: 最大生成token数，不指定则使用默认值
            top_p: 核采样参数
            stream: 是否使用流式输出（此方法为非流式，流式请用 generate_stream）

        Returns:
            生成的文本内容，失败返回None
        """
        try:
            if temperature is None:
                temperature = self.default_temperature
            if max_tokens is None:
                max_tokens = self.default_max_tokens

            logger.debug(f"调用OpenAI API: model={self.model}, temperature={temperature}")

            params = dict(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            if top_p is not None:
                params['top_p'] = top_p

            resp = self.client.chat.completions.create(**params)
            content = resp.choices[0].message.content
            logger.debug(f"OpenAI API调用成功: {len(content)}字符")
            return content

        except Exception as e:
            logger.error(f"OpenAI API调用失败: {e}", exc_info=True)
            return None

    def generate_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        """
        流式生成（生成器）

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大生成token数

        Yields:
            生成的文本片段
        """
        try:
            if temperature is None:
                temperature = self.default_temperature
            if max_tokens is None:
                max_tokens = self.default_max_tokens

            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content

        except Exception as e:
            logger.error(f"OpenAI 流式生成失败: {e}", exc_info=True)
            yield ""

    def check_health(self) -> bool:
        """
        检查服务健康状态

        Returns:
            True表示服务正常
        """
        try:
            test_messages = [{"role": "user", "content": "hi"}]
            response = self.generate(test_messages, max_tokens=5)
            return response is not None
        except Exception as e:
            logger.debug(f"OpenAI健康检查失败: {e}")
            return False


# 单例模式
_openai_client_instance = None


def get_openai_client() -> OpenAIClient:
    """获取OpenAI兼容客户端单例"""
    global _openai_client_instance

    if _openai_client_instance is None:
        from src.config import get_config
        config = get_config()

        _openai_client_instance = OpenAIClient(
            base_url=config.openai_base_url,
            api_key=config.openai_api_key,
            model=config.openai_model,
            temperature=config.openai_temperature,
            max_tokens=config.openai_max_tokens,
        )

    return _openai_client_instance
