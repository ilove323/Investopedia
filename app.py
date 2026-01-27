"""
政策库知识库+知识图谱系统
主应用入口

使用 streamlit run app.py 启动应用
"""
import logging
import sys
from pathlib import Path

import streamlit as st
from streamlit_option_menu import option_menu

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

# ===== 导入新的配置系统 =====
# 说明：使用新的ConfigLoader替代旧的config.app_config
# ConfigLoader会自动读取config.ini并支持环境变量覆盖
from src.config import get_config

# 获取全局配置对象
config = get_config()

# ===== 从配置中提取应用参数 =====
# 说明：这些变量从config.ini中读取，环境变量可以覆盖INI配置
APP_NAME = config.app_name  # 应用名称
APP_DESCRIPTION = config.app_description  # 应用描述
APP_ICON = config.app_icon  # 应用图标
APP_LAYOUT = config.app_layout  # Streamlit布局（wide/centered）
DATA_DIR = config.data_dir  # 数据目录路径
LOGS_DIR = config.logs_dir  # 日志目录路径

# ===== 定义页面导航菜单 =====
# 说明：这个字典定义了左侧导航菜单中显示的页面
# key：显示名称，value：页面标识符
PAGES = {
    "🏠 欢迎": "home",
    "🔍 搜索": "search",
    "💬 聊天": "chat",
    "📊 图谱": "graph",
    "🎤 语音": "voice",
    "📄 文档": "documents",
    "📈 分析": "analysis"
}

from src.database.db_manager import get_db_manager
from src.services.ragflow_client import get_ragflow_client
from src.services.whisper_client import get_whisper_client
from src.utils.logger import setup_logger

# ===== 配置日志 =====
# 说明：日志文件会保存在logs目录中，日志级别从config读取
logger = setup_logger(
    log_file=str(config.logs_dir_path / "app.log"),
    log_level=config.log_level
)

# ===== 初始化数据目录 =====
# 说明：虽然ConfigLoader已经在__init__中创建过这些目录，
# 但这里再创建一次是为了保险起见
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def setup_page_config():
    """配置Streamlit页面"""
    st.set_page_config(
        page_title=APP_NAME,
        page_icon=APP_ICON,
        layout=APP_LAYOUT,
        initial_sidebar_state="auto"  # 改为auto，让用户可以控制
    )

    # 自定义CSS
    st.markdown("""
    <style>
    /* 自定义样式 */
    .main {
        padding: 2rem;
    }

    .stTabs [data-baseweb="tab-list"] button {
        font-size: 16px;
        padding: 10px 20px;
    }

    .stButton>button {
        padding: 10px 20px;
        font-size: 14px;
    }

    [data-testid="stMetricValue"] {
        font-size: 24px;
    }
    
    /* 侧边栏折叠按钮样式 */
    .sidebar-collapse-btn {
        position: fixed;
        top: 10px;
        right: 10px;
        z-index: 999;
        background-color: #f0f2f6;
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 5px 10px;
        cursor: pointer;
    }
    </style>
    """, unsafe_allow_html=True)


def initialize_session_state():
    """初始化会话状态"""
    default_states = {
        'current_page': '搜索',
        'policies': [],
        'selected_policy': None,
        'graph': None,
        'search_query': '',
        'search_results': [],
        'voice_text': '',
        'voice_answer': '',
        'documents': [],
        'stats': {},
        'sidebar_collapsed': False  # 添加侧边栏折叠状态
    }

    for key, value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = value


def initialize_ragflow_config():
    """初始化RAGFlow配置
    
    在应用启动时自动同步知识库配置到RAGFlow
    """
    try:
        if 'ragflow_config_synced' not in st.session_state:
            logger.info("开始同步RAGFlow配置...")
            
            from src.services.config_sync import sync_ragflow_configs
            
            # 同步所有知识库配置
            results = sync_ragflow_configs()
            
            # 记录同步状态
            st.session_state.ragflow_config_synced = True
            st.session_state.ragflow_sync_results = results
            
            # 显示同步结果
            success_count = sum(1 for r in results.values() if r)
            total_count = len(results)
            
            if success_count == total_count:
                logger.info(f"✅ RAGFlow配置同步完成: {success_count}/{total_count}")
            else:
                logger.warning(f"⚠️ RAGFlow配置部分同步: {success_count}/{total_count}")
                
    except Exception as e:
        logger.warning(f"RAGFlow配置同步失败: {e}")
        st.session_state.ragflow_config_synced = False


def check_services():
    """检查外部服务状态"""
    with st.sidebar:
        st.subheader("服务状态")

        # 检查RAGFlow
        try:
            ragflow = get_ragflow_client()
            ragflow_status = ragflow.check_health()
            ragflow_indicator = "✅" if ragflow_status else "⚠️"
            
            # 显示配置状态
            config_status = st.session_state.get('ragflow_configured', False)
            config_indicator = "✅" if config_status else "⚠️"
            
        except Exception as e:
            logger.warning(f"RAGFlow连接检查失败: {e}")
            ragflow_indicator = "❌"
            ragflow_status = False
            config_indicator = "❌"

        # 检查Whisper
        try:
            whisper = get_whisper_client()
            whisper_status = whisper.check_health()
            whisper_indicator = "✅" if whisper_status else "⚠️"
        except Exception as e:
            logger.warning(f"Whisper连接检查失败: {e}")
            whisper_indicator = "❌"
            whisper_status = False

        # 检查数据库
        try:
            db = get_db_manager()
            db_indicator = "✅"
            db_status = True
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            db_indicator = "❌"
            db_status = False

        col1, col2 = st.columns(2)
        with col1:
            st.write(f"{ragflow_indicator} RAGFlow")
            st.write(f"{config_indicator} 配置应用")
        with col2:
            st.write(f"{whisper_indicator} Whisper")
            st.write(f"{db_indicator} 数据库")

        # 配置详情
        with st.expander("🔧 配置详情"):
            if config_status:
                st.success("RAGFlow配置已自动应用")
                st.info("知识库: " + getattr(config, 'ragflow_kb_name', 'policy_demo_kb'))
                
                # 显示部分配置参数
                doc_config = config.ragflow_document_config  # 这是property，不需要()
                st.text(f"分块大小: {doc_config.get('chunk_size', 800)}")
                st.text(f"PDF解析器: {doc_config.get('pdf_parser', 'deepdoc')}")
                st.text(f"检索方法: {doc_config.get('retrieval_method', 'General')}")
            else:
                st.warning("RAGFlow配置未完全生效")
                if st.button("🔄 重新配置"):
                    # 手动触发配置
                    try:
                        ragflow = get_ragflow_client()
                        if ragflow.configure_knowledge_base():
                            st.session_state.ragflow_configured = True
                            st.rerun()
                        else:
                            st.error("配置失败")
                    except Exception as e:
                        st.error(f"配置失败: {e}")

    # 警告信息
    if not all([ragflow_status, whisper_status, db_status]):
        st.warning("⚠️ 部分服务异常，某些功能可能不可用")


def show_sidebar():
    """显示侧边栏"""
    with st.sidebar:
        st.title(f"{APP_ICON} {APP_NAME}")
        st.caption(APP_DESCRIPTION)

        # 检查服务状态
        check_services()

        st.divider()

        # 快速统计
        st.subheader("统计信息")
        try:
            from src.database.policy_dao import get_policy_dao
            dao = get_policy_dao()
            stats = dao.get_stats()

            col1, col2 = st.columns(2)
            with col1:
                st.metric("总政策数", stats.get('total', 0))
            with col2:
                st.metric("已上传文件", stats.get('total', 0))

            if 'by_type' in stats:
                st.write("按类型分布:")
                for policy_type, count in stats['by_type'].items():
                    st.write(f"  - {policy_type}: {count}")

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")

        st.divider()

        # 快速链接
        st.subheader("快速链接")
        st.markdown("""
        - [知识库文档](./know-how.md)
        - [API文档](./docs/api.md)
        - [部署指南](./README.md)
        """)

        # 关于
        st.divider()
        st.caption("v1.0.0-beta | 2024")


def show_home():
    """显示首页"""
    st.title("🏠 欢迎来到政策库知识系统")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("已加载政策", 0)

    with col2:
        st.metric("知识图谱节点", 0)

    with col3:
        st.metric("已标记标签", 0)

    st.divider()

    # 功能介绍
    st.subheader("系统功能")

    features = {
        "🔍 政策搜索": "快速搜索和检索政策文档，支持多维度筛选",
        "📊 知识图谱": "可视化展示政策之间的关系和依赖",
        "🎤 语音问答": "通过语音提问，获取政策相关建议",
        "📄 文档管理": "上传和管理政策文档，自动提取元数据",
        "📈 政策分析": "分析政策时效性和影响范围"
    }

    for feature, description in features.items():
        st.info(f"**{feature}** - {description}")

    st.divider()

    # 快速开始
    st.subheader("快速开始")
    st.markdown("""
    1. **上传政策文档**：在"文档管理"页面上传政策文档
    2. **搜索政策**：在"政策搜索"页面查找相关政策
    3. **浏览图谱**：在"知识图谱"页面查看政策关系
    4. **语音问答**：在"语音问答"页面提问获取建议
    5. **数据分析**：在"政策分析"页面查看趋势和影响
    """)


def main():
    """主应用函数"""
    # 配置页面
    setup_page_config()

    # 初始化会话状态
    initialize_session_state()
    
    # 初始化RAGFlow配置
    initialize_ragflow_config()

    # 显示侧边栏
    show_sidebar()

    # 创建导航菜单
    with st.sidebar:
        st.divider()
        selected_page = option_menu(
            menu_title="导航",
            options=list(PAGES.keys()),
            icons=["house", "search", "diagram-2", "mic", "file-earmark", "bar-chart"],
            menu_icon="cast",
            default_index=0,
            orientation="vertical"
        )

    # 根据选择显示不同页面
    page_key = selected_page.split()[-1].lower() if selected_page else "search"

    try:
        if "欢迎" in selected_page or page_key == "home":
            show_home()
        elif "搜索" in selected_page:
            from src.pages.search_page import show as show_search_page
            show_search_page()
        elif "聊天" in selected_page:
            from src.pages.chat_page import show as show_chat_page
            show_chat_page()
        elif "图谱" in selected_page:
            from src.pages.graph_page import show as show_graph_page
            show_graph_page()
        elif "语音" in selected_page:
            from src.pages.voice_page import show as show_voice_page
            show_voice_page()
        elif "文档" in selected_page:
            from src.pages.documents_page import show as show_documents_page
            show_documents_page()
        elif "分析" in selected_page:
            from src.pages.analysis_page import show as show_analysis_page
            show_analysis_page()
        else:
            show_home()

    except ImportError as e:
        logger.warning(f"页面模块未实现: {e}")
        st.info("该页面还未实现，请稍候...")
    except Exception as e:
        logger.error(f"页面渲染错误: {e}")
        st.error(f"页面加载出错: {str(e)}")


if __name__ == "__main__":
    main()
