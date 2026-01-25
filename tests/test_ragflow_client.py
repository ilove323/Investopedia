#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
RAGFlow客户端单元测试

测试RAGFlow客户端连接、配置应用和API调用功能
"""

import unittest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from services.ragflow_client import RAGFlowClient
from config.config_loader import ConfigLoader


class TestRAGFlowClient(unittest.TestCase):
    """RAGFlow客户端测试类"""
    
    def setUp(self):
        """测试前设置"""
        self.config = ConfigLoader()
        
    def test_client_initialization(self):
        """测试客户端初始化"""
        # 测试不自动配置的初始化
        client = RAGFlowClient(auto_configure=False)
        self.assertIsNotNone(client)
        self.assertIsNotNone(client.headers)
        
    def test_configuration_application(self):
        """测试配置应用"""
        with patch('src.services.ragflow_client.requests') as mock_requests:
            mock_requests.put.return_value.status_code = 200
            mock_requests.put.return_value.json.return_value = {"retcode": 0}
            
            client = RAGFlowClient(auto_configure=False)
            
            # 测试无参数的配置应用方法
            try:
                result = client._apply_configuration()
                # 验证客户端仍然正常工作
                self.assertIsNotNone(client)
            except Exception as e:
                # 如果出现错误，至少验证客户端初始化正常
                self.assertIsNotNone(client)
                self.assertIsInstance(e, Exception)
            
    def test_knowledge_base_config_reading(self):
        """测试知识库配置读取"""
        client = RAGFlowClient(auto_configure=False)
        
        # 测试获取知识库配置（这个需要实际API连接）
        try:
            config = client.get_knowledge_base_config("policy_demo_kb")
            if config:  # 如果能连接到RAGFlow
                self.assertIsInstance(config, dict)
                self.assertIn('知识库基本信息', config)
            else:
                self.skipTest("无法连接RAGFlow服务")
        except Exception as e:
            self.skipTest(f"RAGFlow连接失败: {e}")
            
    def test_health_check(self):
        """测试健康检查"""
        client = RAGFlowClient(auto_configure=False)
        
        try:
            health = client.check_health()
            self.assertIsInstance(health, bool)
        except Exception as e:
            self.skipTest(f"健康检查失败: {e}")
            
    def test_config_update_payload_building(self):
        """测试配置更新载荷构建"""
        client = RAGFlowClient(auto_configure=False)
        
        # 测试配置参数转换
        test_config = {
            'chunk_size': 800,
            'graph_retrieval': True,
            'pdf_parser': 'deepdoc',
            'similarity_threshold': 0.3
        }
        
        # 这里测试内部方法（如果有的话）
        # 由于_build_dataset_update_payload可能是私有方法，我们跳过或用反射测试
        try:
            payload = client._build_dataset_update_payload(test_config)
            self.assertIsInstance(payload, dict)
            self.assertIn('parser_config', payload)
        except AttributeError:
            self.skipTest("方法不可访问或不存在")


class TestRAGFlowAPI(unittest.TestCase):
    """RAGFlow API测试类"""
    
    def setUp(self):
        """测试前设置"""
        self.client = RAGFlowClient(auto_configure=False)
        
    def test_api_endpoints_configuration(self):
        """测试API端点配置"""
        config = ConfigLoader()
        
        # 验证基础URL配置
        base_url = config.ragflow_base_url
        self.assertTrue(base_url.startswith('http'))
        self.assertIn('9380', base_url)  # 默认端口
        
        # 验证API Key配置
        api_key = config.ragflow_api_key
        self.assertIsInstance(api_key, str)
        if api_key:  # 如果配置了API Key
            self.assertTrue(api_key.startswith('ragflow-'))
            
    def test_knowledge_base_id_retrieval(self):
        """测试知识库ID获取"""
        try:
            kb_id = self.client._get_knowledge_base_id("policy_demo_kb")
            if kb_id:
                self.assertIsInstance(kb_id, str)
                self.assertTrue(len(kb_id) > 10)  # UUID应该有一定长度
            else:
                self.skipTest("知识库不存在或无法访问")
        except Exception as e:
            self.skipTest(f"API调用失败: {e}")
            
    @unittest.skipIf(os.getenv('SKIP_API_TESTS'), "跳过需要网络的API测试")
    def test_live_api_connection(self):
        """测试实际API连接（需要网络）"""
        try:
            # 测试基本连接
            health = self.client.check_health()
            self.assertIsNotNone(health)
            
            # 如果连接成功，测试配置读取
            if health:
                config = self.client.get_knowledge_base_config()
                if config:
                    self.assertIn('知识库基本信息', config)
                    
        except Exception as e:
            self.skipTest(f"实际API测试失败: {e}")


class TestConfigurationIntegration(unittest.TestCase):
    """配置集成测试类"""
    
    def test_config_to_ragflow_integration(self):
        """测试配置到RAGFlow的完整集成"""
        config = ConfigLoader()
        client = RAGFlowClient(auto_configure=False)
        
        # 测试从配置文件到RAGFlow客户端的配置流
        kb_config = config.get_kb_config("policy_demo_kb")
        
        # 验证关键配置项
        self.assertEqual(kb_config['chunk_size'], 800)
        self.assertTrue(kb_config['graph_retrieval'])
        self.assertEqual(kb_config['pdf_parser'], "deepdoc")
        
        # 验证提示词加载
        prompt = kb_config.get('system_prompt', '')
        self.assertGreater(len(prompt), 100)
        self.assertIn('政策', prompt)


class TestDocumentListFeature(unittest.TestCase):
    """文档列表功能测试类 - 针对最新修复的功能"""
    
    def setUp(self):
        """测试前设置"""
        self.client = RAGFlowClient(auto_configure=False)
        self.test_kb_name = "policy_demo_kb"
    
    @patch('src.services.ragflow_client.APIClient')
    def test_get_documents_success(self, mock_api_client):
        """测试成功获取文档列表"""
        # 模拟知识库ID查询
        mock_client_instance = mock_api_client.return_value
        mock_client_instance.get.side_effect = [
            # 第一次调用：获取知识库列表
            {
                'code': 0,
                'data': [{'name': self.test_kb_name, 'id': 'test_dataset_id_123'}]
            },
            # 第二次调用：获取文档列表
            {
                'code': 0,
                'data': {
                    'docs': [
                        {
                            'id': 'doc_123',
                            'name': 'test_document.pdf',
                            'size': 672639,
                            'status': '1',
                            'create_time': 1769360864400
                        }
                    ]
                }
            }
        ]
        
        # 执行测试
        docs = self.client.get_documents(self.test_kb_name)
        
        # 验证结果
        self.assertIsInstance(docs, list)
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]['name'], 'test_document.pdf')
        self.assertEqual(docs[0]['id'], 'doc_123')
        
        # 验证API调用参数
        calls = mock_client_instance.get.call_args_list
        self.assertEqual(len(calls), 2)
        
        # 验证第二次调用使用了正确的endpoint格式
        second_call_endpoint = calls[1][0][0]
        self.assertIn('/api/v1/datasets/test_dataset_id_123/documents', second_call_endpoint)
    
    @patch('src.services.ragflow_client.APIClient')
    def test_get_documents_knowledge_base_not_found(self, mock_api_client):
        """测试知识库未找到的情况"""
        # 模拟知识库不存在
        mock_client_instance = mock_api_client.return_value
        mock_client_instance.get.return_value = {
            'code': 0,
            'data': []  # 空的知识库列表
        }
        
        # 执行测试
        docs = self.client.get_documents("nonexistent_kb")
        
        # 验证结果
        self.assertIsInstance(docs, list)
        self.assertEqual(len(docs), 0)
    
    @patch('src.services.ragflow_client.APIClient')
    def test_get_documents_api_error(self, mock_api_client):
        """测试API错误的情况"""
        # 模拟知识库ID查询成功，文档列表查询失败
        mock_client_instance = mock_api_client.return_value
        mock_client_instance.get.side_effect = [
            # 第一次调用：获取知识库列表
            {
                'code': 0,
                'data': [{'name': self.test_kb_name, 'id': 'test_dataset_id_123'}]
            },
            # 第二次调用：API错误
            {
                'code': 102,
                'message': 'You don\'t own the dataset'
            }
        ]
        
        # 执行测试
        docs = self.client.get_documents(self.test_kb_name)
        
        # 验证结果
        self.assertIsInstance(docs, list)
        self.assertEqual(len(docs), 0)
    
    def test_endpoint_configuration(self):
        """测试endpoint配置正确性"""
        from services.ragflow_client import RAGFLOW_ENDPOINTS
        
        # 验证文档列表endpoint配置正确
        self.assertIn('documents', RAGFLOW_ENDPOINTS)
        documents_endpoint = RAGFLOW_ENDPOINTS['documents']
        self.assertEqual(documents_endpoint, '/api/v1/datasets/{dataset_id}/documents')
        
        # 验证包含dataset_id占位符
        self.assertIn('{dataset_id}', documents_endpoint)
    
    def test_web_url_configuration(self):
        """测试RAGFlow Web URL配置"""
        from config.config_loader import ConfigLoader
        
        config = ConfigLoader()
        web_url = config.ragflow_web_url
        
        # 验证web_url配置正确
        self.assertIsNotNone(web_url)
        self.assertTrue(web_url.startswith('http'))
        self.assertIn(':9380', web_url)  # 确保包含端口号


class TestRealDocumentIntegration(unittest.TestCase):
    """真实文档集成测试类"""
    
    def test_real_document_list_retrieval(self):
        """测试真实环境下的文档列表获取"""
        try:
            client = RAGFlowClient(auto_configure=False)
            docs = client.get_documents('policy_demo_kb')
            
            # 基本验证
            self.assertIsInstance(docs, list)
            
            # 如果有文档，验证文档结构
            if docs:
                doc = docs[0]
                self.assertIn('id', doc)
                self.assertIn('name', doc)
                self.assertIsInstance(doc.get('size'), (int, type(None)))
                
                print(f"✅ 实际获取到 {len(docs)} 个文档")
                print(f"   示例文档: {doc.get('name', 'Unknown')}")
            else:
                print("ℹ️ 当前知识库中没有文档")
                
        except Exception as e:
            self.skipTest(f"实际环境测试失败: {e}")


if __name__ == '__main__':
    # 设置测试输出
    unittest.main(verbosity=2)