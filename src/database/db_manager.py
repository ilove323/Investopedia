"""
数据库管理器
===========
负责数据库初始化、连接管理、事务处理等核心功能。

核心功能：
- 数据库连接管理（SQLite）
- 表创建和初始化
- 标签体系初始化
- 查询执行（CRUD操作）
- 数据库备份

依赖：
- src.config.ConfigLoader - 获取数据库配置
- sqlite3 - SQLite数据库支持

使用示例：
    from src.database.db_manager import get_db_manager

    # 获取全局数据库管理器
    db = get_db_manager()

    # 执行查询
    results = db.execute_query("SELECT * FROM policies WHERE type = ?", ("专项债",))

    # 执行更新
    affected_rows = db.execute_update("UPDATE policies SET status = ? WHERE id = ?", ("active", 1))
"""
import sqlite3
import logging
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, List, Dict, Any

# ===== 导入新的配置系统 =====
# 说明：使用ConfigLoader替代旧的config.database_config
from src.config import get_config

# ===== 获取数据库配置 =====
# 说明：从ConfigLoader读取数据库相关的配置参数
config = get_config()

DATABASE_FILE = str(config.sqlite_path)  # 数据库文件路径
DATABASE_DIR = config.sqlite_path.parent  # 数据库目录
SQLITE_CONFIG = config.sqlite_config  # SQLite连接配置
AUTO_CREATE_TABLES = config.auto_create_tables  # 是否自动创建表
AUTO_INIT_TAGS = config.auto_init_tags  # 是否自动初始化标签
DB_LOG_LEVEL = config.log_level  # 数据库日志级别

logger = logging.getLogger(__name__)
logger.setLevel(DB_LOG_LEVEL)


class DatabaseManager:
    """数据库管理器"""

    def __init__(self):
        """初始化数据库管理器"""
        self.db_file = Path(DATABASE_FILE)
        self._ensure_db_dir()
        self._init_database()

    def _ensure_db_dir(self):
        """确保数据库目录存在"""
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"数据库目录: {DATABASE_DIR}")

    def _init_database(self):
        """初始化数据库"""
        if not self.db_file.exists():
            logger.info("创建新数据库...")
            self.db_file.touch()

        if AUTO_CREATE_TABLES:
            self._create_tables()
            if AUTO_INIT_TAGS:
                self._init_tags()

        logger.info(f"数据库初始化完成: {self.db_file}")

    def _create_tables(self):
        """从schema.sql创建表"""
        schema_file = Path(__file__).parent / "schema.sql"

        if not schema_file.exists():
            logger.error(f"Schema文件不存在: {schema_file}")
            return

        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                sql_script = f.read()

            conn = sqlite3.connect(str(self.db_file))
            cursor = conn.cursor()
            cursor.executescript(sql_script)
            conn.commit()
            conn.close()
            logger.info("数据库表创建成功")
        except Exception as e:
            logger.error(f"创建表失败: {e}")
            raise

    def _init_tags(self):
        """初始化标签体系"""
        tags_data = self._get_initial_tags()

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                for tag_info in tags_data:
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO tags
                        (name, level, parent_id, policy_type, description, display_order)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            tag_info['name'],
                            tag_info['level'],
                            tag_info['parent_id'],
                            tag_info['policy_type'],
                            tag_info['description'],
                            tag_info['display_order']
                        )
                    )
                conn.commit()
            logger.info("标签体系初始化成功")
        except Exception as e:
            logger.error(f"初始化标签体系失败: {e}")

    @staticmethod
    def _get_initial_tags() -> List[Dict[str, Any]]:
        """获取初始标签体系"""
        return [
            # 专项债标签
            {'name': '专项债', 'level': 1, 'parent_id': None, 'policy_type': 'special_bonds', 'description': '专项债券相关政策', 'display_order': 1},
            {'name': '发行管理', 'level': 2, 'parent_id': 1, 'policy_type': 'special_bonds', 'description': '发行管理', 'display_order': 1},
            {'name': '资金使用', 'level': 2, 'parent_id': 1, 'policy_type': 'special_bonds', 'description': '资金使用规范', 'display_order': 2},
            {'name': '偿还机制', 'level': 2, 'parent_id': 1, 'policy_type': 'special_bonds', 'description': '偿还机制', 'display_order': 3},
            {'name': '绩效评价', 'level': 2, 'parent_id': 1, 'policy_type': 'special_bonds', 'description': '绩效评价', 'display_order': 4},

            # 特许经营标签
            {'name': '特许经营', 'level': 1, 'parent_id': None, 'policy_type': 'franchise', 'description': '特许经营相关政策', 'display_order': 2},
            {'name': '适用范围', 'level': 2, 'parent_id': 6, 'policy_type': 'franchise', 'description': '适用范围', 'display_order': 1},
            {'name': '操作流程', 'level': 2, 'parent_id': 6, 'policy_type': 'franchise', 'description': '操作流程', 'display_order': 2},
            {'name': '运营管理', 'level': 2, 'parent_id': 6, 'policy_type': 'franchise', 'description': '运营管理', 'display_order': 3},
            {'name': '风险管理', 'level': 2, 'parent_id': 6, 'policy_type': 'franchise', 'description': '风险管理', 'display_order': 4},

            # 数据资产标签
            {'name': '数据资产', 'level': 1, 'parent_id': None, 'policy_type': 'data_assets', 'description': '数据资产相关政策', 'display_order': 3},
            {'name': '会计处理', 'level': 2, 'parent_id': 11, 'policy_type': 'data_assets', 'description': '会计处理', 'display_order': 1},
            {'name': '交易流转', 'level': 2, 'parent_id': 11, 'policy_type': 'data_assets', 'description': '交易流转', 'display_order': 2},
            {'name': '合规管理', 'level': 2, 'parent_id': 11, 'policy_type': 'data_assets', 'description': '合规管理', 'display_order': 3},
            {'name': '价值管理', 'level': 2, 'parent_id': 11, 'policy_type': 'data_assets', 'description': '价值管理', 'display_order': 4},
        ]

    @contextmanager
    def get_connection(self):
        """获取数据库连接上下文管理器"""
        conn = sqlite3.connect(str(self.db_file), check_same_thread=False, timeout=10.0)
        conn.row_factory = sqlite3.Row  # 返回类似字典的行
        try:
            yield conn
        finally:
            conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """执行查询"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"查询执行失败: {e}")
            raise

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """执行更新（INSERT/UPDATE/DELETE）"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"更新执行失败: {e}")
            raise

    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """批量执行更新"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"批量更新执行失败: {e}")
            raise

    def get_last_insert_id(self) -> int:
        """获取最后插入的ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT last_insert_rowid()")
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"获取最后插入ID失败: {e}")
            raise

    def table_exists(self, table_name: str) -> bool:
        """检查表是否存在"""
        try:
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
            result = self.execute_query(query, (table_name,))
            return len(result) > 0
        except Exception as e:
            logger.error(f"检查表存在性失败: {e}")
            return False

    def get_table_count(self, table_name: str) -> int:
        """获取表中的记录数"""
        try:
            query = f"SELECT COUNT(*) FROM {table_name}"
            result = self.execute_query(query)
            return result[0][0] if result else 0
        except Exception as e:
            logger.error(f"获取表记录数失败: {e}")
            return 0

    def delete_all(self, table_name: str) -> int:
        """删除表中所有记录"""
        try:
            query = f"DELETE FROM {table_name}"
            return self.execute_update(query)
        except Exception as e:
            logger.error(f"删除表记录失败: {e}")
            raise

    def backup(self) -> bool:
        """备份数据库"""
        try:
            backup_file = self.db_file.parent / f"{self.db_file.stem}_backup.db"
            with self.get_connection() as conn:
                backup_conn = sqlite3.connect(str(backup_file))
                conn.backup(backup_conn)
                backup_conn.close()
            logger.info(f"数据库备份成功: {backup_file}")
            return True
        except Exception as e:
            logger.error(f"数据库备份失败: {e}")
            return False


# 全局数据库管理器实例
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """获取全局数据库管理器实例"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
