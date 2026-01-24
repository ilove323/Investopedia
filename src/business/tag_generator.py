"""
标签生成器
从政策文本自动生成标签
"""
import logging
import re
from typing import List, Dict, Optional, Set
from src.database.policy_dao import get_policy_dao

logger = logging.getLogger(__name__)


class TagGenerator:
    """标签生成器"""

    # 三级标签体系定义
    TAG_HIERARCHY = {
        'special_bonds': {
            'name': '专项债',
            'children': {
                'issue_management': {'name': '发行管理', 'keywords': ['发行', '审批', '限额', '配置']},
                'fund_usage': {'name': '资金使用', 'keywords': ['使用', '支出', '投向', '安排']},
                'repayment': {'name': '偿还机制', 'keywords': ['偿还', '还本', '付息', '偿债']},
                'performance': {'name': '绩效评价', 'keywords': ['绩效', '评估', '评价', '监督']},
            }
        },
        'franchise': {
            'name': '特许经营',
            'children': {
                'scope': {'name': '适用范围', 'keywords': ['适用', '范围', '领域', '项目']},
                'process': {'name': '操作流程', 'keywords': ['流程', '程序', '步骤', '操作']},
                'operation': {'name': '运营管理', 'keywords': ['运营', '管理', '维护', '操作']},
                'risk': {'name': '风险管理', 'keywords': ['风险', '防范', '防止', '应对']},
            }
        },
        'data_assets': {
            'name': '数据资产',
            'children': {
                'accounting': {'name': '会计处理', 'keywords': ['会计', '处理', '计量', '核算']},
                'transaction': {'name': '交易流转', 'keywords': ['交易', '流转', '交换', '转让']},
                'compliance': {'name': '合规管理', 'keywords': ['合规', '管理', '规范', '管制']},
                'valuation': {'name': '价值管理', 'keywords': ['价值', '评估', '定价', '衡量']},
            }
        }
    }

    # 通用关键词（用于文本匹配）
    COMMON_KEYWORDS = {
        '发布': 1, '管理': 1, '办法': 1, '规定': 1,
        '指导': 1, '意见': 1, '通知': 1, '文件': 1,
        '申请': 1, '审批': 1, '流程': 1, '程序': 1,
        '风险': 2, '合规': 2, '监管': 2, '监督': 2,
        '评估': 2, '分析': 2, '评价': 2, '检查': 2,
    }

    def __init__(self):
        """初始化标签生成器"""
        self.dao = get_policy_dao()
        self._build_keyword_map()

    def _build_keyword_map(self):
        """构建关键词到标签ID的映射"""
        self.keyword_to_tags: Dict[str, List[int]] = {}

        # 从数据库加载标签
        try:
            from src.database.db_manager import get_db_manager
            db = get_db_manager()

            # 查询所有标签
            query = "SELECT id, name FROM tags"
            results = db.execute_query(query)

            for row in results:
                tag_id = row[0]
                tag_name = row[1]

                if tag_name not in self.keyword_to_tags:
                    self.keyword_to_tags[tag_name] = []

                self.keyword_to_tags[tag_name].append(tag_id)

        except Exception as e:
            logger.warning(f"加载标签失败: {e}")

    def generate_tags(self, content: str, policy_type: Optional[str] = None,
                      manual_tags: Optional[List[str]] = None) -> List[Dict[str, any]]:
        """
        生成标签

        Args:
            content: 政策文本
            policy_type: 政策类型（用于限制标签范围）
            manual_tags: 手动指定的标签名称列表

        Returns:
            标签列表 [{'id': 1, 'name': '标签名', 'level': 1, 'confidence': 0.9, 'source': 'auto'}, ...]
        """
        tags = []

        # 自动生成标签
        auto_tags = self._extract_auto_tags(content, policy_type)
        tags.extend(auto_tags)

        # 添加手动标签
        if manual_tags:
            manual_tag_objects = self._get_manual_tags(manual_tags)
            for tag in manual_tag_objects:
                # 避免重复
                if not any(t['id'] == tag['id'] for t in tags):
                    tag['source'] = 'manual'
                    tag['confidence'] = 1.0
                    tags.append(tag)

        # 排序：优先级高的在前，置信度高的在前
        tags.sort(key=lambda x: (-x.get('level', 0), -x.get('confidence', 0)))

        logger.info(f"生成标签数量: {len(tags)}")
        return tags

    def _extract_auto_tags(self, content: str, policy_type: Optional[str] = None) -> List[Dict[str, any]]:
        """自动提取标签"""
        tags = []
        keyword_scores: Dict[str, float] = {}

        # 分词并计算关键词分数
        words = re.findall(r'[\u4e00-\u9fff]+', content)

        for word in words:
            # 检查是否在关键词映射中
            if word in self.keyword_to_tags:
                keyword_scores[word] = keyword_scores.get(word, 0) + 1

            # 检查是否在通用关键词中
            if word in self.COMMON_KEYWORDS:
                keyword_scores[word] = keyword_scores.get(word, 0) + self.COMMON_KEYWORDS[word]

        # 根据关键词分数生成标签
        for keyword, score in sorted(keyword_scores.items(), key=lambda x: -x[1])[:10]:
            if keyword in self.keyword_to_tags:
                for tag_id in self.keyword_to_tags[keyword]:
                    # 计算置信度 (0-1)
                    confidence = min(1.0, score / max(1, len(words)) * 10)

                    tags.append({
                        'id': tag_id,
                        'name': keyword,
                        'confidence': confidence,
                        'source': 'auto'
                    })

        # 如果没有提取到标签，返回默认标签
        if not tags:
            logger.warning("未能自动提取标签，使用默认标签")
            tags = self._get_default_tags(policy_type)

        return tags

    def _get_default_tags(self, policy_type: Optional[str] = None) -> List[Dict[str, any]]:
        """获取默认标签"""
        try:
            from src.database.db_manager import get_db_manager
            db = get_db_manager()

            # 根据政策类型获取默认标签
            if policy_type:
                query = "SELECT id, name, level FROM tags WHERE policy_type = ? AND level = 1"
                results = db.execute_query(query, (policy_type,))
            else:
                query = "SELECT id, name, level FROM tags WHERE level = 1 LIMIT 5"
                results = db.execute_query(query)

            return [
                {
                    'id': row[0],
                    'name': row[1],
                    'level': row[2],
                    'confidence': 0.5,
                    'source': 'auto'
                }
                for row in results
            ]

        except Exception as e:
            logger.error(f"获取默认标签失败: {e}")
            return []

    def _get_manual_tags(self, tag_names: List[str]) -> List[Dict[str, any]]:
        """根据标签名称获取标签信息"""
        tags = []

        try:
            from src.database.db_manager import get_db_manager
            db = get_db_manager()

            for tag_name in tag_names:
                query = "SELECT id, name, level FROM tags WHERE name = ?"
                results = db.execute_query(query, (tag_name,))

                if results:
                    row = results[0]
                    tags.append({
                        'id': row[0],
                        'name': row[1],
                        'level': row[2],
                        'confidence': 1.0,
                        'source': 'manual'
                    })
                else:
                    logger.warning(f"标签不存在: {tag_name}")

        except Exception as e:
            logger.error(f"获取手动标签失败: {e}")

        return tags

    def get_suggested_tags(self, content: str, limit: int = 5) -> List[str]:
        """
        获取建议标签

        Args:
            content: 政策文本
            limit: 返回数量限制

        Returns:
            建议标签名称列表
        """
        auto_tags = self._extract_auto_tags(content)
        # 按置信度排序并返回前limit个
        return [tag['name'] for tag in auto_tags[:limit]]

    @staticmethod
    def standardize_tag_name(tag_name: str) -> str:
        """标准化标签名称"""
        # 去掉前后空格
        tag_name = tag_name.strip()

        # 转换为小写（对于英文）
        # 对中文不做大小写转换

        # 去掉特殊字符
        tag_name = re.sub(r'[^\u4e00-\u9fff\w-]', '', tag_name)

        return tag_name


# 全局生成器实例
_generator: Optional[TagGenerator] = None


def get_tag_generator() -> TagGenerator:
    """获取全局标签生成器实例"""
    global _generator
    if _generator is None:
        _generator = TagGenerator()
    return _generator
