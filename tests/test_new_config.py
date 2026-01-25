#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试新的配置系统和提示词加载
"""

import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config.config_loader import ConfigLoader

def test_new_config():
    print("🔧 测试新配置系统")
    print("=" * 50)
    
    try:
        config = ConfigLoader()
        
        # 测试基本配置
        print("\n📋 基本配置:")
        print(f"  项目根目录: {config.project_root}")
        print(f"  提示词目录: {config.prompts_dir}")
        
        # 测试政策库配置
        print("\n🏛️ 政策库配置:")
        print(f"  知识库名称: {config.policy_kb_name}")
        print(f"  知识库描述: {config.policy_kb_description}")
        print(f"  知识库语言: {config.policy_kb_language}")
        
        # 测试政策专用配置
        print("\n⚙️ 政策专用配置:")
        policy_config = config.get_policy_config()
        for key, value in policy_config.items():
            print(f"  {key}: {value}")
        
        # 测试提示词加载
        print("\n📝 提示词配置:")
        print(f"  系统提示词长度: {len(config.policy_kb_system_prompt)} 字符")
        print(f"  问答提示词长度: {len(config.policy_kb_qa_prompt)} 字符")
        print(f"  实体抽取提示词长度: {len(config.policy_kb_entity_extraction)} 字符")
        print(f"  政策摘要提示词长度: {len(config.policy_summarize_prompt)} 字符")
        
        # 展示部分提示词内容
        print("\n📖 政策库系统提示词预览:")
        system_prompt = config.policy_kb_system_prompt
        print(system_prompt[:200] + "..." if len(system_prompt) > 200 else system_prompt)
        
        # 测试多知识库配置支持
        print("\n🔄 多知识库配置支持测试:")
        print("  政策库配置:")
        policy_config = config.get_kb_config("policy")
        print(f"    分块大小: {policy_config['chunk_size']}")
        print(f"    相似度阈值: {policy_config['similarity_threshold']}")
        print(f"    图谱检索: {policy_config['graph_retrieval']}")
        
        print("  通用库配置（示例）:")
        general_config = config.get_kb_config("general")
        print(f"    分块大小: {general_config['chunk_size']}")
        print(f"    相似度阈值: {general_config['similarity_threshold']}")
        print(f"    图谱检索: {general_config['graph_retrieval']}")
        
        print("\n✅ 配置系统测试完成！")
        
    except Exception as e:
        print(f"❌ 配置系统测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_new_config()