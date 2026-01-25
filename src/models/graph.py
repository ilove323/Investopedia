"""
知识图谱数据模型
=============
定义知识图谱的数据结构，基于NetworkX实现政策关系网络的表示和操作。

核心类：
- NodeType：节点类型（政策、机关、地区、概念、项目）
- RelationType：关系类型（发布、适用、引用、影响、替代、修订、相关）
- GraphNode：图谱节点，代表一个对象（政策、机关等）
- GraphEdge：图谱边，代表两个对象间的关系
- PolicyGraph：政策图谱，基于NetworkX的完整实现

功能特性：
- 支持添加/删除节点和边
- 支持路径查询、连通分量、自我网络等图论算法
- 支持图谱统计和子图提取
- 支持序列化为字典格式

使用示例：
    from src.models.graph import PolicyGraph, GraphNode, GraphEdge, NodeType, RelationType

    graph = PolicyGraph()
    node1 = GraphNode(node_id='policy_1', label='政策A', node_type=NodeType.POLICY)
    node2 = GraphNode(node_id='auth_1', label='财政部', node_type=NodeType.AUTHORITY)

    graph.add_node(node1)
    graph.add_node(node2)

    edge = GraphEdge(source_id='policy_1', target_id='auth_1', relation_type=RelationType.ISSUED_BY)
    graph.add_edge(edge)
"""
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List, Any, Set, Tuple
from enum import Enum
import networkx as nx


class NodeType(str, Enum):
    """节点类型"""
    POLICY = "policy"
    AUTHORITY = "authority"
    REGION = "region"
    CONCEPT = "concept"
    PROJECT = "project"


class RelationType(str, Enum):
    """关系类型"""
    ISSUED_BY = "issued_by"  # 由...发布
    APPLIES_TO = "applies_to"  # 适用于...
    REFERENCES = "references"  # 引用...
    AFFECTS = "affects"  # 影响...
    REPLACES = "replaces"  # 替代...
    AMENDS = "amends"  # 修订...
    RELATES_TO = "relates_to"  # 相关...


@dataclass
class GraphNode:
    """图谱节点"""
    node_id: str
    label: str
    node_type: NodeType = NodeType.POLICY
    attributes: Dict[str, Any] = None

    def __post_init__(self):
        """初始化后处理"""
        if self.attributes is None:
            self.attributes = {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.node_id,
            'label': self.label,
            'type': self.node_type.value,
            'attributes': self.attributes
        }

    def set_attribute(self, key: str, value: Any):
        """设置属性"""
        self.attributes[key] = value

    def get_attribute(self, key: str, default: Any = None) -> Any:
        """获取属性"""
        return self.attributes.get(key, default)


@dataclass
class GraphEdge:
    """图谱边"""
    source_id: str
    target_id: str
    relation_type: RelationType
    label: str = ""
    attributes: Dict[str, Any] = None

    def __post_init__(self):
        """初始化后处理"""
        if self.attributes is None:
            self.attributes = {}
        if not self.label:
            self.label = self.relation_type.value

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'source': self.source_id,
            'target': self.target_id,
            'relation_type': self.relation_type.value,
            'label': self.label,
            'attributes': self.attributes
        }

    def set_attribute(self, key: str, value: Any):
        """设置属性"""
        self.attributes[key] = value


class PolicyGraph:
    """政策知识图谱（NetworkX封装）"""

    def __init__(self):
        """初始化图谱"""
        self.graph = nx.Graph()
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []

    def add_node(self, node: GraphNode) -> bool:
        """
        添加节点

        Args:
            node: GraphNode对象

        Returns:
            是否成功添加
        """
        try:
            if node.node_id not in self.nodes:
                self.graph.add_node(
                    node.node_id,
                    label=node.label,
                    type=node.node_type.value,
                    **node.attributes
                )
                self.nodes[node.node_id] = node
                return True
            return False
        except Exception:
            return False

    def add_edge(self, edge: GraphEdge) -> bool:
        """
        添加边

        Args:
            edge: GraphEdge对象

        Returns:
            是否成功添加
        """
        try:
            # 确保两个节点都存在
            if edge.source_id not in self.nodes or edge.target_id not in self.nodes:
                return False

            # 避免重复边
            for existing_edge in self.edges:
                if (existing_edge.source_id == edge.source_id and
                    existing_edge.target_id == edge.target_id and
                    existing_edge.relation_type == edge.relation_type):
                    return False

            self.graph.add_edge(
                edge.source_id,
                edge.target_id,
                relation_type=edge.relation_type.value,
                label=edge.label,
                **edge.attributes
            )
            self.edges.append(edge)
            return True
        except Exception:
            return False

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """获取节点"""
        return self.nodes.get(node_id)

    def get_neighbors(self, node_id: str) -> List[GraphNode]:
        """获取节点的邻接节点"""
        if node_id not in self.graph:
            return []

        neighbor_ids = list(self.graph.neighbors(node_id))
        return [self.nodes[nid] for nid in neighbor_ids if nid in self.nodes]

    def get_related_nodes(self, node_id: str, relation_type: Optional[RelationType] = None) -> List[Tuple[GraphNode, RelationType]]:
        """
        获取指定关系类型的相关节点

        Args:
            node_id: 节点ID
            relation_type: 关系类型（None表示所有关系）

        Returns:
            [(相关节点, 关系类型), ...]
        """
        result = []

        if node_id not in self.graph:
            return result

        for edge in self.edges:
            if edge.source_id == node_id:
                if relation_type is None or edge.relation_type == relation_type:
                    target_node = self.nodes.get(edge.target_id)
                    if target_node:
                        result.append((target_node, edge.relation_type))
            elif edge.target_id == node_id:
                if relation_type is None or edge.relation_type == relation_type:
                    source_node = self.nodes.get(edge.source_id)
                    if source_node:
                        result.append((source_node, edge.relation_type))

        return result

    def get_shortest_path(self, source_id: str, target_id: str) -> Optional[List[str]]:
        """获取两个节点之间的最短路径"""
        try:
            if source_id not in self.graph or target_id not in self.graph:
                return None
            return nx.shortest_path(self.graph, source_id, target_id)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def get_connected_component(self, node_id: str) -> List[GraphNode]:
        """获取节点所在的连通分量中的所有节点"""
        if node_id not in self.graph:
            return []

        component_ids = nx.node_connected_component(self.graph, node_id)
        return [self.nodes[nid] for nid in component_ids if nid in self.nodes]

    def get_subgraph_by_nodes(self, node_ids: List[str]) -> 'PolicyGraph':
        """
        获取由指定节点组成的子图

        Args:
            node_ids: 节点ID列表

        Returns:
            子图
        """
        subgraph = PolicyGraph()

        # 添加节点
        for node_id in node_ids:
            if node_id in self.nodes:
                subgraph.add_node(self.nodes[node_id])

        # 添加边
        for edge in self.edges:
            if edge.source_id in node_ids and edge.target_id in node_ids:
                subgraph.add_edge(edge)

        return subgraph

    def get_ego_graph(self, node_id: str, radius: int = 1) -> 'PolicyGraph':
        """
        获取节点的自我网络（ego graph）

        Args:
            node_id: 中心节点ID
            radius: 半径

        Returns:
            自我网络
        """
        if node_id not in self.graph:
            return PolicyGraph()

        ego_subgraph = nx.ego_graph(self.graph, node_id, radius=radius)
        ego_node_ids = list(ego_subgraph.nodes())

        return self.get_subgraph_by_nodes(ego_node_ids)

    def get_stats(self) -> Dict[str, Any]:
        """获取图谱统计信息"""
        node_count = len(self.nodes)
        edge_count = len(self.edges)
        
        # 对于空图或无效图的安全处理
        if node_count == 0:
            return {
                'node_count': 0,
                'edge_count': 0,
                'density': 0,
                'number_of_connected_components': 0,
                'diameter': None
            }
        
        try:
            # 计算图谱统计信息
            density = nx.density(self.graph) if self.graph.number_of_nodes() > 0 else 0
            num_components = nx.number_connected_components(self.graph)
            
            # 计算直径需要图是连通的且有足够节点
            diameter = None
            if node_count > 1 and nx.is_connected(self.graph):
                try:
                    diameter = nx.diameter(self.graph)
                except (nx.NetworkXError, nx.NetworkXNoPath):
                    diameter = None
            
            return {
                'node_count': node_count,
                'edge_count': edge_count,
                'density': density,
                'number_of_connected_components': num_components,
                'diameter': diameter
            }
        except Exception as e:
            # 如果计算统计信息失败，返回基本信息
            return {
                'node_count': node_count,
                'edge_count': edge_count,
                'density': 0,
                'number_of_connected_components': 0,
                'diameter': None,
                'error': str(e)
            }

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'nodes': [node.to_dict() for node in self.nodes.values()],
            'edges': [edge.to_dict() for edge in self.edges],
            'stats': self.get_stats()
        }

    def get_node_count(self) -> int:
        """获取节点数"""
        return len(self.nodes)

    def get_edge_count(self) -> int:
        """获取边数"""
        return len(self.edges)

    def is_valid(self) -> bool:
        """检查图谱是否有效"""
        return len(self.nodes) > 0 and len(self.edges) > 0

    def clear(self):
        """清空图谱"""
        self.graph.clear()
        self.nodes.clear()
        self.edges.clear()

    def get_nx_graph(self) -> nx.Graph:
        """获取NetworkX图对象（用于可视化）"""
        return self.graph
