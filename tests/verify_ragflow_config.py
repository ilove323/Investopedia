#!/usr/bin/env python3
"""
RAGFlow配置更新验证工具
=======================

尝试所有可能的API端点来更新知识库配置，并验证结果

使用方法：
    python verify_ragflow_config.py
"""
import sys
from pathlib import Path
import requests
import json

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.config import get_config


def test_config_update_methods():
    """测试所有可能的配置更新方法"""
    print("🔧 RAGFlow配置更新验证")
    print("=" * 50)
    
    config = get_config()
    base_url = config.ragflow_base_url
    api_key = config.ragflow_api_key
    kb_name = getattr(config, 'ragflow_kb_name', 'policy_demo_kb')
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 目标配置
    target_config = {
        "chunk_token_num": 800,
        "similarity_threshold": 0.3,
        "layout_recognize": "deepdoc",
        "enable_metadata": True,
        "overlapped_percent": 0.125  # 100/800 = 0.125
    }
    
    print(f"知识库: {kb_name}")
    print(f"目标配置: {target_config}")
    
    # 首先获取知识库ID
    kb_id = get_knowledge_base_id(base_url, headers, kb_name)
    if not kb_id:
        print("❌ 无法获取知识库ID")
        return
        
    print(f"知识库ID: {kb_id}")
    
    # 测试不同的更新端点和方法
    endpoints_to_test = [
        # 使用知识库名称
        f"/api/v1/datasets/{kb_name}",
        f"/api/v1/datasets/{kb_name}/config",
        f"/api/v1/datasets/{kb_name}/parser_config",
        f"/api/v1/datasets/{kb_name}/chunk_config",
        
        # 使用知识库ID
        f"/api/v1/datasets/{kb_id}",
        f"/api/v1/datasets/{kb_id}/config", 
        f"/api/v1/datasets/{kb_id}/parser_config",
        f"/api/v1/datasets/{kb_id}/chunk_config",
    ]
    
    methods_to_test = ["PUT", "PATCH", "POST"]
    
    print(f"\n🧪 测试 {len(endpoints_to_test)} 个端点 x {len(methods_to_test)} 种方法...")
    
    success_count = 0
    
    for endpoint in endpoints_to_test:
        print(f"\n📍 端点: {endpoint}")
        
        for method in methods_to_test:
            try:
                url = f"{base_url.rstrip('/')}{endpoint}"
                
                if method == "PUT":
                    response = requests.put(url, headers=headers, json=target_config, timeout=10)
                elif method == "PATCH":
                    response = requests.patch(url, headers=headers, json=target_config, timeout=10)
                else:  # POST
                    response = requests.post(url, headers=headers, json=target_config, timeout=10)
                
                status = response.status_code
                
                if status == 200:
                    print(f"  ✅ {method}: {status} - 成功")
                    try:
                        data = response.json()
                        if data.get('code') == 0:
                            print(f"    🎉 配置更新成功!")
                            success_count += 1
                        else:
                            print(f"    ⚠️ 响应: {data}")
                    except:
                        print(f"    📄 响应: {response.text[:100]}...")
                        
                elif status == 405:
                    print(f"  🚫 {method}: {status} - 方法不允许")
                elif status == 404:
                    print(f"  ❓ {method}: {status} - 端点不存在")
                elif status in [401, 403]:
                    print(f"  🔐 {method}: {status} - 权限问题")
                else:
                    print(f"  ❗ {method}: {status}")
                    try:
                        error_data = response.json()
                        print(f"    错误: {error_data}")
                    except:
                        print(f"    错误: {response.text[:100]}...")
                        
            except requests.exceptions.Timeout:
                print(f"  ⏰ {method}: 超时")
            except Exception as e:
                print(f"  💥 {method}: 异常 - {e}")
    
    print(f"\n📊 总结:")
    print(f"成功的更新: {success_count}")
    
    if success_count > 0:
        print(f"\n🔍 验证配置是否真的更新了...")
        verify_configuration_changed(base_url, headers, kb_name)
    else:
        print(f"\n❌ 没有找到有效的配置更新方法")
        print_manual_config_instruction(kb_name)


def get_knowledge_base_id(base_url, headers, kb_name):
    """获取知识库ID"""
    try:
        response = requests.get(f"{base_url}/api/v1/datasets", headers=headers)
        data = response.json()
        
        for dataset in data.get('data', []):
            if dataset.get('name') == kb_name:
                return dataset.get('id')
        return None
    except Exception as e:
        print(f"获取知识库ID失败: {e}")
        return None


def verify_configuration_changed(base_url, headers, kb_name):
    """验证配置是否真的改变了"""
    try:
        response = requests.get(f"{base_url}/api/v1/datasets", headers=headers)
        data = response.json()
        
        for dataset in data.get('data', []):
            if dataset.get('name') == kb_name:
                parser_config = dataset.get('parser_config', {})
                
                print(f"当前配置:")
                print(f"  分块Token数: {parser_config.get('chunk_token_num')}")
                print(f"  相似度阈值: {dataset.get('similarity_threshold')}")
                print(f"  布局识别: {parser_config.get('layout_recognize')}")
                print(f"  启用元数据: {parser_config.get('enable_metadata')}")
                
                return
                
    except Exception as e:
        print(f"验证配置失败: {e}")


def print_manual_config_instruction(kb_name):
    """打印手动配置指导"""
    print(f"\n💡 手动配置指导:")
    config = get_config()
    print(f"1. 访问RAGFlow界面: {config.ragflow_base_url}")
    print(f"2. 进入知识库 '{kb_name}' 的设置")
    print(f"3. 手动设置以下参数:")
    print(f"   - 分块大小: 800")
    print(f"   - 分块重叠: 100") 
    print(f"   - 相似度阈值: 0.3")
    print(f"   - 解析器: deepdoc")
    print(f"   - 启用元数据: True")


if __name__ == "__main__":
    test_config_update_methods()