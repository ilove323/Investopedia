"""
政策数据访问对象（DAO）
====================
提供数据库操作接口，实现政策、标签、关系、日志等表的CRUD操作。

核心类：
- PolicyDAO：政策数据访问对象

核心方法：
- 政策操作：create_policy, get_policy_by_id, get_policies, update_policy, delete_policy
- 标签操作：add_policy_tag, get_policy_tags
- 关系操作：add_policy_relation, get_policy_relations
- 日志操作：log_processing, get_processing_logs
- 统计操作：get_stats, count_policies

使用示例：
    from src.database.policy_dao import get_policy_dao

    dao = get_policy_dao()

    # 创建政策
    policy_id = dao.create_policy({
        'title': '某政策',
        'document_number': '财预〔2024〕1号',
        'policy_type': 'special_bonds',
        'content': '...'
    })

    # 查询政策
    policy = dao.get_policy_by_id(policy_id)

    # 添加标签
    dao.add_policy_tag(policy_id, tag_id=1, confidence=0.9)

    # 获取统计
    stats = dao.get_stats()
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from src.database.db_manager import get_db_manager

logger = logging.getLogger(__name__)


class PolicyDAO:
    """政策数据访问对象"""

    def __init__(self):
        """初始化DAO"""
        self.db = get_db_manager()

    def create_policy(self, policy_data: Dict[str, Any]) -> int:
        """创建政策记录"""
        query = """
        INSERT INTO policies
        (title, document_number, issuing_authority, publish_date, effective_date,
         expiration_date, policy_type, region, content, summary, status, file_path, ragflow_doc_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            policy_data.get('title'),
            policy_data.get('document_number'),
            policy_data.get('issuing_authority'),
            policy_data.get('publish_date'),
            policy_data.get('effective_date'),
            policy_data.get('expiration_date'),
            policy_data.get('policy_type'),
            policy_data.get('region'),
            policy_data.get('content'),
            policy_data.get('summary'),
            policy_data.get('status', 'active'),
            policy_data.get('file_path'),
            policy_data.get('ragflow_doc_id')
        )

        try:
            # 在同一连接中执行插入和获取ID
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                # 在同一连接上获取最后插入的ID
                cursor.execute("SELECT last_insert_rowid()")
                policy_id = cursor.fetchone()[0]
                logger.info(f"创建政策成功: ID={policy_id}, 标题={policy_data.get('title')}")
                return policy_id
        except Exception as e:
            logger.error(f"创建政策失败: {e}")
            raise

    def get_policy_by_id(self, policy_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取政策"""
        query = "SELECT * FROM policies WHERE id = ?"
        try:
            result = self.db.execute_query(query, (policy_id,))
            if result:
                return dict(result[0])
            return None
        except Exception as e:
            logger.error(f"获取政策失败: {e}")
            raise

    def get_policy_by_document_number(self, document_number: str) -> Optional[Dict[str, Any]]:
        """根据文号获取政策"""
        query = "SELECT * FROM policies WHERE document_number = ?"
        try:
            result = self.db.execute_query(query, (document_number,))
            if result:
                return dict(result[0])
            return None
        except Exception as e:
            logger.error(f"根据文号获取政策失败: {e}")
            raise

    def get_policy_by_ragflow_id(self, ragflow_doc_id: str) -> Optional[Dict[str, Any]]:
        """根据RAGFlow ID获取政策"""
        query = "SELECT * FROM policies WHERE ragflow_doc_id = ?"
        try:
            result = self.db.execute_query(query, (ragflow_doc_id,))
            if result:
                return dict(result[0])
            return None
        except Exception as e:
            logger.error(f"根据RAGFlow ID获取政策失败: {e}")
            raise

    def get_policies(self, filters: Optional[Dict[str, Any]] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """获取政策列表"""
        query = "SELECT * FROM policies WHERE 1=1"
        params = []

        if filters:
            if 'policy_type' in filters and filters['policy_type']:
                query += " AND policy_type = ?"
                params.append(filters['policy_type'])

            if 'status' in filters and filters['status']:
                query += " AND status = ?"
                params.append(filters['status'])

            if 'region' in filters and filters['region']:
                query += " AND region = ?"
                params.append(filters['region'])

            if 'date_from' in filters and filters['date_from']:
                query += " AND publish_date >= ?"
                params.append(filters['date_from'])

            if 'date_to' in filters and filters['date_to']:
                query += " AND publish_date <= ?"
                params.append(filters['date_to'])

        query += " ORDER BY publish_date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        try:
            result = self.db.execute_query(query, tuple(params))
            return [dict(row) for row in result]
        except Exception as e:
            logger.error(f"获取政策列表失败: {e}")
            raise

    def count_policies(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """获取政策总数"""
        query = "SELECT COUNT(*) FROM policies WHERE 1=1"
        params = []

        if filters:
            if 'policy_type' in filters and filters['policy_type']:
                query += " AND policy_type = ?"
                params.append(filters['policy_type'])

            if 'status' in filters and filters['status']:
                query += " AND status = ?"
                params.append(filters['status'])

            if 'region' in filters and filters['region']:
                query += " AND region = ?"
                params.append(filters['region'])

        try:
            result = self.db.execute_query(query, tuple(params))
            return result[0][0] if result else 0
        except Exception as e:
            logger.error(f"获取政策总数失败: {e}")
            raise

    def update_policy(self, policy_id: int, update_data: Dict[str, Any]) -> bool:
        """更新政策"""
        if not update_data:
            return False

        # 构建动态UPDATE语句
        set_clauses = [f"{key} = ?" for key in update_data.keys()]
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        query = f"UPDATE policies SET {', '.join(set_clauses)} WHERE id = ?"

        params = list(update_data.values())
        params.append(policy_id)

        try:
            rowcount = self.db.execute_update(query, tuple(params))
            return rowcount > 0
        except Exception as e:
            logger.error(f"更新政策失败: {e}")
            raise

    def delete_policy(self, policy_id: int) -> bool:
        """删除政策"""
        query = "DELETE FROM policies WHERE id = ?"
        try:
            rowcount = self.db.execute_update(query, (policy_id,))
            return rowcount > 0
        except Exception as e:
            logger.error(f"删除政策失败: {e}")
            raise

    def add_policy_tag(self, policy_id: int, tag_id: int, confidence: float = 1.0, source: str = 'auto') -> bool:
        """添加政策标签"""
        query = """
        INSERT OR REPLACE INTO policy_tags (policy_id, tag_id, confidence, source)
        VALUES (?, ?, ?, ?)
        """
        try:
            self.db.execute_update(query, (policy_id, tag_id, confidence, source))
            return True
        except Exception as e:
            logger.error(f"添加政策标签失败: {e}")
            raise

    def get_policy_tags(self, policy_id: int) -> List[Dict[str, Any]]:
        """获取政策的标签"""
        query = """
        SELECT t.*, pt.confidence, pt.source
        FROM tags t
        JOIN policy_tags pt ON t.id = pt.tag_id
        WHERE pt.policy_id = ?
        ORDER BY t.level, t.display_order
        """
        try:
            result = self.db.execute_query(query, (policy_id,))
            return [dict(row) for row in result]
        except Exception as e:
            logger.error(f"获取政策标签失败: {e}")
            raise

    def add_policy_relation(self, source_policy_id: int, target_policy_id: int,
                           relation_type: str, description: str = '', confidence: float = 1.0) -> bool:
        """添加政策关系"""
        query = """
        INSERT OR REPLACE INTO policy_relations
        (source_policy_id, target_policy_id, relation_type, description, confidence)
        VALUES (?, ?, ?, ?, ?)
        """
        try:
            self.db.execute_update(query, (source_policy_id, target_policy_id, relation_type, description, confidence))
            return True
        except Exception as e:
            logger.error(f"添加政策关系失败: {e}")
            raise

    def get_policy_relations(self, policy_id: int, as_source: bool = True) -> List[Dict[str, Any]]:
        """获取政策关系"""
        if as_source:
            query = """
            SELECT pr.*, p1.title as source_title, p2.title as target_title
            FROM policy_relations pr
            JOIN policies p1 ON pr.source_policy_id = p1.id
            JOIN policies p2 ON pr.target_policy_id = p2.id
            WHERE pr.source_policy_id = ?
            """
        else:
            query = """
            SELECT pr.*, p1.title as source_title, p2.title as target_title
            FROM policy_relations pr
            JOIN policies p1 ON pr.source_policy_id = p1.id
            JOIN policies p2 ON pr.target_policy_id = p2.id
            WHERE pr.target_policy_id = ?
            """

        try:
            result = self.db.execute_query(query, (policy_id,))
            return [dict(row) for row in result]
        except Exception as e:
            logger.error(f"获取政策关系失败: {e}")
            raise

    def log_processing(self, policy_id: Optional[int], action: str, status: str,
                      message: str = '', error_detail: str = '', duration_ms: int = 0) -> bool:
        """记录处理日志"""
        query = """
        INSERT INTO processing_logs
        (policy_id, action, status, message, error_detail, duration_ms)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        try:
            self.db.execute_update(query, (policy_id, action, status, message, error_detail, duration_ms))
            return True
        except Exception as e:
            logger.error(f"记录处理日志失败: {e}")
            raise

    def get_processing_logs(self, policy_id: Optional[int] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取处理日志"""
        query = "SELECT * FROM processing_logs WHERE 1=1"
        params = []

        if policy_id:
            query += " AND policy_id = ?"
            params.append(policy_id)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        try:
            result = self.db.execute_query(query, tuple(params))
            return [dict(row) for row in result]
        except Exception as e:
            logger.error(f"获取处理日志失败: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            # 按政策类型统计
            type_stats = {}
            query = "SELECT policy_type, COUNT(*) as count FROM policies GROUP BY policy_type"
            result = self.db.execute_query(query)
            for row in result:
                type_stats[row[0]] = row[1]

            # 按状态统计
            status_stats = {}
            query = "SELECT status, COUNT(*) as count FROM policies GROUP BY status"
            result = self.db.execute_query(query)
            for row in result:
                status_stats[row[0]] = row[1]

            # 总数
            total = self.db.get_table_count('policies')

            return {
                'total': total,
                'by_type': type_stats,
                'by_status': status_stats
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            raise


# 全局DAO实例
_policy_dao: Optional[PolicyDAO] = None


def get_policy_dao() -> PolicyDAO:
    """获取全局DAO实例"""
    global _policy_dao
    if _policy_dao is None:
        _policy_dao = PolicyDAO()
    return _policy_dao
