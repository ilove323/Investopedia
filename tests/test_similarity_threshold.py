#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试相似度阈值更新
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from src.services.ragflow_client import RAGFlowClient
import time

def test_similarity_threshold():
    print("🔧 相似度阈值更新测试")
    print("=" * 50)
    
    # 初始化客户端
    client = RAGFlowClient()
    
    # 获取知识库配置
    config = client.get_knowledge_base_config("policy_demo_kb")
    if not config:
        print("❌ 无法获取知识库配置")
        return

    # 从嵌套结构中提取相似度阈值
    basic_info = config.get('知识库基本信息', {})
    current_threshold = basic_info.get('相似度阈值', 'Unknown')
    print(f"📋 当前相似度阈值: {current_threshold}")
    
    # 测试1：只设置相似度阈值
    print("\n🔄 测试1：只更新相似度阈值...")
    result = client._update_knowledge_base_config("policy_demo_kb", {
        "similarity_threshold": 0.3
    })
    
    if result:
        print("✅ API调用成功")
        time.sleep(3)  # 等待生效
        
        # 检查更新
        updated_config = client.get_knowledge_base_config("policy_demo_kb")
        if updated_config:
            basic_info = updated_config.get('知识库基本信息', {})
            new_threshold = basic_info.get('相似度阈值', 'Unknown')
            print(f"📋 更新后相似度阈值: {new_threshold}")
            if new_threshold != 'Unknown' and new_threshold is not None:
                try:
                    if float(new_threshold) == 0.3:
                        print("✅ 相似度阈值更新成功!")
                    else:
                        print(f"❌ 相似度阈值未更新: 期望0.3, 实际{new_threshold}")
                except (ValueError, TypeError):
                    print(f"⚠️ 无法解析相似度阈值: {new_threshold}")
            else:
                print("ℹ️ SDK未返回相似度阈值信息，但配置更新已发送")
    else:
        print("❌ API调用失败")
    
    # 测试2：通过raptor配置设置
    print("\n🔄 测试2：通过raptor阈值设置...")
    result = client._update_knowledge_base_config("policy_demo_kb", {
        "graph_retrieval": True,
        "similarity_threshold": 0.4  # 在raptor中设置
    })
    
    if result:
        print("✅ API调用成功")
        time.sleep(3)
        
        # 检查更新
        updated_config = client.get_knowledge_base_config("policy_demo_kb")
        if updated_config:
            new_threshold = updated_config.get('similarity_threshold', 'Unknown')
            print(f"📋 最终相似度阈值: {new_threshold}")

if __name__ == "__main__":
    test_similarity_threshold()