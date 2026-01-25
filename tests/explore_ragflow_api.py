#!/usr/bin/env python3
"""
RAGFlow API端点探索工具
=======================

探索RAGFlow实际可用的API端点

使用方法：
    python explore_ragflow_api.py
"""
import sys
from pathlib import Path
import requests
import json

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.config import get_config
from src.services.api_utils import APIClient


def explore_api_endpoints():
    """探索可用的API端点"""
    config = get_config()
    
    base_url = config.ragflow_base_url
    api_key = config.ragflow_api_key
    
    headers = {
        "Authorization": f"Bearer {api_key}" if api_key else "",
        "Content-Type": "application/json"
    }
    
    print("🔍 RAGFlow API端点探索")
    print("=" * 50)
    print(f"Base URL: {base_url}")
    print(f"API Key: {'配置' if api_key else '未配置'}")
    
    # 要测试的端点列表
    endpoints_to_test = [
        # 根路径
        "/",
        "/api",
        "/v1",
        "/api/v1",
        
        # 知识库相关
        "/api/v1/kb",
        "/api/v1/datasets", 
        "/api/v1/knowledge_bases",
        "/v1/datasets",
        "/datasets",
        "/kb",
        
        # 具体知识库
        "/api/v1/datasets/policy_demo_kb",
        "/api/v1/kb/policy_demo_kb",
        "/v1/datasets/policy_demo_kb",
        "/datasets/policy_demo_kb",
        
        # 配置相关
        "/api/v1/datasets/policy_demo_kb/config",
        "/api/v1/kb/policy_demo_kb/config",
        "/api/v1/datasets/policy_demo_kb/chunk_method",
        
        # 文档相关
        "/api/v1/documents",
        "/api/documents",
        "/documents",
        
        # 其他可能的端点
        "/api/v1/chat",
        "/api/v1/retrieval",
        "/api/health",
        "/health",
        "/status",
        "/info"
    ]
    
    working_endpoints = []
    
    print(f"\n📡 测试 {len(endpoints_to_test)} 个端点...")
    
    for endpoint in endpoints_to_test:
        url = f"{base_url.rstrip('/')}{endpoint}"
        
        try:
            # 尝试GET请求
            response = requests.get(url, headers=headers, timeout=5)
            status = response.status_code
            
            if status == 200:
                print(f"✅ {endpoint} - {status} (成功)")
                working_endpoints.append((endpoint, status, "GET"))
                try:
                    data = response.json()
                    if isinstance(data, dict) and len(data) > 0:
                        print(f"   数据类型: {type(data)} 键: {list(data.keys())[:3]}")
                except:
                    print(f"   响应长度: {len(response.text)} 字符")
                    
            elif status == 405:  # Method Not Allowed
                print(f"🔄 {endpoint} - {status} (方法不允许，可能支持POST)")
                working_endpoints.append((endpoint, status, "POST"))
                
            elif status == 401:
                print(f"🔐 {endpoint} - {status} (需要认证)")
                working_endpoints.append((endpoint, status, "AUTH"))
                
            elif status == 404:
                print(f"❌ {endpoint} - {status}")
                
            else:
                print(f"❓ {endpoint} - {status}")
                working_endpoints.append((endpoint, status, "OTHER"))
                
        except requests.exceptions.ConnectionError:
            print(f"🔌 {endpoint} - 连接失败")
        except requests.exceptions.Timeout:
            print(f"⏰ {endpoint} - 超时")
        except Exception as e:
            print(f"❗ {endpoint} - 错误: {e}")
    
    print(f"\n📊 可用端点总结:")
    print("=" * 50)
    
    if working_endpoints:
        for endpoint, status, method in working_endpoints:
            print(f"{endpoint:40} {status} ({method})")
            
        # 专门测试知识库列表
        print(f"\n📚 详细测试知识库端点:")
        kb_endpoints = [ep for ep in working_endpoints if 'dataset' in ep[0] or 'kb' in ep[0]]
        
        for endpoint, status, method in kb_endpoints:
            if status == 200:
                url = f"{base_url.rstrip('/')}{endpoint}"
                try:
                    response = requests.get(url, headers=headers, timeout=5)
                    data = response.json()
                    print(f"\n{endpoint}:")
                    print(json.dumps(data, indent=2, ensure_ascii=False)[:500] + "...")
                except:
                    pass
                    
    else:
        print("❌ 没有找到可用的端点")
        
    return working_endpoints


if __name__ == "__main__":
    explore_api_endpoints()