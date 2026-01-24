"""
Whisper服务客户端
=================
负责与Whisper服务的API交互（语音转文字）。

核心功能：
- 健康检查（验证Whisper服务连接）
- 音频文件上传
- 语音转写（将音频转换为文字）
- 音频预处理（格式转换、降噪等）
- 错误处理和超时控制

依赖：
- src.config.ConfigLoader - Whisper服务配置
- src.services.api_utils - HTTP请求工具

配置项（来自config.ini的[WHISPER]部分）：
- host: Whisper服务主机地址
- port: Whisper服务端口
- timeout: API调用超时时间
- retry_times: 重试次数
- transcribe_task: 转写任务类型（transcribe/translate）
- transcribe_language: 语言设置
- audio_sample_rate: 采样率
- audio_channels: 声道数

使用示例：
    from src.services.whisper_client import get_whisper_client

    client = get_whisper_client()

    # 检查连接
    if client.check_health():
        print("Whisper服务正常")

    # 转写音频
    text = client.transcribe_audio("audio.wav")
"""
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any

# ===== 导入新的配置系统 =====
from src.config import get_config
from src.services.api_utils import APIClient, APIError

# ===== 获取Whisper配置 =====
config = get_config()

WHISPER_BASE_URL = config.whisper_base_url  # Whisper服务URL（http://host:port）
WHISPER_TIMEOUT = config.whisper_timeout  # API调用超时时间（秒）
WHISPER_RETRY_TIMES = config.whisper_retry_times  # 失败重试次数
WHISPER_RETRY_DELAY = config.whisper_retry_delay  # 重试延迟（秒）
WHISPER_TRANSCRIBE_CONFIG = config.whisper_transcribe_config  # 转写配置
WHISPER_AUDIO_CONFIG = config.whisper_audio_config  # 音频处理配置
WHISPER_FILE_CONFIG = config.whisper_file_config  # 文件配置（大小、格式等）

# Whisper API端点定义
WHISPER_ENDPOINTS = {
    'health': '/api/health',
    'transcribe': '/api/transcribe',
    'translate': '/api/translate',
    'models': '/api/models'
}

# Whisper API请求头
WHISPER_HEADERS = {
    'Accept': 'application/json'
}

logger = logging.getLogger(__name__)


class WhisperError(APIError):
    """Whisper API错误"""
    pass


class WhisperClient:
    """Whisper客户端"""

    def __init__(self):
        """初始化Whisper客户端"""
        self.client = APIClient(
            base_url=WHISPER_BASE_URL,
            timeout=WHISPER_TIMEOUT,
            retry_times=WHISPER_RETRY_TIMES
        )
        self.headers = WHISPER_HEADERS
        self._check_connection()

    def _check_connection(self):
        """检查与Whisper的连接"""
        try:
            health_endpoint = WHISPER_ENDPOINTS['health']
            is_healthy = self.client.check_health(health_endpoint)
            if is_healthy:
                logger.info("Whisper服务连接成功")
            else:
                logger.warning("Whisper服务可能不可用")
        except Exception as e:
            logger.warning(f"Whisper服务连接检查失败: {e}")

    def check_health(self) -> bool:
        """检查Whisper服务健康状态"""
        try:
            endpoint = WHISPER_ENDPOINTS['health']
            self.client.get(endpoint, headers=self.headers)
            return True
        except APIError:
            return False

    def transcribe(self, audio_file_path: str,
                  task: str = "transcribe",
                  language: str = "zh",
                  word_timestamps: bool = False) -> Optional[Dict[str, Any]]:
        """
        将音频文件转换为文本

        Args:
            audio_file_path: 音频文件路径
            task: 任务类型 ('transcribe' 或 'translate')
            language: 语言代码 ('zh', 'en', 等)
            word_timestamps: 是否包含词级时间戳

        Returns:
            转写结果，包含文本和时间戳信息
        """
        try:
            # 验证文件
            file_path = Path(audio_file_path)
            if not file_path.exists():
                raise WhisperError(f"音频文件不存在: {audio_file_path}")

            file_size = file_path.stat().st_size
            if file_size > WHISPER_FILE_CONFIG['max_file_size']:
                raise WhisperError(f"文件过大: {file_size / 1024 / 1024:.2f}MB")

            # 检查文件格式
            suffix = file_path.suffix.lower()
            if suffix not in WHISPER_FILE_CONFIG['supported_formats']:
                raise WhisperError(f"不支持的文件格式: {suffix}")

            # 准备请求
            with open(audio_file_path, 'rb') as f:
                files = {
                    'audio_file': (file_path.name, f)
                }

                params = {
                    'task': task,
                    'language': language,
                    'word_timestamps': 'true' if word_timestamps else 'false'
                }

                endpoint = WHISPER_ENDPOINTS['transcribe']
                logger.info(f"开始转写音频文件: {file_path.name}")

                response = self.client.post(
                    endpoint,
                    headers=self.headers,
                    files=files,
                    params=params
                )

                logger.info(f"音频转写成功: {file_path.name}")
                return response

        except APIError as e:
            logger.error(f"转写失败: {e}")
            return None
        except Exception as e:
            logger.error(f"转写异常: {e}")
            return None

    def transcribe_from_bytes(self, audio_bytes: bytes, file_name: str,
                             task: str = "transcribe",
                             language: str = "zh",
                             word_timestamps: bool = False) -> Optional[Dict[str, Any]]:
        """
        从字节数据转换音频

        Args:
            audio_bytes: 音频字节数据
            file_name: 文件名
            task: 任务类型
            language: 语言代码
            word_timestamps: 是否包含词级时间戳

        Returns:
            转写结果
        """
        try:
            # 验证大小
            if len(audio_bytes) > WHISPER_FILE_CONFIG['max_file_size']:
                raise WhisperError(f"音频数据过大: {len(audio_bytes) / 1024 / 1024:.2f}MB")

            files = {
                'audio_file': (file_name, audio_bytes)
            }

            params = {
                'task': task,
                'language': language,
                'word_timestamps': 'true' if word_timestamps else 'false'
            }

            endpoint = WHISPER_ENDPOINTS['transcribe']
            logger.info(f"开始转写音频: {file_name}")

            response = self.client.post(
                endpoint,
                headers=self.headers,
                files=files,
                params=params
            )

            logger.info(f"音频转写成功: {file_name}")
            return response

        except APIError as e:
            logger.error(f"从字节转写失败: {e}")
            return None
        except Exception as e:
            logger.error(f"从字节转写异常: {e}")
            return None

    def get_languages(self) -> List[str]:
        """
        获取支持的语言列表

        Returns:
            语言代码列表
        """
        try:
            endpoint = WHISPER_ENDPOINTS['languages']
            response = self.client.get(endpoint, headers=self.headers)

            languages = response.get('languages', []) if isinstance(response, dict) else response
            logger.info(f"获取支持的语言列表: {languages}")
            return languages

        except APIError as e:
            logger.error(f"获取语言列表失败: {e}")
            return ["zh", "en"]  # 返回默认语言
        except Exception as e:
            logger.error(f"获取语言列表异常: {e}")
            return ["zh", "en"]

    def extract_text(self, result: Dict[str, Any]) -> str:
        """
        从转写结果中提取文本

        Args:
            result: 转写结果

        Returns:
            识别文本
        """
        if isinstance(result, dict):
            # 尝试不同的字段名
            if 'text' in result:
                return result['text']
            elif 'transcript' in result:
                return result['transcript']
            elif 'result' in result:
                return result['result'].get('text', '')

        return ""

    def extract_segments(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从转写结果中提取分段

        Args:
            result: 转写结果

        Returns:
            分段列表 [{'text': '...', 'start': 0.0, 'end': 5.0}, ...]
        """
        if isinstance(result, dict):
            if 'segments' in result:
                return result['segments']
            elif 'result' in result and 'segments' in result['result']:
                return result['result']['segments']

        return []

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
_whisper_client: Optional[WhisperClient] = None


def get_whisper_client() -> WhisperClient:
    """获取全局Whisper客户端实例"""
    global _whisper_client
    if _whisper_client is None:
        _whisper_client = WhisperClient()
    return _whisper_client
