"""
调试RAGFlow文档信息
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.ragflow_client import get_ragflow_client
from src.config import get_config
import json

config = get_config()
ragflow = get_ragflow_client()
kb_name = config.ragflow_kb_name

print(f"知识库: {kb_name}")
print("=" * 60)

# 直接使用RAGFlow SDK
print("\n【方法1】使用封装的get_documents方法：")
docs = ragflow.get_documents(kb_name)
print(f"文档总数: {len(docs)}")
for doc in docs:
    print(f"  - {doc.get('name')}: chunk_num={doc.get('chunk_num')}, token_num={doc.get('token_num')}")

# 直接访问RAGFlow SDK
print("\n【方法2】直接使用RAGFlow SDK原始API：")
try:
    dataset = ragflow.rag.get_dataset(name=kb_name)
    if dataset:
        print(f"Dataset对象: {dataset}")
        raw_docs = dataset.list_documents(page=1, page_size=100)
        print(f"原始文档数: {len(raw_docs)}")
        
        for idx, doc in enumerate(raw_docs, 1):
            print(f"\n文档 {idx}: {doc.name}")
            print(f"  原始对象类型: {type(doc)}")
            print(f"  所有属性:")
            for attr in dir(doc):
                if not attr.startswith('_'):
                    try:
                        value = getattr(doc, attr)
                        if not callable(value):
                            print(f"    {attr} = {value}")
                    except:
                        pass
except Exception as e:
    print(f"直接访问失败: {e}")
    import traceback
    traceback.print_exc()


