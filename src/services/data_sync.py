"""
数据同步服务
============
提供RAGFlow文档到本地数据库的同步功能，自动提取元数据并生成标签。

核心功能：
- RAGFlow文档同步到本地数据库
- 自动元数据提取和标签生成
- 增量同步（更新已存在的记录）
- 同步状态和错误报告
- 知识图谱构建和存储

使用示例：
    from src.services.data_sync import DataSyncService
    
    sync_service = DataSyncService()
    results = sync_service.sync_documents_to_database("policy_demo_kb")
    print(f"同步完成: 新增{results['new_policies']}个")
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from src.clients.ragflow_client import RAGFlowClient
from src.services.entity_extraction_service import get_entity_extraction_service
from src.database.policy_dao import PolicyDAO
from src.database.graph_dao import GraphDAO
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
            self.graph_dao = None  # 延迟初始化
            self.entity_service = None  # 延迟初始化
            self.metadata_extractor = MetadataExtractor()
            self.tag_generator = TagGenerator()
            logger.info("数据同步服务初始化完成")
        except Exception as e:
            logger.error(f"数据同步服务初始化失败: {e}")
            raise
    
    def _init_entity_service(self):
        """延迟初始化实体抽取服务"""
        if self.entity_service is None:
            try:
                self.entity_service = get_entity_extraction_service()
                logger.info("实体抽取服务初始化成功")
            except Exception as e:
                logger.error(f"实体抽取服务初始化失败: {e}")
                raise
        return self.entity_service
    
    def _init_graph_dao(self):
        """延迟初始化GraphDAO"""
        if self.graph_dao is None:
            from src.config import get_config
            config = get_config()
            db_path = config.data_dir / "database" / "policies.db"
            self.graph_dao = GraphDAO(str(db_path))
        return self.graph_dao
    
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
    
    def build_knowledge_graph(self, kb_name: str = "policy_demo_kb", 
                             is_incremental: bool = False,
                             progress_callback=None,
                             max_workers: int = 3) -> Dict[str, Any]:
        """
        从RAGFlow构建知识图谱并存储到数据库（支持并发处理）
        
        Args:
            kb_name: 知识库名称
            is_incremental: 是否增量更新（True=增量，False=全量重建）
            progress_callback: 进度回调函数，接收(current, total, message)
            max_workers: 最大并发数（默认3，避免触发API限流）
            
        Returns:
            构建结果字典
        """
        import time
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        start_time = time.time()
        
        try:
            logger.info(f"开始构建知识图谱 (增量={is_incremental}, 并发数={max_workers})")
            
            # 初始化GraphDAO
            graph_dao = self._init_graph_dao()
            
            # 步骤1: 获取所有文档
            if progress_callback:
                progress_callback(1, 5, "正在获取文档列表...")
            
            documents = self.ragflow.get_documents(kb_name)
            if not documents:
                logger.warning("没有找到文档，无法构建图谱")
                return {
                    'success': False,
                    'error': '知识库中没有文档',
                    'node_count': 0,
                    'edge_count': 0,
                    'doc_count': 0,
                    'elapsed_time': f"{time.time() - start_time:.2f}秒"
                }
            
            # 步骤2: 并发处理文档
            if progress_callback:
                progress_callback(2, 5, f"正在并发分析 {len(documents)} 个文档...")
            
            # 初始化实体抽取服务
            entity_service = self._init_entity_service()
            
            all_nodes = []
            all_edges = []
            processed_docs = 0
            seen_doc_names = set()  # 用于去重文档
            seen_node_ids = set()  # 用于去重节点ID
            failed_docs = []
            
            # 准备待处理文档列表（去重）
            docs_to_process = []
            for doc in documents:
                doc_name = doc.get('name', '').replace('.pdf', '').replace('.docx', '').strip()
                if doc_name not in seen_doc_names:
                    seen_doc_names.add(doc_name)
                    docs_to_process.append(doc)
            
            logger.info(f"去重后待处理文档数: {len(docs_to_process)}")
            
            # 并发处理文档
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有任务
                future_to_doc = {
                    executor.submit(
                        self._process_single_document,
                        doc,
                        kb_name,
                        entity_service
                    ): doc
                    for doc in docs_to_process
                }
                
                # 处理完成的任务
                completed = 0
                for future in as_completed(future_to_doc):
                    completed += 1
                    doc = future_to_doc[future]
                    doc_name = doc.get('name', '')
                    
                    if progress_callback:
                        progress_callback(
                            2, 5, 
                            f"进度 {completed}/{len(docs_to_process)}: {doc_name[:30]}..."
                        )
                    
                    try:
                        result = future.result()
                        if result:
                            doc_nodes, doc_edges = result
                            
                            # 去重节点（基于ID）
                            for node in doc_nodes:
                                node_id = node.get('id')
                                if node_id and node_id not in seen_node_ids:
                                    seen_node_ids.add(node_id)
                                    all_nodes.append(node)
                            
                            all_edges.extend(doc_edges)
                            processed_docs += 1
                        else:
                            failed_docs.append(doc_name)
                    
                    except Exception as e:
                        logger.warning(f"处理文档失败 {doc_name}: {e}")
                        failed_docs.append(doc_name)
                        continue
            
            if failed_docs:
                logger.warning(f"失败文档数: {len(failed_docs)}/{len(docs_to_process)}")
            
            # 步骤3: 构建图谱数据结构
            if progress_callback:
                progress_callback(3, 5, "正在构建图谱结构...")
            
            graph_data = {
                'nodes': all_nodes,
                'edges': all_edges
            }
            
            # 步骤4: 存储到数据库
            if progress_callback:
                progress_callback(4, 5, "正在保存到数据库...")
            
            graph_dao.save_graph(graph_data, is_incremental=is_incremental)
            
            # 步骤5: 完成
            elapsed = time.time() - start_time
            if progress_callback:
                progress_callback(5, 5, "图谱构建完成!")
            
            result = {
                'success': True,
                'node_count': len(all_nodes),
                'edge_count': len(all_edges),
                'doc_count': processed_docs,
                'is_incremental': is_incremental,
                'elapsed_time': f"{elapsed:.2f}秒",
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"图谱构建成功: {result['node_count']}个节点, {result['edge_count']}条边, 耗时{result['elapsed_time']}")
            return result
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"图谱构建失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'node_count': 0,
                'edge_count': 0,
                'doc_count': 0,
                'elapsed_time': f"{elapsed:.2f}秒"
            }
    
    def _process_single_document(self, doc: Dict, kb_name: str, entity_service) -> Optional[Tuple[List[Dict], List[Dict]]]:
        """
        处理单个文档（用于并发调用）
        
        Args:
            doc: 文档对象
            kb_name: 知识库名称
            entity_service: 实体抽取服务
            
        Returns:
            (nodes, edges) 或 None（失败时）
        """
        try:
            doc_name = doc.get('name', '').replace('.pdf', '').replace('.docx', '').strip()
            doc_id = doc.get('id')
            
            # 获取文档内容
            doc_content = self.ragflow.get_document_content(doc_id, kb_name)
            
            if not doc_content or len(doc_content) < 50:
                logger.warning(f"文档内容为空或过短: {doc_name}")
                return None
            
            # 使用Qwen提取实体和关系
            doc_nodes, doc_edges = self._extract_entities_and_relations(
                doc_content, 
                doc_name
            )
            
            return (doc_nodes, doc_edges)
            
        except Exception as e:
            logger.error(f"处理文档异常 {doc.get('name', '')}: {e}")
            return None
    
    def _extract_entities_and_relations(self, text: str, doc_title: str) -> Tuple[List[Dict], List[Dict]]:
        """
        使用实体抽取服务提取实体和关系
        
        Args:
            text: 文档文本内容
            doc_title: 文档标题
            
        Returns:
            (nodes, edges) 节点列表和边列表
        """
        logger.info(f"提取实体: {doc_title}")
        
        # 调用实体抽取服务
        result = self.entity_service.extract_from_document(text, doc_title)
        
        entities_data = result.get('entities', [])
        relations_data = result.get('relations', [])
        
        print(f"\n[DEBUG] 文档: {doc_title}")
        print(f"[DEBUG] 抽取结果: {len(entities_data)}个实体, {len(relations_data)}个关系")
        if entities_data:
            print(f"[DEBUG] 前5个实体: {[e.get('text') for e in entities_data[:5]]}")
        if relations_data:
            print(f"[DEBUG] 前5个关系:")
            for i, r in enumerate(relations_data[:5], 1):
                print(f"  {i}. {r.get('source')} -> {r.get('target')} ({r.get('type')})")
        
        # 构建节点
        nodes = []
        entity_map = {}  # {entity_text: node_id}
        
        # 首先添加文档节点（去掉.pdf等后缀）
        clean_doc_title = doc_title.replace('.pdf', '').replace('.docx', '').strip()
        doc_node_id = f"doc_{hash(clean_doc_title) % 100000}"
        nodes.append({
            'id': doc_node_id,
            'label': clean_doc_title,
            'type': 'document',
            'title': f'📄 文档: {clean_doc_title}',
            'size': 30,
            'color': '#FF6B6B'
        })
        entity_map[clean_doc_title] = doc_node_id
        
        # 添加提取的实体节点
        for idx, entity in enumerate(entities_data):
            entity_text = entity.get('text', '').strip()
            entity_type = entity.get('type', 'unknown')
            description = entity.get('description', '')
            
            if not entity_text or len(entity_text) < 2:
                continue
            
            # 避免重复
            if entity_text in entity_map:
                continue
            
            node_id = f"entity_{hash(doc_title + entity_text) % 100000}"
            entity_map[entity_text] = node_id
            
            nodes.append({
                'id': node_id,
                'label': entity_text,
                'type': entity_type,
                'title': f'{self._get_entity_icon(entity_type)} {entity_type}: {entity_text}\n{description}',
                'size': self._get_entity_size(entity_type),
                'color': self._get_entity_color(entity_type)
            })
        
        # 构建边
        edges = []
        
        # 文档与所有实体的"包含"关系
        for entity_text, node_id in entity_map.items():
            if node_id != doc_node_id:  # 排除文档自己
                edges.append({
                    'from': doc_node_id,
                    'to': node_id,
                    'type': '包含',
                    'label': '包含',
                    'arrows': 'to',
                    'color': {'color': '#CCCCCC', 'opacity': 0.5}
                })
        
        print(f"\n[DEBUG] entity_map包含 {len(entity_map)} 个实体")
        print(f"[DEBUG] entity_map所有键: {list(entity_map.keys())}")
        
        # 实体间的关系
        matched_relations = 0
        for relation in relations_data:
            source_text = relation.get('source', '').strip()
            target_text = relation.get('target', '').strip()
            relation_type = relation.get('type', 'related')
            
            source_id = entity_map.get(source_text)
            target_id = entity_map.get(target_text)
            
            if not source_id:
                print(f"[WARN] 关系源实体未找到: '{source_text}'")
                continue
            
            if not target_id:
                print(f"[WARN] 关系目标实体未找到: '{target_text}'")
                continue
            
            if source_id and target_id and source_id != target_id:
                edges.append({
                    'from': source_id,
                    'to': target_id,
                    'type': relation_type,
                    'label': relation_type,
                    'arrows': 'to',
                    'color': {'color': self._get_relation_color(relation_type)}
                })
                matched_relations += 1
        
        print(f"\n[DEBUG] 成功匹配 {matched_relations}/{len(relations_data)} 个关系")
        print(f"[DEBUG] 最终: {len(nodes)}个节点, {len(edges)}条边")
        
        logger.info(f"实体抽取完成: {len(nodes)}个节点, {len(edges)}条边 (包含文档关系)")
        logger.info(f"  - 实体节点: {len(nodes)-1}")
        logger.info(f"  - 文档-实体关系: {len([e for e in edges if e['type']=='包含'])}")
        logger.info(f"  - 实体间关系: {len([e for e in edges if e['type']!='包含'])}")
        
        return nodes, edges
    
    def _get_entity_icon(self, entity_type: str) -> str:
        """根据实体类型返回emoji图标"""
        icon_map = {
            'document': '📄',
            '政策名称': '📋',
            '法律法规': '⚖️',
            '发文机关': '🏛️',
            '地区': '🌍',
            '领域': '🎯',
            '文号': '🔖',
            '时间': '📅',
            '关键概念': '💡',
        }
        return icon_map.get(entity_type, '🔹')
    
    def _get_entity_size(self, entity_type: str) -> int:
        """根据实体类型返回节点大小"""
        size_map = {
            'document': 30,
            '政策名称': 25,
            '法律法规': 25,
            '发文机关': 20,
            '地区': 18,
            '领域': 18,
            '文号': 15,
            '时间': 12,
            '关键概念': 15,
        }
        return size_map.get(entity_type, 15)
    
    def _get_entity_color(self, entity_type: str) -> str:
        """根据实体类型返回节点颜色"""
        color_map = {
            'document': '#FF6B6B',
            '政策名称': '#4ECDC4',
            '法律法规': '#45B7D1',
            '发文机关': '#FFA07A',
            '地区': '#F7DC6F',
            '领域': '#BB8FCE',
            '文号': '#98D8C8',
            '时间': '#85C1E2',
            '关键概念': '#52BE80',
        }
        return color_map.get(entity_type, '#95A5A6')
    
    def _get_relation_color(self, relation_type: str) -> str:
        """根据关系类型返回边颜色"""
        color_map = {
            '发布': '#FF6B6B',
            '依据': '#4ECDC4',
            '适用于': '#F7DC6F',
            '涉及': '#BB8FCE',
            '修订': '#FFA07A',
            '废止': '#E74C3C',
            '引用': '#98D8C8',
            '实施时间': '#85C1E2',
            '包含': '#CCCCCC',
        }
        return color_map.get(relation_type, '#95A5A6')


def get_data_sync_service() -> DataSyncService:
    """获取数据同步服务实例"""
    return DataSyncService()