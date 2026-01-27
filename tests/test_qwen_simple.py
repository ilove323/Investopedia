"""简单测试Qwen实体抽取"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import get_config
from src.services.qwen_client import get_qwen_client
import time

def main():
    config = get_config()
    
    # 测试文本
    test_text = """
广东省商事登记条例
第一条 为优化营商环境，保护市场主体合法权益，促进市场主体发展，
根据《中华人民共和国公司法》等法律法规，结合本省实际，制定本条例。
第二条 本条例适用于在本省行政区域内依法设立的有限责任公司、
股份有限公司、合伙企业、个人独资企业、个体工商户、农民专业合作社
等市场主体的商事登记。
第三条 广东省市场监督管理部门负责本省商事登记工作的指导和监督。
    """
    
    print("=" * 80)
    print("开始测试Qwen实体抽取...")
    print("=" * 80)
    
    start_time = time.time()
    
    try:
        qwen = get_qwen_client()
        print(f"✓ Qwen客户端初始化成功")
        print(f"  模型: {qwen.model}")
        print(f"  Temperature: {qwen.temperature}")
        print()
        
        print("调用Qwen API...")
        result = qwen.extract_entities_and_relations(
            text=test_text, 
            doc_title="广东省商事登记条例"
        )
        
        elapsed = time.time() - start_time
        print(f"✓ API调用完成 (耗时: {elapsed:.2f}秒)")
        print()
        
        # 打印结果
        entities = result.get('entities', [])
        relations = result.get('relations', [])
        
        print(f"提取结果:")
        print(f"  实体数量: {len(entities)}")
        print(f"  关系数量: {len(relations)}")
        print()
        
        if entities:
            print("实体列表:")
            for i, entity in enumerate(entities[:10], 1):
                print(f"  {i}. {entity.get('text')} ({entity.get('type')})")
            if len(entities) > 10:
                print(f"  ... 还有 {len(entities)-10} 个实体")
            print()
        
        if relations:
            print("关系列表:")
            for i, rel in enumerate(relations[:10], 1):
                print(f"  {i}. {rel.get('source')} -> {rel.get('target')} ({rel.get('type')})")
            if len(relations) > 10:
                print(f"  ... 还有 {len(relations)-10} 个关系")
        else:
            print("⚠️  未提取到任何关系！")
        
        print()
        print("=" * 80)
        
        if not relations:
            print("\n问题诊断:")
            print("1. 检查提示词是否明确要求返回relations")
            print("2. 检查Qwen返回的原始JSON")
            print("3. 检查实体text是否能匹配上")
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
