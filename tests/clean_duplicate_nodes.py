"""清理图谱中的重复节点"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.graph_dao import GraphDAO
from src.config import get_config

def main():
    print("=" * 80)
    print("清理图谱重复节点")
    print("=" * 80)
    print()
    
    config = get_config()
    db_path = config.data_dir / "database" / "policies.db"
    
    graph_dao = GraphDAO(str(db_path))
    
    print("正在清理重复节点...")
    result = graph_dao.remove_duplicate_nodes()
    
    print()
    print("清理结果:")
    print(f"  删除节点数: {result.get('removed_nodes', 0)}")
    print(f"  删除边数: {result.get('removed_edges', 0)}")
    
    if 'error' in result:
        print(f"  错误: {result['error']}")
    
    # 显示清理后的统计
    print()
    print("清理后的图谱统计:")
    stats = graph_dao.get_stats()
    if stats:
        print(f"  节点总数: {stats.get('node_count', 0)}")
        print(f"  边总数: {stats.get('edge_count', 0)}")
    
    print()
    print("=" * 80)
    print("✅ 清理完成！请刷新浏览器页面查看效果")
    print("=" * 80)

if __name__ == '__main__':
    main()
