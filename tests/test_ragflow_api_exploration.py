#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
RAGFlow API探索和诊断工具

用于发现RAGFlow API端点、测试连接性能和诊断配置问题的工具集
"""

import unittest
import requests
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from config.config_loader import ConfigLoader


class TestRAGFlowAPIExploration(unittest.TestCase):
    """RAGFlow API探索测试类"""
    
    def setUp(self):
        """测试前设置"""
        self.config = ConfigLoader()
        self.base_url = self.config.ragflow_base_url
        self.headers = {
            "Authorization": f"Bearer {self.config.ragflow_api_key}",
            "Content-Type": "application/json"
        }
        
    def test_basic_connectivity(self):
        """测试基本连接性"""
        try:
            response = requests.get(self.base_url, timeout=5)
            self.assertIn(response.status_code, [200, 404, 405], 
                         f"服务器应该有响应，状态码: {response.status_code}")
        except requests.exceptions.RequestException as e:
            self.fail(f"基本连接失败: {e}")
            
    def test_datasets_endpoint(self):
        """测试datasets端点"""
        endpoint = f"{self.base_url}/api/v1/datasets"
        
        try:
            response = requests.get(endpoint, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.assertIn('code', data)
                if data.get('code') == 0:
                    self.assertIn('data', data)
                    datasets = data['data']
                    self.assertIsInstance(datasets, list)
                    
                    # 查找政策知识库
                    policy_kb = None
                    for dataset in datasets:
                        if dataset.get('name') == 'policy_demo_kb':
                            policy_kb = dataset
                            break
                            
                    if policy_kb:
                        self.assertIn('id', policy_kb)
                        self.assertIn('chunk_method', policy_kb)
                        self.assertIn('parser_config', policy_kb)
                    else:
                        self.skipTest("未找到policy_demo_kb知识库")
                        
            else:
                self.skipTest(f"端点不可访问，状态码: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.skipTest(f"API请求失败: {e}")
            
    def test_knowledge_base_id_discovery(self):
        """测试知识库ID发现"""
        endpoint = f"{self.base_url}/api/v1/datasets"
        
        try:
            response = requests.get(endpoint, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    datasets = data.get('data', [])
                    
                    kb_ids = {}
                    for dataset in datasets:
                        name = dataset.get('name')
                        kb_id = dataset.get('id')
                        if name and kb_id:
                            kb_ids[name] = kb_id
                            
                    self.assertGreater(len(kb_ids), 0, "应该发现至少一个知识库")
                    
                    if 'policy_demo_kb' in kb_ids:
                        kb_id = kb_ids['policy_demo_kb']
                        self.assertIsInstance(kb_id, str)
                        self.assertGreater(len(kb_id), 10, "知识库ID应该有足够长度")
                        
        except requests.exceptions.RequestException as e:
            self.skipTest(f"知识库发现失败: {e}")


class TestRAGFlowAPIEndpoints(unittest.TestCase):
    """RAGFlow API端点测试类"""
    
    def setUp(self):
        """测试前设置"""
        self.config = ConfigLoader()
        self.base_url = self.config.ragflow_base_url
        self.headers = {
            "Authorization": f"Bearer {self.config.ragflow_api_key}",
            "Content-Type": "application/json"
        }
        
        # 获取测试用的知识库ID
        self.kb_id = self._get_test_kb_id()
        
    def _get_test_kb_id(self):
        """获取测试用知识库ID"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/datasets", 
                                  headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    datasets = data.get('data', [])
                    for dataset in datasets:
                        if dataset.get('name') == 'policy_demo_kb':
                            return dataset.get('id')
            return None
        except:
            return None
            
    def test_dataset_detail_endpoint(self):
        """测试数据集详情端点"""
        if not self.kb_id:
            self.skipTest("未找到测试知识库ID")
            
        endpoint = f"{self.base_url}/api/v1/datasets/{self.kb_id}"
        
        try:
            response = requests.get(endpoint, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.assertIn('code', data)
                
                if data.get('code') == 0:
                    dataset_info = data.get('data', {})
                    
                    # 验证关键字段存在
                    required_fields = ['name', 'id', 'chunk_method', 'parser_config']
                    for field in required_fields:
                        self.assertIn(field, dataset_info, f"缺少必需字段: {field}")
                        
                    # 验证parser_config结构
                    parser_config = dataset_info.get('parser_config', {})
                    self.assertIsInstance(parser_config, dict)
                    self.assertIn('chunk_token_num', parser_config)
                    
            else:
                self.skipTest(f"端点不可访问，状态码: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.skipTest(f"API请求失败: {e}")
            
    def test_config_update_endpoint_structure(self):
        """测试配置更新端点结构"""
        if not self.kb_id:
            self.skipTest("未找到测试知识库ID")
            
        endpoint = f"{self.base_url}/api/v1/datasets/{self.kb_id}"
        
        # 构建测试载荷
        test_payload = {
            "parser_config": {
                "chunk_token_num": 800
            }
        }
        
        try:
            # 使用PUT方法测试端点
            response = requests.put(endpoint, headers=self.headers, 
                                  json=test_payload, timeout=10)
            
            # 验证响应结构
            self.assertIn(response.status_code, [200, 400, 401, 403], 
                         f"应该返回有效的HTTP状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.assertIn('code', data)
                # code为0表示成功，非0表示业务错误
                self.assertIsInstance(data['code'], int)
                
        except requests.exceptions.RequestException as e:
            self.skipTest(f"端点结构测试失败: {e}")


class TestRAGFlowPerformance(unittest.TestCase):
    """RAGFlow性能测试类"""
    
    def setUp(self):
        """测试前设置"""
        self.config = ConfigLoader()
        self.base_url = self.config.ragflow_base_url
        self.headers = {
            "Authorization": f"Bearer {self.config.ragflow_api_key}",
            "Content-Type": "application/json"
        }
        
    def test_api_response_time(self):
        """测试API响应时间"""
        endpoint = f"{self.base_url}/api/v1/datasets"
        
        try:
            start_time = time.time()
            response = requests.get(endpoint, headers=self.headers, timeout=30)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # API响应时间应该在合理范围内
            self.assertLess(response_time, 10.0, f"API响应时间过长: {response_time:.2f}秒")
            
            if response.status_code == 200:
                self.assertLess(response_time, 5.0, f"成功响应时间应该更快: {response_time:.2f}秒")
                
        except requests.exceptions.RequestException as e:
            self.skipTest(f"性能测试失败: {e}")
            
    def test_concurrent_api_calls(self):
        """测试并发API调用"""
        import concurrent.futures
        
        def make_api_call():
            try:
                response = requests.get(f"{self.base_url}/api/v1/datasets", 
                                      headers=self.headers, timeout=10)
                return response.status_code
            except:
                return None
                
        # 测试5个并发请求
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_api_call) for _ in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
        # 至少一半的请求应该成功
        successful_calls = sum(1 for result in results if result == 200)
        self.assertGreaterEqual(successful_calls, 2, "并发调用成功率过低")


if __name__ == '__main__':
    # 设置测试输出
    unittest.main(verbosity=2)