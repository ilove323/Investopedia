"""
配置加载器 - 从config.ini和知识库配置文件读取配置
"""
import configparser
import os
from pathlib import Path
from typing import Dict, Optional


class ConfigLoader:
    """配置加载器类"""

    def __init__(self):
        """初始化配置加载器"""
        self.config = configparser.ConfigParser()
        self.config_path = self._find_config_file()

        if self.config_path and self.config_path.exists():
            self.config.read(self.config_path, encoding='utf-8')
        else:
            raise FileNotFoundError(
                "config.ini 文件不存在。请复制 config/config.ini.template 为 config/config.ini"
            )

        # 初始化项目路径
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "data"
        self.logs_dir = self.project_root / "logs"

        # 创建必要的目录
        self._ensure_directories()
        
        # 知识库配置缓存
        self._kb_configs = {}

    def _find_config_file(self) -> Path:
        """查找config.ini文件"""
        # 优先从项目根目录的config目录查找
        project_root = Path(__file__).parent.parent.parent
        config_file = project_root / "config" / "config.ini"
        return config_file

    def _ensure_directories(self):
        """确保必要的目录存在"""
        dirs = [
            self.data_dir,
            self.data_dir / "database",
            self.data_dir / "uploads",
            self.data_dir / "graphs",
            self.logs_dir,
        ]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)

    def _load_kb_config(self, kb_name: str) -> Optional[configparser.ConfigParser]:
        """加载知识库专用配置文件"""
        if kb_name in self._kb_configs:
            return self._kb_configs[kb_name]
            
        try:
            # 获取知识库配置文件名
            config_filename = self.get("KNOWLEDGE_BASES", kb_name, f"{kb_name}.ini")
            kb_config_dir = self.get("KNOWLEDGE_BASES", "knowledgebase_config_dir", "config/knowledgebase")
            config_path = self.project_root / kb_config_dir / config_filename
            
            if config_path.exists():
                kb_config = configparser.ConfigParser()
                kb_config.read(config_path, encoding='utf-8')
                self._kb_configs[kb_name] = kb_config
                return kb_config
            else:
                print(f"Warning: 知识库配置文件 {config_path} 不存在")
                return None
                
        except Exception as e:
            print(f"Error: 加载知识库配置 {kb_name} 失败: {e}")
            return None

    def get(self, section: str, option: str, fallback=None):
        """获取配置值"""
        try:
            return self.config.get(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback

    def get_int(self, section: str, option: str, fallback=None):
        """获取整数配置值"""
        try:
            return self.config.getint(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback

    def get_float(self, section: str, option: str, fallback=None):
        """获取浮点数配置值"""
        try:
            return self.config.getfloat(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback

    def get_bool(self, section: str, option: str, fallback=False):
        """获取布尔值配置"""
        try:
            return self.config.getboolean(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback

    def get_list(self, section: str, option: str, fallback=None, separator=","):
        """获取列表配置值（逗号分隔）"""
        value = self.get(section, option)
        if value is None:
            return fallback if fallback is not None else []
        return [item.strip() for item in value.split(separator)]

    # ===== APP 配置 =====
    @property
    def app_name(self) -> str:
        return self.get("APP", "name", "政策库知识库+知识图谱系统")

    @property
    def app_description(self) -> str:
        return self.get("APP", "description", "专项债、特许经营、数据资产政策知识库")

    @property
    def app_icon(self) -> str:
        return self.get("APP", "icon", "📋")

    @property
    def app_layout(self) -> str:
        return self.get("APP", "layout", "wide")

    @property
    def app_debug(self) -> bool:
        return self.get_bool("APP", "debug", False)

    @property
    def llm_provider(self) -> str:
        """大模型提供商：qwen 或 openai"""
        return self.get("APP", "provider", "qwen").lower()

    @property
    def default_language(self) -> str:
        return self.get("APP", "default_language", "zh")

    @property
    def supported_languages(self) -> list:
        return self.get_list("APP", "supported_languages", ["zh", "en"])

    @property
    def search_results_per_page(self) -> int:
        return self.get_int("APP", "search_results_per_page", 10)

    @property
    def max_search_results(self) -> int:
        return self.get_int("APP", "max_search_results", 100)

    @property
    def graph_max_nodes(self) -> int:
        return self.get_int("APP", "graph_max_nodes", 200)

    @property
    def graph_max_edges(self) -> int:
        return self.get_int("APP", "graph_max_edges", 500)

    @property
    def default_graph_layout(self) -> str:
        return self.get("APP", "default_graph_layout", "force_directed")

    @property
    def expiration_warning_days(self) -> int:
        return self.get_int("APP", "expiration_warning_days", 30)

    @property
    def max_upload_size(self) -> int:
        return self.get_int("APP", "max_upload_size", 52428800)  # 50MB

    @property
    def allowed_file_types(self) -> dict:
        """获取允许的文件类型"""
        extensions = self.get_list("APP", "allowed_file_types", ["pdf", "docx", "xlsx", "txt"])
        mime_types = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "txt": "text/plain"
        }
        return {ext: mime_types.get(ext, "") for ext in extensions}

    # ===== RAGFLOW 配置 =====
    @property
    def ragflow_host(self) -> str:
        return os.getenv("RAGFLOW_HOST") or self.get("RAGFLOW", "host", "localhost")

    @property
    def ragflow_port(self) -> int:
        port = os.getenv("RAGFLOW_PORT") or self.get("RAGFLOW", "port")
        return int(port) if port else 9380

    @property
    def ragflow_base_url(self) -> str:
        return f"http://{self.ragflow_host}:{self.ragflow_port}"

    @property
    def ragflow_api_key(self) -> str:
        """获取RAGFlow API Key（支持环境变量覆盖）"""
        return os.getenv("RAGFLOW_API_KEY") or self.get("RAGFLOW", "api_key", "")

    @property
    def ragflow_web_url(self) -> str:
        """获取RAGFlow Web界面URL"""
        return self.get("RAGFLOW", "web_url", self.ragflow_base_url)

    @property
    def ragflow_timeout(self) -> int:
        return self.get_int("RAGFLOW", "timeout", 30)

    @property
    def ragflow_retry_times(self) -> int:
        return self.get_int("RAGFLOW", "retry_times", 3)

    @property
    def ragflow_retry_delay(self) -> int:
        return self.get_int("RAGFLOW", "retry_delay", 1)

    @property
    def ragflow_search_config(self) -> dict:
        return {
            "top_k": self.get_int("RAGFLOW", "search_top_k", 10),
            "score_threshold": self.get_float("RAGFLOW", "search_score_threshold", 0.5),
            "search_type": self.get("RAGFLOW", "search_type", "hybrid"),
        }

    @property
    def ragflow_qa_config(self) -> dict:
        return {
            "max_tokens": self.get_int("RAGFLOW", "qa_max_tokens", 2000),
            "temperature": self.get_float("RAGFLOW", "qa_temperature", 0.1),
            "top_p": self.get_float("RAGFLOW", "qa_top_p", 0.9),
        }

    @property
    def ragflow_document_config(self) -> dict:
        """获取RAGFlow文档处理和元数据配置"""
        return {
            'chunk_size': self.config.getint('RAGFLOW', 'document_chunk_size', fallback=800),
            'chunk_overlap': self.config.getint('RAGFLOW', 'document_chunk_overlap', fallback=100),
            'smart_chunking': self.config.getboolean('RAGFLOW', 'document_smart_chunking', fallback=True),
            'pdf_parser': self.config.get('RAGFLOW', 'ragflow_pdf_parser', fallback='deepdoc'),
            'auto_metadata': self.config.getboolean('RAGFLOW', 'ragflow_auto_metadata', fallback=True),
            'metadata_extraction': self.config.getboolean('RAGFLOW', 'ragflow_metadata_extraction', fallback=True),
            'table_recognition': self.config.getboolean('RAGFLOW', 'ragflow_table_recognition', fallback=True),
            'formula_recognition': self.config.getboolean('RAGFLOW', 'ragflow_formula_recognition', fallback=False),
            'ocr_enabled': self.config.getboolean('RAGFLOW', 'ragflow_ocr_enabled', fallback=True)
        }

    @property
    def ragflow_advanced_config(self) -> dict:
        """获取RAGFlow高级配置"""
        return {
            'max_tokens': self.config.getint('RAGFLOW', 'ragflow_max_tokens', fallback=2048),
            'similarity_threshold': self.config.getfloat('RAGFLOW', 'ragflow_similarity_threshold', fallback=0.3),
            'max_clusters': self.config.getint('RAGFLOW', 'ragflow_max_clusters', fallback=50),
            'random_seed': self.config.getint('RAGFLOW', 'ragflow_random_seed', fallback=42),
            'retrieval_mode': self.config.get('RAGFLOW', 'ragflow_retrieval_mode', fallback='general'),
            'entity_normalization': self.config.getboolean('RAGFLOW', 'ragflow_entity_normalization', fallback=True),
            'graph_retrieval': self.config.getboolean('RAGFLOW', 'ragflow_graph_retrieval', fallback=True)
        }

    @property
    def ragflow_kb_config(self) -> dict:
        return {
            "name": self.get("RAGFLOW", "kb_name", "policy_demo_kb"),
            "description": self.get("RAGFLOW", "kb_description", "政策知识库 - 专项债/特许经营/数据资产"),
        }

    @property
    def ragflow_kb_name(self) -> str:
        """获取RAGFlow知识库名称"""
        return self.get("RAGFLOW", "kb_name", "policy_demo_kb")

    @property
    def deepseek_api_key(self) -> str:
        return os.getenv("DEEPSEEK_API_KEY") or self.get("RAGFLOW", "deepseek_api_key", "")

    # ===== WHISPER 配置 =====
    @property
    def whisper_host(self) -> str:
        return os.getenv("WHISPER_HOST") or self.get("WHISPER", "host", "localhost")

    @property
    def whisper_port(self) -> int:
        port = os.getenv("WHISPER_PORT") or self.get("WHISPER", "port")
        return int(port) if port else 9000

    @property
    def whisper_base_url(self) -> str:
        return f"http://{self.whisper_host}:{self.whisper_port}"

    @property
    def whisper_timeout(self) -> int:
        return self.get_int("WHISPER", "timeout", 60)

    @property
    def whisper_retry_times(self) -> int:
        return self.get_int("WHISPER", "retry_times", 3)

    @property
    def whisper_retry_delay(self) -> int:
        return self.get_int("WHISPER", "retry_delay", 1)

    @property
    def whisper_transcribe_config(self) -> dict:
        return {
            "task": self.get("WHISPER", "transcribe_task", "transcribe"),
            "language": self.get("WHISPER", "transcribe_language", "zh"),
            "word_timestamps": self.get_bool("WHISPER", "word_timestamps", False),
        }

    @property
    def whisper_audio_config(self) -> dict:
        return {
            "sample_rate": self.get_int("WHISPER", "audio_sample_rate", 16000),
            "channels": self.get_int("WHISPER", "audio_channels", 1),
            "normalize": self.get_bool("WHISPER", "audio_normalize", True),
            "remove_silence": self.get_bool("WHISPER", "audio_remove_silence", False),
            "max_duration": self.get_int("WHISPER", "audio_max_duration", 300),
        }

    @property
    def whisper_file_config(self) -> dict:
        return {
            "max_file_size": self.get_int("WHISPER", "audio_max_file_size", 52428800),
            "supported_formats": self.get_list("WHISPER", "audio_supported_formats", [".wav", ".mp3", ".m4a", ".flac", ".ogg"]),
        }

    @property
    def whisper_model_config(self) -> dict:
        return {
            "model": self.get("WHISPER", "whisper_model", "base"),
            "device": self.get("WHISPER", "whisper_device", "cpu"),
            "compute_type": self.get("WHISPER", "whisper_compute_type", "float32"),
        }

    # ===== DATABASE 配置 =====
    @property
    def db_type(self) -> str:
        return self.get("DATABASE", "type", "sqlite")

    @property
    def sqlite_path(self) -> Path:
        sqlite_file = self.get("DATABASE", "sqlite_path", "data/database/policy.db")
        if not Path(sqlite_file).is_absolute():
            return self.project_root / sqlite_file
        return Path(sqlite_file)

    @property
    def sqlite_config(self) -> dict:
        return {
            "database": str(self.sqlite_path),
            "check_same_thread": self.get_bool("DATABASE", "sqlite_check_same_thread", False),
            "timeout": self.get_float("DATABASE", "sqlite_timeout", 10.0),
        }

    @property
    def connection_pool_config(self) -> dict:
        return {
            "pool_size": self.get_int("DATABASE", "pool_size", 5),
            "max_overflow": self.get_int("DATABASE", "max_overflow", 10),
            "pool_recycle": self.get_int("DATABASE", "pool_recycle", 3600),
        }

    @property
    def auto_create_tables(self) -> bool:
        return self.get_bool("DATABASE", "auto_create_tables", True)

    @property
    def auto_init_tags(self) -> bool:
        return self.get_bool("DATABASE", "auto_init_tags", True)

    @property
    def query_timeout(self) -> int:
        return self.get_int("DATABASE", "query_timeout", 30)

    @property
    def batch_size(self) -> int:
        return self.get_int("DATABASE", "batch_size", 100)

    # ===== GRAPH 配置 =====
    @property
    def graphs_dir(self) -> Path:
        graph_dir = self.get("GRAPH", "graph_storage_dir", "data/graphs")
        if not Path(graph_dir).is_absolute():
            return self.project_root / graph_dir
        return Path(graph_dir)

    @property
    def is_directed(self) -> bool:
        return self.get_bool("GRAPH", "is_directed", False)

    @property
    def pyvis_config(self) -> dict:
        return {
            "height": self.get("GRAPH", "pyvis_height", "750px"),
            "width": self.get("GRAPH", "pyvis_width", "100%"),
            "bgcolor": self.get("GRAPH", "pyvis_bgcolor", "#222222"),
            "font_color": self.get("GRAPH", "pyvis_font_color", "white"),
            "font_size": self.get_int("GRAPH", "pyvis_font_size", 14),
            "physics": {
                "enabled": self.get_bool("GRAPH", "pyvis_physics_enabled", True),
                "stabilization": {
                    "iterations": self.get_int("GRAPH", "pyvis_stabilization_iterations", 200)
                }
            }
        }

    @property
    def graph_limits(self) -> dict:
        return {
            "max_nodes": self.get_int("GRAPH", "max_nodes", 200),
            "max_edges": self.get_int("GRAPH", "max_edges", 500),
            "max_node_label_length": self.get_int("GRAPH", "max_node_label_length", 20),
        }

    @property
    def graph_export_formats(self) -> list:
        return self.get_list("GRAPH", "export_formats", ["html", "json", "svg"])

    @property
    def graph_save_html(self) -> bool:
        return self.get_bool("GRAPH", "save_html", True)

    # ===== LOGGING 配置 =====
    @property
    def logs_dir_path(self) -> Path:
        log_dir = self.get("LOGGING", "log_dir", "logs")
        if not Path(log_dir).is_absolute():
            return self.project_root / log_dir
        return Path(log_dir)

    @property
    def log_level(self) -> str:
        return self.get("LOGGING", "log_level", "INFO")

    @property
    def log_format(self) -> str:
        return self.get("LOGGING", "log_format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    @property
    def rotating_max_bytes(self) -> int:
        return self.get_int("LOGGING", "rotating_max_bytes", 10485760)  # 10MB

    @property
    def rotating_backup_count(self) -> int:
        return self.get_int("LOGGING", "rotating_backup_count", 5)
    
    # ==================== 知识库配置系统 ====================
    
    @property
    def default_kb_name(self) -> str:
        """获取默认知识库名称"""
        return self.get("KNOWLEDGE_BASES", "default_kb", "policy_demo_kb")
    
    @property
    def prompts_dir(self) -> Path:
        """获取提示词目录路径"""
        prompts_dir = self.get("KNOWLEDGE_BASES", "prompts_dir", "config/prompts")
        return self.project_root / prompts_dir
    
    def get_kb_config(self, kb_name: str = None) -> Dict:
        """获取指定知识库的完整配置
        
        Args:
            kb_name: 知识库名称，默认使用default_kb
            
        Returns:
            知识库配置字典
        """
        if kb_name is None:
            kb_name = self.default_kb_name
            
        kb_config = self._load_kb_config(kb_name)
        if not kb_config:
            return {}
            
        try:
            # 构建完整配置
            config = {}
            
            # 基本信息
            config.update({
                "kb_name": kb_config.get("KNOWLEDGE_BASE", "name", fallback=kb_name),
                "kb_description": kb_config.get("KNOWLEDGE_BASE", "description", fallback=""),
                "kb_language": kb_config.get("KNOWLEDGE_BASE", "language", fallback="Chinese"),
            })
            
            # 文档处理配置
            config.update({
                "chunk_size": kb_config.getint("DOCUMENT_PROCESSING", "chunk_size", fallback=800),
                "chunk_overlap": kb_config.getint("DOCUMENT_PROCESSING", "chunk_overlap", fallback=100),
                "chunk_method": kb_config.get("DOCUMENT_PROCESSING", "chunk_method", fallback="naive"),
                "pdf_parser": kb_config.get("DOCUMENT_PROCESSING", "pdf_parser", fallback="deepdoc"),
                "auto_metadata": kb_config.getboolean("DOCUMENT_PROCESSING", "auto_metadata", fallback=True),
                "table_recognition": kb_config.getboolean("DOCUMENT_PROCESSING", "table_recognition", fallback=True),
                "formula_recognition": kb_config.getboolean("DOCUMENT_PROCESSING", "formula_recognition", fallback=False),
                "ocr_enabled": kb_config.getboolean("DOCUMENT_PROCESSING", "ocr_enabled", fallback=True),
                "layout_recognize": kb_config.get("DOCUMENT_PROCESSING", "layout_recognize", fallback="deepdoc"),
            })
            
            # 检索配置
            config.update({
                "similarity_threshold": kb_config.getfloat("RETRIEVAL", "similarity_threshold", fallback=0.3),
                "max_tokens": kb_config.getint("RETRIEVAL", "max_tokens", fallback=2048),
                "graph_retrieval": kb_config.getboolean("RETRIEVAL", "graph_retrieval", fallback=True),
                "entity_normalization": kb_config.getboolean("RETRIEVAL", "entity_normalization", fallback=True),
                "max_clusters": kb_config.getint("RETRIEVAL", "max_clusters", fallback=50),
            })
            
            # 问答配置
            config.update({
                "qa_max_tokens": kb_config.getint("QA", "max_tokens", fallback=2000),
                "qa_temperature": kb_config.getfloat("QA", "temperature", fallback=0.1),
                "qa_top_p": kb_config.getfloat("QA", "top_p", fallback=0.9),
            })
            
            # 提示词配置
            prompt_file = kb_config.get("QA", "system_prompt_file", fallback=f"{kb_name}.txt")
            config["system_prompt"] = self._load_prompt_file(prompt_file)
            
            return config
            
        except Exception as e:
            print(f"Error: 解析知识库配置 {kb_name} 失败: {e}")
            return {}
    
    def _load_prompt_file(self, filename: str) -> str:
        """加载提示词文件内容"""
        try:
            file_path = self.prompts_dir / filename
            if file_path.exists():
                return file_path.read_text(encoding='utf-8')
            else:
                print(f"Warning: 提示词文件 {file_path} 不存在")
                return "你是一个专业的智能助手，请基于提供的文档内容准确回答用户问题。"
        except Exception as e:
            print(f"Error: 读取提示词文件 {filename} 失败: {e}")
            return "你是一个专业的智能助手，请基于提供的文档内容准确回答用户问题。"
    
    def get_available_kb_names(self) -> list:
        """获取所有可用的知识库名称"""
        kb_names = []
        if self.config.has_section("KNOWLEDGE_BASES"):
            for key, value in self.config.items("KNOWLEDGE_BASES"):
                if key.endswith("_kb") or key not in ["default_kb", "knowledgebase_config_dir", "prompts_dir"]:
                    if not key.startswith("default") and not key.endswith("_dir"):
                        kb_names.append(key)
        return kb_names
    
    # ==================== RAGFlow连接配置 ====================
    
    @property
    def ragflow_host(self) -> str:
        return os.getenv("RAGFLOW_HOST") or self.get("RAGFLOW", "host", "localhost")
    
    @property  
    def ragflow_port(self) -> int:
        port = os.getenv("RAGFLOW_PORT") or self.get("RAGFLOW", "port")
        if port:
            return int(port)
        return 9380
    
    @property
    def ragflow_base_url(self) -> str:
        return f"http://{self.ragflow_host}:{self.ragflow_port}"
    
    @property
    def ragflow_api_key(self) -> str:
        return os.getenv("RAGFLOW_API_KEY") or self.get("RAGFLOW", "api_key", "")
    
    @property
    def ragflow_timeout(self) -> int:
        return self.get_int("RAGFLOW", "timeout", 30)
    
    @property
    def ragflow_retry_times(self) -> int:
        return self.get_int("RAGFLOW", "retry_times", 3)
    
    @property
    def ragflow_retry_delay(self) -> int:
        return self.get_int("RAGFLOW", "retry_delay", 1)
    
    # ===== QWEN配置 =====
    @property
    def qwen_api_key(self) -> str:
        """Qwen API密钥"""
        return self.get('QWEN', 'api_key', '')
    
    @property
    def qwen_model(self) -> str:
        """Qwen模型名称"""
        return self.get('QWEN', 'model', 'qwen-plus')
    
    @property
    def qwen_temperature(self) -> float:
        """Qwen温度参数"""
        return self.get_float('QWEN', 'temperature', 0.1)
    
    @property
    def qwen_max_tokens(self) -> int:
        """Qwen最大token数"""
        return self.get_int('QWEN', 'max_tokens', 2000)
    
    @property
    def entity_prompt_file(self) -> str:
        """实体提取提示词文件路径"""
        return self.get('APP', 'entity_prompt_file', 'config/prompts/entity_extraction.txt')

    # ===== OPENAI配置 =====
    @property
    def openai_base_url(self) -> str:
        """OpenAI 兼容接口地址"""
        return self.get('OPENAI', 'base_url', 'https://api.openai.com/v1')

    @property
    def openai_api_key(self) -> str:
        """OpenAI API密钥"""
        return self.get('OPENAI', 'api_key', '')

    @property
    def openai_model(self) -> str:
        """OpenAI 模型名称"""
        return self.get('OPENAI', 'model', 'gpt-4o-mini')

    @property
    def openai_temperature(self) -> float:
        """OpenAI 温度参数"""
        return self.get_float('OPENAI', 'temperature', 0.1)

    @property
    def openai_max_tokens(self) -> int:
        """OpenAI 最大token数"""
        return self.get_int('OPENAI', 'max_tokens', 500)

        return self.default_kb_name
    
    def get_policy_config(self) -> dict:
        """兼容性方法：获取政策库配置"""
        return self.get_kb_config("policy_demo_kb")
