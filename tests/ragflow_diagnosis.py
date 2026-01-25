#!/usr/bin/env python3
"""
RAGFlow 诊断和配置助手
====================

帮助诊断和修复RAGFlow配置问题

使用方法：
    python ragflow_diagnosis.py
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.config import get_config
from src.services.ragflow_client import get_ragflow_client


def print_diagnosis_header():
    """打印诊断标题"""
    print("=" * 60)
    print("🔍 RAGFlow 系统诊断")
    print("=" * 60)


def check_configuration():
    """检查配置状态"""
    print("\n📋 配置检查:")
    
    config = get_config()
    
    # 基础连接信息
    print(f"   RAGFlow URL: {config.ragflow_base_url}")
    print(f"   API Key: {'✅ 已配置' if config.ragflow_api_key else '❌ 未配置'}")
    print(f"   知识库名称: {getattr(config, 'ragflow_kb_name', 'policy_demo_kb')}")
    
    # 配置参数统计
    doc_config = config.ragflow_document_config
    advanced_config = config.ragflow_advanced_config
    print(f"   文档配置: {len(doc_config)} 个参数")
    print(f"   高级配置: {len(advanced_config)} 个参数")


def check_connectivity():
    """检查连接状态"""
    print("\n🌐 连接检查:")
    
    try:
        client = get_ragflow_client()
        
        if client.check_health():
            print("   ✅ RAGFlow 服务在线")
        else:
            print("   ❌ RAGFlow 服务离线")
            return False
            
        return True
    except Exception as e:
        print(f"   ❌ 连接失败: {e}")
        return False


def check_knowledge_base():
    """检查知识库状态"""
    print("\n📚 知识库检查:")
    
    try:
        config = get_config()
        client = get_ragflow_client()
        kb_name = getattr(config, 'ragflow_kb_name', 'policy_demo_kb')
        
        kb_exists = client._check_knowledge_base_exists(kb_name)
        
        if kb_exists:
            print(f"   ✅ 知识库 '{kb_name}' 存在")
            return True
        else:
            print(f"   ❌ 知识库 '{kb_name}' 不存在")
            return False
            
    except Exception as e:
        print(f"   ❌ 知识库检查失败: {e}")
        return False


def print_manual_config_guide():
    """打印手动配置指南"""
    print("\n" + "=" * 60)
    print("🔧 RAGFlow配置指南 (需手动操作)")
    print("=" * 60)
    
    config = get_config()
    kb_name = getattr(config, 'ragflow_kb_name', 'policy_demo_kb')
    
    print(f"\n⚠️  重要说明:")
    print(f"   当前RAGFlow版本不支持通过API自动配置知识库参数")
    print(f"   需要手动在Web界面中配置以下参数")
    
    print(f"\n📝 手动配置步骤:")
    print(f"\n1. 访问RAGFlow Web界面:")
    print(f"   👉 {config.ragflow_base_url}")
    
    print(f"\n2. 进入知识库设置:")
    print(f"   • 找到并选择知识库: {kb_name}")
    print(f"   • 点击 '设置' 或 '编辑' 按钮")
    
    print(f"\n3. 配置文档处理参数:")
    
    # 文档处理配置
    doc_config = config.ragflow_document_config
    print(f"\n   📄 分块和解析设置:")
    print(f"      • 分块大小(chunk_token_num): {doc_config.get('chunk_size', 800)}")
    print(f"      • 分块重叠(overlapped_percent): {doc_config.get('chunk_overlap', 100)/doc_config.get('chunk_size', 800):.3f} (约{doc_config.get('chunk_overlap', 100)}字符)")
    print(f"      • 解析器(layout_recognize): {doc_config.get('pdf_parser', 'deepdoc').upper()}")
    print(f"      • 启用元数据(enable_metadata): {'是' if doc_config.get('auto_metadata', True) else '否'}")
    print(f"      • 表格识别(table_enable): {'是' if doc_config.get('table_recognition', True) else '否'}")
    print(f"      • 公式识别(formula_enable): {'是' if doc_config.get('formula_recognition', False) else '否'}")
    
    # 高级配置
    advanced_config = config.ragflow_advanced_config
    print(f"\n   ⚙️ 检索和相似度设置:")
    print(f"      • 相似度阈值(similarity_threshold): {advanced_config.get('similarity_threshold', 0.3)}")
    print(f"      • 向量相似度权重: 0.3 (推荐)")
    print(f"      • 检索模式: {advanced_config.get('retrieval_mode', 'general')}")
    print(f"      • 实体归一化(entity_resolution): {'启用' if advanced_config.get('entity_normalization', True) else '禁用'}")
    print(f"      • 图谱检索(use_graphrag): {'启用' if advanced_config.get('graph_retrieval', True) else '禁用'}")
    
    print(f"\n4. 保存配置:")
    print(f"   • 点击 '保存' 或 '确定' 按钮")
    print(f"   • 等待配置生效(可能需要重新处理文档)")
    
    print(f"\n5. 验证配置:")
    print(f"   • 运行: python test_ragflow_config.py")
    print(f"   • 检查配置对比分析结果")
    
    print(f"\n💡 配置优化建议:")
    print(f"   • 政策文档通常较长，建议分块大小800-1000")
    print(f"   • 使用Laws分块方法处理法律文档") 
    print(f"   • 启用图谱功能增强语义检索")
    print(f"   • 启用表格识别提取结构化数据")
    
    print(f"\n🔄 配置验证:")
    print(f"   配置完成后，请再次运行测试脚本验证:")
    print(f"   python test_ragflow_config.py")


def print_troubleshooting():
    """打印故障排除指南"""
    print("\n" + "=" * 60)
    print("🔧 故障排除")
    print("=" * 60)
    
    print(f"\n❓ 常见问题和解决方案:")
    
    print(f"\n1. API 404 错误:")
    print(f"   • 原因: RAGFlow版本不同导致API端点差异")
    print(f"   • 解决: 使用Web界面手动配置")
    
    print(f"\n2. 知识库不存在:")
    print(f"   • 解决: 在RAGFlow界面创建知识库 'policy_demo_kb'")
    
    print(f"\n3. 连接失败:")
    print(f"   • 检查: RAGFlow服务是否正在运行")
    print(f"   • 检查: 网络连接和防火墙设置")
    
    print(f"\n4. 配置不生效:")
    print(f"   • 确认: 知识库已重新处理文档")
    print(f"   • 确认: 配置参数格式正确")


def main():
    """主函数"""
    print_diagnosis_header()
    
    # 执行诊断检查
    check_configuration()
    
    connectivity_ok = check_connectivity()
    if not connectivity_ok:
        print_troubleshooting()
        return
    
    kb_ok = check_knowledge_base()
    
    # 提供解决方案
    print_manual_config_guide()
    
    if not kb_ok:
        print_troubleshooting()
    
    print(f"\n" + "=" * 60)
    print("✅ 诊断完成")
    print("=" * 60)


if __name__ == "__main__":
    main()