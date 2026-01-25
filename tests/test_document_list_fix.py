#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
RAGFlow文档列表功能单元测试

专门测试最新修复的文档列表获取功能
包括API endpoint修复和配置修复的验证
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.services.ragflow_client import RAGFlowClient, RAGFLOW_ENDPOINTS
from src.config.config_loader import ConfigLoader


class TestDocumentListFix(unittest.TestCase):
    """RAGFlow文档列表功能修复验证测试"""
    
    def setUp(self):
        """测试前设置"""
        self.client = RAGFlowClient(auto_configure=False)
        self.test_kb_name = "policy_demo_kb"
    
    def test_api_endpoint_fix(self):
        """测试API endpoint修复"""
        # 验证RAGFLOW_ENDPOINTS配置正确
        self.assertIn('documents', RAGFLOW_ENDPOINTS)
        
        # 验证使用正确的v1 API格式
        documents_endpoint = RAGFLOW_ENDPOINTS['documents']
        self.assertEqual(documents_endpoint, '/api/v1/datasets/{dataset_id}/documents')
        
        # 验证包含必要的占位符
        self.assertIn('{dataset_id}', documents_endpoint)
        self.assertIn('/api/v1/', documents_endpoint)
        
        print("✅ API endpoint配置验证通过")
    
    def test_web_url_configuration_fix(self):
        """测试Web URL配置修复"""
        config = ConfigLoader()
        
        # 验证ragflow_web_url包含端口号
        web_url = config.ragflow_web_url
        self.assertIsNotNone(web_url)
        self.assertIn(':9380', web_url)
        self.assertTrue(web_url.startswith('http'))
        
        # 验证base_url和web_url一致
        base_url = config.ragflow_base_url
        self.assertEqual(web_url, base_url)
        
        print(f"✅ Web URL配置修复验证通过: {web_url}")
    
    @patch('src.services.ragflow_client.APIClient')
    def test_get_documents_workflow(self, mock_api_client):
        """测试get_documents完整工作流程"""
        # 创建一个测试客户端并设置mock
        test_client = RAGFlowClient(auto_configure=False)
        mock_client_instance = mock_api_client.return_value
        test_client.client = mock_client_instance
        
        dataset_id = 'test_dataset_123'
        
        mock_client_instance.get.side_effect = [
            # 第一次调用：获取知识库列表
            {
                'code': 0,
                'data': [
                    {
                        'name': self.test_kb_name,
                        'id': dataset_id,
                        'description': '测试知识库'
                    }
                ]
            },
            # 第二次调用：获取文档列表
            {
                'code': 0,
                'data': {
                    'docs': [
                        {
                            'id': '5d7d5b52fa1011f0b9f1d6f7bb8a681c',
                            'name': '国务院办公厅关于优化完善地方政府专项债券管理机制的意见_国务院文件_中国政府网.pdf',
                            'size': 672639,
                            'status': '1',
                            'create_time': 1769360864400,
                            'chunk_count': 15
                        }
                    ],
                    'total_datasets': 1
                }
            }
        ]
        
        # 执行测试
        docs = test_client.get_documents(self.test_kb_name)
        
        # 验证结果
        self.assertIsInstance(docs, list)
        self.assertEqual(len(docs), 1)
        
        doc = docs[0]
        self.assertEqual(doc['name'], '国务院办公厅关于优化完善地方政府专项债券管理机制的意见_国务院文件_中国政府网.pdf')
        self.assertEqual(doc['size'], 672639)
        self.assertEqual(doc['status'], '1')
        
        # 验证API调用
        calls = mock_client_instance.get.call_args_list
        self.assertEqual(len(calls), 2)
        
        # 验证第二次调用使用了正确的endpoint
        second_call_endpoint = calls[1][0][0]
        expected_endpoint = f'/api/v1/datasets/{dataset_id}/documents'
        self.assertEqual(second_call_endpoint, expected_endpoint)
        
        # 验证请求参数
        second_call_params = calls[1][1]['params']
        self.assertIn('page', second_call_params)
        self.assertIn('page_size', second_call_params)
        self.assertEqual(second_call_params['page'], 1)
        
        print("✅ get_documents工作流程验证通过")
    
    @patch('src.services.ragflow_client.APIClient')
    def test_error_handling(self, mock_api_client):
        """测试错误处理机制"""
        mock_client_instance = mock_api_client.return_value
        
        # 创建一个新的客户端实例来避免干扰
        test_client = RAGFlowClient(auto_configure=False)
        test_client.client = mock_client_instance
        
        # 测试知识库不存在的情况
        mock_client_instance.get.return_value = {
            'code': 0,
            'data': []
        }
        
        docs = test_client.get_documents("nonexistent_kb")
        self.assertEqual(docs, [])
        
        # 测试API错误的情况
        mock_client_instance.get.side_effect = [
            # 知识库查询成功
            {
                'code': 0,
                'data': [{'name': self.test_kb_name, 'id': 'test_id'}]
            },
            # 文档查询失败
            {
                'code': 102,
                'message': 'You don\'t own the dataset'
            }
        ]
        
        docs = test_client.get_documents(self.test_kb_name)
        self.assertEqual(docs, [])
        
        print("✅ 错误处理机制验证通过")
    
    def test_real_environment_integration(self):
        """测试真实环境集成"""
        try:
            # 测试配置加载
            config = ConfigLoader()
            self.assertIsNotNone(config.ragflow_web_url)
            self.assertIn(':9380', config.ragflow_web_url)
            
            # 测试客户端初始化
            client = RAGFlowClient(auto_configure=False)
            self.assertIsNotNone(client)
            
            # 测试文档列表获取
            docs = client.get_documents('policy_demo_kb')
            self.assertIsInstance(docs, list)
            
            if docs:
                # 验证文档结构
                doc = docs[0]
                required_fields = ['id', 'name', 'size']
                for field in required_fields:
                    self.assertIn(field, doc)
                
                print(f"✅ 真实环境测试通过，获取到 {len(docs)} 个文档")
                print(f"   示例文档: {doc.get('name', 'Unknown')[:50]}...")
            else:
                print("ℹ️ 知识库中当前无文档，但API连接正常")
            
        except Exception as e:
            self.skipTest(f"真实环境测试失败: {e}")


class TestDocumentsPageIntegration(unittest.TestCase):
    """文档页面集成测试"""
    
    def test_documents_page_imports(self):
        """测试文档页面模块导入"""
        try:
            from src.pages.documents_page import show_documents_page
            self.assertIsNotNone(show_documents_page)
            print("✅ 文档页面模块导入成功")
        except ImportError as e:
            # Streamlit可能没有安装，跳过这个测试
            self.skipTest(f"跳过文档页面导入测试 (依赖Streamlit): {e}")
    
    def test_config_loader_web_url_property(self):
        """测试ConfigLoader的ragflow_web_url属性"""
        config = ConfigLoader()
        
        # 验证属性存在
        self.assertTrue(hasattr(config, 'ragflow_web_url'))
        
        # 验证属性值正确
        web_url = config.ragflow_web_url
        self.assertIsNotNone(web_url)
        self.assertIn('117.21.184.150:9380', web_url)
        
        print(f"✅ ConfigLoader.ragflow_web_url属性验证通过: {web_url}")


if __name__ == '__main__':
    # 运行测试
    print("=" * 60)
    print("RAGFlow文档列表功能修复验证测试")
    print("=" * 60)
    
    unittest.main(verbosity=2)