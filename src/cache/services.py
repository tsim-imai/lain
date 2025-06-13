"""
キャッシュサービス層 - キャッシュ機能の統合管理
"""
import logging
from typing import Optional, List, Dict, Any
from .cache_manager import CacheManager
from .database import DatabaseManager
from ..utils.config import ConfigManager
from ..utils.exceptions import CacheError

logger = logging.getLogger(__name__)


class CacheService:
    """キャッシュサービスクラス - キャッシュ機能の統合管理"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
        """
        self.config_manager = config_manager
        self.cache_manager = CacheManager(config_manager)
        self.db_manager = DatabaseManager(config_manager)
        
        # 起動時に期限切れキャッシュをクリーンアップ
        self._startup_cleanup()
        
        logger.info("キャッシュサービスを初期化")
    
    def _startup_cleanup(self) -> None:
        """
        起動時のクリーンアップ処理
        """
        try:
            deleted_count = self.cache_manager.cleanup_expired_cache()
            if deleted_count > 0:
                logger.info(f"起動時クリーンアップ: {deleted_count}件の期限切れキャッシュを削除")
        except Exception as e:
            logger.warning(f"起動時クリーンアップエラー: {str(e)}")
    
    def get_or_cache_results(
        self,
        query: str,
        search_function: callable,
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        キャッシュから結果を取得、または検索を実行してキャッシュに保存
        
        Args:
            query: 検索クエリ
            search_function: 検索実行関数
            force_refresh: 強制的にキャッシュを無視して検索
            
        Returns:
            検索結果
        """
        try:
            # 強制更新でない場合、キャッシュをチェック
            if not force_refresh:
                cached_results = self.cache_manager.get_cached_results(query)
                if cached_results is not None:
                    logger.info(f"キャッシュから結果取得: '{query}'")
                    return cached_results
            
            # キャッシュがない場合、検索を実行
            logger.info(f"新規検索実行: '{query}'")
            search_results = search_function(query)
            
            # 結果をキャッシュに保存
            if search_results:
                self.cache_manager.cache_results(query, search_results)
            
            return search_results
            
        except Exception as e:
            logger.error(f"キャッシュサービスエラー: {str(e)}")
            # エラー時は検索関数を直接実行
            try:
                return search_function(query)
            except Exception as search_error:
                logger.error(f"検索実行エラー: {str(search_error)}")
                raise CacheError(f"検索とキャッシュの両方に失敗しました: {str(e)}")
    
    def invalidate_query_cache(self, query: str) -> bool:
        """
        特定クエリのキャッシュを無効化
        
        Args:
            query: 検索クエリ
            
        Returns:
            無効化成功時True
        """
        return self.cache_manager.invalidate_cache(query)
    
    def clear_all_cache(self) -> int:
        """
        全キャッシュを削除
        
        Returns:
            削除されたレコード数
        """
        return self.cache_manager.clear_all_cache()
    
    def cleanup_expired_cache(self) -> int:
        """
        期限切れキャッシュをクリーンアップ
        
        Returns:
            削除されたレコード数
        """
        return self.cache_manager.cleanup_expired_cache()
    
    def is_query_cached(self, query: str) -> bool:
        """
        クエリがキャッシュされているかチェック
        
        Args:
            query: 検索クエリ
            
        Returns:
            キャッシュされている場合True
        """
        return self.cache_manager.is_cached(query)
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        キャッシュ統計情報を取得
        
        Returns:
            統計情報辞書
        """
        return self.cache_manager.get_cache_stats()
    
    def get_recent_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        最近のクエリ一覧を取得
        
        Args:
            limit: 取得件数上限
            
        Returns:
            最近のクエリ情報のリスト
        """
        return self.cache_manager.get_recent_queries(limit)
    
    def optimize_cache(self) -> None:
        """
        キャッシュを最適化
        """
        try:
            # 期限切れキャッシュをクリーンアップ
            deleted_count = self.cleanup_expired_cache()
            
            # データベースを最適化
            self.db_manager.vacuum_database()
            
            logger.info(f"キャッシュ最適化完了: {deleted_count}件削除")
            
        except Exception as e:
            logger.error(f"キャッシュ最適化エラー: {str(e)}")
            raise CacheError(f"キャッシュ最適化に失敗しました: {str(e)}")
    
    def backup_cache(self, backup_path: str) -> None:
        """
        キャッシュデータベースをバックアップ
        
        Args:
            backup_path: バックアップファイルパス
        """
        try:
            self.db_manager.backup_database(backup_path)
            logger.info(f"キャッシュバックアップ完了: {backup_path}")
        except Exception as e:
            logger.error(f"キャッシュバックアップエラー: {str(e)}")
            raise CacheError(f"キャッシュバックアップに失敗しました: {str(e)}")
    
    def health_check(self) -> Dict[str, Any]:
        """
        キャッシュシステムのヘルスチェック
        
        Returns:
            ヘルスチェック結果
        """
        try:
            # データベース統計を取得
            stats = self.get_cache_statistics()
            
            # 基本的なヘルスチェック
            health_status = {
                "status": "healthy",
                "database_accessible": True,
                "cache_functional": True,
                "stats": stats
            }
            
            # データベースアクセステスト
            try:
                test_query = "health_check_test"
                self.cache_manager.is_cached(test_query)
            except Exception as e:
                health_status["database_accessible"] = False
                health_status["status"] = "unhealthy"
                health_status["database_error"] = str(e)
            
            return health_status
            
        except Exception as e:
            logger.error(f"ヘルスチェックエラー: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "database_accessible": False,
                "cache_functional": False
            }