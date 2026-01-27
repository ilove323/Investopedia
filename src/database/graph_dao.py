"""
知识图谱数据访问对象
提供图谱在SQLite中的存储和查询功能
"""
import json
import sqlite3
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)


class GraphDAO:
    """知识图谱数据访问类"""
    
    def __init__(self, db_path: str):
        """初始化GraphDAO
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._init_table()
    
    def _init_table(self):
        """创建知识图谱表"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_graph (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                graph_data TEXT NOT NULL,
                node_count INTEGER DEFAULT 0,
                edge_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            conn.commit()
            conn.close()
            logger.info("知识图谱表初始化成功")
        except Exception as e:
            logger.error(f"知识图谱表初始化失败: {e}")
            raise
    
    def save_graph(self, graph_data: Dict[str, Any], is_incremental: bool = False) -> int:
        """保存图谱到数据库
        
        Args:
            graph_data: 图谱数据，格式：{'nodes': [...], 'edges': [...]}
            is_incremental: 是否增量更新
            
        Returns:
            图谱ID
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if is_incremental:
                # 增量更新：合并现有图谱
                existing = self.load_graph()
                if existing:
                    graph_data = self._merge_graphs(existing, graph_data)
            else:
                # 全量更新：删除旧数据
                cursor.execute("DELETE FROM knowledge_graph")
            
            # 统计节点和边
            node_count = len(graph_data.get('nodes', []))
            edge_count = len(graph_data.get('edges', []))
            
            # 转换为JSON
            graph_json = json.dumps(graph_data, ensure_ascii=False)
            
            # 插入新数据
            cursor.execute("""
            INSERT INTO knowledge_graph (graph_data, node_count, edge_count, updated_at)
            VALUES (?, ?, ?, ?)
            """, (graph_json, node_count, edge_count, datetime.now()))
            
            graph_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"图谱保存成功: {node_count}个节点, {edge_count}条边 (增量={is_incremental})")
            return graph_id
            
        except Exception as e:
            logger.error(f"图谱保存失败: {e}")
            raise
    
    def load_graph(self) -> Optional[Dict[str, Any]]:
        """从数据库加载最新的图谱
        
        Returns:
            图谱数据字典，如果不存在返回None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT graph_data FROM knowledge_graph 
            ORDER BY updated_at DESC LIMIT 1
            """)
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                graph_data = json.loads(result[0])
                logger.debug(f"图谱加载成功: {len(graph_data.get('nodes', []))}个节点")
                return graph_data
            
            logger.info("数据库中没有图谱数据")
            return None
            
        except Exception as e:
            logger.error(f"图谱加载失败: {e}")
            return None
    
    def remove_duplicate_nodes(self) -> Dict[str, int]:
        """
        清理图谱中重复的节点（基于label）
        
        Returns:
            清理结果：{'removed_nodes': 数量, 'removed_edges': 数量}
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取最新图谱
            cursor.execute("""
            SELECT id, graph_data FROM knowledge_graph 
            ORDER BY updated_at DESC LIMIT 1
            """)
            
            result = cursor.fetchone()
            if not result:
                conn.close()
                return {'removed_nodes': 0, 'removed_edges': 0}
            
            graph_id, graph_json = result
            graph_data = json.loads(graph_json)
            
            # 去重节点（保留第一个出现的）
            seen_labels = {}
            old_to_new_id = {}  # 旧ID到新ID的映射
            unique_nodes = []
            
            for node in graph_data.get('nodes', []):
                label = node.get('label', '')
                node_id = node.get('id')
                
                # 规范化label（去除文件后缀）
                normalized_label = label.replace('.pdf', '').replace('.docx', '').strip()
                
                if normalized_label not in seen_labels:
                    # 第一次见到这个label，保留（并更新label去掉后缀）
                    node['label'] = normalized_label
                    node['title'] = node.get('title', '').replace('.pdf', '').replace('.docx', '')
                    seen_labels[normalized_label] = node_id
                    old_to_new_id[node_id] = node_id
                    unique_nodes.append(node)
                else:
                    # 重复节点，记录ID映射
                    old_to_new_id[node_id] = seen_labels[normalized_label]
            
            # 更新边，使用新的节点ID映射
            unique_edges = []
            valid_node_ids = set(seen_labels.values())
            
            for edge in graph_data.get('edges', []):
                from_id = old_to_new_id.get(edge.get('from'))
                to_id = old_to_new_id.get(edge.get('to'))
                
                # 只保留有效的边
                if from_id and to_id and from_id in valid_node_ids and to_id in valid_node_ids:
                    # 更新边的节点ID
                    edge['from'] = from_id
                    edge['to'] = to_id
                    
                    # 避免重复边
                    edge_key = f"{from_id}->{to_id}-{edge.get('type', '')}"
                    if edge_key not in seen_labels:
                        seen_labels[edge_key] = True
                        unique_edges.append(edge)
            
            removed_nodes = len(graph_data['nodes']) - len(unique_nodes)
            removed_edges = len(graph_data['edges']) - len(unique_edges)
            
            if removed_nodes > 0 or removed_edges > 0:
                # 更新数据库
                graph_data['nodes'] = unique_nodes
                graph_data['edges'] = unique_edges
                
                cursor.execute("""
                UPDATE knowledge_graph 
                SET graph_data = ?, node_count = ?, edge_count = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """, (
                    json.dumps(graph_data, ensure_ascii=False),
                    len(unique_nodes),
                    len(unique_edges),
                    graph_id
                ))
                
                conn.commit()
                logger.info(f"清理完成: 删除{removed_nodes}个重复节点, {removed_edges}条无效边")
            
            conn.close()
            return {'removed_nodes': removed_nodes, 'removed_edges': removed_edges}
            
        except Exception as e:
            logger.error(f"清理重复节点失败: {e}")
            return {'removed_nodes': 0, 'removed_edges': 0, 'error': str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """获取图谱统计信息
        
        Returns:
            统计信息字典
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT node_count, edge_count, updated_at, created_at
            FROM knowledge_graph 
            ORDER BY updated_at DESC LIMIT 1
            """)
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'node_count': result[0],
                    'edge_count': result[1],
                    'last_updated': result[2],
                    'created_at': result[3]
                }
            
            return {
                'node_count': 0,
                'edge_count': 0,
                'last_updated': None,
                'created_at': None
            }
            
        except Exception as e:
            logger.error(f"获取图谱统计失败: {e}")
            return {}
    
    def _merge_graphs(self, existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        """合并两个图谱（增量更新时使用）
        
        Args:
            existing: 现有图谱
            new: 新图谱
            
        Returns:
            合并后的图谱
        """
        # 合并节点（基于id去重）
        existing_nodes = {node['id']: node for node in existing.get('nodes', [])}
        new_nodes = {node['id']: node for node in new.get('nodes', [])}
        existing_nodes.update(new_nodes)
        
        # 合并边（基于 from-to 去重）
        existing_edges = {(edge['from'], edge['to']): edge for edge in existing.get('edges', [])}
        new_edges = {(edge['from'], edge['to']): edge for edge in new.get('edges', [])}
        existing_edges.update(new_edges)
        
        merged = {
            'nodes': list(existing_nodes.values()),
            'edges': list(existing_edges.values())
        }
        
        logger.info(f"图谱合并完成: {len(merged['nodes'])}个节点, {len(merged['edges'])}条边")
        return merged
    
    def clear_graph(self):
        """清空所有图谱数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM knowledge_graph")
            conn.commit()
            conn.close()
            logger.info("图谱数据已清空")
        except Exception as e:
            logger.error(f"清空图谱失败: {e}")
            raise
