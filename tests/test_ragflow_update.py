#!/usr/bin/env python3
"""
RAGFlow配置更新测试
===================

使用正确的API文档格式更新知识库配置

使用方法：
    python test_ragflow_update.py
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.config import get_config
from src.services.ragflow_client import get_ragflow_client


def test_configuration_update():
    """测试配置更新功能"""
    print("🔧 RAGFlow配置更新测试")
    print("=" * 50)
    
    config = get_config()
    kb_name = getattr(config, 'ragflow_kb_name', 'policy_demo_kb')
    
    # 获取RAGFlow客户端
    client = get_ragflow_client()
    
    print(f"知识库: {kb_name}")
    
    # 显示更新前的配置
    print(f"\n📋 更新前的配置:")
    current_config = client.get_knowledge_base_config(kb_name)
    if current_config:
        basic_info = current_config.get("知识库基本信息", {})
        parser_config = current_config.get("解析器配置", {})
        
        print(f"  分块方法: {basic_info.get('分块方法')}")
        print(f"  分块Token数: {parser_config.get('分块Token数')}")
        print(f"  相似度阈值: {basic_info.get('相似度阈值')}")
        print(f"  启用元数据: {parser_config.get('启用元数据')}")
    else:
        print("  无法获取当前配置")
    
    # 准备配置参数
    doc_config = config.ragflow_document_config
    advanced_config = config.ragflow_advanced_config
    config_params = {**doc_config, **advanced_config}
    
    print(f"\n🎯 目标配置:")
    print(f"  分块大小: {config_params.get('chunk_size', 800)}")
    print(f"  相似度阈值: {config_params.get('similarity_threshold', 0.3)}")
    print(f"  PDF解析器: {config_params.get('pdf_parser', 'deepdoc')}")
    print(f"  图谱检索: {config_params.get('graph_retrieval', True)}")
    print(f"  实体归一化: {config_params.get('entity_normalization', True)}")
    
    # 执行配置更新
    print(f"\n🔄 开始配置更新...")
    success = client._update_knowledge_base_config(kb_name, config_params)
    
    if success:
        print(f"✅ 配置更新成功!")
        
        # 等待一下让配置生效
        import time
        print(f"⏳ 等待配置生效...")
        time.sleep(3)
        
        # 验证更新后的配置
        print(f"\n📋 更新后的配置:")
        updated_config = client.get_knowledge_base_config(kb_name)
        if updated_config:
            basic_info = updated_config.get("知识库基本信息", {})
            parser_config = updated_config.get("解析器配置", {})
            
            print(f"  分块方法: {basic_info.get('分块方法')}")
            print(f"  分块Token数: {parser_config.get('分块Token数')}")
            print(f"  相似度阈值: {basic_info.get('相似度阈值')}")
            print(f"  启用元数据: {parser_config.get('启用元数据')}")
            
            # 配置对比
            print(f"\n🔍 配置验证:")
            comparisons = [
                ("分块Token数", config_params.get('chunk_size', 800), parser_config.get('分块Token数')),
                ("相似度阈值", config_params.get('similarity_threshold', 0.3), basic_info.get('相似度阈值')),
            ]
            
            for name, expected, actual in comparisons:
                if str(expected) == str(actual):
                    print(f"    ✅ {name}: {actual} (正确)")
                else:
                    print(f"    ❌ {name}: 期望={expected}, 实际={actual}")
        else:
            print("  ❌ 无法获取更新后的配置")
    else:
        print(f"❌ 配置更新失败")


if __name__ == "__main__":
    test_configuration_update()