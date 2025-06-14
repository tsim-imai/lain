"""
チャット機能のテスト
"""
import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from src.cache.chat_manager import ChatHistoryManager
from src.cli.app import LainApp
from src.utils.config import ConfigManager


class TestChatHistoryManager:
    """チャット履歴管理のテスト"""
    
    @pytest.fixture
    def temp_config(self):
        """テスト用の一時設定"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # テスト用データベースパス
            db_path = os.path.join(temp_dir, "test_chat.db")
            
            # モック設定マネージャー
            mock_config = Mock(spec=ConfigManager)
            mock_config.get_scraper_config.return_value = {
                "cache": {
                    "database_path": db_path,
                    "ttl_hours": 24
                }
            }
            
            yield mock_config
    
    def test_chat_manager_initialization(self, temp_config):
        """チャット履歴マネージャーの初期化テスト"""
        chat_manager = ChatHistoryManager(temp_config)
        assert chat_manager is not None
        assert chat_manager.config_manager == temp_config
    
    def test_create_session(self, temp_config):
        """セッション作成テスト"""
        chat_manager = ChatHistoryManager(temp_config)
        session_id = chat_manager.create_session()
        
        assert session_id is not None
        assert isinstance(session_id, str)
        assert len(session_id) > 0
    
    def test_save_and_get_chat_entry(self, temp_config):
        """チャットエントリの保存・取得テスト"""
        chat_manager = ChatHistoryManager(temp_config)
        session_id = chat_manager.create_session()
        
        # チャットエントリを保存
        user_query = "テストクエリ"
        llm_response = "テスト回答"
        
        chat_manager.save_chat_entry(
            session_id=session_id,
            user_query=user_query,
            llm_response=llm_response,
            search_performed=False
        )
        
        # 履歴を取得
        history = chat_manager.get_session_history(session_id, 10)
        
        assert len(history) == 1
        assert history[0]["user_query"] == user_query
        assert history[0]["llm_response"] == llm_response
        assert history[0]["search_performed"] == False
    
    def test_save_chat_entry_with_search(self, temp_config):
        """検索付きチャットエントリの保存テスト"""
        chat_manager = ChatHistoryManager(temp_config)
        session_id = chat_manager.create_session()
        
        # 検索付きチャットエントリを保存
        user_query = "検索クエリ"
        llm_response = "検索回答"
        search_query = "検索キーワード"
        
        chat_manager.save_chat_entry(
            session_id=session_id,
            user_query=user_query,
            llm_response=llm_response,
            search_performed=True,
            search_query=search_query
        )
        
        # 履歴を取得
        history = chat_manager.get_session_history(session_id, 10)
        
        assert len(history) == 1
        assert history[0]["search_performed"] == True
        assert history[0]["search_query"] == search_query
    
    def test_format_history_for_llm(self, temp_config):
        """LLM用履歴フォーマットテスト"""
        chat_manager = ChatHistoryManager(temp_config)
        session_id = chat_manager.create_session()
        
        # 複数のエントリを保存
        entries = [
            ("質問1", "回答1"),
            ("質問2", "回答2"),
        ]
        
        for user_query, llm_response in entries:
            chat_manager.save_chat_entry(
                session_id=session_id,
                user_query=user_query,
                llm_response=llm_response,
                search_performed=False
            )
        
        # フォーマット済み履歴を取得
        formatted_history = chat_manager.format_history_for_llm(session_id, 10)
        
        assert "ユーザー: 質問1" in formatted_history
        assert "AI: 回答1" in formatted_history
        assert "ユーザー: 質問2" in formatted_history
        assert "AI: 回答2" in formatted_history
    
    def test_clear_session_history(self, temp_config):
        """セッション履歴削除テスト"""
        chat_manager = ChatHistoryManager(temp_config)
        session_id = chat_manager.create_session()
        
        # エントリを保存
        chat_manager.save_chat_entry(
            session_id=session_id,
            user_query="テスト",
            llm_response="回答",
            search_performed=False
        )
        
        # 履歴があることを確認
        history = chat_manager.get_session_history(session_id, 10)
        assert len(history) == 1
        
        # 履歴を削除
        deleted_count = chat_manager.clear_session_history(session_id)
        assert deleted_count == 1
        
        # 履歴が空になったことを確認
        history = chat_manager.get_session_history(session_id, 10)
        assert len(history) == 0
    
    def test_get_chat_statistics(self, temp_config):
        """チャット統計テスト"""
        chat_manager = ChatHistoryManager(temp_config)
        session_id = chat_manager.create_session()
        
        # 複数のエントリを保存
        chat_manager.save_chat_entry(session_id, "質問1", "回答1", False)
        chat_manager.save_chat_entry(session_id, "質問2", "回答2", True, "検索クエリ")
        
        # 統計を取得
        stats = chat_manager.get_chat_statistics()
        
        assert stats["total_messages"] == 2
        assert stats["total_sessions"] == 1
        assert stats["search_performed_count"] == 1
        assert stats["average_messages_per_session"] == 2.0


class TestLainAppChat:
    """LainAppのチャット機能テスト"""
    
    @pytest.fixture
    def mock_app(self):
        """モックLainAppインスタンス"""
        with patch('src.cli.app.LLMService'), \
             patch('src.cli.app.ScraperService'), \
             patch('src.cli.app.CacheService'), \
             patch('src.cli.app.ChatHistoryManager') as mock_chat_manager:
            
            mock_config = Mock(spec=ConfigManager)
            app = LainApp(mock_config, enable_color=False)
            
            # チャットマネージャーのモック設定
            mock_chat_manager_instance = Mock()
            app.chat_manager = mock_chat_manager_instance
            
            yield app, mock_chat_manager_instance
    
    def test_start_chat_session(self, mock_app):
        """チャットセッション開始テスト"""
        app, mock_chat_manager = mock_app
        
        # モックの戻り値を設定
        expected_session_id = "test-session-123"
        mock_chat_manager.create_session.return_value = expected_session_id
        
        # セッション開始
        session_id = app.start_chat_session()
        
        assert session_id == expected_session_id
        mock_chat_manager.create_session.assert_called_once()
    
    def test_get_chat_history(self, mock_app):
        """チャット履歴取得テスト"""
        app, mock_chat_manager = mock_app
        
        # モックの戻り値を設定
        expected_history = [
            {"user_query": "テスト", "llm_response": "回答"}
        ]
        mock_chat_manager.get_session_history.return_value = expected_history
        
        # 履歴取得
        session_id = "test-session"
        history = app.get_chat_history(session_id, 10)
        
        assert history == expected_history
        mock_chat_manager.get_session_history.assert_called_once_with(session_id, 10)
    
    def test_clear_chat_session(self, mock_app):
        """チャットセッションクリアテスト"""
        app, mock_chat_manager = mock_app
        
        # モックの戻り値を設定
        mock_chat_manager.clear_session_history.return_value = 5
        
        # セッションクリア
        session_id = "test-session"
        deleted_count = app.clear_chat_session(session_id)
        
        assert deleted_count == 5
        mock_chat_manager.clear_session_history.assert_called_once_with(session_id)
    
    @patch('src.cli.app.time.time')
    def test_process_chat_query_direct_answer(self, mock_time, mock_app):
        """チャットクエリ処理（直接回答）テスト"""
        app, mock_chat_manager = mock_app
        
        # 時間のモック
        mock_time.return_value = 1000.0
        
        # サービスのモック設定
        app.llm_service.should_search.return_value = False
        app.llm_service.direct_answer.return_value = "直接回答"
        mock_chat_manager.format_history_for_llm.return_value = "履歴"
        
        # チャットクエリ処理
        result = app.process_chat_query(
            query="テストクエリ",
            session_id="test-session",
            show_progress=False
        )
        
        # 結果の検証
        assert result["query"] == "テストクエリ"
        assert result["session_id"] == "test-session"
        assert result["search_performed"] == False
        assert result["response"] == "直接回答"
        assert result["history_used"] == True
        
        # サービスメソッドの呼び出し確認
        app.llm_service.should_search.assert_called_once_with("テストクエリ")
        app.llm_service.direct_answer.assert_called_once_with("テストクエリ", "履歴")
        mock_chat_manager.save_chat_entry.assert_called_once()


class TestChatIntegration:
    """チャット機能の統合テスト"""
    
    def test_chat_functionality_methods_exist(self):
        """チャット機能のメソッドが存在することを確認"""
        # テスト用の最小限の設定
        mock_config = Mock(spec=ConfigManager)
        
        with patch('src.cli.app.LLMService'), \
             patch('src.cli.app.ScraperService'), \
             patch('src.cli.app.CacheService'), \
             patch('src.cli.app.ChatHistoryManager'):
            
            app = LainApp(mock_config, enable_color=False)
            
            # チャット関連メソッドの存在確認
            assert hasattr(app, 'process_chat_query')
            assert hasattr(app, 'start_chat_session')
            assert hasattr(app, 'get_chat_history')
            assert hasattr(app, 'clear_chat_session')
            assert hasattr(app, 'get_recent_chat_sessions')
            
            # メソッドが呼び出し可能であることを確認
            assert callable(app.process_chat_query)
            assert callable(app.start_chat_session)
            assert callable(app.get_chat_history)
            assert callable(app.clear_chat_session)
            assert callable(app.get_recent_chat_sessions)