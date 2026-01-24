"""
元数据提取器
从政策文本中自动提取元数据（文号、发文机关、日期等）
"""
import re
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """元数据提取器"""

    # 文号提取的正则表达式集合
    DOCUMENT_NUMBER_PATTERNS = [
        r'(财预|财库)〔\d{4}〕\d+号',  # 财政部文号
        r'(财办|财税)〔\d{4}〕\d+号',  # 财税文号
        r'(\w+)\〔\d{4}\〕\d+号',  # 通用格式
        r'(国发|国办)〔\d{4}〕\d+号',  # 国务院文号
        r'([^〔]+)〔(\d{4})〕(\d+)号',  # 宽松格式
    ]

    # 发文机关关键词
    ISSUING_AUTHORITY_KEYWORDS = [
        '财政部', '国家发改委', '国务院', '央行', '银保监会',
        '发改委', '税务总局', '自然资源部', '生态环境部', '交通运输部',
        '住建部', '教育部', '工业和信息化部', '商务部', '科技部',
        '地方政府', '省政府', '市政府', '县政府'
    ]

    # 日期提取的正则表达式集合
    DATE_PATTERNS = {
        'publish': [
            r'发布日期[：:]\s*(\d{4}[-年]\d{1,2}[-月]\d{1,2})',
            r'印发日期[：:]\s*(\d{4}[-年]\d{1,2}[-月]\d{1,2})',
            r'(\d{4}年\d{1,2}月\d{1,2}日)发布',
        ],
        'effective': [
            r'自(\d{4}[-年]\d{1,2}[-月]\d{1,2})起.*?实施',
            r'自(\d{4}[-年]\d{1,2}[-月]\d{1,2})起.*?施行',
            r'生效日期[：:]\s*(\d{4}[-年]\d{1,2}[-月]\d{1,2})',
        ],
        'expiration': [
            r'([^至到]*)(\d{4}[-年]\d{1,2}[-月]\d{1,2})失效',
            r'([^至到]*)(\d{4}[-年]\d{1,2}[-月]\d{1,2})废止',
            r'有效期[：:]\s*(\d{4}[-年]\d{1,2}[-月]\d{1,2})',
        ]
    }

    # 政策类型关键词
    POLICY_TYPE_KEYWORDS = {
        'special_bonds': ['专项债', '专项债券', '地方政府债券', '专项资金'],
        'franchise': ['特许经营', 'PPP', '政府和社会资本合作', '经营权'],
        'data_assets': ['数据资产', '数据要素', '数据资源', '数据资本化']
    }

    def extract_all(self, content: str) -> Dict[str, Any]:
        """
        提取所有元数据

        Args:
            content: 政策文本内容

        Returns:
            包含所有提取的元数据的字典
        """
        return {
            'document_number': self.extract_document_number(content),
            'issuing_authority': self.extract_issuing_authority(content),
            'publish_date': self.extract_date(content, 'publish'),
            'effective_date': self.extract_date(content, 'effective'),
            'expiration_date': self.extract_date(content, 'expiration'),
            'policy_type': self.extract_policy_type(content),
            'region': self.extract_region(content),
            'summary': self.extract_summary(content)
        }

    def extract_document_number(self, content: str) -> Optional[str]:
        """提取文号"""
        for pattern in self.DOCUMENT_NUMBER_PATTERNS:
            match = re.search(pattern, content)
            if match:
                doc_num = match.group(0)
                logger.info(f"提取文号: {doc_num}")
                return doc_num
        return None

    def extract_issuing_authority(self, content: str) -> Optional[str]:
        """提取发文机关"""
        # 查找文件开头附近的机构名称
        lines = content.split('\n')
        for i, line in enumerate(lines[:20]):  # 查看前20行
            for authority in self.ISSUING_AUTHORITY_KEYWORDS:
                if authority in line:
                    logger.info(f"提取发文机关: {authority}")
                    return authority

        # 如果没找到，尝试从正文中查找
        for authority in self.ISSUING_AUTHORITY_KEYWORDS:
            if authority in content:
                logger.info(f"提取发文机关: {authority}")
                return authority

        return None

    def extract_date(self, content: str, date_type: str) -> Optional[str]:
        """
        提取日期

        Args:
            content: 文本内容
            date_type: 日期类型 ('publish', 'effective', 'expiration')

        Returns:
            日期字符串（YYYY-MM-DD格式）
        """
        if date_type not in self.DATE_PATTERNS:
            return None

        patterns = self.DATE_PATTERNS[date_type]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                date_str = match.group(1)
                try:
                    # 标准化日期格式
                    normalized_date = self._normalize_date(date_str)
                    logger.info(f"提取{date_type}日期: {normalized_date}")
                    return normalized_date
                except Exception as e:
                    logger.warning(f"日期格式化失败: {date_str}, {e}")

        return None

    def extract_policy_type(self, content: str) -> Optional[str]:
        """提取政策类型"""
        for policy_type, keywords in self.POLICY_TYPE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in content:
                    logger.info(f"提取政策类型: {policy_type}")
                    return policy_type
        return None

    def extract_region(self, content: str) -> Optional[str]:
        """提取适用地区"""
        # 简单的地区提取逻辑
        regions = [
            '全国', '北京', '上海', '广东', '浙江', '江苏', '山东',
            '四川', '湖北', '福建', '天津', '重庆', '陕西', '湖南',
            '河南', '河北', '吉林', '辽宁', '安徽', '江西', '云南'
        ]

        for region in regions:
            if region in content:
                logger.info(f"提取地区: {region}")
                return region

        return '全国'  # 默认返回全国

    def extract_summary(self, content: str) -> str:
        """提取摘要（前200字）"""
        # 移除换行符和多余空格
        clean_content = ' '.join(content.split())

        # 取前200个字符作为摘要
        summary = clean_content[:200]
        if len(clean_content) > 200:
            summary += '...'

        logger.info(f"提取摘要，长度: {len(summary)}")
        return summary

    @staticmethod
    def _normalize_date(date_str: str) -> str:
        """
        标准化日期格式为YYYY-MM-DD

        Args:
            date_str: 日期字符串，可能的格式：
                     2024-01-01, 2024年1月1日, 2024/1/1, 等

        Returns:
            YYYY-MM-DD格式的日期字符串
        """
        # 替换中文日期符号
        date_str = date_str.replace('年', '-').replace('月', '-').replace('日', '')

        # 替换其他分隔符
        date_str = date_str.replace('/', '-')

        # 分割日期部分
        parts = date_str.split('-')
        if len(parts) >= 3:
            year = int(parts[0])
            month = int(parts[1])
            day = int(parts[2])

            # 创建日期对象验证
            date_obj = datetime(year, month, day)
            return date_obj.strftime('%Y-%m-%d')

        raise ValueError(f"无效的日期格式: {date_str}")


# 全局提取器实例
_extractor: Optional[MetadataExtractor] = None


def get_metadata_extractor() -> MetadataExtractor:
    """获取全局元数据提取器实例"""
    global _extractor
    if _extractor is None:
        _extractor = MetadataExtractor()
    return _extractor
