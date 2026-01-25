"""
数据同步服务
============
提供RAGFlow文档到本地数据库的同步功能，自动提取元数据并生成标签。

核心功能：
- RAGFlow文档同步到本地数据库
- 自动元数据提取和标签生成
- 增量同步（更新已存在的记录）
- 同步状态和错误报告

使用示例：
    from src.services.data_sync import DataSyncService
    
    sync_service = DataSyncService()
    results = sync_service.sync_documents_to_database("policy_demo_kb")
    print(f"同步完成: 新增{results['new_policies']}个")
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.services.ragflow_client import RAGFlowClient
from src.database.policy_dao import PolicyDAO
from src.business.metadata_extractor import MetadataExtractor
from src.business.tag_generator import TagGenerator
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataSyncService:
    """RAGFlow到本地数据库的数据同步服务"""
    
    def __init__(self):
        """初始化同步服务"""
        try:
            self.ragflow = RAGFlowClient()
            self.dao = PolicyDAO()
            self.metadata_extractor = MetadataExtractor()
            self.tag_generator = TagGenerator()
            logger.info("数据同步服务初始化完成")
        except Exception as e:
            logger.error(f"数据同步服务初始化失败: {e}")
            raise
    
    def sync_documents_to_database(self, kb_name: str = "policy_demo_kb") -> Dict[str, Any]:
        """
        同步RAGFlow文档到本地数据库
        
        Args:
            kb_name: 知识库名称
            
        Returns:
            同步结果字典，包含统计信息和错误列表
        """
        try:
            logger.info(f"开始同步知识库: {kb_name}")
            
            # 1. 获取RAGFlow中的文档
            documents = self.ragflow.get_documents(kb_name)
            logger.info(f"从RAGFlow获取到 {len(documents)} 个文档")
            
            sync_results = {
                "total_documents": len(documents),
                "new_policies": 0,
                "updated_policies": 0,
                "errors": [],
                "sync_time": datetime.now().isoformat()
            }
            
            if not documents:
                logger.warning("RAGFlow中没有找到文档")
                return sync_results
            
            for doc in documents:
                try:
                    # 2. 处理单个文档
                    self._sync_single_document(doc, sync_results)
                    
                except Exception as e:
                    error_msg = f"处理文档 {doc.get('name', 'Unknown')} 时出错: {str(e)}"
                    sync_results["errors"].append(error_msg)
                    logger.error(error_msg)
            
            logger.info(f"同步完成: 新增{sync_results['new_policies']}个, 更新{sync_results['updated_policies']}个")
            return sync_results
            
        except Exception as e:
            logger.error(f"数据同步失败: {str(e)}")
            raise
    
    def _sync_single_document(self, doc: Dict[str, Any], sync_results: Dict[str, Any]) -> None:
        """
        同步单个文档
        
        Args:
            doc: RAGFlow文档数据
            sync_results: 同步结果累计器
        """
        doc_id = doc.get('id')
        doc_name = doc.get('name', 'Unknown')
        
        # 检查是否已存在
        existing_policy = self.dao.get_policy_by_ragflow_id(doc_id)
        
        # 提取元数据
        metadata = self._extract_policy_metadata(doc)
        
        if existing_policy:
            # 更新现有政策
            try:
                self.dao.update_policy(existing_policy['id'], metadata)
                sync_results["updated_policies"] += 1
                logger.info(f"更新政策: {metadata['title']}")
            except Exception as e:
                logger.warning(f"更新政策失败: {metadata.get('title')}, 错误: {e}")
                sync_results["failed_documents"] += 1
        else:
            # 创建新政策
            try:
                policy_id = self.dao.create_policy(metadata)
                
                # 生成和添加标签
                self._add_policy_tags(policy_id, metadata)
                
                sync_results["new_policies"] += 1
                logger.info(f"创建新政策: {metadata['title']}")
            except Exception as e:
                # 如果文号已存在，记录警告但不视为失败
                if '已存在' in str(e) or 'UNIQUE constraint' in str(e):
                    logger.info(f"政策已存在，跳过: {metadata.get('title')}")
                else:
                    logger.warning(f"创建政策失败: {metadata.get('title')}, 错误: {e}")
                    sync_results["failed_documents"] += 1
    
    def _extract_policy_metadata(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        从RAGFlow文档提取政策元数据
        
        Args:
            doc: RAGFlow文档数据
            
        Returns:
            提取的元数据字典
        """
        # 基础信息
        title = doc.get('name', '').replace('.pdf', '').replace('.docx', '')
        doc_id = doc.get('id')
        
        # 从RAGFlow获取文档实际内容
        try:
            content = self.ragflow.get_document_content(doc_id) or ''
            logger.info(f"成功获取文档内容，长度: {len(content)}")
        except Exception as e:
            logger.warning(f"获取文档内容失败: {e}")
            content = ''
        
        metadata = {
            'ragflow_document_id': doc_id,
            'title': title,
            'content': content,
            'file_path': doc.get('location', ''),
            'file_size': doc.get('size', 0),
            'upload_time': doc.get('create_time'),
            'status': 'active',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # 使用元数据提取器进一步分析
        if content:
            try:
                extracted_metadata = self.metadata_extractor.extract_all(content)
                metadata.update(extracted_metadata)
                logger.info(f"元数据提取完成: policy_type={extracted_metadata.get('policy_type')}")
            except Exception as e:
                logger.warning(f"元数据提取失败: {e}")
                # 设置默认值
                metadata.update({
                    'policy_type': 'unknown',
                    'issuing_authority': '',
                    'region': '',
                    'effective_date': None,
                    'document_number': ''
                })
        else:
            logger.warning(f"文档内容为空，无法提取元数据")
            metadata.update({
                'policy_type': 'unknown',
                'issuing_authority': '',
                'region': '',
                'effective_date': None,
                'document_number': ''
            })
        
        return metadata
    
    def _add_policy_tags(self, policy_id: int, metadata: Dict[str, Any]) -> None:
        """
        为政策添加标签
        
        Args:
            policy_id: 政策ID
            metadata: 政策元数据
        """
        try:
            content = metadata.get('content', '')
            policy_type = metadata.get('policy_type')
            
            if not content:
                logger.warning(f"政策内容为空，跳过标签生成")
                return
                
            tags = self.tag_generator.generate_tags(content, policy_type=policy_type)
            for tag in tags:
                tag_name = tag.get('name')
                tag_type = tag.get('type', 'general')
                if tag_name:
                    tag_id = self.dao.get_or_create_tag(tag_name, tag_type)
                    self.dao.add_policy_tag(policy_id, tag_id)
        except Exception as e:
            logger.warning(f"标签生成失败: {e}")
    
    def get_sync_status(self) -> Dict[str, Any]:
        """
        获取同步状态信息
        
        Returns:
            包含数据库统计和RAGFlow连接状态的字典
        """
        try:
            # 数据库统计
            policies_count = len(self.dao.get_policies())
            
            # RAGFlow连接检查
            ragflow_status = "connected"
            try:
                docs = self.ragflow.get_documents("policy_demo_kb")
                ragflow_docs_count = len(docs)
            except:
                ragflow_status = "disconnected"
                ragflow_docs_count = 0
            
            return {
                "database_policies": policies_count,
                "ragflow_documents": ragflow_docs_count,
                "ragflow_status": ragflow_status,
                "last_check": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"获取同步状态失败: {e}")
            return {
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }


def get_data_sync_service() -> DataSyncService:
    """获取数据同步服务实例"""
    return DataSyncService()