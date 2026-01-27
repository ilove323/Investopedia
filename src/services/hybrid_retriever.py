"""
混合检索器：本地知识图谱 + RAGFlow向量检索
===========================================

核心思路：图谱粗筛 + 向量精排
- 从查询中提取实体
- 在本地图谱中模糊匹配节点
- 构建子图并提取相关政策的document_ids
- 返回图谱上下文（用于增强prompt和可视化）
"""
import logging
import re
from typing import List, Dict, Any, Optional

from src.models.graph import PolicyGraph, NodeType

logger = logging.getLogger(__name__)


class HybridRetriever:
    """混合检索器：知识图谱 + 向量检索"""
    
    def __init__(self):
        self.graph = None
    
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
            
            # 如果缓存不存在，则构建新图谱（仅首次或缓存失效时）
            from src.pages.graph_page import build_policy_graph
            logger.warning("⚠️ 缓存不存在，正在构建知识图谱（可能较慢）...")
            self.graph = build_policy_graph()
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
        从查询中提取实体
        
        简单实现：分词 + 过滤常见词
        高级实现：可以调用NER模型
        """
        # 提取中文词（2个字以上）
        words = re.findall(r'[\u4e00-\u9fa5]{2,}', query)
        
        # 过滤停用词
        stopwords = {
            '的', '有', '是', '对', '和', '与', '在', '了', '吗', '呢', 
            '什么', '如何', '怎么', '为什么', '哪些', '可以', '需要', 
            '应该', '能否', '关于', '这个', '那个', '这些', '那些',
            '我们', '你们', '他们', '我的', '你的', '他的'
        }
        entities = [w for w in words if w not in stopwords and len(w) >= 2]
        
        # 去重并保持顺序
        seen = set()
        unique_entities = []
        for entity in entities:
            if entity not in seen:
                seen.add(entity)
                unique_entities.append(entity)
        
        return unique_entities
    
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
