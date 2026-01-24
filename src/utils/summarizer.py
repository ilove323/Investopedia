"""
文本摘要生成工具
================
使用RAGFlow API生成文本摘要。

优先级：RAGFlow > 文本截取

Prompt管理：
- 所有Prompt存储在 prompts/ 目录下
- summarize_policy.txt：政策摘要Prompt
"""
import logging
import requests
from typing import Optional
from pathlib import Path
from src.config import get_config

logger = logging.getLogger(__name__)

# 加载Prompt
def _load_prompt(prompt_name: str) -> str:
    """加载Prompt文件"""
    prompt_path = Path(__file__).parent.parent.parent / "prompts" / f"{prompt_name}.txt"
    if prompt_path.exists():
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        logger.warning(f"Prompt文件不存在: {prompt_path}")
        return ""


def generate_summary(text: str, max_length: int = 1500) -> str:
    """
    生成政策文本摘要

    使用RAGFlow生成摘要，失败则回退到文本截取

    Args:
        text: 要摘要的文本内容（政策文档）
        max_length: 摘要最大长度（字符）

    Returns:
        生成的摘要文本，格式包括：政策目的、核心内容、适用范围、关键时间、主要影响
    """
    if not text or len(text.strip()) == 0:
        return ""

    # 如果文本很短，直接返回
    if len(text) <= max_length:
        return text

    # 使用 RAGFlow
    summary = _summarize_with_ragflow(text, max_length)
    if summary:
        return summary

    # 回退到文本截取
    logger.warning("RAGFlow 失败，使用文本截取作为摘要")
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
        
        # 加载Prompt
        prompt_template = _load_prompt("summarize_policy")
        if not prompt_template:
            return None

        # RAGFlow 生成摘要通常需要特定的端点或方法
        ragflow_url = f"{config.ragflow_base_url}/api/llm_chat"

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        if config.ragflow_api_key:
            headers['Authorization'] = f'Bearer {config.ragflow_api_key}'

        # 构建请求 - 使用Prompt模板
        full_prompt = prompt_template + "\n\n---政策文本开始---\n\n" + text[:3000] + "\n\n---政策文本结束---"
        
        payload = {
            "message": full_prompt,
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
