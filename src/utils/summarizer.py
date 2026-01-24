"""
文本摘要生成工具
================
使用RAGFlow或DeepSeek API生成文本摘要。

优先级：RAGFlow > DeepSeek > 文本截取
"""
import logging
import requests
from typing import Optional
from src.config import get_config

logger = logging.getLogger(__name__)


def generate_summary(text: str, max_length: int = 200) -> str:
    """
    生成文本摘要

    优先使用RAGFlow，失败则使用DeepSeek，再失败则返回文本截取

    Args:
        text: 要摘要的文本
        max_length: 摘要最大长度

    Returns:
        生成的摘要文本
    """
    if not text or len(text.strip()) == 0:
        return ""

    # 如果文本很短，直接返回
    if len(text) <= max_length:
        return text

    # 尝试使用 RAGFlow
    summary = _summarize_with_ragflow(text, max_length)
    if summary:
        return summary

    # 尝试使用 DeepSeek
    summary = _summarize_with_deepseek(text, max_length)
    if summary:
        return summary

    # 回退到文本截取
    logger.warning("RAGFlow 和 DeepSeek 都失败，使用文本截取作为摘要")
    return text[:max_length] + "..."


def _summarize_with_ragflow(text: str, max_length: int) -> Optional[str]:
    """
    使用 RAGFlow 生成摘要

    Args:
        text: 要摘要的文本
        max_length: 摘要最大长度

    Returns:
        摘要文本，失败返回 None
    """
    try:
        config = get_config()

        # RAGFlow 生成摘要通常需要特定的端点或方法
        # 这里尝试使用问答功能来生成摘要
        ragflow_url = f"{config.ragflow_base_url}/api/llm_chat"

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        if config.ragflow_api_key:
            headers['Authorization'] = f'Bearer {config.ragflow_api_key}'

        # 构建请求
        payload = {
            "message": f"请用200字以内的中文摘要以下文本：\n\n{text[:2000]}",
            "stream": False
        }

        response = requests.post(
            ragflow_url,
            json=payload,
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            if isinstance(result, dict) and 'data' in result:
                summary = result['data'].get('response', '')
                if summary:
                    logger.info("✅ RAGFlow 摘要生成成功")
                    return summary[:max_length]
        else:
            logger.debug(f"RAGFlow 返回状态码 {response.status_code}")

    except requests.exceptions.Timeout:
        logger.warning("RAGFlow 请求超时")
    except Exception as e:
        logger.debug(f"RAGFlow 摘要生成失败: {e}")

    return None


def _summarize_with_deepseek(text: str, max_length: int) -> Optional[str]:
    """
    使用 DeepSeek API 生成摘要

    Args:
        text: 要摘要的文本
        max_length: 摘要最大长度

    Returns:
        摘要文本，失败返回 None
    """
    try:
        config = get_config()
        api_key = config.deepseek_api_key

        if not api_key:
            logger.debug("DeepSeek API Key 未配置")
            return None

        # 调用 DeepSeek API
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "user",
                        "content": f"请用200字以内的中文摘要以下文本，摘要必须简洁准确：\n\n{text[:2000]}"
                    }
                ],
                "temperature": 0.5,
                "max_tokens": 300
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            if result.get('choices') and len(result['choices']) > 0:
                summary = result['choices'][0]['message']['content'].strip()
                if summary:
                    logger.info("✅ DeepSeek 摘要生成成功")
                    return summary[:max_length]
        else:
            logger.debug(f"DeepSeek 返回状态码 {response.status_code}")

    except requests.exceptions.Timeout:
        logger.warning("DeepSeek 请求超时")
    except Exception as e:
        logger.debug(f"DeepSeek 摘要生成失败: {e}")

    return None
