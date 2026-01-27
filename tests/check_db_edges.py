"""检查数据库中的边（关系）数据"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3

def main():
    db_path = "data/database/investopedia.db"
    
    print("=" * 80)
    print("检查数据库中的图谱数据")
    print("=" * 80)
    print()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查nodes表
    cursor.execute("SELECT COUNT(*) FROM graph_nodes")
    node_count = cursor.fetchone()[0]
    print(f"📊 节点总数: {node_count}")
    
    if node_count > 0:
        cursor.execute("SELECT id, label, type FROM graph_nodes LIMIT 10")
        print("\n前10个节点:")
        for row in cursor.fetchall():
            print(f"  ID={row[0]}, Label={row[1][:40]}, Type={row[2]}")
    
    print()
    
    # 检查edges表
    cursor.execute("SELECT COUNT(*) FROM graph_edges")
    edge_count = cursor.fetchone()[0]
    print(f"🔗 边总数: {edge_count}")
    
    if edge_count > 0:
        cursor.execute("SELECT id, source_id, target_id, type, label FROM graph_edges LIMIT 20")
        print("\n前20条边:")
        for row in cursor.fetchall():
            print(f"  ID={row[0]}, {row[1]} -> {row[2]}, Type={row[3]}, Label={row[4]}")
    else:
        print("\n⚠️  数据库中没有边数据！")
        print("检查graph_edges表结构:")
        cursor.execute("PRAGMA table_info(graph_edges)")
        for col in cursor.fetchall():
            print(f"  {col[1]} ({col[2]})")
    
    conn.close()
    
    print()
    print("=" * 80)

if __name__ == '__main__':
    main()
