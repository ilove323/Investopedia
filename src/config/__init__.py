"""
配置管理模块
从config/config.ini读取应用配置
"""
from src.config.config_loader import ConfigLoader

# 全局配置加载器单例
_config_loader = None


def get_config():
    """获取全局配置加载器"""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader


__all__ = ["get_config", "ConfigLoader"]
