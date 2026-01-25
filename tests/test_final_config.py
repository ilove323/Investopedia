#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试重构后的配置系统
"""

import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config.config_loader import ConfigLoader
from services.ragflow_client import RAGFlowClient

def test_new_config_system():
    print("🔧 测试重构后的配置系统")
    print("=" * 60)
    
    try:
        config = ConfigLoader()
        
        # 1. 测试基本配置
        print("\n📋 基本配置:")
        print(f"  默认知识库: {config.default_kb_name}")
        print(f"  RAGFlow地址: {config.ragflow_base_url}")
        print(f"  提示词目录: {config.prompts_dir}")
        
        # 2. 测试可用知识库
        print("\n📚 可用知识库:")
        kb_names = config.get_available_kb_names()
        for kb_name in kb_names:
            print(f"  - {kb_name}")
        
        # 3. 测试政策库配置加载
        print("\n🏛️ 政策库配置:")
        policy_config = config.get_kb_config("policy_demo_kb")
        if policy_config:
            print(f"  知识库名称: {policy_config.get('kb_name')}")
            print(f"  知识库描述: {policy_config.get('kb_description')}")
            print(f"  分块大小: {policy_config.get('chunk_size')}")
            print(f"  图谱检索: {policy_config.get('graph_retrieval')}")
            print(f"  PDF解析器: {policy_config.get('pdf_parser')}")
            print(f"  提示词长度: {len(policy_config.get('system_prompt', ''))} 字符")
            
            # 显示提示词预览
            prompt = policy_config.get('system_prompt', '')
            if prompt:
                print(f"  提示词预览: {prompt[:100]}...")
        else:
            print("  ❌ 无法加载政策库配置")
        
        # 4. 测试默认配置（兼容性）
        print("\n🔄 兼容性测试:")
        default_config = config.get_kb_config()  # 使用默认知识库
        print(f"  默认库名称: {default_config.get('kb_name')}")
        print(f"  默认分块大小: {default_config.get('chunk_size')}")
        
        # 5. 测试RAGFlow客户端
        print("\n🚀 RAGFlow客户端测试:")
        client = RAGFlowClient(auto_configure=True)
        
        # 读取实际配置
        kb_config = client.get_knowledge_base_config()
        if kb_config:
            基本信息 = kb_config.get('知识库基本信息', {})
            解析器配置 = kb_config.get('解析器配置', {})
            
            print(f"✅ 成功连接RAGFlow:")
            print(f"  实际分块Token数: {解析器配置.get('分块Token数')}")
            print(f"  实际分块方法: {基本信息.get('分块方法')}")
            print(f"  实际布局识别: {解析器配置.get('布局识别')}")
            
            # 验证配置是否生效
            chunk_size = 解析器配置.get('分块Token数')
            if chunk_size and chunk_size >= 800:
                print("  ✅ 政策文档分块配置正确")
            else:
                print(f"  ⚠️  分块配置可能需要调整: {chunk_size}")
        else:
            print("  ❌ 无法连接RAGFlow或读取配置")
        
        print("\n🎉 配置系统测试完成！")
        print("\n💡 添加新知识库的步骤:")
        print("  1. 复制 config/knowledgebase/template.ini 为 新库名.ini")
        print("  2. 修改新配置文件中的参数")
        print("  3. 在 config/prompts/ 添加对应的提示词文件")
        print("  4. 在 config.ini 的 [KNOWLEDGE_BASES] 段添加映射")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_new_config_system()