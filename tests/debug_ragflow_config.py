#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
调试RAGFlow配置更新
"""

import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.ragflow_client import RAGFlowClient
import requests
import time

def debug_config_update():
    print("🔧 RAGFlow配置更新调试")
    print("=" * 50)
    
    # 初始化客户端
    client = RAGFlowClient()
    
    # 获取知识库信息
    kb_id = client._get_knowledge_base_id("policy_demo_kb")
    print(f"知识库ID: {kb_id}")
    
    if not kb_id:
        print("❌ 无法获取知识库ID")
        return
    
    # 1. 获取当前配置（完整信息）
    print("\n📋 获取详细配置信息...")
    
    # 构建请求参数
    base_url = "http://117.21.184.150:9380"
    headers = {
        "Authorization": "Bearer ragflow-231x38fUEnq_MSZwhOaD-6_spHL97oNJC8Wch61h0lo",
        "Content-Type": "application/json"
    }
    
    response = requests.get(
        f"{base_url}/api/v1/datasets/{kb_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("code") == 200:
            dataset_info = data.get("data", {})
            print("📄 完整数据集信息:")
            print(json.dumps(dataset_info, indent=2, ensure_ascii=False))
            
            # 提取关键配置信息
            chunk_method = dataset_info.get("chunk_method")
            parser_config = dataset_info.get("parser_config", {})
            
            print(f"\n🔍 当前配置解析:")
            print(f"  分块方法: {chunk_method}")
            print(f"  parser_config: {json.dumps(parser_config, indent=2, ensure_ascii=False)}")
    
    # 2. 构建正确的更新载荷
    print("\n🔄 构建更新载荷...")
    
    # 简单的更新，只改parser_config中的chunk_token_num
    update_payload = {
        "parser_config": {
            "chunk_token_num": 1000  # 改为1000，容易识别
        }
    }
    
    print(f"📦 更新载荷: {json.dumps(update_payload, indent=2, ensure_ascii=False)}")
    
    # 3. 发送更新请求
    print("\n📨 发送更新请求...")
    response = requests.put(
        f"{base_url}/api/v1/datasets/{kb_id}",
        headers=headers,
        json=update_payload
    )
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    
    # 4. 等待并检查更新
    if response.status_code == 200 and response.json().get("code") == 200:
        print("\n⏳ 等待5秒让更新生效...")
        time.sleep(5)
        
        print("\n📋 检查更新结果...")
        check_response = requests.get(
            f"{base_url}/api/v1/datasets/{kb_id}",
            headers=headers
        )
        
        if check_response.status_code == 200:
            check_data = check_response.json()
            if check_data.get("code") == 200:
                updated_dataset = check_data.get("data", {})
                updated_parser_config = updated_dataset.get("parser_config", {})
                
                print(f"🔍 更新后的parser_config:")
                print(json.dumps(updated_parser_config, indent=2, ensure_ascii=False))
                
                # 检查chunk_token_num
                chunk_token_num = updated_parser_config.get("chunk_token_num")
                print(f"\n✅ chunk_token_num: {chunk_token_num}")
                
                if chunk_token_num == 1000:
                    print("🎉 配置更新成功！")
                else:
                    print("❌ 配置更新失败")

if __name__ == "__main__":
    debug_config_update()