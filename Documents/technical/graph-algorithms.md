# 🕸️ 知识图谱算法详解

> PolicyGraph实现和图算法应用  
> 阅读时间: 20分钟

---

## 🎯 图谱数据结构

### 节点（GraphNode）

```python
@dataclass
class GraphNode:
    id: str                  # 唯一标识，如 "POLICY_科技创新政策"
    label: str               # 显示名称
    type: NodeType           # 节点类型
    properties: Dict         # 扩展属性
```

**NodeType枚举**:
```python
class NodeType(Enum):
    POLICY = "政策文档"
    AUTHORITY = "发布机构"
    REGION = "地区"
    CONCEPT = "概念/领域"
    PROJECT = "项目/计划"
```

---

### 边（GraphEdge）

```python
@dataclass
class GraphEdge:
    from_node: str           # 源节点ID
    to_node: str             # 目标节点ID
    type: RelationType       # 关系类型
    properties: Dict         # 扩展属性（如权重、时间戳）
```

**RelationType枚举**:
```python
class RelationType(Enum):
    ISSUED_BY = "发布关系"          # 政策 → 机构
    APPLIES_TO = "适用关系"         # 政策 → 对象
    REFERENCES = "引用关系"         # 政策 → 政策
    AFFECTS = "影响关系"            # 政策 → 概念
    BELONGS_TO = "从属关系"         # 机构 → 地区
    RELATED_TO = "相关关系"         # 通用关系
```

---

## 🏗️ PolicyGraph实现

### 核心类

```python
# src/models/graph.py
import networkx as nx
from typing import List, Dict, Optional, Tuple

class PolicyGraph:
    """
    政策知识图谱
    基于NetworkX封装，提供业务层图算法
    """
    
    def __init__(self):
        # 使用有向图
        self.graph = nx.DiGraph()
    
    def add_node(self, node: GraphNode):
        """添加节点"""
        self.graph.add_node(
            node.id,
            label=node.label,
            type=node.type.value,
            **node.properties
        )
    
    def add_edge(self, edge: GraphEdge):
        """添加边"""
        self.graph.add_edge(
            edge.from_node,
            edge.to_node,
            type=edge.type.value,
            **edge.properties
        )
    
    def get_node(self, node_id: str) -> Optional[Dict]:
        """获取节点数据"""
        if node_id in self.graph:
            data = self.graph.nodes[node_id]
            return {
                'id': node_id,
                'label': data.get('label'),
                'type': data.get('type'),
                **data
            }
        return None
    
    def get_neighbors(self, node_id: str, direction: str = 'both') -> List[str]:
        """
        获取邻居节点
        
        Args:
            node_id: 节点ID
            direction: 'in'(入边), 'out'(出边), 'both'(双向)
        """
        if direction == 'in':
            return list(self.graph.predecessors(node_id))
        elif direction == 'out':
            return list(self.graph.successors(node_id))
        else:
            return list(self.graph.predecessors(node_id)) + list(self.graph.successors(node_id))
    
    def find_shortest_path(self, source: str, target: str) -> Optional[List[str]]:
        """
        查找最短路径（Dijkstra算法）
        """
        try:
            return nx.shortest_path(self.graph, source, target)
        except nx.NetworkXNoPath:
            return None
    
    def find_all_paths(self, source: str, target: str, cutoff: int = 5) -> List[List[str]]:
        """
        查找所有路径（限制最大长度）
        """
        try:
            return list(nx.all_simple_paths(self.graph, source, target, cutoff=cutoff))
        except nx.NodeNotFound:
            return []
    
    def get_connected_components(self) -> List[List[str]]:
        """
        获取连通分量（无向图视角）
        """
        undirected = self.graph.to_undirected()
        return list(nx.connected_components(undirected))
    
    def calculate_centrality(self, algorithm: str = 'degree') -> Dict[str, float]:
        """
        计算节点中心性
        
        Args:
            algorithm: 'degree', 'betweenness', 'closeness', 'pagerank'
        """
        if algorithm == 'degree':
            return dict(self.graph.degree())
        elif algorithm == 'betweenness':
            return nx.betweenness_centrality(self.graph)
        elif algorithm == 'closeness':
            return nx.closeness_centrality(self.graph)
        elif algorithm == 'pagerank':
            return nx.pagerank(self.graph)
        else:
            raise ValueError(f"未知算法: {algorithm}")
    
    def get_subgraph(self, node_ids: List[str]) -> 'PolicyGraph':
        """
        提取子图
        """
        subgraph = PolicyGraph()
        subgraph.graph = self.graph.subgraph(node_ids).copy()
        return subgraph
    
    def filter_by_node_type(self, node_type: NodeType) -> 'PolicyGraph':
        """
        按节点类型筛选
        """
        filtered_nodes = [
            n for n, data in self.graph.nodes(data=True)
            if data.get('type') == node_type.value
        ]
        return self.get_subgraph(filtered_nodes)
    
    def filter_by_edge_type(self, edge_type: RelationType) -> 'PolicyGraph':
        """
        按边类型筛选
        """
        filtered_graph = PolicyGraph()
        
        # 复制所有节点
        for node, data in self.graph.nodes(data=True):
            filtered_graph.graph.add_node(node, **data)
        
        # 只添加匹配类型的边
        for u, v, data in self.graph.edges(data=True):
            if data.get('type') == edge_type.value:
                filtered_graph.graph.add_edge(u, v, **data)
        
        return filtered_graph
    
    def get_stats(self) -> Dict:
        """
        获取图谱统计信息
        """
        return {
            'node_count': self.graph.number_of_nodes(),
            'edge_count': self.graph.number_of_edges(),
            'density': nx.density(self.graph),
            'is_connected': nx.is_weakly_connected(self.graph),
            'average_degree': sum(dict(self.graph.degree()).values()) / max(self.graph.number_of_nodes(), 1),
            'node_types': self._count_node_types(),
            'edge_types': self._count_edge_types()
        }
    
    def _count_node_types(self) -> Dict[str, int]:
        """统计各类型节点数量"""
        counts = {}
        for _, data in self.graph.nodes(data=True):
            node_type = data.get('type', 'UNKNOWN')
            counts[node_type] = counts.get(node_type, 0) + 1
        return counts
    
    def _count_edge_types(self) -> Dict[str, int]:
        """统计各类型边数量"""
        counts = {}
        for _, _, data in self.graph.edges(data=True):
            edge_type = data.get('type', 'UNKNOWN')
            counts[edge_type] = counts.get(edge_type, 0) + 1
        return counts
    
    def to_dict(self) -> Dict:
        """
        导出为字典格式（用于JSON存储）
        """
        return {
            'nodes': [
                {
                    'id': n,
                    **data
                }
                for n, data in self.graph.nodes(data=True)
            ],
            'edges': [
                {
                    'from': u,
                    'to': v,
                    **data
                }
                for u, v, data in self.graph.edges(data=True)
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PolicyGraph':
        """
        从字典加载（用于JSON读取）
        """
        graph = cls()
        
        # 添加节点
        for node in data.get('nodes', []):
            node_id = node.pop('id')
            graph.graph.add_node(node_id, **node)
        
        # 添加边
        for edge in data.get('edges', []):
            from_node = edge.pop('from')
            to_node = edge.pop('to')
            graph.graph.add_edge(from_node, to_node, **edge)
        
        return graph
```

---

## 🧮 图算法应用

### 1. 最短路径查询

**应用场景**: 查找两个政策/机构之间的关系链路

```python
# src/pages/graph_page.py
def find_policy_relationship(source_policy: str, target_policy: str):
    """
    查找两个政策之间的关系路径
    """
    graph = load_graph_from_database()
    
    source_id = f"POLICY_{source_policy}"
    target_id = f"POLICY_{target_policy}"
    
    path = graph.find_shortest_path(source_id, target_id)
    
    if path:
        print(f"最短路径 ({len(path)-1}步):")
        for i in range(len(path) - 1):
            from_node = graph.get_node(path[i])
            to_node = graph.get_node(path[i+1])
            edge_data = graph.graph[path[i]][path[i+1]]
            
            print(f"{from_node['label']} --[{edge_data['type']}]--> {to_node['label']}")
    else:
        print("未找到路径")
```

**示例输出**:
```
最短路径 (3步):
科技创新政策 --[ISSUED_BY]--> 广东省科技厅
广东省科技厅 --[BELONGS_TO]--> 广东省
广东省 --[CONTAINS]--> 深圳市创新政策
```

---

### 2. 中心性分析

**应用场景**: 找出最重要的政策/机构

```python
def analyze_policy_importance():
    """
    分析政策重要性（基于中心性）
    """
    graph = load_graph_from_database()
    
    # 度中心性（直接连接数）
    degree_centrality = graph.calculate_centrality('degree')
    
    # PageRank（考虑间接影响）
    pagerank = graph.calculate_centrality('pagerank')
    
    # 只分析政策节点
    policy_nodes = [
        (n, d) for n, d in graph.graph.nodes(data=True)
        if d.get('type') == 'POLICY'
    ]
    
    # 按PageRank排序
    ranked_policies = sorted(
        policy_nodes,
        key=lambda x: pagerank.get(x[0], 0),
        reverse=True
    )
    
    print("Top 10最重要政策:")
    for i, (node_id, data) in enumerate(ranked_policies[:10]):
        print(f"{i+1}. {data['label']}")
        print(f"   度中心性: {degree_centrality.get(node_id, 0)}")
        print(f"   PageRank: {pagerank.get(node_id, 0):.4f}")
```

---

### 3. 社区发现

**应用场景**: 识别政策簇（如同一领域的政策）

```python
def discover_policy_communities():
    """
    发现政策社区（基于Louvain算法）
    """
    graph = load_graph_from_database()
    
    # 转为无向图
    undirected = graph.graph.to_undirected()
    
    # Louvain社区发现
    import community as community_louvain
    partition = community_louvain.best_partition(undirected)
    
    # 按社区分组
    communities = {}
    for node, comm_id in partition.items():
        if comm_id not in communities:
            communities[comm_id] = []
        communities[comm_id].append(node)
    
    # 输出结果
    for comm_id, members in communities.items():
        print(f"\n社区 {comm_id} ({len(members)}个节点):")
        for node_id in members[:5]:  # 只显示前5个
            node = graph.get_node(node_id)
            print(f"  - {node['label']} ({node['type']})")
```

---

### 4. 影响力传播

**应用场景**: 分析政策变更的影响范围

```python
def analyze_policy_impact(policy_id: str, max_depth: int = 3):
    """
    分析政策影响范围（BFS广度优先搜索）
    """
    graph = load_graph_from_database()
    
    visited = set()
    queue = [(policy_id, 0)]  # (节点, 深度)
    impact_nodes = {0: [policy_id]}  # 按层级记录
    
    while queue:
        current_node, depth = queue.pop(0)
        
        if depth >= max_depth or current_node in visited:
            continue
        
        visited.add(current_node)
        
        # 获取所有出边（影响的节点）
        neighbors = graph.get_neighbors(current_node, direction='out')
        
        for neighbor in neighbors:
            if neighbor not in visited:
                queue.append((neighbor, depth + 1))
                
                if depth + 1 not in impact_nodes:
                    impact_nodes[depth + 1] = []
                impact_nodes[depth + 1].append(neighbor)
    
    # 输出结果
    policy = graph.get_node(policy_id)
    print(f"政策 '{policy['label']}' 的影响分析:")
    
    for depth, nodes in sorted(impact_nodes.items()):
        print(f"\n第{depth}层影响 ({len(nodes)}个节点):")
        for node_id in nodes[:5]:
            node = graph.get_node(node_id)
            print(f"  - {node['label']} ({node['type']})")
```

---

## 🎨 可视化算法

### Pyvis布局算法

```python
# src/components/graph_ui.py
from pyvis.network import Network

def render_network_graph(graph: PolicyGraph, title: str = "知识图谱"):
    """
    渲染交互式网络图
    """
    net = Network(
        height="700px",
        width="100%",
        bgcolor="#ffffff",
        font_color="black",
        directed=True
    )
    
    # 设置物理布局
    net.set_options("""
    {
        "physics": {
            "enabled": true,
            "barnesHut": {
                "gravitationalConstant": -8000,
                "centralGravity": 0.3,
                "springLength": 95,
                "springConstant": 0.04,
                "damping": 0.09
            }
        },
        "nodes": {
            "font": {"size": 14},
            "borderWidth": 2,
            "shadow": true
        },
        "edges": {
            "arrows": {"to": {"enabled": true, "scaleFactor": 0.5}},
            "smooth": {"type": "continuous"}
        }
    }
    """)
    
    # 定义颜色映射
    color_map = {
        'POLICY': '#3498db',      # 蓝色
        'AUTHORITY': '#2ecc71',   # 绿色
        'REGION': '#f39c12',      # 橙色
        'CONCEPT': '#9b59b6',     # 紫色
        'PROJECT': '#e74c3c'      # 红色
    }
    
    # 添加节点
    for node_id, data in graph.graph.nodes(data=True):
        net.add_node(
            node_id,
            label=data.get('label', node_id),
            color=color_map.get(data.get('type'), '#95a5a6'),
            title=f"{data.get('type')}: {data.get('label')}",  # 悬停提示
            size=20
        )
    
    # 添加边
    for u, v, data in graph.graph.edges(data=True):
        net.add_edge(
            u, v,
            title=data.get('type', ''),  # 悬停提示
            label=data.get('type', '')
        )
    
    # 生成HTML
    html = net.generate_html()
    
    # 在Streamlit中显示
    import streamlit.components.v1 as components
    components.html(html, height=700)
```

---

## 🔍 高级查询

### 复杂路径查询

```python
def find_policy_influence_chain(start_policy: str, target_entity: str):
    """
    查找政策如何影响特定实体（支持多跳）
    """
    graph = load_graph_from_database()
    
    start_id = f"POLICY_{start_policy}"
    
    # 查找所有可能路径（限制最大5跳）
    all_paths = []
    for node_id in graph.graph.nodes():
        node = graph.get_node(node_id)
        if target_entity.lower() in node['label'].lower():
            paths = graph.find_all_paths(start_id, node_id, cutoff=5)
            all_paths.extend(paths)
    
    if all_paths:
        print(f"找到 {len(all_paths)} 条影响路径:")
        for i, path in enumerate(all_paths[:3]):  # 只显示前3条
            print(f"\n路径 {i+1}:")
            for j in range(len(path) - 1):
                from_node = graph.get_node(path[j])
                to_node = graph.get_node(path[j+1])
                edge_data = graph.graph[path[j]][path[j+1]]
                print(f"  {from_node['label']} --[{edge_data['type']}]--> {to_node['label']}")
```

---

## 🔗 相关文档

- [02-ARCHITECTURE.md](../02-ARCHITECTURE.md) - 系统架构
- [data-flow.md](data-flow.md) - 数据流详解
- [modules-inventory.md](modules-inventory.md) - 模块清单

---

**Last Updated**: 2026-02-01
