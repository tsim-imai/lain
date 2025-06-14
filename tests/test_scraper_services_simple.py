"""
スクレイパーサービスの簡単なテスト
"""
import pytest
from unittest.mock import Mock, patch
from src.scraper.services import ScraperService


class TestScraperServiceSimple:
    """スクレイパーサービス簡単テストクラス"""
    
    def test_initialization(self, config_manager):
        """スクレイパーサービスの初期化テスト"""
        service = ScraperService(config_manager)
        
        assert service.config_manager == config_manager
        assert service.scraper_config is not None
        assert service.primary_engine == "duckduckgo"
        assert service.fallback_engine == "brave"
        assert service.duckduckgo_scraper is not None
        assert service.brave_scraper is not None
    
    def test_search_with_engine_duckduckgo(self, scraper_service):
        """DuckDuckGo検索エンジンテスト"""
        with patch.object(scraper_service.duckduckgo_scraper, 'search') as mock_search:
            mock_search.return_value = [{"title": "test", "url": "https://example.com", "snippet": "test snippet"}]
            
            results = scraper_service._search_with_engine("duckduckgo", "クエリ", 5)
            
            mock_search.assert_called_once_with("クエリ", 5)
            assert len(results) == 1
            assert results[0]["title"] == "test"
    
    def test_search_with_engine_brave(self, scraper_service):
        """Brave検索エンジンテスト"""
        with patch.object(scraper_service.brave_scraper, 'search') as mock_search:
            mock_search.return_value = [{"title": "brave test", "url": "https://brave.com", "snippet": "brave snippet"}]
            
            results = scraper_service._search_with_engine("brave", "クエリ", 5)
            
            mock_search.assert_called_once_with("クエリ", 5)
            assert len(results) == 1
            assert results[0]["title"] == "brave test"
    
    def test_search_with_engine_unknown(self, scraper_service):
        """未知の検索エンジンテスト"""
        results = scraper_service._search_with_engine("unknown_engine", "クエリ", 5)
        assert results == []
    
    def test_clean_search_results_basic(self, scraper_service):
        """基本的な検索結果クリーンアップテスト"""
        raw_results = [
            {
                "title": "正常なタイトル",
                "url": "https://example.com",
                "snippet": "正常なスニペット",
                "source": "duckduckgo"
            },
            {
                "title": "",  # 空のタイトル（除外されるべき）
                "url": "https://empty.com",
                "snippet": "スニペットあり",
                "source": "duckduckgo"
            }
        ]
        
        cleaned = scraper_service._clean_search_results(raw_results)
        
        # 有効な結果のみが残ることを確認
        assert len(cleaned) == 1
        assert cleaned[0]["title"] == "正常なタイトル"
        assert cleaned[0]["snippet"] == "正常なスニペット"
    
    def test_remove_duplicates(self, scraper_service):
        """重複除去テスト"""
        results_with_duplicates = [
            {"title": "タイトル1", "url": "https://example.com", "snippet": "スニペット1"},
            {"title": "タイトル2", "url": "https://different.com", "snippet": "スニペット2"},
            {"title": "タイトル3", "url": "https://example.com", "snippet": "スニペット3"},  # 重複URL
        ]
        
        unique_results = scraper_service._remove_duplicates(results_with_duplicates)
        
        # 重複が除去されることを確認
        assert len(unique_results) == 2
        urls = [r["url"] for r in unique_results]
        assert "https://example.com" in urls
        assert "https://different.com" in urls
    
    def test_get_scraper_stats(self, scraper_service):
        """スクレイパー統計情報テスト"""
        stats = scraper_service.get_scraper_stats()
        
        assert "available_scrapers" in stats
        assert "duckduckgo" in stats["available_scrapers"]
        assert "brave" in stats["available_scrapers"]
        assert stats["primary_engine"] == "duckduckgo"
        assert stats["fallback_engine"] == "brave"
        assert "rate_limit" in stats
        assert stats["max_results"] == 10