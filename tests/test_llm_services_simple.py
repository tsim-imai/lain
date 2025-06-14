"""
LLMサービスの簡単なテスト
"""
import pytest
from unittest.mock import Mock, patch
from src.llm.services import LLMService


class TestLLMServiceSimple:
    """LLMサービス簡単テストクラス"""
    
    def test_initialization(self, config_manager):
        """LLMサービスの初期化テスト"""
        service = LLMService(config_manager)
        assert service.config_manager == config_manager
        assert service.client is not None
        assert service.prompt_manager is not None
    
    @patch('src.llm.services.LLMClient')
    def test_should_search_with_mock(self, mock_client_class, config_manager):
        """検索判断のモックテスト"""
        # LLMClientのモック設定
        mock_client = Mock()
        mock_client.generate_response.return_value = "YES"
        mock_client_class.return_value = mock_client
        
        service = LLMService(config_manager)
        service.client = mock_client
        
        result = service.should_search("岸田文雄の誕生日は？")
        
        # LLMが呼ばれることを確認
        mock_client.generate_response.assert_called_once()
        assert result == True
    
    @patch('src.llm.services.LLMClient')
    def test_generate_search_query_with_mock(self, mock_client_class, config_manager):
        """検索クエリ生成のモックテスト"""
        # LLMClientのモック設定
        mock_client = Mock()
        mock_client.generate_response.return_value = "岸田文雄 誕生日"
        mock_client_class.return_value = mock_client
        
        service = LLMService(config_manager)
        service.client = mock_client
        
        result = service.generate_search_query("岸田文雄の誕生日は？")
        
        # LLMが呼ばれることを確認
        mock_client.generate_response.assert_called_once()
        assert result == "岸田文雄 誕生日"
    
    @patch('src.llm.services.LLMClient')
    def test_direct_answer_with_mock(self, mock_client_class, config_manager):
        """直接回答のモックテスト"""
        # LLMClientのモック設定
        mock_client = Mock()
        mock_client.generate_response.return_value = "こんにちは！"
        mock_client_class.return_value = mock_client
        
        service = LLMService(config_manager)
        service.client = mock_client
        
        result = service.direct_answer("こんにちは")
        
        # LLMが呼ばれることを確認
        mock_client.generate_response.assert_called_once()
        assert result == "こんにちは！"
    
