"""
时效性检查器
===========
检查政策的有效期和更新状态。

核心功能：
- 检查政策失效状态
- 计算失效预警
- 检查政策替代关系
- 更新政策状态

依赖：
- src.config.ConfigLoader - 失效预警天数配置
- src.database.policy_dao - 政策数据访问

使用示例：
    from src.business.validity_checker import get_validity_checker

    checker = get_validity_checker()
    result = checker.check_policy(policy_id=1)
"""
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Optional, List, Any

from src.config import get_config
from src.database.policy_dao import get_policy_dao

# ===== 获取时效性检查配置 =====
config = get_config()
EXPIRATION_WARNING_DAYS = config.expiration_warning_days  # 失效预警天数（默认30天）

logger = logging.getLogger(__name__)


class ValidityChecker:
    """时效性检查器"""

    STATUS_ACTIVE = 'active'
    STATUS_EXPIRED = 'expired'
    STATUS_UPDATED = 'updated'
    STATUS_EXPIRING_SOON = 'expiring_soon'

    def __init__(self):
        """初始化时效性检查器"""
        self.dao = get_policy_dao()

    def check_policy(self, policy_id: int) -> Dict[str, Any]:
        """
        检查单个政策的时效性

        Args:
            policy_id: 政策ID

        Returns:
            检查结果 {'status': 'active|expired|updated|expiring_soon', 'message': '...', 'days_to_expiration': int}
        """
        try:
            policy = self.dao.get_policy_by_id(policy_id)
            if not policy:
                return {'status': 'unknown', 'message': '政策不存在'}

            return self.check_policy_data(policy)

        except Exception as e:
            logger.error(f"检查政策时效性失败: {e}")
            return {'status': 'error', 'message': str(e)}

    def check_policy_data(self, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        检查政策数据的时效性

        Args:
            policy_data: 政策数据字典

        Returns:
            检查结果
        """
        try:
            today = date.today()
            expiration_date = policy_data.get('expiration_date')
            effective_date = policy_data.get('effective_date')
            current_status = policy_data.get('status', self.STATUS_ACTIVE)

            # 如果没有失效日期，认为长期有效
            if not expiration_date:
                return {
                    'status': self.STATUS_ACTIVE,
                    'message': '该政策为长期有效',
                    'days_to_expiration': -1
                }

            # 解析日期
            try:
                exp_date = datetime.strptime(expiration_date, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                logger.warning(f"无效的失效日期格式: {expiration_date}")
                return {
                    'status': self.STATUS_ACTIVE,
                    'message': '失效日期格式错误',
                    'days_to_expiration': -1
                }

            # 计算天数差
            days_to_expiration = (exp_date - today).days

            # 判断状态
            if current_status == self.STATUS_UPDATED:
                return {
                    'status': self.STATUS_UPDATED,
                    'message': '该政策已被更新，请查看最新版本',
                    'days_to_expiration': days_to_expiration
                }

            if days_to_expiration < 0:
                return {
                    'status': self.STATUS_EXPIRED,
                    'message': f'该政策已失效（于{expiration_date}）',
                    'days_to_expiration': days_to_expiration
                }

            if days_to_expiration <= EXPIRATION_WARNING_DAYS:
                return {
                    'status': self.STATUS_EXPIRING_SOON,
                    'message': f'该政策即将失效，还有{days_to_expiration}天',
                    'days_to_expiration': days_to_expiration
                }

            return {
                'status': self.STATUS_ACTIVE,
                'message': f'该政策有效，还有{days_to_expiration}天到期',
                'days_to_expiration': days_to_expiration
            }

        except Exception as e:
            logger.error(f"检查政策数据失败: {e}")
            return {
                'status': self.STATUS_ACTIVE,
                'message': '无法判断政策状态',
                'days_to_expiration': -1
            }

    def check_all_policies(self) -> Dict[str, Any]:
        """
        检查所有政策的时效性

        Returns:
            统计结果 {'active': int, 'expired': int, 'expiring_soon': int, 'updated': int, 'policies': [...]}
        """
        try:
            all_policies = self.dao.get_policies(limit=10000)

            stats = {
                'active': 0,
                'expired': 0,
                'expiring_soon': 0,
                'updated': 0,
                'total': len(all_policies)
            }

            policies_with_status = []

            for policy in all_policies:
                result = self.check_policy_data(policy)
                status = result['status']

                # 更新统计
                if status in stats:
                    stats[status] += 1

                # 只返回非活跃的政策
                if status != self.STATUS_ACTIVE:
                    policies_with_status.append({
                        'id': policy['id'],
                        'title': policy['title'],
                        'status': status,
                        'message': result['message'],
                        'days_to_expiration': result['days_to_expiration']
                    })

            return {
                'stats': stats,
                'policies': policies_with_status
            }

        except Exception as e:
            logger.error(f"检查所有政策失败: {e}")
            return {
                'stats': {'active': 0, 'expired': 0, 'expiring_soon': 0, 'updated': 0},
                'policies': []
            }

    def get_expiring_soon(self, days: int = EXPIRATION_WARNING_DAYS) -> List[Dict[str, Any]]:
        """
        获取即将失效的政策

        Args:
            days: 提前多少天预警

        Returns:
            即将失效的政策列表
        """
        try:
            all_policies = self.dao.get_policies(limit=10000)
            today = date.today()
            expiring_policies = []

            for policy in all_policies:
                expiration_date = policy.get('expiration_date')
                if not expiration_date:
                    continue

                try:
                    exp_date = datetime.strptime(expiration_date, '%Y-%m-%d').date()
                    days_left = (exp_date - today).days

                    if 0 <= days_left <= days:
                        expiring_policies.append({
                            'id': policy['id'],
                            'title': policy['title'],
                            'expiration_date': expiration_date,
                            'days_left': days_left,
                            'policy_type': policy.get('policy_type')
                        })

                except (ValueError, TypeError):
                    continue

            # 按失效日期排序
            expiring_policies.sort(key=lambda x: x['days_left'])

            logger.info(f"找到{len(expiring_policies)}个即将失效的政策")
            return expiring_policies

        except Exception as e:
            logger.error(f"获取即将失效的政策失败: {e}")
            return []

    def get_expired_policies(self) -> List[Dict[str, Any]]:
        """
        获取已失效的政策

        Returns:
            已失效的政策列表
        """
        try:
            all_policies = self.dao.get_policies(limit=10000)
            today = date.today()
            expired_policies = []

            for policy in all_policies:
                expiration_date = policy.get('expiration_date')
                if not expiration_date:
                    continue

                try:
                    exp_date = datetime.strptime(expiration_date, '%Y-%m-%d').date()

                    if exp_date < today:
                        expired_policies.append({
                            'id': policy['id'],
                            'title': policy['title'],
                            'expiration_date': expiration_date,
                            'days_expired': (today - exp_date).days,
                            'policy_type': policy.get('policy_type')
                        })

                except (ValueError, TypeError):
                    continue

            # 按失效日期排序（最近失效的在前）
            expired_policies.sort(key=lambda x: -x['days_expired'])

            logger.info(f"找到{len(expired_policies)}个已失效的政策")
            return expired_policies

        except Exception as e:
            logger.error(f"获取已失效的政策失败: {e}")
            return []

    def update_policy_status(self, policy_id: int, new_status: str) -> bool:
        """
        更新政策状态

        Args:
            policy_id: 政策ID
            new_status: 新状态

        Returns:
            更新是否成功
        """
        try:
            return self.dao.update_policy(policy_id, {'status': new_status})
        except Exception as e:
            logger.error(f"更新政策状态失败: {e}")
            return False

    def auto_update_statuses(self) -> int:
        """
        自动更新所有政策的状态

        Returns:
            更新的政策数量
        """
        try:
            all_policies = self.dao.get_policies(limit=10000)
            updated_count = 0

            for policy in all_policies:
                result = self.check_policy_data(policy)
                status = result['status']

                # 如果状态改变，更新数据库
                if status != policy.get('status'):
                    if self.dao.update_policy(policy['id'], {'status': status}):
                        updated_count += 1
                        logger.info(f"更新政策{policy['id']}状态为{status}")

            logger.info(f"共更新{updated_count}个政策的状态")
            return updated_count

        except Exception as e:
            logger.error(f"自动更新政策状态失败: {e}")
            return 0


# 全局检查器实例
_checker: Optional[ValidityChecker] = None


def get_validity_checker() -> ValidityChecker:
    """获取全局时效性检查器实例"""
    global _checker
    if _checker is None:
        _checker = ValidityChecker()
    return _checker
