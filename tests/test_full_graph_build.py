"""完整测试图谱构建流程"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.data_sync import DataSyncService
from src.config import get_config

def main():
    config = get_config()
    
    print("=" * 80)
    print("开始测试完整图谱构建流程...")
    print("=" * 80)
    print()
    
    try:
        # 创建数据同步服务
        sync_service = DataSyncService()
        
        # 构建图谱
        print("正在构建知识图谱...")
        result = sync_service.build_knowledge_graph()
        
        print()
        print("=" * 80)
        print("图谱构建完成!")
        print("=" * 80)
        print()
        print(f"成功: {result.get('success')}")
        print(f"节点数: {result.get('node_count', 0)}")
        print(f"边数: {result.get('edge_count', 0)}")
        print(f"文档数: {result.get('doc_count', 0)}")
        print(f"耗时: {result.get('elapsed_time')}")
        print()
        
        if result.get('edge_count', 0) == 0:
            print("⚠️  警告: 图谱中没有边（关系）！")
            print()
            print("可能的原因:")
            print("1. Qwen提取的关系source/target匹配不上entities")
            print("2. 实体ID映射有问题")
            print("3. 关系未被正确添加到edges列表")
            print()
            print("请查看上面的日志输出，特别注意:")
            print("- '实体抽取完成'的日志，查看有多少实体间关系")
            print("- '关系源实体未找到'或'关系目标实体未找到'的警告")
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
