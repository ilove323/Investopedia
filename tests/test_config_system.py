#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置系统单元测试

测试新的配置加载器和知识库配置系统功能
"""

import unittest
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from config.config_loader import ConfigLoader


class TestConfigSystem(unittest.TestCase):
    """配置系统测试类"""
    
    def setUp(self):
        """测试前设置"""
        self.config = ConfigLoader()
    
    def test_basic_config_loading(self):
        """测试基本配置加载"""
        # 测试RAGFlow连接配置
        self.assertIsInstance(self.config.ragflow_host, str)
        self.assertIsInstance(self.config.ragflow_port, int)
        self.assertTrue(self.config.ragflow_base_url.startswith('http'))
        
        # 测试默认知识库
        self.assertEqual(self.config.default_kb_name, "policy_demo_kb")
        
    def test_prompts_dir_exists(self):
        """测试提示词目录存在"""
        prompts_dir = self.config.prompts_dir
        self.assertTrue(prompts_dir.exists(), f"提示词目录不存在: {prompts_dir}")
        
    def test_available_knowledge_bases(self):
        """测试可用知识库列表"""
        kb_names = self.config.get_available_kb_names()
        self.assertIsInstance(kb_names, list)
        self.assertIn("policy_demo_kb", kb_names)
        
    def test_policy_kb_config_loading(self):
        """测试政策库配置加载"""
        config = self.config.get_kb_config("policy_demo_kb")
        
        self.assertIsInstance(config, dict)
        self.assertIn('kb_name', config)
        self.assertIn('chunk_size', config)
        self.assertIn('system_prompt', config)
        
        # 验证政策库特定配置
        self.assertEqual(config['kb_name'], "policy_demo_kb")
        self.assertEqual(config['chunk_size'], 800)  # 政策文档使用大分块
        self.assertTrue(config['graph_retrieval'])   # 启用图谱检索
        self.assertEqual(config['pdf_parser'], "deepdoc")  # 使用深度解析
        
    def test_policy_kb_prompt_loading(self):
        """测试政策库提示词加载"""
        config = self.config.get_kb_config("policy_demo_kb")
        prompt = config.get('system_prompt', '')
        
        self.assertIsInstance(prompt, str)
        self.assertGreater(len(prompt), 100)  # 提示词应该有一定长度
        self.assertIn('政策', prompt)  # 应该包含政策相关内容
        
    def test_compatibility_methods(self):
        """测试兼容性方法"""
        # 测试旧方法仍可用
        self.assertEqual(self.config.policy_kb_name, "policy_demo_kb")
        
        old_config = self.config.get_policy_config()
        new_config = self.config.get_kb_config("policy_demo_kb")
        
        # 关键配置应该一致
        self.assertEqual(old_config['chunk_size'], new_config['chunk_size'])
        self.assertEqual(old_config['graph_retrieval'], new_config['graph_retrieval'])


class TestConfigFiles(unittest.TestCase):
    """配置文件测试类"""
    
    def setUp(self):
        """测试前设置"""
        self.project_root = Path(__file__).parent.parent
        
    def test_main_config_exists(self):
        """测试主配置文件存在"""
        config_file = self.project_root / "config" / "config.ini"
        self.assertTrue(config_file.exists(), "主配置文件 config.ini 不存在")
        
    def test_policy_kb_config_exists(self):
        """测试政策库配置文件存在"""
        kb_config_file = self.project_root / "config" / "knowledgebase" / "policy_demo_kb.ini"
        self.assertTrue(kb_config_file.exists(), "政策库配置文件不存在")
        
    def test_template_config_exists(self):
        """测试配置模板存在"""
        template_file = self.project_root / "config" / "knowledgebase" / "template.ini"
        self.assertTrue(template_file.exists(), "配置模板文件不存在")
        
    def test_policy_prompt_exists(self):
        """测试政策库提示词文件存在"""
        prompt_file = self.project_root / "config" / "prompts" / "policy_demo_kb.txt"
        self.assertTrue(prompt_file.exists(), "政策库提示词文件不存在")


if __name__ == '__main__':
    # 设置测试输出
    unittest.main(verbosity=2)