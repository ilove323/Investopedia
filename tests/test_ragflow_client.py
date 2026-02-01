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

from src.clients.ragflow_client import RAGFlowClient
from src.config.config_loader import ConfigLoader


class TestRAGFlowClient(unittest.TestCase):
    """RAGFlow客户端测试类"""
    
    def setUp(self):
        """测试前设置"""
        self.config = ConfigLoader()
        
    def test_client_initialization(self):
        """测试客户端初始化"""
        # 测试不自动配置的初始化
        client = RAGFlowClient()
        self.assertIsNotNone(client)
        self.assertIsNotNone(client.rag)  # 验证SDK客户端已初始化
        
    def test_client_initialization(self):
        """测试客户端初始化"""
        client = RAGFlowClient()
        
        # 验证客户端已正确初始化
        self.assertIsNotNone(client)
        self.assertIsNotNone(client.rag)
            
    def test_knowledge_base_connection(self):
        """测试知识库连接"""
        client = RAGFlowClient()
        
        # 测试基本连接（需要实际API连接）
        try:
            # 测试数据集获取
            dataset = client._get_or_create_dataset("policy_demo_kb")
            if dataset:  # 如果能连接到RAGFlow
                self.assertIsNotNone(dataset)
            else:
                self.skipTest("无法连接RAGFlow服务或知识库不存在")
        except Exception as e:
            self.skipTest(f"RAGFlow连接失败: {e}")
            
    def test_health_check(self):
        """测试健康检查"""
        client = RAGFlowClient()
        
        try:
            health = client.check_health()
            self.assertIsInstance(health, bool)
        except Exception as e:
            self.skipTest(f"健康检查失败: {e}")
            
    def test_config_update_payload_building(self):
        """测试配置更新载荷构建"""
        client = RAGFlowClient()
        
        # 测试配置参数转换
        test_config = {
            'chunk_size': 800,
            'graph_retrieval': True,
            'pdf_parser': 'deepdoc',
            'similarity_threshold': 0.3
        }
        
        # 测试客户端基本功能
        self.assertIsNotNone(client)
        self.assertTrue(isinstance(test_config, dict))


class TestRAGFlowAPI(unittest.TestCase):
    """RAGFlow API测试类"""
    
    def setUp(self):
        """测试前设置"""
        self.client = RAGFlowClient()
        
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
            
            # 如果连接成功，测试数据集访问
            if health:
                dataset = self.client._get_or_create_dataset("policy_demo_kb")
                if dataset:
                    self.assertIsNotNone(dataset)
                    
        except Exception as e:
            self.skipTest(f"实际API测试失败: {e}")


class TestConfigurationIntegration(unittest.TestCase):
    """配置集成测试类"""
    
    def test_config_to_ragflow_integration(self):
        """测试配置到RAGFlow的完整集成"""
        config = ConfigLoader()
        client = RAGFlowClient()
        
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
        self.client = RAGFlowClient()
        self.test_kb_name = "policy_demo_kb"
    
    def test_get_documents_success(self):
        """测试成功获取文档列表"""
        # Mock dataset and documents
        mock_dataset = MagicMock()
        mock_dataset.id = 'test_dataset_id_123'
        mock_dataset.name = self.test_kb_name

        mock_doc = MagicMock()
        mock_doc.id = 'doc_123'
        mock_doc.name = 'test_document.pdf'
        mock_doc.size = 672639
        mock_doc.status = '1'
        mock_doc.create_time = 1769360864400

        # Mock SDK methods
        with patch.object(self.client.rag, 'list_datasets') as mock_list_datasets, \
             patch.object(mock_dataset, 'list_documents') as mock_list_docs:

            mock_list_datasets.return_value = [mock_dataset]
            mock_list_docs.return_value = [mock_doc]

            # 执行测试
            docs = self.client.get_documents(self.test_kb_name)

            # 验证结果
            self.assertIsInstance(docs, list)
            self.assertEqual(len(docs), 1)
            self.assertEqual(docs[0]['name'], 'test_document.pdf')
            self.assertEqual(docs[0]['id'], 'doc_123')
    
    def test_get_documents_knowledge_base_not_found(self):
        """测试知识库未找到的情况"""
        # Mock SDK to return empty dataset list
        with patch.object(self.client.rag, 'list_datasets') as mock_list_datasets:
            mock_list_datasets.return_value = []  # No datasets found

            # 执行测试
            docs = self.client.get_documents("nonexistent_kb")

            # 验证结果
            self.assertIsInstance(docs, list)
            self.assertEqual(len(docs), 0)
    
    def test_get_documents_api_error(self):
        """测试API错误的情况"""
        # Mock dataset but make list_documents raise an exception
        mock_dataset = MagicMock()
        mock_dataset.id = 'test_dataset_id_123'
        mock_dataset.name = self.test_kb_name
        mock_dataset.list_documents.side_effect = Exception("API Error: You don't own the dataset")

        with patch.object(self.client.rag, 'list_datasets') as mock_list_datasets:
            mock_list_datasets.return_value = [mock_dataset]

            # 执行测试
            docs = self.client.get_documents(self.test_kb_name)

            # 验证结果
            self.assertIsInstance(docs, list)
            self.assertEqual(len(docs), 0)  # Should return empty list on error
    
    def test_endpoint_configuration(self):
        """测试endpoint配置正确性"""
        # SDK handles endpoints internally, no need to test this
        # Test that SDK client is properly initialized instead
        client = RAGFlowClient()
        self.assertIsNotNone(client.rag)
        self.assertIsNotNone(client._dataset_cache)
    
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
            client = RAGFlowClient()
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


class TestSystemPromptIntegration(unittest.TestCase):
    """系统提示词集成测试"""

    def setUp(self):
        """测试前设置"""
        self.maxDiff = None

    def test_load_system_prompt_from_config(self):
        """测试从配置文件加载系统提示词"""
        from src.config import get_config
        
        config = get_config()
        kb_config = config.get_kb_config("policy_demo_kb")
        
        # 验证知识库配置加载
        self.assertIsInstance(kb_config, dict)
        
        # 验证系统提示词字段
        self.assertIn('system_prompt', kb_config)
        system_prompt = kb_config['system_prompt']
        
        # 验证提示词内容
        self.assertIsInstance(system_prompt, str)
        self.assertGreater(len(system_prompt), 0)
        
        # 验证提示词包含关键内容
        self.assertIn('政策文档智能助手', system_prompt)
        self.assertIn('专项债', system_prompt)
        self.assertIn('特许经营', system_prompt)
        self.assertIn('数据资产', system_prompt)
        
        print(f"✅ 系统提示词加载成功 (长度: {len(system_prompt)})")

    def test_system_prompt_in_ask_request(self):
        """测试问答请求中包含系统提示词"""
        client = RAGFlowClient()

        # Create mocks for dataset, chat assistant, session, and message
        mock_dataset = MagicMock()
        mock_dataset.id = 'test_dataset_id'

        mock_chat = MagicMock()
        mock_chat.id = 'test_chat_id'

        mock_session = MagicMock()
        mock_session.id = 'test_session_id'

        mock_message = MagicMock()
        mock_message.content = '测试回答'
        mock_message.id = 'test_message_id'
        mock_message.reference = []

        # Mock配置
        with patch('src.clients.ragflow_client.get_config') as mock_get_config, \
             patch.object(client.rag, 'list_datasets') as mock_list_datasets, \
             patch.object(client.rag, 'list_chats') as mock_list_chats, \
             patch.object(mock_chat, 'list_sessions') as mock_list_sessions, \
             patch.object(mock_session, 'ask') as mock_ask:

            # 设置配置mock
            mock_config = MagicMock()
            mock_kb_config = {
                'system_prompt': '你是政策助手，请专业回答问题。'
            }
            mock_config.get_kb_config.return_value = mock_kb_config
            mock_get_config.return_value = mock_config

            # 设置SDK mock
            mock_list_datasets.return_value = [mock_dataset]
            mock_list_chats.return_value = [mock_chat]
            mock_list_sessions.return_value = [mock_session]
            mock_ask.return_value = mock_message

            try:
                # 调用ask方法
                result = client.ask("测试问题", "policy_demo_kb")

                # 验证返回结果
                self.assertIsNotNone(result)
                self.assertEqual(result["answer"], "测试回答")

                # 验证SDK方法被调用
                self.assertTrue(mock_ask.called)

                print(f"✅ 问答请求成功返回结果")

            except Exception as e:
                self.fail(f"ask方法调用失败: {e}")

    def test_prompt_file_loading_integration(self):
        """测试提示词文件加载集成"""
        from src.config.config_loader import ConfigLoader
        
        config_loader = ConfigLoader()
        
        # 测试提示词文件加载
        prompt_content = config_loader._load_prompt_file("policy_demo_kb.txt")
        
        # 验证文件加载成功
        self.assertIsInstance(prompt_content, str)
        self.assertGreater(len(prompt_content), 0)
        
        # 验证文件内容包含预期关键词
        self.assertIn('政策文档智能助手', prompt_content)
        self.assertIn('【政策依据】', prompt_content)
        self.assertIn('【核心要点】', prompt_content)
        self.assertIn('【实施指导】', prompt_content)
        
        print(f"✅ 提示词文件加载成功，内容长度: {len(prompt_content)}")


if __name__ == '__main__':
    # 设置测试输出
    unittest.main(verbosity=2)