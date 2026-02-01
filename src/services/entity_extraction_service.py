"""
实体抽取服务
===========
使用Qwen大模型从政策文档中抽取实体和关系。

业务功能：
- 加载实体抽取prompt模板
- 构建针对政策文档的用户prompt
- 调用Qwen API进行实体抽取
- 解析和验证抽取结果

依赖：
- src.clients.qwen_client - Qwen API客户端
- config/prompts/entity_extraction.txt - 提示词模板

使用示例：
    from src.services.entity_extraction_service import EntityExtractionService
    
    service = EntityExtractionService()
    result = service.extract_from_document(
        text="政策内容...",
        doc_title="政策文件名"
    )
    
    entities = result['entities']
    relations = result['relations']
"""
import json
import logging
from typing import Dict, List
from pathlib import Path

from src.clients.qwen_client import get_qwen_client

logger = logging.getLogger(__name__)


class EntityExtractionService:
    """实体抽取业务服务"""
    
    def __init__(self, 
                 prompt_file: str = "config/prompts/entity_extraction.txt",
                 max_text_length: int = 32000):
        """
        初始化实体抽取服务
        
        Args:
            prompt_file: 提示词模板文件路径
            max_text_length: 最大文本长度限制（字符数）
                - 32000: 默认值，平衡成本和效果（约64页A4纸）
                - 64000: 超长文档模式（约128页A4纸）
                - 0: 不限制（完整文档，可能很贵！）
        """
        self.qwen_client = get_qwen_client()
        self.prompt_file = Path(prompt_file)
        self.system_prompt = self._load_prompt_template()
        self.max_text_length = max_text_length
    
    def _load_prompt_template(self) -> str:
        """加载提示词模板"""
        try:
            if self.prompt_file.exists():
                with open(self.prompt_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                logger.info(f"成功加载提示词模板: {self.prompt_file}")
                return content
            else:
                logger.warning(f"提示词文件不存在: {self.prompt_file}，使用默认提示词")
                return self._get_default_prompt()
        except Exception as e:
            logger.error(f"加载提示词文件失败: {e}，使用默认提示词")
            return self._get_default_prompt()
    
    def _get_default_prompt(self) -> str:
        """获取默认提示词"""
        return "你是一个专业的政策文件分析助手，擅长从政策法规文本中抽取实体和关系。"
    
    def extract_from_document(self, text: str, doc_title: str) -> Dict:
        """
        从政策文档中提取实体和关系
        
        Args:
            text: 政策文本内容
            doc_title: 文档标题
            
        Returns:
            包含entities和relations的字典
        """
        user_prompt = self._build_user_prompt(text, doc_title)
        
        try:
            logger.info(f"开始提取实体: {doc_title[:50]}...")
            
            # 调用Qwen客户端
            messages = [
                {'role': 'system', 'content': self.system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]
            
            response_content = self.qwen_client.generate(messages)
            
            if response_content:
                result = self._parse_extraction_result(response_content)
                
                entity_count = len(result.get('entities', []))
                relation_count = len(result.get('relations', []))
                logger.info(f"实体抽取成功: {entity_count}个实体, {relation_count}个关系")
                
                return result
            else:
                logger.error("Qwen API调用失败")
                return {'entities': [], 'relations': []}
                
        except Exception as e:
            logger.error(f"实体抽取异常: {e}", exc_info=True)
            return {'entities': [], 'relations': []}
    
    def _build_user_prompt(self, text: str, doc_title: str) -> str:
        """构建用户提示词"""
        # 使用配置的文本长度限制
        max_length = self.max_text_length
        
        # 如果设置为0，表示不限制长度（完整发送）
        if max_length == 0:
            logger.info(f"🚀 完整文档模式：{len(text)} 字符，无截断")
        elif len(text) > max_length:
            # 智能截断策略：头部70% + 尾部30%
            # 头部包含更多信息（标题、背景、主要条款）
            head = text[:int(max_length * 0.7)]
            tail = text[-int(max_length * 0.3):]
            truncated_chars = len(text) - max_length
            text = head + f"\n\n...【已省略{truncated_chars}字符，约{truncated_chars//500}页内容】...\n\n" + tail
            logger.info(f"📄 文档已截断：{len(text)+truncated_chars} → {max_length} 字符")
            text = head + f"\n\n...【已省略{truncated_chars}字符，约{truncated_chars//500}页内容】...\n\n" + tail
        
        user_prompt = f"""
**文档标题**: {doc_title}

**文档内容**:
{text}

---

请按照要求提取实体和关系，直接返回JSON格式结果。
"""
        return user_prompt
    
    def _parse_extraction_result(self, content: str) -> Dict:
        """解析Qwen返回的实体抽取结果"""
        try:
            # 清理内容
            content = content.strip()
            
            # 如果包含markdown代码块，提取其中的JSON
            if '```json' in content:
                start = content.find('```json') + 7
                end = content.find('```', start)
                content = content[start:end].strip()
            elif '```' in content:
                start = content.find('```') + 3
                end = content.find('```', start)
                content = content[start:end].strip()
            
            # 尝试解析JSON
            result = json.loads(content)
            
            # 验证格式
            if 'entities' not in result or 'relations' not in result:
                logger.warning("返回结果缺少entities或relations字段")
                return {'entities': [], 'relations': []}
            
            # 验证entities格式
            if not isinstance(result['entities'], list):
                logger.warning("entities不是列表格式")
                result['entities'] = []
            
            # 验证relations格式
            if not isinstance(result['relations'], list):
                logger.warning("relations不是列表格式")
                result['relations'] = []
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}\n返回内容: {content[:500]}")
            return {'entities': [], 'relations': []}
        except Exception as e:
            logger.error(f"结果解析异常: {e}", exc_info=True)
            return {'entities': [], 'relations': []}


# 单例模式
_entity_extraction_service = None


def get_entity_extraction_service() -> EntityExtractionService:
    """获取实体抽取服务单例"""
    global _entity_extraction_service
    
    if _entity_extraction_service is None:
        from src.config import get_config
        config = get_config()
        
        _entity_extraction_service = EntityExtractionService(
            prompt_file=config.qwen_prompt_file
        )
    
    return _entity_extraction_service
