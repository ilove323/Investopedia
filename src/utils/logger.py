"""
日志工具
=======
提供统一的日志配置和记录功能。

核心功能：
- 日志记录器配置
- 控制台和文件输出
- 日志轮转（避免文件过大）
- 异常记录

依赖：
- src.config.ConfigLoader - 日志目录配置（可选）

使用示例：
    from src.utils.logger import get_logger, log_exception

    # 获取模块日志记录器
    logger = get_logger(__name__)

    # 记录日志
    logger.info("操作成功")
    logger.error("发生错误")

    # 记录异常
    try:
        do_something()
    except Exception as e:
        log_exception(logger, e, "执行操作失败")
"""
import logging
import logging.handlers
from pathlib import Path
from typing import Optional


def setup_logger(name: str = "policy_system",
                 level: str = "INFO",
                 log_file: Optional[Path] = None,
                 log_level: Optional[str] = None) -> logging.Logger:
    """
    配置日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别（传入时优先使用log_level参数）
        log_file: 日志文件路径。如果为None，则只输出到控制台
        log_level: 日志级别（优先级更高）

    Returns:
        配置好的Logger对象
    """
    logger = logging.getLogger(name)

    # 使用log_level参数（优先级更高）
    if log_level:
        logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    else:
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # 防止重复添加处理器
    if logger.handlers:
        return logger

    # 日志格式
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器（仅在log_file不为None时添加）
    if log_file is None:
        # ===== 尝试从ConfigLoader获取日志目录 =====
        # 说明：为了避免循环依赖，这里延迟导入ConfigLoader
        # 如果调用者没有提供log_file，我们尝试从config中获取
        try:
            from src.config import get_config
            config = get_config()
            log_file = config.logs_dir_path / f"{name}.log"
        except Exception:
            # 如果ConfigLoader获取失败，使用当前目录
            log_file = Path("logs") / f"{name}.log"

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # 使用RotatingFileHandler进行日志轮转
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,  # 保留5个备份文件
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# 创建默认日志记录器
logger = setup_logger()


def get_logger(name: str) -> logging.Logger:
    """获取模块日志记录器"""
    return logging.getLogger(name)


def log_exception(logger: logging.Logger, exception: Exception, context: str = ""):
    """
    记录异常信息

    Args:
        logger: 日志记录器
        exception: 异常对象
        context: 上下文信息
    """
    msg = f"发生异常: {context}" if context else "发生异常"
    logger.exception(f"{msg}: {str(exception)}")
