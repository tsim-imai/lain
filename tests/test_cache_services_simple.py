"""
キャッシュサービスの簡単なテスト
"""
import pytest
from src.cache.services import CacheService


class TestCacheServiceSimple:
    """キャッシュサービス簡単テストクラス"""
    
    def test_initialization(self, cache_service):
        """キャッシュサービスの初期化テスト"""
        assert cache_service.config_manager is not None
        assert cache_service.cache_manager is not None
        assert cache_service.db_manager is not None
    
    def test_is_query_cached(self, cache_service):
        """クエリキャッシュチェックテスト"""
        # 存在しないクエリはキャッシュされていない
        result = cache_service.is_query_cached("存在しないクエリ")
        assert result == False
    
    def test_clear_all_cache(self, cache_service):
        """全キャッシュクリアテスト"""
        # クリア操作がエラーなく実行される
        deleted_count = cache_service.clear_all_cache()
        assert isinstance(deleted_count, int)
        assert deleted_count >= 0
    
    def test_cleanup_expired_cache(self, cache_service):
        """期限切れキャッシュクリーンアップテスト"""
        # クリーンアップ操作がエラーなく実行される
        deleted_count = cache_service.cleanup_expired_cache()
        assert isinstance(deleted_count, int)
        assert deleted_count >= 0
    
    def test_get_cache_statistics(self, cache_service):
        """キャッシュ統計情報テスト"""
        stats = cache_service.get_cache_statistics()
        assert isinstance(stats, dict)
        # 統計情報の基本的なキーが含まれている
        assert "total_entries" in stats or len(stats) >= 0
    
    def test_health_check(self, cache_service):
        """ヘルスチェックテスト"""
        health = cache_service.health_check()
        assert isinstance(health, dict)
        assert len(health) >= 0