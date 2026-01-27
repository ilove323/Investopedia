#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试更新后的RAGFlow客户端和政策库专用配置
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.ragflow_client import RAGFlowClient
from config.config_loader import ConfigLoader

def test_updated_ragflow_client():
    print("🔧 测试更新后的RAGFlow客户端")
    print("=" * 50)
    
    try:
        # 1. 测试配置加载
        print("\n📋 加载配置:")
        config = ConfigLoader()
        print(f"  政策库名称: {config.policy_kb_name}")
        print(f"  政策库描述: {config.policy_kb_description}")
        
        # 显示政策专用配置
        policy_config = config.get_policy_config()
        print(f"  政策专用配置: {len(policy_config)} 个参数")
        print(f"  分块大小: {policy_config['chunk_size']}")
        print(f"  图谱检索: {policy_config['graph_retrieval']}")
        print(f"  PDF解析器: {policy_config['pdf_parser']}")
        
        # 2. 测试RAGFlow客户端初始化
        print("\n🔄 初始化RAGFlow客户端:")
        client = RAGFlowClient()
        
        # 3. 测试健康检查
        print("\n📖 测试RAGFlow连接:")
        health = client.check_health()
        
        if health:
            print(f"✅ 成功连接RAGFlow")
        else:
            print(f"❌ 无法连接RAGFlow")
            print(f"  图谱检索: {图谱配置.get('使用图谱')}")
            print(f"  实体归一化: {图谱配置.get('实体归一化')}")
            print(f"  布局识别: {解析器配置.get('布局识别')}")
            
            # 检查配置是否符合政策库要求
            print("\n🔍 配置验证:")
            chunk_size = 解析器配置.get('分块Token数')
            graph_enabled = 图谱配置.get('使用图谱')
            layout_parser = 解析器配置.get('布局识别')
            
            if chunk_size and chunk_size >= 800:
                print("  ✅ 分块大小适合政策文档")
            else:
                print(f"  ⚠️  分块大小可能过小: {chunk_size}")
                
            if graph_enabled:
                print("  ✅ 图谱检索已启用")
            else:
                print("  ⚠️  图谱检索未启用")
                
            if layout_parser == 'deepdoc':
                print("  ✅ 使用深度文档解析")
            else:
                print(f"  ⚠️  未使用深度解析器: {layout_parser}")
        else:
            print("❌ 无法读取知识库配置")
        
        # 4. 测试提示词
        print("\n📝 测试提示词:")
        system_prompt = config.policy_kb_system_prompt
        qa_prompt = config.policy_kb_qa_prompt
        
        print(f"  系统提示词: {len(system_prompt)} 字符")
        print(f"  问答提示词: {len(qa_prompt)} 字符")
        
        if "专项债" in system_prompt and "特许经营" in system_prompt:
            print("  ✅ 包含政策相关内容")
        else:
            print("  ⚠️  提示词可能不够具体")
        
        print("\n🎉 RAGFlow客户端测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_updated_ragflow_client()