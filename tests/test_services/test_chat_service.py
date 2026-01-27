"""
测试ChatService聊天服务
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.services.chat_service import ChatService, get_chat_service


class TestChatService:
    """测试ChatService类"""
    
    @pytest.fixture
    def chat_service(self):
        """创建ChatService实例"""
        with patch('src.services.chat_service.get_ragflow_client'):
            with patch('src.services.chat_service.get_hybrid_retriever'):
                with patch('src.services.chat_service.get_config'):
                    service = ChatService()
                    return service
    
    @pytest.fixture
    def mock_assistant(self):
        """创建模拟Assistant"""
        assistant = Mock()
        assistant.id = "test_assistant_id"
        assistant.name = "政策聊天助手"
        return assistant
    
    @pytest.fixture
    def mock_session(self):
        """创建模拟Session"""
        session = Mock()
        session.id = "test_session_id"
        return session
    
    def test_assistant_name_matches_config(self, chat_service):
        """测试Assistant名称与配置文件一致"""
        assert chat_service.assistant_name == "政策聊天助手"
    
    def test_get_or_find_assistant_success(self, chat_service, mock_assistant):
        """测试成功找到Assistant"""
        chat_service.ragflow = Mock()
        chat_service.ragflow.rag.list_chats.return_value = [mock_assistant]
        
        result = chat_service._get_or_find_assistant()
        
        assert result == mock_assistant
        assert chat_service.assistant == mock_assistant
    
    def test_get_or_find_assistant_not_found(self, chat_service):
        """测试Assistant不存在时抛出异常"""
        chat_service.ragflow = Mock()
        chat_service.ragflow.rag.list_chats.return_value = []
        chat_service.config = Mock()
        chat_service.config.ragflow_base_url = "http://test.com"
        chat_service.config.default_kb_name = "test_kb"
        
        with pytest.raises(ValueError) as exc_info:
            chat_service._get_or_find_assistant()
        
        error_msg = str(exc_info.value)
        assert "政策聊天助手" in error_msg
        assert "不存在" in error_msg
        assert "config/chat_assistant_config.ini" in error_msg
    
    def test_get_or_find_assistant_cached(self, chat_service, mock_assistant):
        """测试Assistant缓存机制"""
        chat_service.assistant = mock_assistant
        chat_service.ragflow = Mock()
        
        result = chat_service._get_or_find_assistant()
        
        # 不应该再次调用list_chats
        chat_service.ragflow.rag.list_chats.assert_not_called()
        assert result == mock_assistant
    
    def test_build_enhanced_question_with_relations(self, chat_service):
        """测试图谱关系注入"""
        question = "专项债券的用途是什么？"
        graph_context = {
            'relations': [
                {'source': '政策A', 'relation': '规定', 'target': '专项债券'},
                {'source': '专项债券', 'relation': '用于', 'target': '基础设施'}
            ]
        }
        
        enhanced = chat_service._build_enhanced_question(question, graph_context)
        
        assert question in enhanced
        assert "[知识图谱关系]" in enhanced
        assert "政策A → 规定 → 专项债券" in enhanced
        assert "专项债券 → 用于 → 基础设施" in enhanced
    
    def test_build_enhanced_question_no_relations(self, chat_service):
        """测试无图谱关系时返回原问题"""
        question = "测试问题"
        graph_context = {'relations': []}
        
        enhanced = chat_service._build_enhanced_question(question, graph_context)
        
        assert enhanced == question
    
    def test_build_enhanced_question_limit_relations(self, chat_service):
        """测试关系数量限制（最多10条）"""
        question = "测试问题"
        # 创建15条关系
        relations = [
            {'source': f'A{i}', 'relation': '关系', 'target': f'B{i}'}
            for i in range(15)
        ]
        graph_context = {'relations': relations}
        
        enhanced = chat_service._build_enhanced_question(question, graph_context)
        
        # 每条关系格式为：A → 关系 → B，有10条关系就有20个→
        relation_count = enhanced.count('→')
        # 代码中使用relations[:10]限制，所以是10条 * 2 = 20个→
        assert relation_count == 20, f"Expected 20 arrows (10 relations * 2), got {relation_count}"
    
    def test_format_references(self, chat_service):
        """测试参考文档格式化"""
        mock_refs = [
            Mock(
                content="文档内容1",
                document_name="政策文件1.pdf",
                document_id="doc1",
                chunk_id="chunk1",
                similarity=0.85
            ),
            Mock(
                content="文档内容2",
                document_name="政策文件2.pdf",
                document_id="doc2",
                chunk_id="chunk2",
                similarity=0.72
            )
        ]
        
        formatted = chat_service._format_references(mock_refs)
        
        assert len(formatted) == 2
        assert formatted[0]['content'] == "文档内容1"
        assert formatted[0]['document_name'] == "政策文件1.pdf"
        assert formatted[0]['similarity'] == 0.85
        assert formatted[1]['document_name'] == "政策文件2.pdf"
    
    def test_chat_session_creation(self, chat_service, mock_assistant, mock_session):
        """测试创建新session"""
        chat_service.assistant = mock_assistant
        chat_service.retriever = Mock()
        chat_service.retriever.retrieve.return_value = {
            'document_ids': [],
            'relations': []
        }
        
        mock_assistant.create_session.return_value = mock_session
        mock_session.ask.return_value = [
            Mock(content="测试回答", reference=None)
        ]
        
        with patch.object(chat_service, '_get_or_find_assistant', return_value=mock_assistant):
            results = list(chat_service.chat("测试问题", session_id=None))
        
        # 验证创建了新session
        mock_assistant.create_session.assert_called_once()
        
        # 验证返回了结果
        assert len(results) > 0
    
    def test_chat_session_reuse(self, chat_service, mock_assistant, mock_session):
        """测试重用已有session"""
        chat_service.assistant = mock_assistant
        chat_service.retriever = Mock()
        chat_service.retriever.retrieve.return_value = {
            'document_ids': [],
            'relations': []
        }
        
        mock_assistant.get_session.return_value = mock_session
        mock_session.ask.return_value = [
            Mock(content="测试回答", reference=None)
        ]
        
        with patch.object(chat_service, '_get_or_find_assistant', return_value=mock_assistant):
            list(chat_service.chat("测试问题", session_id="existing_session"))
        
        # 验证使用了已有session
        mock_assistant.get_session.assert_called_once_with("existing_session")
        mock_assistant.create_session.assert_not_called()
    
    def test_chat_session_fallback(self, chat_service, mock_assistant, mock_session):
        """测试session失效时自动创建新session"""
        chat_service.assistant = mock_assistant
        chat_service.retriever = Mock()
        chat_service.retriever.retrieve.return_value = {
            'document_ids': [],
            'relations': []
        }
        
        # 模拟get_session失败
        mock_assistant.get_session.side_effect = Exception("Session not found")
        mock_assistant.create_session.return_value = mock_session
        mock_session.ask.return_value = [
            Mock(content="测试回答", reference=None)
        ]
        
        with patch.object(chat_service, '_get_or_find_assistant', return_value=mock_assistant):
            list(chat_service.chat("测试问题", session_id="invalid_session"))
        
        # 验证尝试获取session失败后创建了新session
        mock_assistant.get_session.assert_called_once()
        mock_assistant.create_session.assert_called_once()
    
    def test_chat_stream_chunks(self, chat_service, mock_assistant, mock_session):
        """测试流式返回chunks"""
        chat_service.assistant = mock_assistant
        chat_service.retriever = Mock()
        chat_service.retriever.retrieve.return_value = {
            'document_ids': [],
            'relations': [],
            'subgraph': None
        }
        
        # 模拟流式返回
        mock_chunks = [
            Mock(content="第一", reference=None),
            Mock(content="部分", reference=None),
            Mock(content="答案", reference=None)
        ]
        mock_assistant.create_session.return_value = mock_session
        mock_session.ask.return_value = mock_chunks
        
        with patch.object(chat_service, '_get_or_find_assistant', return_value=mock_assistant):
            results = list(chat_service.chat("测试问题"))
        
        # 验证返回了chunk类型的结果
        chunk_results = [r for r in results if r['type'] == 'chunk']
        assert len(chunk_results) == 3
        assert chunk_results[0]['content'] == "第一"
        assert chunk_results[1]['content'] == "部分"
        assert chunk_results[2]['content'] == "答案"
    
    def test_chat_with_references(self, chat_service, mock_assistant, mock_session):
        """测试返回参考文档"""
        chat_service.assistant = mock_assistant
        chat_service.retriever = Mock()
        chat_service.retriever.retrieve.return_value = {
            'document_ids': [],
            'relations': []
        }
        
        # 模拟返回参考文档
        mock_ref = Mock(
            content="参考内容",
            document_name="文档.pdf",
            document_id="doc1",
            chunk_id="chunk1",
            similarity=0.9
        )
        mock_chunks = [
            Mock(content="答案", reference=[mock_ref])
        ]
        mock_assistant.create_session.return_value = mock_session
        mock_session.ask.return_value = mock_chunks
        
        with patch.object(chat_service, '_get_or_find_assistant', return_value=mock_assistant):
            results = list(chat_service.chat("测试问题"))
        
        # 验证返回了reference类型的结果
        ref_results = [r for r in results if r['type'] == 'reference']
        assert len(ref_results) == 1
        assert len(ref_results[0]['docs']) == 1
        assert ref_results[0]['docs'][0]['document_name'] == "文档.pdf"
    
    def test_chat_error_handling_value_error(self, chat_service):
        """测试ValueError错误处理（Assistant不存在）"""
        with patch.object(chat_service, '_get_or_find_assistant', side_effect=ValueError("找不到Assistant")):
            results = list(chat_service.chat("测试问题"))
        
        # 验证返回错误信息
        error_results = [r for r in results if r['type'] == 'error']
        assert len(error_results) == 1
        assert "找不到Assistant" in error_results[0]['message']
    
    def test_chat_error_handling_connection_error(self, chat_service, mock_assistant):
        """测试ConnectionError错误处理"""
        chat_service.assistant = mock_assistant
        chat_service.retriever = Mock()
        chat_service.config = Mock()
        chat_service.config.ragflow_base_url = "http://test.com"
        
        with patch.object(chat_service, '_get_or_find_assistant', return_value=mock_assistant):
            chat_service.retriever.retrieve.side_effect = ConnectionError("连接失败")
            results = list(chat_service.chat("测试问题"))
        
        error_results = [r for r in results if r['type'] == 'error']
        assert len(error_results) == 1
        assert "RAGFlow服务" in error_results[0]['message']
    
    def test_clear_session_success(self, chat_service, mock_assistant):
        """测试清除会话成功"""
        chat_service.assistant = mock_assistant
        
        with patch.object(chat_service, '_get_or_find_assistant', return_value=mock_assistant):
            chat_service.clear_session("test_session_id")
        
        mock_assistant.delete_session.assert_called_once_with("test_session_id")
    
    def test_clear_session_failure(self, chat_service, mock_assistant):
        """测试清除会话失败不抛异常"""
        chat_service.assistant = mock_assistant
        mock_assistant.delete_session.side_effect = Exception("删除失败")
        
        with patch.object(chat_service, '_get_or_find_assistant', return_value=mock_assistant):
            # 不应该抛出异常
            chat_service.clear_session("test_session_id")
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        with patch('src.services.chat_service.get_ragflow_client'):
            with patch('src.services.chat_service.get_hybrid_retriever'):
                with patch('src.services.chat_service.get_config'):
                    instance1 = get_chat_service()
                    instance2 = get_chat_service()
                    assert instance1 is instance2


class TestChatServiceFurtherConsiderations:
    """测试Further Considerations中的要求"""
    
    def test_assistant_not_found_shows_detailed_guide(self):
        """测试Assistant不存在时显示详细指导"""
        with patch('src.services.chat_service.get_ragflow_client') as mock_ragflow_getter:
            with patch('src.services.chat_service.get_hybrid_retriever'):
                with patch('src.services.chat_service.get_config') as mock_config_getter:
                    mock_config = Mock()
                    mock_config.ragflow_base_url = "http://localhost:9380"
                    mock_config.default_kb_name = "policy_demo_kb"
                    mock_config_getter.return_value = mock_config
                    
                    mock_ragflow = Mock()
                    mock_ragflow.rag.list_chats.return_value = []
                    mock_ragflow_getter.return_value = mock_ragflow
                    
                    service = ChatService()
                    
                    with pytest.raises(ValueError) as exc_info:
                        service._get_or_find_assistant()
                    
                    error_msg = str(exc_info.value)
                    # 验证包含所有必要指导信息
                    assert "政策聊天助手" in error_msg
                    assert "config/chat_assistant_config.ini" in error_msg
                    assert "http://localhost:9380" in error_msg
                    assert "policy_demo_kb" in error_msg
    
    def test_session_management_in_session_state(self):
        """测试session存储在st.session_state.chat_session_id"""
        # 这个测试通过chat_page.py的代码验证
        # chat_page.py中使用了st.session_state.chat_session_id
        import src.pages.chat_page as chat_page
        import inspect
        
        source = inspect.getsource(chat_page.show)
        assert "st.session_state.chat_session_id" in source
        assert "clear_session" in source
    
    def test_graph_relations_injected_in_question(self):
        """测试图谱关系注入到question中而非System Prompt"""
        with patch('src.services.chat_service.get_ragflow_client'):
            with patch('src.services.chat_service.get_hybrid_retriever'):
                with patch('src.services.chat_service.get_config'):
                    service = ChatService()
                    
                    question = "测试问题"
                    graph_context = {
                        'relations': [
                            {'source': 'A', 'relation': 'R', 'target': 'B'}
                        ]
                    }
                    
                    enhanced = service._build_enhanced_question(question, graph_context)
                    
                    # 验证关系注入到question中
                    assert question in enhanced
                    assert "[知识图谱关系]" in enhanced
                    assert "A → R → B" in enhanced
    
    def test_relations_limit_10_to_20(self):
        """测试关系数量限制为10-20条（实际代码限制为10条）"""
        with patch('src.services.chat_service.get_ragflow_client'):
            with patch('src.services.chat_service.get_hybrid_retriever'):
                with patch('src.services.chat_service.get_config'):
                    service = ChatService()
                    
                    # 测试输入20条关系
                    relations_20 = [
                        {'source': f'A{i}', 'relation': 'R', 'target': f'B{i}'}
                        for i in range(20)
                    ]
                    graph_context_20 = {'relations': relations_20}
                    enhanced_20 = service._build_enhanced_question("问题", graph_context_20)
                    
                    # 代码使用relations[:10]限制为10条
                    # 每条关系格式为：source → relation → target，所以有20个→
                    relation_count = enhanced_20.count('→')
                    assert relation_count == 20, f"Expected 20 arrows (10 relations * 2), got {relation_count}"
