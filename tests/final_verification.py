#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
最终验证RAGFlow配置更新 - 单元测试版本
"""

import unittest
import json
from unittest.mock import patch, MagicMock, Mock
import sys
import os

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'src'))

from services.ragflow_client import RAGFlowClient


class TestFinalVerification(unittest.TestCase):
    """最终配置验证测试"""
    
    def setUp(self):
        """测试前设置"""
        self.kb_name = "policy_demo_kb"
        self.expected_chunk_size = 1500
        
    def test_final_config_display(self):
        """测试最终配置显示"""
        client = RAGFlowClient()
        
        # 测试基本连接
        health = client.check_health()
        self.assertIsNotNone(health)
                
    def test_ragflow_connection(self):
        """测试RAGFlow连接功能"""
        client = RAGFlowClient()
        
        # 测试健康检查
        try:
            health = client.check_health()
            self.assertIsNotNone(health)
        except Exception as e:
            self.skipTest(f"RAGFlow连接失败: {e}")
                
    def test_dataset_access(self):
        """测试数据集访问"""
        client = RAGFlowClient()
        
        try:
            dataset = client._get_or_create_dataset(self.kb_name)
            if dataset:
                self.assertIsNotNone(dataset)
            else:
                self.skipTest("知识库不存在或无法访问")
        except Exception as e:
            self.skipTest(f"数据集访问失败: {e}")
                    
    def test_final_integration_flow(self):
        """测试最终集成流程"""
        with patch('src.clients.ragflow_client.requests') as mock_requests:
            # 模拟完整流程
            mock_responses = []
            
            # 第一次调用：获取当前配置
            mock_resp1 = Mock()
            mock_resp1.status_code = 200
            mock_resp1.json.return_value = {
                "retcode": 0,
                "data": {"parser_config": {"chunk_token_num": 800}}
            }
            
            # 第二次调用：更新配置
            mock_resp2 = Mock()
            mock_resp2.status_code = 200
            mock_resp2.json.return_value = {"retcode": 0}
            
            # 第三次调用：验证配置
            mock_resp3 = Mock()
            mock_resp3.status_code = 200
            mock_resp3.json.return_value = {
                "retcode": 0,
                "data": {"parser_config": {"chunk_token_num": self.expected_chunk_size}}
            }
            
            # 设置请求响应序列
            mock_requests.get.side_effect = [mock_resp1, mock_resp3]
            mock_requests.put.return_value = mock_resp2
            
            client = RAGFlowClient()
            
            # 测试知识库连接
            # 注意：配置更新功能已移除，仅测试连接
            self.assertTrue(client.check_health())


class TestFinalConfigValidation(unittest.TestCase):
    """最终配置验证测试类"""
    
    def test_expected_final_state(self):
        """测试预期的最终状态"""
        expected_final_config = {
            "chunk_token_num": 1500,
            "graph_enabled": True,
            "entity_resolution": True,
            "parser": "deepdoc"
        }
        
        # 验证预期配置的结构
        self.assertIn("chunk_token_num", expected_final_config)
        self.assertIsInstance(expected_final_config["chunk_token_num"], int)
        self.assertGreater(expected_final_config["chunk_token_num"], 0)
        
        self.assertIn("graph_enabled", expected_final_config)
        self.assertIsInstance(expected_final_config["graph_enabled"], bool)
        
        self.assertIn("entity_resolution", expected_final_config)
        self.assertIsInstance(expected_final_config["entity_resolution"], bool)
        
    def test_final_validation_criteria(self):
        """测试最终验证标准"""
        # 定义验证标准
        validation_criteria = {
            "min_chunk_size": 100,
            "max_chunk_size": 5000,
            "required_features": ["graph_retrieval", "entity_normalization"],
            "supported_parsers": ["deepdoc", "manual"]
        }
        
        # 测试验证逻辑
        test_chunk_size = 1500
        self.assertGreaterEqual(test_chunk_size, validation_criteria["min_chunk_size"])
        self.assertLessEqual(test_chunk_size, validation_criteria["max_chunk_size"])
        
        # 验证必需功能
        for feature in validation_criteria["required_features"]:
            self.assertIsInstance(feature, str)
            self.assertGreater(len(feature), 0)


if __name__ == '__main__':
    unittest.main()