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
    "📄 文档": "documents",
    "📈 分析": "analysis"
}

from src.database.db_manager import get_db_manager
from src.clients.ragflow_client import get_ragflow_client
from src.clients.whisper_client import get_whisper_client
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



def check_services():
    """检查外部服务状态"""
    with st.sidebar:
        st.subheader("服务状态")

        # 检查RAGFlow
        try:
            ragflow = get_ragflow_client()
            ragflow_status = ragflow.check_health()
            ragflow_indicator = "✅" if ragflow_status else "⚠️"
            
        except Exception as e:
            logger.warning(f"RAGFlow连接检查失败: {e}")
            ragflow_indicator = "❌"
            ragflow_status = False

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
        with col2:
            st.write(f"{whisper_indicator} Whisper")
            st.write(f"{db_indicator} 数据库")

        # 配置详情
        with st.expander("🔧 配置详情"):
            st.info("知识库: " + getattr(config, 'ragflow_kb_name', 'policy_demo_kb'))
            
            # 显示部分配置参数
            doc_config = config.ragflow_document_config  # 这是property，不需要()
            st.text(f"分块大小: {doc_config.get('chunk_size', 1024)}")
            st.text(f"分块方法: {doc_config.get('chunk_method', 'laws')}")
            st.text(f"检索模式: {doc_config.get('retrieval_mode', 'general')}")

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
            from src.database.graph_dao import GraphDAO
            
            # 获取RAGFlow文档数
            ragflow = get_ragflow_client()
            kb_name = getattr(config, 'ragflow_kb_name', 'policy_demo_kb')
            
            col1, col2 = st.columns(2)
            
            # 显示RAGFlow文档数
            if ragflow.check_health():
                docs = ragflow.get_documents(kb_name)
                with col1:
                    st.metric("📄 文档数", len(docs))
            else:
                with col1:
                    st.metric("📄 文档数", "N/A")
            
            # 显示图谱节点数
            try:
                db_path = config.data_dir / "database" / "policies.db"
                graph_dao = GraphDAO(str(db_path))
                graph_stats = graph_dao.get_stats()
                with col2:
                    st.metric("🕸️ 图谱节点", graph_stats.get('node_count', 0) if graph_stats else 0)
            except Exception:
                with col2:
                    st.metric("🕸️ 图谱节点", 0)

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

    # 获取实际数据
    try:
        config = get_config()
        kb_name = getattr(config, 'ragflow_kb_name', 'policy_demo_kb')
        
        # RAGFlow文档数
        doc_count = 0
        try:
            ragflow = get_ragflow_client()
            if ragflow.check_health():
                docs = ragflow.get_documents(kb_name)
                doc_count = len(docs)
        except Exception as e:
            logger.debug(f"获取文档数失败: {e}")
        
        # 图谱节点数
        node_count = 0
        try:
            from src.database.graph_dao import GraphDAO
            db_path = config.data_dir / "database" / "policies.db"
            graph_dao = GraphDAO(str(db_path))
            graph_stats = graph_dao.get_stats()
            if graph_stats:
                node_count = graph_stats.get('node_count', 0)
        except Exception as e:
            logger.debug(f"获取图谱节点数失败: {e}")
        
        with col1:
            st.metric("📄 RAGFlow文档", doc_count)

        with col2:
            st.metric("🕸️ 知识图谱节点", node_count)

        with col3:
            # 关系数替代标签数（因为没有标签功能）
            edge_count = 0
            if graph_stats:
                edge_count = graph_stats.get('edge_count', 0)
            st.metric("🔗 图谱关系", edge_count)
    
    except Exception as e:
        logger.error(f"获取首页统计数据失败: {e}")
        with col1:
            st.metric("📄 文档", "N/A")
        with col2:
            st.metric("🕸️ 节点", "N/A")
        with col3:
            st.metric("🔗 关系", "N/A")

    st.divider()

    # 功能介绍
    st.subheader("系统功能")

    features = {
        "🔍 政策搜索": "快速搜索和检索政策文档，支持多维度筛选",
        "� 智能问答": "基于RAGFlow和Qwen的AI问答系统",
        "📊 知识图谱": "可视化展示政策之间的关系和依赖",
        "📄 文档管理": "上传和管理政策文档，自动提取元数据",
        "📈 数据统计": "查看文档和图谱统计信息"
    }

    for feature, description in features.items():
        st.info(f"**{feature}** - {description}")

    st.divider()

    # 快速开始
    st.subheader("快速开始")
    st.markdown("""
    1. **上传政策文档**：在"文档管理"页面上传政策文档到RAGFlow
    2. **搜索政策**：在"搜索"页面查找相关政策
    3. **智能问答**：在"聊天"页面与AI对话获取政策建议
    4. **浏览图谱**：在"图谱"页面查看政策关系网络
    5. **数据统计**：在"分析"页面查看文档和图谱统计
    """)


def main():
    """主应用函数"""
    # 配置页面
    setup_page_config()

    # 初始化会话状态
    initialize_session_state()

    # 显示侧边栏
    show_sidebar()

    # 创建导航菜单
    with st.sidebar:
        st.divider()
        selected_page = option_menu(
            menu_title="导航",
            options=list(PAGES.keys()),
            icons=["house", "search", "chat", "diagram-2", "file-earmark", "bar-chart"],
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
