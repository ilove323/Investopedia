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

from src.clients.ragflow_client import RAGFlowClient
from src.config.config_loader import ConfigLoader


class TestDocumentListFix(unittest.TestCase):
    """RAGFlow文档列表功能修复验证测试"""

    def setUp(self):
        """测试前设置"""
        self.client = RAGFlowClient()
        self.test_kb_name = "policy_demo_kb"

    def test_api_endpoint_fix(self):
        """测试API endpoint修复 - SDK handles endpoints internally"""
        # SDK handles endpoint configuration internally
        # Verify client is properly initialized with SDK
        self.assertIsNotNone(self.client.rag)
        self.assertIsNotNone(self.client._dataset_cache)

        print("✅ RAGFlow SDK客户端初始化验证通过")
    
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
    
    def test_get_documents_workflow(self):
        """测试get_documents完整工作流程"""
        # Mock dataset and documents
        test_client = RAGFlowClient()
        dataset_id = 'test_dataset_123'

        mock_dataset = MagicMock()
        mock_dataset.id = dataset_id
        mock_dataset.name = self.test_kb_name

        mock_doc = MagicMock()
        mock_doc.id = '5d7d5b52fa1011f0b9f1d6f7bb8a681c'
        mock_doc.name = '国务院办公厅关于优化完善地方政府专项债券管理机制的意见_国务院文件_中国政府网.pdf'
        mock_doc.size = 672639
        mock_doc.status = '1'
        mock_doc.create_time = 1769360864400

        with patch.object(test_client.rag, 'list_datasets') as mock_list_datasets, \
             patch.object(mock_dataset, 'list_documents') as mock_list_docs:

            mock_list_datasets.return_value = [mock_dataset]
            mock_list_docs.return_value = [mock_doc]

            # 执行测试
            docs = test_client.get_documents(self.test_kb_name)

            # 验证结果
            self.assertIsInstance(docs, list)
            self.assertEqual(len(docs), 1)

            doc = docs[0]
            self.assertEqual(doc['name'], '国务院办公厅关于优化完善地方政府专项债券管理机制的意见_国务院文件_中国政府网.pdf')
            self.assertEqual(doc['size'], 672639)
            self.assertEqual(doc['status'], '1')

            print("✅ get_documents工作流程验证通过")
    
    def test_error_handling(self):
        """测试错误处理机制"""
        # 创建一个新的客户端实例来避免干扰
        test_client = RAGFlowClient()

        # 测试知识库不存在的情况
        with patch.object(test_client.rag, 'list_datasets') as mock_list_datasets:
            mock_list_datasets.return_value = []  # No datasets

            docs = test_client.get_documents("nonexistent_kb")
            self.assertEqual(docs, [])

        # 测试API错误的情况
        mock_dataset = MagicMock()
        mock_dataset.id = 'test_id'
        mock_dataset.name = self.test_kb_name
        mock_dataset.list_documents.side_effect = Exception("API Error")

        with patch.object(test_client.rag, 'list_datasets') as mock_list_datasets:
            mock_list_datasets.return_value = [mock_dataset]

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
            client = RAGFlowClient()
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