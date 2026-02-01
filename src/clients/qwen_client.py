"""
Qwen大模型客户端
用于实体抽取和关系抽取
"""
import json
from typing import Dict, List, Optional
from pathlib import Path
import dashscope
from dashscope import Generation

from src.utils.logger import get_logger

logger = get_logger(__name__)


class QwenClient:
    """Qwen大模型客户端"""
    
    def __init__(
        self, 
        api_key: str, 
        model: str = "qwen-plus", 
        temperature: float = 0.1,
        max_tokens: int = 2000,
        prompt_file: str = "config/prompts/entity_extraction.txt"
    ):
        """
        初始化Qwen客户端
        
        Args:
            api_key: DashScope API密钥
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大生成token数
            prompt_file: 提示词文件路径
        """
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.prompt_file = Path(prompt_file)
        
        dashscope.api_key = api_key
        
        # 加载提示词模板
        self.system_prompt = self._load_prompt_template()
    
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
    
    def extract_entities_and_relations(self, text: str, doc_title: str) -> Dict:
        """
        从政策文本中提取实体和关系
        
        Args:
            text: 政策文本内容
            doc_title: 文档标题
            
        Returns:
            包含entities和relations的字典
        """
        user_prompt = self._build_user_prompt(text, doc_title)
        
        try:
            logger.info(f"开始调用Qwen API提取实体: {doc_title[:50]}...")
            
            response = Generation.call(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': self.system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                result_format='message'
            )
            
            if response.status_code == 200:
                content = response.output.choices[0].message.content
                result = self._parse_extraction_result(content)
                
                entity_count = len(result.get('entities', []))
                relation_count = len(result.get('relations', []))
                logger.info(f"实体抽取成功: {entity_count}个实体, {relation_count}个关系")
                
                return result
            else:
                logger.error(f"Qwen API调用失败: {response.code} - {response.message}")
                return {'entities': [], 'relations': []}
                
        except Exception as e:
            logger.error(f"实体抽取异常: {e}", exc_info=True)
            return {'entities': [], 'relations': []}
    
    def _build_user_prompt(self, text: str, doc_title: str) -> str:
        """构建用户提示词"""
        # 截断过长文本
        max_length = 3000
        if len(text) > max_length:
            text = text[:max_length] + "\n...[文本过长，已截断]"
        
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
_qwen_client_instance = None

def get_qwen_client() -> QwenClient:
    """获取Qwen客户端单例"""
    global _qwen_client_instance
    
    if _qwen_client_instance is None:
        from src.config import get_config
        config = get_config()
        
        _qwen_client_instance = QwenClient(
            api_key=config.qwen_api_key,
            model=config.qwen_model,
            temperature=config.qwen_temperature,
            max_tokens=config.qwen_max_tokens,
            prompt_file=config.qwen_prompt_file
        )
    
    return _qwen_client_instance
