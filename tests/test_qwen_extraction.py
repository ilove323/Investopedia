"""
测试Qwen实体抽取
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.qwen_client import get_qwen_client
from src.services.ragflow_client import get_ragflow_client
from src.config import get_config
import json

config = get_config()
ragflow = get_ragflow_client()
qwen = get_qwen_client()

kb_name = config.ragflow_kb_name

# 获取一个文档的内容
docs = ragflow.get_documents(kb_name)
if docs:
    doc = docs[0]
    print(f"测试文档: {doc['name']}")
    print("=" * 60)
    
    # 获取文档内容
    content = ragflow.get_document_content(doc['id'], kb_name)
    if content:
        # 截取前2000字符测试
        test_content = content[:2000]
        print(f"\n文档内容长度: {len(content)}")
        print(f"测试内容（前2000字符）:\n{test_content}\n")
        print("=" * 60)
        
        # 调用Qwen提取实体
        print("\n开始调用Qwen提取实体和关系...")
        result = qwen.extract_entities_and_relations(test_content, doc['name'])
        
        print(f"\n提取结果:")
        print(f"实体数量: {len(result.get('entities', []))}")
        print(f"关系数量: {len(result.get('relations', []))}")
        
        print("\n实体列表:")
        for idx, entity in enumerate(result.get('entities', []), 1):
            print(f"  {idx}. {entity.get('text')} ({entity.get('type')})")
            print(f"     描述: {entity.get('description', 'N/A')}")
        
        print("\n关系列表:")
        for idx, relation in enumerate(result.get('relations', []), 1):
            print(f"  {idx}. {relation.get('source')} --[{relation.get('type')}]--> {relation.get('target')}")
        
        print("\n完整结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("无法获取文档内容")
else:
    print("没有文档")
