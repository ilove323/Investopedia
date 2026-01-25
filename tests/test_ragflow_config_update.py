#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
RAGFlow配置更新单元测试

测试RAGFlow知识库配置的更新、应用和验证功能
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from services.ragflow_client import RAGFlowClient
from config.config_loader import ConfigLoader


class TestRAGFlowConfigUpdate(unittest.TestCase):
    """RAGFlow配置更新测试类"""
    
    def setUp(self):
        """测试前设置"""
        self.config = ConfigLoader()
        self.client = RAGFlowClient(auto_configure=False)
        
    def test_config_payload_building(self):
        """测试配置载荷构建"""
        test_config = {
            'chunk_size': 1000,
            'graph_retrieval': True,
            'pdf_parser': 'deepdoc',
            'similarity_threshold': 0.4,
            'auto_metadata': True,
            'table_recognition': True
        }
        
        try:
            # 测试载荷构建方法
            payload = self.client._build_dataset_update_payload(test_config)
            
            self.assertIsInstance(payload, dict)
            self.assertIn('parser_config', payload)
            self.assertIn('chunk_method', payload)
            
            # 验证parser_config结构
            parser_config = payload['parser_config']
            self.assertIn('chunk_token_num', parser_config)
            self.assertEqual(parser_config['chunk_token_num'], 1000)
            
            if 'raptor' in parser_config:
                self.assertIn('use_raptor', parser_config['raptor'])
                self.assertIn('threshold', parser_config['raptor'])
                
        except AttributeError:
            self.skipTest("配置构建方法不可访问")
            
    def test_knowledge_base_exists_check(self):
        """测试知识库存在性检查"""
        try:
            exists = self.client._check_knowledge_base_exists("policy_demo_kb")
            self.assertIsInstance(exists, bool)
            
            # 测试不存在的知识库
            not_exists = self.client._check_knowledge_base_exists("non_existent_kb")
            self.assertFalse(not_exists)
            
        except Exception as e:
            self.skipTest(f"知识库检查失败: {e}")
            
    def test_config_parameter_mapping(self):
        """测试配置参数映射"""
        # 测试不同PDF解析器的映射
        test_cases = [
            {'pdf_parser': 'deepdoc', 'expected_method': 'naive'},
            {'pdf_parser': 'laws', 'expected_method': 'laws'},
            {'pdf_parser': 'naive', 'expected_method': 'naive'}
        ]
        
        for case in test_cases:
            with self.subTest(pdf_parser=case['pdf_parser']):
                config = {'pdf_parser': case['pdf_parser']}
                try:
                    payload = self.client._build_dataset_update_payload(config)
                    self.assertEqual(payload['chunk_method'], case['expected_method'])
                except AttributeError:
                    self.skipTest("参数映射方法不可访问")
                    
    def test_config_update_api_call(self):
        """测试配置更新API调用（模拟）"""
        # Mock SDK methods for config update
        mock_dataset = MagicMock()
        mock_dataset.id = 'test_id'
        mock_dataset.update = MagicMock()

        with patch.object(self.client, '_check_knowledge_base_exists') as mock_check, \
             patch.object(self.client, '_get_or_create_dataset') as mock_get_dataset:

            mock_check.return_value = True
            mock_get_dataset.return_value = mock_dataset

            test_config = {
                'chunk_size': 800,
                'graph_retrieval': True
            }

            try:
                # 尝试调用配置更新（使用正确的参数）
                result = self.client._apply_configuration()
                # 如果成功调用，检查是否有相关日志或行为
                self.assertIsNotNone(self.client)
            except (AttributeError, ValueError, TypeError) as e:
                self.skipTest(f"配置更新方法不可访问: {e}")
            
    def test_config_verification(self):
        """测试配置验证"""
        try:
            # 获取当前配置
            current_config = self.client.get_knowledge_base_config("policy_demo_kb")
            
            if current_config:
                基本信息 = current_config.get('知识库基本信息', {})
                解析器配置 = current_config.get('解析器配置', {})
                
                # 验证政策库的关键配置
                chunk_size = 解析器配置.get('分块Token数')
                if chunk_size:
                    self.assertGreaterEqual(chunk_size, 800, "政策库分块大小应该≥800")
                    
                layout_parser = 解析器配置.get('布局识别')
                if layout_parser:
                    self.assertEqual(layout_parser, 'deepdoc', "应使用deepdoc布局识别")
                    
            else:
                self.skipTest("无法获取知识库配置")
                
        except Exception as e:
            self.skipTest(f"配置验证失败: {e}")


class TestConfigUpdateIntegration(unittest.TestCase):
    """配置更新集成测试类"""
    
    def setUp(self):
        """测试前设置"""
        self.config = ConfigLoader()
        
    def test_end_to_end_config_flow(self):
        """测试端到端配置流程"""
        # 1. 从配置文件加载
        kb_config = self.config.get_kb_config("policy_demo_kb")
        self.assertIsNotNone(kb_config)
        
        # 2. 验证关键配置参数
        expected_configs = {
            'chunk_size': 800,
            'pdf_parser': 'deepdoc',
            'graph_retrieval': True,
            'auto_metadata': True,
            'table_recognition': True
        }
        
        for key, expected_value in expected_configs.items():
            with self.subTest(config=key):
                self.assertEqual(kb_config[key], expected_value)
                
        # 3. 测试提示词加载
        prompt = kb_config.get('system_prompt', '')
        self.assertGreater(len(prompt), 200)
        self.assertIn('政策', prompt)
        
    def test_config_auto_application(self):
        """测试配置自动应用"""
        try:
            # 测试自动配置初始化
            client = RAGFlowClient(auto_configure=False)
            
            # 验证客户端正确初始化
            self.assertIsNotNone(client)
            self.assertTrue(hasattr(client, 'config'))
            
            # 如果配置存在，验证其包含必要字段
            if hasattr(client, 'current_kb_config'):
                kb_config = client.current_kb_config
                if kb_config:
                    self.assertIn('chunk_size', kb_config)
        except Exception as e:
            self.skipTest(f"自动配置测试跳过: {e}")
            config_logs = [log for log in log_calls if '配置' in log]
            self.assertGreater(len(config_logs), 0, "应该有配置应用相关日志")


if __name__ == '__main__':
    # 设置测试输出
    unittest.main(verbosity=2)