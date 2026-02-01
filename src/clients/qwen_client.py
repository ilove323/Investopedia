"""
Qwen大模型客户端
===============
纯API客户端，负责与Qwen API的通信。

核心功能：
- 调用Qwen生成API
- 流式响应支持
- 错误处理和重试
- 健康检查

依赖：
- dashscope - 阿里云通义千问SDK
- src.config.ConfigLoader - Qwen服务配置

配置项（来自config.ini的[QWEN]部分）：
- api_key: DashScope API密钥
- model: 模型名称（qwen-plus, qwen-turbo等）
- temperature: 温度参数
- max_tokens: 最大生成token数

使用示例：
    from src.clients.qwen_client import get_qwen_client

    client = get_qwen_client()

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
from typing import Dict, List, Optional, Any
import dashscope
from dashscope import Generation

logger = logging.getLogger(__name__)


class QwenError(Exception):
    """Qwen API错误"""
    pass


class QwenClient:
    """Qwen大模型API客户端 - 纯通信层"""
    
    def __init__(
        self, 
        api_key: str, 
        model: str = "qwen-plus", 
        temperature: float = 0.1,
        max_tokens: int = 2000
    ):
        """
        初始化Qwen客户端
        
        Args:
            api_key: DashScope API密钥
            model: 模型名称
            temperature: 默认温度参数
            max_tokens: 默认最大生成token数
        """
        self.api_key = api_key
        self.model = model
        self.default_temperature = temperature
        self.default_max_tokens = max_tokens
        
        # 设置API密钥
        dashscope.api_key = api_key
        logger.info(f"Qwen客户端初始化成功: model={model}")
    
    def generate(
        self, 
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stream: bool = False
    ) -> Optional[str]:
        """
        调用Qwen生成API
        
        Args:
            messages: 消息列表，格式：[{"role": "user", "content": "..."}]
            temperature: 温度参数，不指定则使用默认值
            max_tokens: 最大生成token数，不指定则使用默认值
            top_p: 核采样参数
            stream: 是否使用流式输出
            
        Returns:
            生成的文本内容，失败返回None
        """
        try:
            # 使用默认值
            if temperature is None:
                temperature = self.default_temperature
            if max_tokens is None:
                max_tokens = self.default_max_tokens
            
            logger.debug(f"调用Qwen API: model={self.model}, temperature={temperature}")
            
            # 构建参数
            params = {
                'model': self.model,
                'messages': messages,
                'temperature': temperature,
                'max_tokens': max_tokens,
                'result_format': 'message'
            }
            
            if top_p is not None:
                params['top_p'] = top_p
            
            # 调用API
            response = Generation.call(**params)
            
            # 检查响应
            if response.status_code == 200:
                content = response.output.choices[0].message.content
                logger.debug(f"Qwen API调用成功: {len(content)}字符")
                return content
            else:
                error_msg = f"Qwen API返回错误: {response.code} - {response.message}"
                logger.error(error_msg)
                raise QwenError(error_msg)
                
        except Exception as e:
            logger.error(f"Qwen API调用失败: {e}", exc_info=True)
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
            
            responses = Generation.call(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                result_format='message',
                stream=True
            )
            
            for response in responses:
                if response.status_code == 200:
                    yield response.output.choices[0].message.content
                else:
                    logger.error(f"流式响应错误: {response.code}")
                    break
                    
        except Exception as e:
            logger.error(f"流式生成失败: {e}", exc_info=True)
            yield ""
    
    def check_health(self) -> bool:
        """
        检查Qwen服务健康状态
        
        Returns:
            True表示服务正常
        """
        try:
            # 发送简单的测试请求
            test_messages = [{"role": "user", "content": "hi"}]
            response = self.generate(test_messages, max_tokens=10)
            return response is not None
        except Exception as e:
            logger.debug(f"Qwen健康检查失败: {e}")
            return False


# 单例模式
_qwen_client_instance = None


def get_qwen_client() -> QwenClient:
    """获取Qwen客户端单例"""
    global _qwen_client_instance
    
    if _qwen_client_instance is None:
        from src.config import get_config
        config = get_config()
        
        _qwen_client_instance = QwenClient(
            api_key=config.qwen_api_key,
            model=config.qwen_model,
            temperature=config.qwen_temperature,
            max_tokens=config.qwen_max_tokens
        )
    
    return _qwen_client_instance
