#!/usr/bin/env python3
"""
数据同步服务测试
===============
测试RAGFlow文档到本地数据库的同步功能，验证元数据提取和标签生成。

测试类：
- TestDataSyncService: 数据同步服务核心功能测试
- TestDataSyncIntegration: 集成测试（需要RAGFlow连接）

运行方式：
    python test_data_sync.py
    python -m unittest test_data_sync.TestDataSyncService -v
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.services.data_sync import DataSyncService
from src.database.policy_dao import PolicyDAO
from src.services.ragflow_client import RAGFlowClient


class TestDataSyncService(unittest.TestCase):
    """数据同步服务测试"""

    def setUp(self):
        """设置测试环境"""
        self.maxDiff = None
        
        # 模拟依赖
        self.mock_ragflow = Mock(spec=RAGFlowClient)
        self.mock_dao = Mock(spec=PolicyDAO)
        self.mock_metadata_extractor = Mock()
        self.mock_tag_generator = Mock()

    @patch('src.services.data_sync.RAGFlowClient')
    @patch('src.services.data_sync.PolicyDAO')
    @patch('src.services.data_sync.MetadataExtractor')
    @patch('src.services.data_sync.TagGenerator')
    def test_init_data_sync_service(self, mock_tag_gen_class, mock_meta_class, mock_dao_class, mock_ragflow_class):
        """测试数据同步服务初始化"""
        # 设置mock
        mock_ragflow_class.return_value = self.mock_ragflow
        mock_dao_class.return_value = self.mock_dao
        mock_meta_class.return_value = self.mock_metadata_extractor
        mock_tag_gen_class.return_value = self.mock_tag_generator
        
        # 创建同步服务
        sync_service = DataSyncService()
        
        # 验证初始化
        self.assertIsNotNone(sync_service.ragflow)
        self.assertIsNotNone(sync_service.dao)
        self.assertIsNotNone(sync_service.metadata_extractor)
        self.assertIsNotNone(sync_service.tag_generator)

    @patch('src.services.data_sync.RAGFlowClient')
    @patch('src.services.data_sync.PolicyDAO')
    @patch('src.services.data_sync.MetadataExtractor')
    @patch('src.services.data_sync.TagGenerator')
    def test_sync_documents_empty_ragflow(self, mock_tag_gen_class, mock_meta_class, mock_dao_class, mock_ragflow_class):
        """测试同步空的RAGFlow知识库"""
        # 设置mock
        mock_ragflow_class.return_value = self.mock_ragflow
        mock_dao_class.return_value = self.mock_dao
        mock_meta_class.return_value = self.mock_metadata_extractor
        mock_tag_gen_class.return_value = self.mock_tag_generator
        
        # RAGFlow返回空文档列表
        self.mock_ragflow.get_documents.return_value = []
        
        sync_service = DataSyncService()
        
        # 执行同步
        result = sync_service.sync_documents_to_database("test_kb")
        
        # 验证结果
        self.assertEqual(result['total_documents'], 0)
        self.assertEqual(result['new_policies'], 0)
        self.assertEqual(result['updated_policies'], 0)
        self.assertEqual(len(result['errors']), 0)

    @patch('src.services.data_sync.RAGFlowClient')
    @patch('src.services.data_sync.PolicyDAO')
    @patch('src.services.data_sync.MetadataExtractor')
    @patch('src.services.data_sync.TagGenerator')
    def test_sync_documents_new_policy(self, mock_tag_gen_class, mock_meta_class, mock_dao_class, mock_ragflow_class):
        """测试同步新政策文档"""
        # 设置mock
        mock_ragflow_class.return_value = self.mock_ragflow
        mock_dao_class.return_value = self.mock_dao
        mock_meta_class.return_value = self.mock_metadata_extractor
        mock_tag_gen_class.return_value = self.mock_tag_generator
        
        # 模拟RAGFlow文档
        mock_doc = {
            'id': 'doc123',
            'name': 'test_policy.pdf',
            'content': '这是一个测试政策文档',
            'size': 1024,
            'location': '/uploads/test_policy.pdf',
            'create_time': '2026-01-26T10:00:00'
        }
        self.mock_ragflow.get_documents.return_value = [mock_doc]
        # 模拟获取文档内容
        self.mock_ragflow.get_document_content.return_value = '这是一个测试政策文档内容'
        
        # DAO返回不存在的政策
        self.mock_dao.get_policy_by_ragflow_id.return_value = None
        self.mock_dao.create_policy.return_value = 1
        self.mock_dao.get_or_create_tag.return_value = 1
        
        # 元数据提取器返回数据
        self.mock_metadata_extractor.extract_all.return_value = {
            'policy_type': 'special_bonds',
            'issuing_authority': '财政部',
            'region': '全国',
            'effective_date': '2026-01-01',
            'document_number': '财预〔2026〕1号'
        }
        
        # 标签生成器返回标签（字典格式）
        self.mock_tag_generator.generate_tags.return_value = [
            {'name': '专项债券', 'type': 'policy_type'},
            {'name': '财政部', 'type': 'authority'},
            {'name': '全国', 'type': 'region'}
        ]
        
        sync_service = DataSyncService()
        
        # 执行同步
        result = sync_service.sync_documents_to_database("test_kb")
        
        # 验证结果
        self.assertEqual(result['total_documents'], 1)
        self.assertEqual(result['new_policies'], 1)
        self.assertEqual(result['updated_policies'], 0)
        self.assertEqual(len(result['errors']), 0)
        
        # 验证调用
        self.mock_dao.create_policy.assert_called_once()
        self.mock_dao.get_or_create_tag.assert_called()
        self.mock_dao.add_policy_tag.assert_called()

    @patch('src.services.data_sync.RAGFlowClient')
    @patch('src.services.data_sync.PolicyDAO')
    @patch('src.services.data_sync.MetadataExtractor')
    @patch('src.services.data_sync.TagGenerator')
    def test_sync_documents_update_existing_policy(self, mock_tag_gen_class, mock_meta_class, mock_dao_class, mock_ragflow_class):
        """测试更新现有政策"""
        # 设置mock
        mock_ragflow_class.return_value = self.mock_ragflow
        mock_dao_class.return_value = self.mock_dao
        mock_meta_class.return_value = self.mock_metadata_extractor
        mock_tag_gen_class.return_value = self.mock_tag_generator
        
        # 模拟RAGFlow文档
        mock_doc = {
            'id': 'doc123',
            'name': 'existing_policy.pdf',
            'content': '这是一个已存在的政策文档（更新版本）',
            'size': 2048,
            'location': '/uploads/existing_policy.pdf',
            'create_time': '2026-01-26T12:00:00'
        }
        self.mock_ragflow.get_documents.return_value = [mock_doc]
        
        # DAO返回已存在的政策
        existing_policy = {'id': 1, 'title': '现有政策'}
        self.mock_dao.get_policy_by_ragflow_id.return_value = existing_policy
        
        # 元数据提取器返回数据
        self.mock_metadata_extractor.extract_from_content.return_value = {
            'policy_type': 'special_bonds',
            'issuing_authority': '财政部',
            'region': '全国'
        }
        
        sync_service = DataSyncService()
        
        # 执行同步
        result = sync_service.sync_documents_to_database("test_kb")
        
        # 验证结果
        self.assertEqual(result['total_documents'], 1)
        self.assertEqual(result['new_policies'], 0)
        self.assertEqual(result['updated_policies'], 1)
        self.assertEqual(len(result['errors']), 0)
        
        # 验证调用
        self.mock_dao.update_policy.assert_called_once()

    @patch('src.services.data_sync.RAGFlowClient')
    @patch('src.services.data_sync.PolicyDAO')
    @patch('src.services.data_sync.MetadataExtractor')
    @patch('src.services.data_sync.TagGenerator')
    def test_sync_documents_with_errors(self, mock_tag_gen_class, mock_meta_class, mock_dao_class, mock_ragflow_class):
        """测试同步过程中的错误处理"""
        # 设置mock
        mock_ragflow_class.return_value = self.mock_ragflow
        mock_dao_class.return_value = self.mock_dao
        mock_meta_class.return_value = self.mock_metadata_extractor
        mock_tag_gen_class.return_value = self.mock_tag_generator
        
        # 模拟两个文档，一个成功一个失败
        mock_docs = [
            {
                'id': 'doc123',
                'name': 'good_policy.pdf',
                'content': '正常文档',
                'size': 1024,
                'location': '/uploads/good_policy.pdf',
                'create_time': '2026-01-26T10:00:00'
            },
            {
                'id': 'doc456',
                'name': 'bad_policy.pdf',
                'content': '有问题的文档',
                'size': 1024,
                'location': '/uploads/bad_policy.pdf',
                'create_time': '2026-01-26T11:00:00'
            }
        ]
        self.mock_ragflow.get_documents.return_value = mock_docs
        
        # 第一个文档成功，第二个失败
        def side_effect(ragflow_id):
            if ragflow_id == 'doc123':
                return None  # 不存在，创建新的
            elif ragflow_id == 'doc456':
                raise Exception("数据库错误")
        
        self.mock_dao.get_policy_by_ragflow_id.side_effect = side_effect
        self.mock_dao.create_policy.return_value = 1
        
        # 元数据提取器正常
        self.mock_metadata_extractor.extract_from_content.return_value = {
            'policy_type': 'special_bonds'
        }
        self.mock_tag_generator.generate_tags.return_value = []
        
        sync_service = DataSyncService()
        
        # 执行同步
        result = sync_service.sync_documents_to_database("test_kb")
        
        # 验证结果
        self.assertEqual(result['total_documents'], 2)
        self.assertEqual(result['new_policies'], 1)  # 只有一个成功
        self.assertEqual(result['updated_policies'], 0)
        self.assertEqual(len(result['errors']), 1)  # 一个错误
        
        # 验证错误信息
        error_msg = result['errors'][0]
        self.assertIn('bad_policy.pdf', error_msg)
        self.assertIn('数据库错误', error_msg)

    def test_extract_policy_metadata(self):
        """测试元数据提取"""
        with patch('src.services.data_sync.RAGFlowClient') as mock_ragflow_class, \
             patch('src.services.data_sync.PolicyDAO'), \
             patch('src.services.data_sync.MetadataExtractor') as mock_meta_class, \
             patch('src.services.data_sync.TagGenerator'):
            
            # 设置mock RAGFlow客户端
            mock_ragflow = Mock()
            mock_ragflow_class.return_value = mock_ragflow
            mock_ragflow.get_document_content.return_value = '测试政策内容'
            
            mock_metadata_extractor = Mock()
            mock_meta_class.return_value = mock_metadata_extractor
            
            # 模拟文档
            doc = {
                'id': 'doc123',
                'name': 'test_policy.pdf',
                'content': '测试政策内容',
                'size': 1024,
                'location': '/uploads/test.pdf',
                'create_time': '2026-01-26T10:00:00'
            }
            
            # 模拟元数据提取器
            mock_metadata_extractor.extract_all.return_value = {
                'policy_type': 'special_bonds',
                'issuing_authority': '财政部'
            }
            
            sync_service = DataSyncService()
            
            # 执行元数据提取
            metadata = sync_service._extract_policy_metadata(doc)
            
            # 验证基础字段
            self.assertEqual(metadata['ragflow_document_id'], 'doc123')
            self.assertEqual(metadata['title'], 'test_policy')  # 移除.pdf
            self.assertEqual(metadata['content'], '测试政策内容')
            self.assertEqual(metadata['file_size'], 1024)
            self.assertEqual(metadata['status'], 'active')
            
            # 验证提取的字段
            self.assertEqual(metadata['policy_type'], 'special_bonds')
            self.assertEqual(metadata['issuing_authority'], '财政部')

    @patch('src.services.data_sync.RAGFlowClient')
    @patch('src.services.data_sync.PolicyDAO')
    @patch('src.services.data_sync.MetadataExtractor')
    @patch('src.services.data_sync.TagGenerator')
    def test_get_sync_status(self, mock_tag_gen_class, mock_meta_class, mock_dao_class, mock_ragflow_class):
        """测试获取同步状态"""
        # 设置mock
        mock_ragflow_class.return_value = self.mock_ragflow
        mock_dao_class.return_value = self.mock_dao
        mock_meta_class.return_value = self.mock_metadata_extractor
        mock_tag_gen_class.return_value = self.mock_tag_generator
        
        # 设置DAO返回
        self.mock_dao.get_policies.return_value = [{'id': 1}, {'id': 2}]  # 2个政策
        
        # 设置RAGFlow返回
        self.mock_ragflow.get_documents.return_value = [{'id': 'doc1'}]  # 1个文档
        
        sync_service = DataSyncService()
        
        # 获取状态
        status = sync_service.get_sync_status()
        
        # 验证状态
        self.assertEqual(status['database_policies'], 2)
        self.assertEqual(status['ragflow_documents'], 1)
        self.assertEqual(status['ragflow_status'], 'connected')
        self.assertIn('last_check', status)


class TestDataSyncIntegration(unittest.TestCase):
    """数据同步集成测试（需要真实RAGFlow连接）"""
    
    def setUp(self):
        """设置测试环境"""
        # 检查是否可以连接到RAGFlow
        try:
            self.sync_service = DataSyncService()
            # 尝试获取状态来测试连接
            status = self.sync_service.get_sync_status()
            if status.get('ragflow_status') != 'connected':
                self.skipTest("RAGFlow服务不可用，跳过集成测试")
        except Exception as e:
            self.skipTest(f"无法连接RAGFlow: {e}")
    
    def test_real_sync_status(self):
        """测试真实环境同步状态"""
        status = self.sync_service.get_sync_status()
        
        # 验证返回的状态结构
        self.assertIn('database_policies', status)
        self.assertIn('ragflow_documents', status)
        self.assertIn('ragflow_status', status)
        self.assertIn('last_check', status)
        
        # 如果连接成功，状态应该是connected
        if status['ragflow_status'] == 'connected':
            self.assertIsInstance(status['database_policies'], int)
            self.assertIsInstance(status['ragflow_documents'], int)


def run_tests():
    """运行所有测试"""
    print("=== 数据同步服务测试 ===\n")
    
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加基础功能测试
    suite.addTest(unittest.makeSuite(TestDataSyncService))
    
    # 添加集成测试（如果可用）
    try:
        suite.addTest(unittest.makeSuite(TestDataSyncIntegration))
    except Exception:
        print("⚠️ 跳过集成测试（RAGFlow不可用）")
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出结果
    print(f"\n=== 测试完成 ===")
    print(f"总测试数: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"跳过: {len(result.skipped)}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)