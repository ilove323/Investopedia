#!/bin/bash

# 政策库系统测试快速运行脚本
# Quick test runner for Policy Knowledge Base System

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录的父目录作为项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ "$SCRIPT_DIR" == */tests ]]; then
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
else
    PROJECT_ROOT="$SCRIPT_DIR"
fi

echo -e "${BLUE}🔧 政策库系统测试运行器${NC}"
echo "脚本目录: $SCRIPT_DIR"
echo "项目根目录: $PROJECT_ROOT"
echo "======================================"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 未找到，请先安装Python3${NC}"
    exit 1
fi

# 设置Python路径
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# 切换到项目根目录
cd "$PROJECT_ROOT"

# 检查依赖
echo -e "${YELLOW}📦 检查依赖...${NC}"
if [ -f "requirements.txt" ]; then
    python3 -c "import requests, configparser, streamlit" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}⚠️ 部分依赖可能缺失，建议运行: pip install -r requirements.txt${NC}"
    fi
fi

# 检查测试目录和运行器是否存在
if [ ! -d "tests" ]; then
    echo -e "${RED}❌ tests目录不存在${NC}"
    exit 1
fi

if [ ! -f "tests/run_tests.py" ]; then
    echo -e "${RED}❌ tests/run_tests.py不存在${NC}"
    exit 1
fi

# 根据参数选择测试类型
case "${1:-all}" in
    "config")
        echo -e "${GREEN}🔧 运行配置系统测试...${NC}"
        python3 tests/run_tests.py --type config
        ;;
    "ragflow")
        echo -e "${GREEN}🚀 运行RAGFlow客户端测试...${NC}"
        python3 tests/run_tests.py --type ragflow
        ;;
    "api")
        echo -e "${GREEN}🔍 运行API探索测试...${NC}"
        python3 tests/run_tests.py --type api
        ;;
    "quick")
        echo -e "${GREEN}⚡ 运行快速测试（跳过网络测试）...${NC}"
        export RAGFLOW_TEST_MODE=1
        python3 tests/run_tests.py --pattern "test_config_*.py"
        ;;
    "verbose")
        echo -e "${GREEN}📝 运行详细测试...${NC}"
        python3 tests/run_tests.py --verbose
        ;;
    "all"|*)
        echo -e "${GREEN}🎯 运行所有测试...${NC}"
        python3 tests/run_tests.py
        ;;
esac

# 检查退出码
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ 测试完成！${NC}"
    echo -e "📊 查看详细报告: tests/TEST_REPORT.md"
    echo -e "📖 测试文档: tests/README.md"
else
    echo -e "\n${RED}❌ 测试失败，请检查输出信息${NC}"
    echo -e "🔧 故障排除:"
    echo -e "   1. 检查依赖: pip install -r requirements.txt"
    echo -e "   2. 检查配置: config/config.ini"
    echo -e "   3. 查看测试文档: tests/README.md"
    exit 1
fi