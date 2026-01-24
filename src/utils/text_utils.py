"""
文本处理工具
"""
import re
import logging
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TextProcessor:
    """文本处理器"""

    @staticmethod
    def clean_text(text: str) -> str:
        """
        清洗文本

        Args:
            text: 原始文本

        Returns:
            清洗后的文本
        """
        # 移除多余的空格和换行符
        text = re.sub(r'\s+', ' ', text)

        # 移除特殊控制字符
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')

        # 移除HTML标签（如果有）
        text = re.sub(r'<[^>]+>', '', text)

        return text.strip()

    @staticmethod
    def extract_sentences(text: str) -> List[str]:
        """
        提取句子

        Args:
            text: 文本

        Returns:
            句子列表
        """
        # 按句号、感叹号、问号分割
        sentences = re.split(r'[。！？；：]', text)

        # 清洗并过滤空句子
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    @staticmethod
    def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
        """
        提取关键词

        Args:
            text: 文本
            max_keywords: 最多返回数量

        Returns:
            关键词列表
        """
        # 简单的关键词提取：基于词频
        words = re.findall(r'[\u4e00-\u9fff]+', text)

        # 计算词频
        word_freq = {}
        for word in words:
            if len(word) >= 2:  # 只保留2个以上字的词
                word_freq[word] = word_freq.get(word, 0) + 1

        # 排序并返回
        sorted_words = sorted(word_freq.items(), key=lambda x: -x[1])
        return [word for word, _ in sorted_words[:max_keywords]]

    @staticmethod
    def truncate_text(text: str, length: int = 100, suffix: str = "...") -> str:
        """
        截断文本

        Args:
            text: 文本
            length: 最大长度
            suffix: 后缀

        Returns:
            截断后的文本
        """
        if len(text) <= length:
            return text

        return text[:length] + suffix

    @staticmethod
    def split_text_by_length(text: str, length: int = 500, overlap: int = 50) -> List[str]:
        """
        按长度分割文本（用于文本分块）

        Args:
            text: 文本
            length: 分块长度
            overlap: 重叠长度

        Returns:
            文本块列表
        """
        chunks = []
        start = 0

        while start < len(text):
            end = min(start + length, len(text))
            chunks.append(text[start:end])

            # 计算下一个起点
            start = end - overlap

        return chunks

    @staticmethod
    def highlight_keywords(text: str, keywords: List[str]) -> str:
        """
        高亮关键词

        Args:
            text: 文本
            keywords: 关键词列表

        Returns:
            标记后的文本（使用HTML标签）
        """
        marked_text = text

        for keyword in keywords:
            # 使用正则表达式进行不区分大小写的替换
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            marked_text = pattern.sub(f'<mark>{keyword}</mark>', marked_text)

        return marked_text

    @staticmethod
    def similar_texts(text1: str, text2: str) -> float:
        """
        计算两个文本的相似度（基于Jaccard相似系数）

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度（0-1）
        """
        # 分词
        words1 = set(re.findall(r'[\u4e00-\u9fff]|[a-zA-Z]+', text1.lower()))
        words2 = set(re.findall(r'[\u4e00-\u9fff]|[a-zA-Z]+', text2.lower()))

        if not words1 or not words2:
            return 0.0

        # 计算Jaccard相似系数
        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """
        标准化空格

        Args:
            text: 文本

        Returns:
            标准化后的文本
        """
        # 将各种空格字符转换为普通空格
        text = re.sub(r'[\u00A0\u3000]', ' ', text)

        # 移除多个连续空格
        text = re.sub(r' +', ' ', text)

        return text.strip()

    @staticmethod
    def parse_date_string(date_str: str) -> Optional[datetime]:
        """
        解析日期字符串

        Args:
            date_str: 日期字符串

        Returns:
            datetime对象，或None
        """
        date_formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%Y年%m月%d日',
            '%Y-%m-%d %H:%M:%S',
            '%Y/%m/%d %H:%M:%S',
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        logger.warning(f"无法解析日期: {date_str}")
        return None

    @staticmethod
    def format_phone(phone: str) -> str:
        """格式化电话号码"""
        # 移除所有非数字字符
        digits = re.sub(r'\D', '', phone)

        if len(digits) == 11:
            return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"

        return phone

    @staticmethod
    def format_number(number: float, decimal_places: int = 2) -> str:
        """格式化数字"""
        return f"{number:,.{decimal_places}f}"

    @staticmethod
    def check_text_quality(text: str) -> dict:
        """
        检查文本质量

        Args:
            text: 文本

        Returns:
            质量指标
        """
        clean = TextProcessor.clean_text(text)
        sentences = TextProcessor.extract_sentences(text)
        words = re.findall(r'[\u4e00-\u9fff]|[a-zA-Z]+', text)

        return {
            'total_chars': len(text),
            'clean_chars': len(clean),
            'sentences': len(sentences),
            'words': len(words),
            'avg_sentence_length': len(text) / len(sentences) if sentences else 0,
            'is_empty': len(clean) == 0,
            'is_short': len(clean) < 50
        }
