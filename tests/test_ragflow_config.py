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


def test_knowledge_base_config():
    """测试知识库配置"""
    print("\n=== 测试知识库配置 ===")
    
    try:
        client = get_ragflow_client()
        
        # 手动配置知识库
        print("开始配置知识库...")
        success = client.configure_knowledge_base()
        
        if success:
            print("✅ 知识库配置成功")
        else:
            print("⚠️ 知识库配置失败或部分失败")
            
        # 获取当前配置
        print("\n📋 知识库当前配置:")
        current_config = client.get_knowledge_base_config()
        
        if current_config:
            for section, values in current_config.items():
                print(f"\n  {section}:")
                for key, value in values.items():
                    print(f"    {key}: {value}")
                    
            # 配置对比
            print(f"\n🔍 配置对比分析:")
            config = get_config()
            expected_config = {**config.ragflow_document_config, **config.ragflow_advanced_config}
            
            actual_basic = current_config.get("知识库基本信息", {})
            actual_parser = current_config.get("解析器配置", {})
            
            comparisons = [
                ("分块大小", expected_config.get('chunk_size', 800), actual_parser.get('分块Token数')),
                ("相似度阈值", expected_config.get('similarity_threshold', 0.3), actual_basic.get('相似度阈值')),
                ("分块方法", expected_config.get('pdf_parser', 'deepdoc'), actual_basic.get('分块方法')),
                ("元数据提取", expected_config.get('metadata_extraction', True), actual_parser.get('启用元数据')),
                ("表格识别", expected_config.get('table_recognition', True), actual_parser.get('表格解析')),
            ]
            
            for name, expected, actual in comparisons:
                status = "✅" if str(expected).lower() == str(actual).lower() else "❌"
                print(f"    {status} {name}: 期望={expected}, 实际={actual}")
                
        else:
            print("  ❌ 无法获取当前配置")
            
    except Exception as e:
        print(f"❌ 知识库配置测试失败: {e}")


def main():
    """主测试函数"""
    print("RAGFlow配置测试开始...\n")
    
    # 1. 测试配置读取
    test_config_loading()
    
    # 2. 测试服务连接
    test_ragflow_connection()
    
    # 3. 测试知识库配置
    test_knowledge_base_config()
    
    print("\n配置测试完成!")


if __name__ == "__main__":
    main()