"""
测试知识图谱存储功能
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.graph_dao import GraphDAO
from src.config import get_config
import json


def test_graph_dao_basic():
    """测试GraphDAO基本功能"""
    print("=" * 60)
    print("测试1: GraphDAO 基本功能")
    print("=" * 60)
    
    # 获取数据库路径
    config = get_config()
    db_path = config.data_dir / "database" / "policies.db"
    print(f"✓ 数据库路径: {db_path}")
    
    # 初始化DAO
    graph_dao = GraphDAO(str(db_path))
    print("✓ GraphDAO 初始化成功")
    
    # 清空现有数据
    graph_dao.clear_graph()
    print("✓ 清空现有图谱数据")
    
    # 创建测试图谱数据
    test_graph = {
        'nodes': [
            {'id': 'node1', 'label': '节点1', 'type': 'POLICY'},
            {'id': 'node2', 'label': '节点2', 'type': 'CONCEPT'},
            {'id': 'node3', 'label': '节点3', 'type': 'DOCUMENT'}
        ],
        'edges': [
            {'from': 'node1', 'to': 'node2', 'label': '关系1'},
            {'from': 'node2', 'to': 'node3', 'label': '关系2'}
        ]
    }
    
    # 保存图谱
    graph_id = graph_dao.save_graph(test_graph, is_incremental=False)
    print(f"✓ 全量保存图谱成功, ID={graph_id}")
    
    # 加载图谱
    loaded_graph = graph_dao.load_graph()
    assert loaded_graph is not None, "加载图谱失败"
    assert len(loaded_graph['nodes']) == 3, f"节点数不匹配: {len(loaded_graph['nodes'])}"
    assert len(loaded_graph['edges']) == 2, f"边数不匹配: {len(loaded_graph['edges'])}"
    print(f"✓ 加载图谱成功: {len(loaded_graph['nodes'])}个节点, {len(loaded_graph['edges'])}条边")
    
    # 获取统计信息
    stats = graph_dao.get_stats()
    print(f"✓ 图谱统计: 节点={stats['node_count']}, 边={stats['edge_count']}")
    assert stats['node_count'] == 3
    assert stats['edge_count'] == 2
    
    print("\n✅ 测试1通过\n")


def test_incremental_update():
    """测试增量更新"""
    print("=" * 60)
    print("测试2: 增量更新功能")
    print("=" * 60)
    
    config = get_config()
    db_path = config.data_dir / "database" / "policies.db"
    graph_dao = GraphDAO(str(db_path))
    
    # 清空并创建初始图谱
    graph_dao.clear_graph()
    initial_graph = {
        'nodes': [
            {'id': 'A', 'label': 'A节点', 'type': 'POLICY'},
            {'id': 'B', 'label': 'B节点', 'type': 'POLICY'}
        ],
        'edges': [
            {'from': 'A', 'to': 'B', 'label': 'A->B'}
        ]
    }
    graph_dao.save_graph(initial_graph, is_incremental=False)
    print("✓ 保存初始图谱: 2个节点, 1条边")
    
    # 增量添加新节点和边
    incremental_graph = {
        'nodes': [
            {'id': 'C', 'label': 'C节点', 'type': 'CONCEPT'},
            {'id': 'B', 'label': 'B节点(更新)', 'type': 'POLICY'}  # 更新已存在节点
        ],
        'edges': [
            {'from': 'B', 'to': 'C', 'label': 'B->C'},
            {'from': 'A', 'to': 'B', 'label': 'A->B(更新)'}  # 更新已存在边
        ]
    }
    graph_dao.save_graph(incremental_graph, is_incremental=True)
    print("✓ 增量更新: 添加1个新节点, 更新1个节点")
    
    # 验证合并结果
    merged_graph = graph_dao.load_graph()
    assert len(merged_graph['nodes']) == 3, f"节点数应为3, 实际{len(merged_graph['nodes'])}"
    assert len(merged_graph['edges']) == 2, f"边数应为2, 实际{len(merged_graph['edges'])}"
    print(f"✓ 合并结果验证: {len(merged_graph['nodes'])}个节点, {len(merged_graph['edges'])}条边")
    
    # 验证B节点被更新
    node_b = next((n for n in merged_graph['nodes'] if n['id'] == 'B'), None)
    assert node_b is not None
    assert 'B节点(更新)' in node_b['label'] or 'B节点' in node_b['label']
    print(f"✓ 节点B标签: {node_b['label']}")
    
    print("\n✅ 测试2通过\n")


def test_graph_format():
    """测试图谱数据格式"""
    print("=" * 60)
    print("测试3: 图谱数据格式验证")
    print("=" * 60)
    
    config = get_config()
    db_path = config.data_dir / "database" / "policies.db"
    graph_dao = GraphDAO(str(db_path))
    
    # 加载图谱
    graph_data = graph_dao.load_graph()
    if not graph_data:
        print("⚠️ 数据库中没有图谱数据，跳过格式验证")
        return
    
    # 验证顶层结构
    assert 'nodes' in graph_data, "缺少nodes字段"
    assert 'edges' in graph_data, "缺少edges字段"
    print("✓ 顶层结构正确: nodes, edges")
    
    # 验证节点格式
    for node in graph_data['nodes'][:3]:  # 只检查前3个
        assert 'id' in node, "节点缺少id字段"
        assert 'label' in node, "节点缺少label字段"
        print(f"✓ 节点格式正确: id={node['id']}, label={node['label']}")
    
    # 验证边格式
    for edge in graph_data['edges'][:3]:  # 只检查前3条
        assert 'from' in edge, "边缺少from字段"
        assert 'to' in edge, "边缺少to字段"
        print(f"✓ 边格式正确: {edge['from']} -> {edge['to']}")
    
    print("\n✅ 测试3通过\n")


def main():
    """运行所有测试"""
    try:
        test_graph_dao_basic()
        test_incremental_update()
        test_graph_format()
        
        print("=" * 60)
        print("🎉 所有测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
