"""
ストリーミング機能のテスト
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.llm.client import LLMClient
from src.llm.services import LLMService
from src.cli.app import LainApp
from src.utils.config import ConfigManager


class TestLLMClientStreaming:
    """LLMクライアントのストリーミング機能テスト"""
    
    @pytest.fixture
    def mock_config(self):
        """モック設定マネージャー"""
        mock_config = Mock(spec=ConfigManager)
        mock_config.get_llm_config.return_value = {
            "lm_studio": {
                "base_url": "http://localhost:1234/v1",
                "api_key": "test-key",
                "model_name": "test-model",
                "max_tokens": 1000,
                "temperature": 0.7
            }
        }
        return mock_config
    
    @patch('src.llm.client.OpenAI')
    def test_generate_response_stream(self, mock_openai_class, mock_config):
        """ストリーミング応答生成テスト"""
        # モッククライアントの設定
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # ストリーミングレスポンスのモック
        mock_chunks = [
            Mock(choices=[Mock(delta=Mock(content="こんに"))]),
            Mock(choices=[Mock(delta=Mock(content="ちは"))]),
            Mock(choices=[Mock(delta=Mock(content="！"))]),
        ]
        mock_client.chat.completions.create.return_value = iter(mock_chunks)
        
        # LLMクライアント初期化
        llm_client = LLMClient(mock_config)
        
        # ストリーミング応答のテスト
        chunks = []
        for chunk in llm_client.generate_response_stream("テストプロンプト"):
            chunks.append(chunk)
        
        assert chunks == ["こんに", "ちは", "！"]
        
        # APIが正しいパラメータで呼ばれたことを確認
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args[1]
        assert call_args["stream"] == True
        assert call_args["model"] == "test-model"
        assert call_args["messages"][0]["content"] == "テストプロンプト"
    
    @patch('src.llm.client.OpenAI')
    def test_generate_response_stream_complete(self, mock_openai_class, mock_config):
        """ストリーミング完全応答テスト"""
        # モッククライアントの設定
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # ストリーミングレスポンスのモック
        mock_chunks = [
            Mock(choices=[Mock(delta=Mock(content="Hello"))]),
            Mock(choices=[Mock(delta=Mock(content=" "))]),
            Mock(choices=[Mock(delta=Mock(content="World"))]),
        ]
        mock_client.chat.completions.create.return_value = iter(mock_chunks)
        
        # LLMクライアント初期化
        llm_client = LLMClient(mock_config)
        
        # 完全応答のテスト
        response = llm_client.generate_response_stream_complete("テストプロンプト")
        
        assert response == "Hello World"
    
    @patch('src.llm.client.OpenAI')
    def test_generate_response_stream_with_callback(self, mock_openai_class, mock_config):
        """コールバック付きストリーミングテスト"""
        # モッククライアントの設定
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # ストリーミングレスポンスのモック
        mock_chunks = [
            Mock(choices=[Mock(delta=Mock(content="テスト"))]),
            Mock(choices=[Mock(delta=Mock(content="応答"))]),
        ]
        mock_client.chat.completions.create.return_value = iter(mock_chunks)
        
        # LLMクライアント初期化
        llm_client = LLMClient(mock_config)
        
        # コールバック関数のモック
        callback_mock = Mock()
        
        # ストリーミング応答のテスト
        chunks = list(llm_client.generate_response_stream(
            "テストプロンプト", 
            callback=callback_mock
        ))
        
        assert chunks == ["テスト", "応答"]
        
        # コールバックが正しく呼ばれたことを確認
        assert callback_mock.call_count == 2
        callback_mock.assert_any_call("テスト")
        callback_mock.assert_any_call("応答")


class TestLLMServiceStreaming:
    """LLMサービスのストリーミング機能テスト"""
    
    @pytest.fixture
    def mock_llm_service(self):
        """モックLLMサービス"""
        with patch('src.llm.services.LLMClient') as mock_client_class, \
             patch('src.llm.services.PromptManager') as mock_prompt_class:
            
            mock_config = Mock(spec=ConfigManager)
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            llm_service = LLMService(mock_config)
            llm_service.client = mock_client
            
            yield llm_service, mock_client
    
    def test_direct_answer_stream(self, mock_llm_service):
        """ストリーミング直接回答テスト"""
        llm_service, mock_client = mock_llm_service
        
        # モックストリーミングレスポンス
        mock_client.generate_response_stream.return_value = iter(["こんに", "ちは"])
        
        # ストリーミング直接回答のテスト
        chunks = list(llm_service.direct_answer_stream("こんにちは"))
        
        assert chunks == ["こんに", "ちは"]
        mock_client.generate_response_stream.assert_called_once()
    
    def test_direct_answer_stream_with_history(self, mock_llm_service):
        """履歴付きストリーミング直接回答テスト"""
        llm_service, mock_client = mock_llm_service
        
        # モックストリーミングレスポンス
        mock_client.generate_response_stream.return_value = iter(["履歴を", "考慮した", "回答"])
        
        # 履歴付きストリーミング直接回答のテスト
        history = "ユーザー: 前の質問\nAI: 前の回答"
        chunks = list(llm_service.direct_answer_stream("新しい質問", history))
        
        assert chunks == ["履歴を", "考慮した", "回答"]
        
        # 履歴がプロンプトに含まれていることを確認
        call_args = mock_client.generate_response_stream.call_args[0]
        assert "過去の会話履歴" in call_args[0]
        assert "前の質問" in call_args[0]
    
    def test_summarize_results_stream(self, mock_llm_service):
        """ストリーミング検索結果要約テスト"""
        llm_service, mock_client = mock_llm_service
        
        # _format_search_resultsメソッドのモック
        llm_service._format_search_results = Mock(return_value="フォーマット済み検索結果")
        
        # モックストリーミングレスポンス
        mock_client.generate_response_stream.return_value = iter(["検索結果", "の要約"])
        
        # 検索結果のモック
        search_results = [
            {"title": "テスト1", "snippet": "内容1"},
            {"title": "テスト2", "snippet": "内容2"}
        ]
        
        # ストリーミング要約のテスト
        chunks = list(llm_service.summarize_results_stream("質問", search_results))
        
        assert chunks == ["検索結果", "の要約"]
        mock_client.generate_response_stream.assert_called_once()
        llm_service._format_search_results.assert_called_once_with(search_results)
    
    def test_stream_complete_methods(self, mock_llm_service):
        """ストリーミング完了メソッドテスト"""
        llm_service, mock_client = mock_llm_service
        
        # モックストリーミングレスポンス
        mock_client.generate_response_stream.return_value = iter(["完全な", "応答"])
        
        # direct_answer_stream_completeのテスト
        complete_response = llm_service.direct_answer_stream_complete("質問")
        assert complete_response == "完全な応答"
        
        # summarize_results_stream_completeのテスト
        llm_service._format_search_results = Mock(return_value="検索結果")
        search_results = [{"title": "テスト"}]
        
        mock_client.generate_response_stream.return_value = iter(["要約", "完了"])
        complete_summary = llm_service.summarize_results_stream_complete("質問", search_results)
        assert complete_summary == "要約完了"


class TestLainAppStreaming:
    """LainAppのストリーミング機能テスト"""
    
    def test_streaming_method_exists(self):
        """ストリーミングメソッドの存在確認のみ"""
        mock_config = Mock(spec=ConfigManager)
        
        with patch('src.cli.app.LLMService'), \
             patch('src.cli.app.ScraperService'), \
             patch('src.cli.app.CacheService'), \
             patch('src.cli.app.ChatHistoryManager'):
            
            app = LainApp(mock_config, enable_color=False)
            
            # ストリーミングメソッドが存在することを確認
            assert hasattr(app, 'process_chat_query_stream')
            assert callable(app.process_chat_query_stream)


class TestStreamingIntegration:
    """ストリーミング機能の統合テスト"""
    
    def test_streaming_methods_exist(self):
        """ストリーミングメソッドの存在確認"""
        # テスト用の設定
        mock_config = Mock(spec=ConfigManager)
        mock_config.get_llm_config.return_value = {
            "lm_studio": {
                "base_url": "http://localhost:1234/v1",
                "api_key": "test-key",
                "model_name": "test-model",
                "max_tokens": 1000,
                "temperature": 0.7
            },
            "prompts": {}  # プロンプト設定も追加
        }
        
        with patch('src.llm.client.OpenAI'):
            
            # LLMクライアントのストリーミングメソッド確認
            llm_client = LLMClient(mock_config)
            assert hasattr(llm_client, 'generate_response_stream')
            assert hasattr(llm_client, 'generate_response_stream_complete')
            assert callable(llm_client.generate_response_stream)
            assert callable(llm_client.generate_response_stream_complete)