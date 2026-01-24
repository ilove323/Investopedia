"""
影响分析器
分析政策的影响范围、程度和实施建议
"""
import logging
import re
from typing import Dict, List, Optional, Any
from enum import Enum

from src.database.policy_dao import get_policy_dao

logger = logging.getLogger(__name__)


class ImpactLevel(Enum):
    """影响程度枚举"""
    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"


class ImpactAnalyzer:
    """影响分析器"""

    # 影响范围关键词
    IMPACT_SCOPE_KEYWORDS = {
        'national': ['全国', '全社会', '全行业', '国家'],
        'regional': ['地方', '区域', '省份', '市'],
        'industry': ['行业', '部门', '领域', '行业内'],
        'enterprise': ['企业', '单位', '机构', '组织'],
        'individual': ['个人', '居民', '职工', '消费者']
    }

    # 影响程度关键词
    IMPACT_INTENSITY_KEYWORDS = {
        'high': ['严格', '强制', '必须', '禁止', '严禁', '明确', '重点', '关键'],
        'medium': ['应该', '需要', '鼓励', '倡导', '建议', '指导'],
        'low': ['可以', '可选', '自愿', '参考', '参与', '试点']
    }

    # 影响对象关键词
    IMPACT_TARGET_KEYWORDS = {
        'government': ['政府', '部门', '机关', '地方', '财政'],
        'enterprise': ['企业', '公司', '法人', '组织', '单位'],
        'market': ['市场', '交易', '流通', '运营'],
        'finance': ['资金', '融资', '投资', '财务', '银行'],
        'technology': ['技术', '创新', '数据', '平台', '系统']
    }

    def __init__(self):
        """初始化影响分析器"""
        self.dao = get_policy_dao()

    def analyze_impact(self, policy_id: int) -> Dict[str, Any]:
        """
        分析单个政策的影响

        Args:
            policy_id: 政策ID

        Returns:
            影响分析结果
        """
        try:
            policy = self.dao.get_policy_by_id(policy_id)
            if not policy:
                return {'error': '政策不存在'}

            return self.analyze_policy_data(policy)

        except Exception as e:
            logger.error(f"分析政策影响失败: {e}")
            return {'error': str(e)}

    def analyze_policy_data(self, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析政策数据的影响

        Args:
            policy_data: 政策数据字典

        Returns:
            影响分析结果
        """
        try:
            content = policy_data.get('content', '') or policy_data.get('summary', '')

            # 分析各个方面
            impact_scope = self.analyze_scope(content)
            impact_intensity = self.analyze_intensity(content)
            impact_targets = self.analyze_targets(content)
            implementation_suggestions = self.generate_suggestions(policy_data)

            return {
                'policy_id': policy_data['id'],
                'policy_title': policy_data.get('title', ''),
                'impact_scope': impact_scope,
                'impact_intensity': impact_intensity,
                'impact_targets': impact_targets,
                'implementation_suggestions': implementation_suggestions,
                'affected_areas': self.get_affected_areas(policy_data),
                'key_impacts': self.extract_key_impacts(content)
            }

        except Exception as e:
            logger.error(f"分析政策数据影响失败: {e}")
            return {'error': str(e)}

    def analyze_scope(self, content: str) -> Dict[str, Any]:
        """
        分析影响范围

        Args:
            content: 政策内容

        Returns:
            影响范围分析结果
        """
        scope_scores = {scope_type: 0 for scope_type in self.IMPACT_SCOPE_KEYWORDS.keys()}

        # 计算各范围的匹配度
        for scope_type, keywords in self.IMPACT_SCOPE_KEYWORDS.items():
            for keyword in keywords:
                scope_scores[scope_type] += content.count(keyword)

        # 找出主要影响范围
        primary_scope = max(scope_scores, key=scope_scores.get)

        return {
            'primary_scope': primary_scope,
            'scope_distribution': scope_scores,
            'description': self._get_scope_description(primary_scope)
        }

    def analyze_intensity(self, content: str) -> Dict[str, Any]:
        """
        分析影响程度

        Args:
            content: 政策内容

        Returns:
            影响程度分析结果
        """
        intensity_scores = {level: 0 for level in self.IMPACT_INTENSITY_KEYWORDS.keys()}

        # 计算各程度的关键词出现次数
        for level, keywords in self.IMPACT_INTENSITY_KEYWORDS.items():
            for keyword in keywords:
                intensity_scores[level] += content.count(keyword)

        # 判断主要影响程度
        if intensity_scores['high'] > intensity_scores['medium'] * 1.5:
            primary_intensity = ImpactLevel.HIGH.value
        elif intensity_scores['low'] > intensity_scores['medium'] * 1.5:
            primary_intensity = ImpactLevel.LOW.value
        else:
            primary_intensity = ImpactLevel.MEDIUM.value

        return {
            'primary_intensity': primary_intensity,
            'intensity_distribution': intensity_scores,
            'description': self._get_intensity_description(primary_intensity)
        }

    def analyze_targets(self, content: str) -> Dict[str, Any]:
        """
        分析影响对象

        Args:
            content: 政策内容

        Returns:
            影响对象分析结果
        """
        target_scores = {target_type: 0 for target_type in self.IMPACT_TARGET_KEYWORDS.keys()}

        # 计算各目标的关键词出现次数
        for target_type, keywords in self.IMPACT_TARGET_KEYWORDS.items():
            for keyword in keywords:
                target_scores[target_type] += content.count(keyword)

        # 按得分排序
        ranked_targets = sorted(target_scores.items(), key=lambda x: -x[1])

        return {
            'primary_targets': [t[0] for t in ranked_targets[:2]],
            'target_distribution': target_scores,
            'descriptions': {target: self._get_target_description(target) for target in target_scores.keys()}
        }

    def get_affected_areas(self, policy_data: Dict[str, Any]) -> List[str]:
        """
        获取受影响的地区

        Args:
            policy_data: 政策数据

        Returns:
            受影响地区列表
        """
        region = policy_data.get('region')

        if region == '全国':
            return ['全国']

        # 基于地区提取相关省份
        affected_areas = [region] if region else []

        # 如果是特定地区，考虑周边地区的潜在影响
        regional_groups = {
            '京津冀': ['北京', '天津', '河北'],
            '长三角': ['上海', '江苏', '浙江', '安徽'],
            '粤港澳': ['广东', '香港', '澳门'],
            '成渝': ['四川', '重庆'],
            '中部': ['湖北', '湖南', '江西', '安徽', '河南']
        }

        for group, provinces in regional_groups.items():
            if region in provinces:
                affected_areas = provinces

        return affected_areas

    def extract_key_impacts(self, content: str) -> List[str]:
        """
        提取关键影响点

        Args:
            content: 政策内容

        Returns:
            关键影响点列表
        """
        key_impacts = []

        # 查找包含"影响"、"涉及"等关键词的句子
        sentences = re.split(r'[。，；：！？]', content)

        for sentence in sentences:
            if any(keyword in sentence for keyword in ['影响', '涉及', '涵盖', '包括', '明确', '规定']):
                cleaned = sentence.strip()
                if len(cleaned) > 10:  # 过滤过短的句子
                    key_impacts.append(cleaned[:100])  # 截断至100字

        return key_impacts[:5]  # 返回前5个关键影响

    def generate_suggestions(self, policy_data: Dict[str, Any]) -> List[str]:
        """
        生成实施建议

        Args:
            policy_data: 政策数据

        Returns:
            实施建议列表
        """
        suggestions = []
        policy_type = policy_data.get('policy_type')

        # 基于政策类型生成建议
        if policy_type == 'special_bonds':
            suggestions = [
                '建立专项债资金使用台账，确保资金流向透明',
                '定期评估项目进展和资金使用情况',
                '建立健全风险防范机制',
                '做好债务化解和偿还计划',
                '加强与上级部门的沟通协调'
            ]
        elif policy_type == 'franchise':
            suggestions = [
                '建立科学的特许经营招标程序',
                '完善社会资本方的选择和评估机制',
                '制定详细的运营管理规范',
                '建立有效的风险分担机制',
                '定期对特许经营方进行绩效评估'
            ]
        elif policy_type == 'data_assets':
            suggestions = [
                '建立数据资产的会计确认和计量体系',
                '完善数据隐私保护和安全管理',
                '推进数据交易市场建设',
                '建立数据资产评估机制',
                '加强数据使用者的数据素养培训'
            ]
        else:
            # 通用建议
            suggestions = [
                '组织学习宣传，确保政策理解到位',
                '完善配套制度和实施细则',
                '建立问题反馈和解决机制',
                '定期评估政策执行效果',
                '根据实施情况及时调整优化'
            ]

        return suggestions

    @staticmethod
    def _get_scope_description(scope: str) -> str:
        """获取范围描述"""
        descriptions = {
            'national': '该政策影响范围广，涉及全国范围',
            'regional': '该政策影响具有区域特征',
            'industry': '该政策主要影响特定行业或领域',
            'enterprise': '该政策主要影响企业层面',
            'individual': '该政策主要影响个人和消费者'
        }
        return descriptions.get(scope, '影响范围广泛')

    @staticmethod
    def _get_intensity_description(intensity: str) -> str:
        """获取程度描述"""
        descriptions = {
            '高': '该政策约束力强，实施要求严格，企业和个人需要认真落实',
            '中': '该政策具有明确的指导性，相关主体需要在框架内灵活实施',
            '低': '该政策具有参考意义，相关主体可根据自身情况选择性实施'
        }
        return descriptions.get(intensity, '影响程度待评估')

    @staticmethod
    def _get_target_description(target: str) -> str:
        """获取目标描述"""
        descriptions = {
            'government': '政府和相关部门是主要的实施主体',
            'enterprise': '企业是主要的受影响对象和实施主体',
            'market': '市场交易和流通环节将受到影响',
            'finance': '融资、投资和资金安排将受到影响',
            'technology': '信息系统、数据处理和技术创新将受到影响'
        }
        return descriptions.get(target, '对象待分析')

    def compare_policies(self, policy_ids: List[int]) -> Dict[str, Any]:
        """
        比较多个政策的影响

        Args:
            policy_ids: 政策ID列表

        Returns:
            对比分析结果
        """
        try:
            analyses = []

            for policy_id in policy_ids:
                analysis = self.analyze_impact(policy_id)
                if 'error' not in analysis:
                    analyses.append(analysis)

            if not analyses:
                return {'error': '无法分析任何政策'}

            # 提取共同特点和差异
            return {
                'analyses': analyses,
                'comparison_summary': self._summarize_comparison(analyses)
            }

        except Exception as e:
            logger.error(f"比较政策影响失败: {e}")
            return {'error': str(e)}

    @staticmethod
    def _summarize_comparison(analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """总结对比结果"""
        if not analyses:
            return {}

        # 提取共同的影响范围
        scopes = [a.get('impact_scope', {}).get('primary_scope') for a in analyses]
        # 提取共同的影响对象
        targets = []
        for a in analyses:
            targets.extend(a.get('impact_targets', {}).get('primary_targets', []))

        return {
            'common_scopes': list(set([s for s in scopes if s])),
            'common_targets': list(set([t for t in targets if t])),
            'policy_count': len(analyses)
        }


# 全局分析器实例
_analyzer: Optional[ImpactAnalyzer] = None


def get_impact_analyzer() -> ImpactAnalyzer:
    """获取全局影响分析器实例"""
    global _analyzer
    if _analyzer is None:
        _analyzer = ImpactAnalyzer()
    return _analyzer
