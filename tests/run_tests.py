#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试套件运行器

统一运行所有单元测试，支持不同的测试模式和输出格式
"""

import unittest
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

def run_all_tests(verbosity=2, pattern='test_*.py'):
    """运行所有测试"""
    print("🔧 运行政策库系统单元测试套件")
    print("=" * 60)
    
    # 设置测试目录
    test_dir = Path(__file__).parent
    
    # 发现并加载测试
    loader = unittest.TestLoader()
    suite = loader.discover(test_dir, pattern=pattern)
    
    # 运行测试
    runner = unittest.TextTestRunner(
        verbosity=verbosity,
        stream=sys.stdout,
        descriptions=True,
        failfast=False
    )
    
    result = runner.run(suite)
    
    # 输出测试结果汇总
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    print(f"  运行测试: {result.testsRun}")
    print(f"  失败: {len(result.failures)}")
    print(f"  错误: {len(result.errors)}")
    print(f"  跳过: {len(result.skipped)}")
    
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100 if result.testsRun > 0 else 0
    print(f"  成功率: {success_rate:.1f}%")
    
    if result.failures:
        print("\n❌ 失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}")
            
    if result.errors:
        print("\n💥 错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}")
            
    if result.skipped:
        print("\n⏭️  跳过的测试:")
        for test, reason in result.skipped:
            print(f"  - {test}: {reason}")
    
    return result.wasSuccessful()

def run_config_tests():
    """只运行配置相关测试"""
    print("🔧 运行配置系统测试")
    print("=" * 40)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 加载配置测试
    from test_config_system import TestConfigSystem, TestConfigFiles
    suite.addTest(loader.loadTestsFromTestCase(TestConfigSystem))
    suite.addTest(loader.loadTestsFromTestCase(TestConfigFiles))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

def run_ragflow_tests():
    """只运行RAGFlow相关测试"""
    print("🚀 运行RAGFlow客户端测试")
    print("=" * 40)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 加载RAGFlow测试
    try:
        from test_ragflow_client import TestRAGFlowClient, TestRAGFlowAPI
        from test_ragflow_config_update import TestRAGFlowConfigUpdate
        from final_verification import TestFinalVerification
        
        suite.addTest(loader.loadTestsFromTestCase(TestRAGFlowClient))
        suite.addTest(loader.loadTestsFromTestCase(TestRAGFlowAPI))
        suite.addTest(loader.loadTestsFromTestCase(TestRAGFlowConfigUpdate))
        suite.addTest(loader.loadTestsFromTestCase(TestFinalVerification))
    except ImportError as e:
        print(f"警告: 无法导入RAGFlow测试模块: {e}")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

def run_api_exploration_tests():
    """只运行API探索测试"""
    print("🔍 运行API探索测试")
    print("=" * 40)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 加载API探索测试
    try:
        from test_ragflow_api_exploration import TestRAGFlowAPIExploration
        suite.addTest(loader.loadTestsFromTestCase(TestRAGFlowAPIExploration))
    except ImportError as e:
        print(f"警告: 无法导入API探索测试: {e}")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='政策库系统测试运行器')
    parser.add_argument('--type', choices=['all', 'config', 'ragflow', 'api'], 
                       default='all', help='测试类型')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='详细输出')
    parser.add_argument('--pattern', default='test_*.py', 
                       help='测试文件模式')
    
    args = parser.parse_args()
    
    verbosity = 2 if args.verbose else 1
    
    if args.type == 'all':
        success = run_all_tests(verbosity, args.pattern)
    elif args.type == 'config':
        success = run_config_tests()
    elif args.type == 'ragflow':
        success = run_ragflow_tests()
    elif args.type == 'api':
        success = run_api_exploration_tests()
    
    sys.exit(0 if success else 1)