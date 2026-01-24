"""
文件处理工具
===========
提供文件上传、保存、验证、删除等操作。

核心功能：
- 文件上传和保存
- 文件验证（大小、格式）
- 文件删除和复制
- 临时文件管理
- 旧文件清理

依赖：
- src.config.ConfigLoader - 文件大小和格式限制配置

配置项（来自config.ini的[APP]部分）：
- max_upload_size: 最大上传文件大小（字节）
- allowed_file_types: 允许的文件类型列表

使用示例：
    from src.utils.file_utils import FileHandler

    # 保存上传文件
    file_path = FileHandler.save_upload_file(uploaded_file)

    # 验证文件
    if FileHandler.validate_file(file_path):
        print("文件有效")

    # 删除文件
    FileHandler.delete_file(file_path)
"""
import logging
import shutil
from pathlib import Path
from typing import Optional, BinaryIO
import tempfile

from src.config import get_config

# ===== 获取文件处理配置 =====
config = get_config()
UPLOADS_DIR = config.data_dir / "uploads"  # 上传文件目录
MAX_UPLOAD_SIZE = config.max_upload_size  # 最大上传文件大小（字节）
ALLOWED_FILE_TYPES = config.allowed_file_types  # 允许的文件类型（字典）

logger = logging.getLogger(__name__)


class FileHandler:
    """文件处理器"""

    @staticmethod
    def save_upload_file(uploaded_file, target_dir: Optional[Path] = None) -> Optional[Path]:
        """
        保存上传的文件

        Args:
            uploaded_file: Streamlit上传的文件对象
            target_dir: 目标目录

        Returns:
            保存的文件路径
        """
        try:
            if target_dir is None:
                target_dir = UPLOADS_DIR

            target_dir.mkdir(parents=True, exist_ok=True)

            # 检查文件大小
            if uploaded_file.size > MAX_UPLOAD_SIZE:
                raise ValueError(f"文件过大: {uploaded_file.size / 1024 / 1024:.2f}MB > {MAX_UPLOAD_SIZE / 1024 / 1024:.2f}MB")

            # 检查文件类型
            file_ext = Path(uploaded_file.name).suffix.lower()
            if file_ext not in ALLOWED_FILE_TYPES:
                raise ValueError(f"不支持的文件格式: {file_ext}")

            # 保存文件
            file_path = target_dir / uploaded_file.name
            with open(file_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())

            logger.info(f"文件保存成功: {file_path}")
            return file_path

        except ValueError as e:
            logger.error(f"文件验证失败: {e}")
            raise
        except Exception as e:
            logger.error(f"文件保存失败: {e}")
            raise

    @staticmethod
    def delete_file(file_path: Path) -> bool:
        """
        删除文件

        Args:
            file_path: 文件路径

        Returns:
            是否成功删除
        """
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"文件删除成功: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"文件删除失败: {e}")
            return False

    @staticmethod
    def get_file_size(file_path: Path) -> int:
        """获取文件大小（字节）"""
        try:
            return file_path.stat().st_size if file_path.exists() else 0
        except Exception as e:
            logger.error(f"获取文件大小失败: {e}")
            return 0

    @staticmethod
    def get_file_extension(file_path: Path) -> str:
        """获取文件扩展名"""
        return file_path.suffix.lower()

    @staticmethod
    def validate_file(file_path: Path) -> bool:
        """
        验证文件

        Args:
            file_path: 文件路径

        Returns:
            文件是否有效
        """
        # 检查文件是否存在
        if not file_path.exists():
            logger.error(f"文件不存在: {file_path}")
            return False

        # 检查文件大小
        file_size = FileHandler.get_file_size(file_path)
        if file_size > MAX_UPLOAD_SIZE:
            logger.error(f"文件过大: {file_size}")
            return False

        # 检查文件格式
        file_ext = FileHandler.get_file_extension(file_path)
        if file_ext not in ALLOWED_FILE_TYPES:
            logger.error(f"不支持的文件格式: {file_ext}")
            return False

        return True

    @staticmethod
    def copy_file(src: Path, dst: Path) -> bool:
        """复制文件"""
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            logger.info(f"文件复制成功: {src} -> {dst}")
            return True
        except Exception as e:
            logger.error(f"文件复制失败: {e}")
            return False

    @staticmethod
    def get_temp_file(suffix: str = "") -> Path:
        """
        创建临时文件

        Args:
            suffix: 文件后缀

        Returns:
            临时文件路径
        """
        fd, path = tempfile.mkstemp(suffix=suffix)
        import os
        os.close(fd)
        return Path(path)

    @staticmethod
    def cleanup_old_files(directory: Path, days: int = 30):
        """
        清理旧文件

        Args:
            directory: 目录路径
            days: 保留天数
        """
        import time
        try:
            if not directory.exists():
                return

            cutoff_time = time.time() - (days * 24 * 60 * 60)

            for file_path in directory.glob('*'):
                if file_path.is_file():
                    if file_path.stat().st_mtime < cutoff_time:
                        file_path.unlink()
                        logger.info(f"旧文件已删除: {file_path}")

        except Exception as e:
            logger.error(f"清理旧文件失败: {e}")
