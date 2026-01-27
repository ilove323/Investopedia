#!/usr/bin/env python3
"""
RAGFlow配置测试脚本
==================

验证config.ini中的RAGFlow配置参数能否正确读取和应用

使用方法：
    python test_ragflow_config.py
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.config import get_config
from src.services.ragflow_client import get_ragflow_client


def test_config_loading():
    """测试配置文件读取"""
    print("=== 测试配置文件读取 ===")
    
    config = get_config()
    
    print(f"RAGFlow基础URL: {config.ragflow_base_url}")
    print(f"API Key: {config.ragflow_api_key[:8]}..." if config.ragflow_api_key else "API Key: 未配置")
    print(f"超时时间: {config.ragflow_timeout}秒")
    
    # 测试文档配置
    doc_config = config.ragflow_document_config
    print(f"\n文档配置参数 ({len(doc_config)}个):")
    for key, value in doc_config.items():
        print(f"  {key}: {value}")
    
    # 测试高级配置
    advanced_config = config.ragflow_advanced_config
    print(f"\n高级配置参数 ({len(advanced_config)}个):")
    for key, value in advanced_config.items():
        print(f"  {key}: {value}")


def test_ragflow_connection():
    """测试RAGFlow连接"""
    print("\n=== 测试RAGFlow连接 ===")
    
    try:
        # 获取客户端（会自动应用配置）
        client = get_ragflow_client()
        
        # 测试知识库存在性
        config = get_config()
        kb_name = getattr(config, 'ragflow_kb_name', 'policy_demo_kb')
        
        print(f"\n检查知识库: {kb_name}")
        kb_exists = client._check_knowledge_base_exists(kb_name)
        
        if kb_exists:
            print(f"✅ 知识库 '{kb_name}' 存在")
        else:
            print(f"❌ 知识库 '{kb_name}' 不存在")
            print(f"💡 请在RAGFlow界面创建知识库: {config.ragflow_base_url}")
        
        # 检查健康状态
        if client.check_health():
            print("✅ RAGFlow服务连接正常")
        else:
            print("⚠️ RAGFlow服务连接异常")
            
    except Exception as e:
        print(f"❌ RAGFlow连接失败: {e}")


def main():
    """主测试函数"""
    print("RAGFlow配置测试开始...\n")
    
    # 1. 测试配置读取
    test_config_loading()
    
    # 2. 测试服务连接
    test_ragflow_connection()
    
    print("\n配置测试完成!")


if __name__ == "__main__":
    main()