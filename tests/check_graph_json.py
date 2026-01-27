"""检查数据库中的图谱JSON数据"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import json

def main():
    db_path = "data/database/policies.db"
    
    print("=" * 80)
    print("检查数据库中的图谱JSON数据")
    print("=" * 80)
    print()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取最新的图谱
    cursor.execute("""
        SELECT id, node_count, edge_count, graph_data 
        FROM knowledge_graph 
        ORDER BY id DESC 
        LIMIT 1
    """)
    
    row = cursor.fetchone()
    if not row:
        print("⚠️  数据库中没有图谱数据")
        return
    
    graph_id, node_count, edge_count, graph_json = row
    
    print(f"图谱ID: {graph_id}")
    print(f"节点数: {node_count}")
    print(f"边数: {edge_count}")
    print()
    
    # 解析JSON
    graph_data = json.loads(graph_json)
    nodes = graph_data.get('nodes', [])
    edges = graph_data.get('edges', [])
    
    print(f"实际解析:")
    print(f"  节点: {len(nodes)}")
    print(f"  边: {len(edges)}")
    print()
    
    if nodes:
        print("前5个节点:")
        for i, node in enumerate(nodes[:5], 1):
            print(f"  {i}. ID={node.get('id')}, Label={node.get('label')[:40]}, Type={node.get('type')}")
        print()
    
    if edges:
        print("前10条边:")
        for i, edge in enumerate(edges[:10], 1):
            print(f"  {i}. {edge.get('from')} -> {edge.get('to')}, Type={edge.get('type')}")
        print()
        
        # 统计边的类型
        edge_types = {}
        for edge in edges:
            edge_type = edge.get('type', 'unknown')
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
        
        print("边类型统计:")
        for edge_type, count in sorted(edge_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {edge_type}: {count}")
    else:
        print("⚠️  JSON中没有edges数据！")
    
    conn.close()
    
    print()
    print("=" * 80)

if __name__ == '__main__':
    main()
