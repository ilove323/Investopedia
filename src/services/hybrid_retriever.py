"""
混合检索器：本地知识图谱 + RAGFlow向量检索
===========================================

核心思路：图谱粗筛 + 向量精排
- 从查询中提取实体（使用大模型）
- 在本地图谱中模糊匹配节点
- 构建子图并提取相关政策的document_ids
- 返回图谱上下文（用于增强prompt和可视化）
"""
import logging
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.models.graph import PolicyGraph, NodeType, GraphNode, GraphEdge, RelationType
from src.clients.qwen_client import get_qwen_client
from src.config import get_config

logger = logging.getLogger(__name__)


class HybridRetriever:
    """混合检索器：知识图谱 + 向量检索"""
    
    def __init__(self):
        self.graph = None
    
    def _load_graph_from_database(self) -> Optional[PolicyGraph]:
        """从数据库加载知识图谱并转换为PolicyGraph对象"""
        try:
            from src.database.graph_dao import GraphDAO
            from src.config import get_config
            
            config = get_config()
            db_path = config.data_dir / "database" / "policies.db"
            graph_dao = GraphDAO(str(db_path))
            graph_data = graph_dao.load_graph()
            
            if not graph_data:
                logger.warning("数据库中没有图谱数据")
                return None
            
            # 将数据库格式转换为PolicyGraph
            graph = PolicyGraph()
            
            # 添加节点
            for node_data in graph_data.get('nodes', []):
                from src.models.graph import GraphNode, NodeType
                try:
                    # 尝试解析节点类型
                    node_type_str = node_data.get('type', 'UNKNOWN')
                    try:
                        node_type = NodeType[node_type_str]
                    except (KeyError, AttributeError):
                        node_type = NodeType.CONCEPT
                    
                    node = GraphNode(
                        node_id=node_data.get('id'),
                        label=node_data.get('label', node_data.get('title', 'Unknown')),
                        node_type=node_type,
                        attributes={
                            'document_id': node_data.get('document_id'),
                            'policy_id': node_data.get('policy_id'),
                            'description': node_data.get('description', '')
                        }
                    )
                    graph.add_node(node)
                except Exception as e:
                    logger.debug(f"跳过无效节点: {e}")
                    continue
            
            # 添加边
            for edge_data in graph_data.get('edges', []):
                from src.models.graph import GraphEdge, RelationType
                try:
                    # 尝试解析关系类型
                    rel_type_str = edge_data.get('type', edge_data.get('label', 'RELATED'))
                    try:
                        rel_type = RelationType[rel_type_str.upper().replace('包含', 'RELATES_TO').replace('发布', 'ISSUED_BY')]
                    except (KeyError, AttributeError):
                        # 如果找不到匹配的类型，使用RELATES_TO作为默认值
                        rel_type = RelationType.RELATES_TO
                    
                    edge = GraphEdge(
                        source_id=edge_data.get('from'),
                        target_id=edge_data.get('to'),
                        relation_type=rel_type,
                        label=edge_data.get('label', edge_data.get('type', rel_type.value))
                    )
                    graph.add_edge(edge)
                except Exception as e:
                    logger.warning(f"跳过无效边: {e}, edge_data={edge_data}")
                    continue
            
            logger.info(f"从数据库转换图谱: {graph.get_node_count()} 节点, {graph.get_edge_count()} 边")
            return graph
            
        except Exception as e:
            logger.error(f"从数据库加载图谱失败: {e}")
            return None
    
    def initialize_graph(self):
        """
        初始化知识图谱（懒加载，优先从缓存读取）
        
        优先从streamlit session_state读取已构建的图谱，
        避免每次对话都重新构建
        """
        if self.graph is None:
            # 尝试从streamlit session读取缓存的图谱
            try:
                import streamlit as st
                if hasattr(st, 'session_state') and 'graph' in st.session_state:
                    self.graph = st.session_state.graph
                    if self.graph:
                        logger.info(f"✅ 从缓存加载知识图谱: {self.graph.get_node_count()} 个节点")
                        return
            except:
                pass
            
            # 如果缓存不存在，则从数据库加载图谱（仅首次或缓存失效时）
            logger.warning("⚠️ 缓存不存在，正在从数据库加载知识图谱...")
            self.graph = self._load_graph_from_database()
            if self.graph:
                logger.info(f"知识图谱已加载: {self.graph.get_node_count()} 个节点")
                # 缓存到session_state供后续使用
                try:
                    import streamlit as st
                    st.session_state.graph = self.graph
                except:
                    pass
            else:
                logger.warning("知识图谱加载失败或为空")
    
    def retrieve(self, query: str, max_nodes: int = 30) -> Dict[str, Any]:
        """
        混合检索
        
        Args:
            query: 用户查询
            max_nodes: 子图最大节点数
        
        Returns:
            {
                'document_ids': [...],  # 相关文档ID列表
                'subgraph': PolicyGraph,  # 子图对象
                'relations': [...],  # 三元组关系列表
                'matched_nodes': [...]  # 匹配到的节点ID列表
            }
        """
        self.initialize_graph()
        
        # 如果图谱为空或不可用，返回空上下文
        if not self.graph or self.graph.get_node_count() == 0:
            logger.warning("图谱为空，跳过图谱检索")
            return {
                'document_ids': [],
                'subgraph': None,
                'relations': [],
                'matched_nodes': []
            }
        
        # 图谱过滤
        graph_context = self._graph_filter(query, max_nodes)
        
        return graph_context
    
    def _graph_filter(self, query: str, max_nodes: int) -> Dict[str, Any]:
        """
        知识图谱过滤
        
        提取实体 → 匹配节点 → 找相关政策 → 返回文档ID
        """
        # 1. 提取查询中的实体（简单分词）
        entities = self._extract_entities_from_query(query)
        logger.info(f"从查询中提取到实体: {entities}")
        
        if not entities:
            return {
                'document_ids': [],
                'subgraph': None,
                'relations': [],
                'matched_nodes': []
            }
        
        # 2. 模糊匹配到图谱节点
        from src.components.search_ui import fuzzy_match_entities_to_nodes
        matched_node_ids = fuzzy_match_entities_to_nodes(entities, self.graph)
        logger.info(f"匹配到 {len(matched_node_ids)} 个图谱节点")
        
        if not matched_node_ids:
            return {
                'document_ids': [],
                'subgraph': None,
                'relations': [],
                'matched_nodes': []
            }
        
        # 3. 构建子图（实体 + 1-2跳邻居）
        from src.components.search_ui import build_subgraph_for_entities
        subgraph = build_subgraph_for_entities(
            self.graph, 
            matched_node_ids,
            max_nodes=max_nodes
        )
        
        # 4. 提取相关政策的文档ID
        document_ids = self._extract_document_ids_from_subgraph(subgraph)
        logger.info(f"从子图提取到 {len(document_ids)} 个文档ID")
        
        # 5. 提取结构化关系（用于增强prompt）
        relations = self._extract_relations_from_subgraph(subgraph)
        
        return {
            'document_ids': document_ids,
            'subgraph': subgraph,
            'relations': relations,
            'matched_nodes': matched_node_ids
        }
    
    def _extract_entities_from_query(self, query: str) -> List[str]:
        """
        从查询中提取实体（使用大模型）
        
        调用Qwen大模型进行智能实体识别，
        比传统分词更准确，能识别专业术语和复合概念
        """
        try:
            # 读取prompt模板
            config = get_config()
            prompt_path = config.project_root / "config" / "prompts" / "query_entity_extraction.txt"
            
            if not prompt_path.exists():
                logger.warning(f"实体提取prompt不存在: {prompt_path}，使用简单分词")
                return self._simple_entity_extraction(query)
            
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
            
            # 构建prompt
            prompt = prompt_template.replace("{query}", query)
            
            # 调用Qwen（使用generate方法，传入messages格式）
            qwen_client = get_qwen_client()
            response = qwen_client.generate(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.1
            )
            
            # 解析返回的实体列表（逗号分隔）
            if response and response.strip():
                entities = [e.strip() for e in response.split(',') if e.strip()]
                logger.info(f"大模型提取到实体: {entities}")
                return entities
            else:
                logger.warning("大模型返回空结果，使用简单分词")
                return self._simple_entity_extraction(query)
                
        except Exception as e:
            logger.error(f"大模型实体提取失败: {e}，回退到简单分词")
            return self._simple_entity_extraction(query)
    
    def _simple_entity_extraction(self, query: str) -> List[str]:
        """
        简单分词（回退方案）
        当大模型不可用时使用
        """
        # 提取2-6个字的中文词组
        words = []
        for i in range(len(query)):
            for j in range(2, 7):
                if i + j <= len(query):
                    word = query[i:i+j]
                    if re.match(r'^[\u4e00-\u9fa5]+$', word):
                        words.append(word)
        
        # 过滤停用词
        stopwords = {
            '的', '有', '是', '对', '和', '与', '在', '了', '吗', '呢', 
            '什么', '如何', '怎么', '为什么', '哪些', '可以', '需要', 
            '应该', '能否', '关于', '这个', '那个', '这些', '那些',
            '我们', '你们', '他们', '我的', '你的', '他的', '包括',
            '内容', '知道', '应当', '那些'
        }
        entities = [w for w in words if w not in stopwords and len(w) >= 2]
        
        # 去重
        seen = set()
        unique = []
        for e in entities:
            if e not in seen:
                seen.add(e)
                unique.append(e)
        
        return unique[:10]  # 限制数量
    
    def _extract_document_ids_from_subgraph(self, subgraph: PolicyGraph) -> List[str]:
        """
        从子图中提取政策文档的ID
        
        假设：政策节点类型为POLICY，且有metadata['document_id']
        """
        if not subgraph:
            return []
        
        document_ids = []
        for node_id, node in subgraph.nodes.items():
            if node.node_type == NodeType.POLICY:
                # 从节点属性中获取文档ID
                doc_id = node.attributes.get('document_id') or node.attributes.get('policy_id')
                if doc_id:
                    document_ids.append(str(doc_id))
        
        return list(set(document_ids))  # 去重
    
    def _extract_relations_from_subgraph(self, subgraph: PolicyGraph) -> List[Dict]:
        """提取三元组关系"""
        if not subgraph:
            return []
        
        relations = []
        for edge in subgraph.edges:
            source = subgraph.get_node(edge.source_id)
            target = subgraph.get_node(edge.target_id)
            if source and target:
                relations.append({
                    'source': source.label,
                    'relation': edge.relation_type.value,
                    'target': target.label
                })
        
        # 限制关系数量，避免prompt过长
        return relations[:20]


# 单例模式
_retriever_instance = None

def get_hybrid_retriever() -> HybridRetriever:
    """获取混合检索器实例（单例）"""
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = HybridRetriever()
    return _retriever_instance
