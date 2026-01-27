"""
运行聊天功能相关的单元测试
"""
import pytest
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    """运行测试"""
    print("=" * 60)
    print("运行聊天功能单元测试")
    print("=" * 60)
    
    # 测试参数
    args = [
        "tests/test_services/test_hybrid_retriever.py",
        "tests/test_services/test_chat_service.py",
        "-v",  # 详细输出
        "--tb=short",  # 简短的traceback
        "--color=yes",  # 彩色输出
        "-x",  # 遇到第一个失败就停止
    ]
    
    # 运行pytest
    exit_code = pytest.main(args)
    
    print("\n" + "=" * 60)
    if exit_code == 0:
        print("✅ 所有测试通过！")
    else:
        print(f"❌ 测试失败，退出码: {exit_code}")
    print("=" * 60)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
