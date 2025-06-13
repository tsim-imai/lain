"""
キャッシュ管理
"""
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from .database import DatabaseManager
from ..utils.config import ConfigManager
from ..utils.exceptions import CacheError

logger = logging.getLogger(__name__)


class CacheManager:
    """キャッシュ管理クラス"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
        """
        self.config_manager = config_manager
        self.db_manager = DatabaseManager(config_manager)
        self.scraper_config = config_manager.get_scraper_config()
        self.cache_config = self.scraper_config["cache"]
        
        logger.info("キャッシュ管理を初期化")
    
    def get_cached_results(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """
        キャッシュされた検索結果を取得
        
        Args:
            query: 検索クエリ
            
        Returns:
            キャッシュされた結果（見つからない場合はNone）
        """
        try:
            query_hash = self._generate_query_hash(query)
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                current_time = datetime.now().isoformat()
                
                cursor.execute('''
                    SELECT results FROM search_cache 
                    WHERE query_hash = ? AND expires_at > ?
                ''', (query_hash, current_time))
                
                result = cursor.fetchone()
                
                if result:
                    cached_results = json.loads(result['results'])
                    logger.info(f"キャッシュヒット: '{query}' -> {len(cached_results)}件")
                    return cached_results
                else:
                    logger.debug(f"キャッシュミス: '{query}'")
                    return None
                    
        except Exception as e:
            logger.error(f"キャッシュ取得エラー: {str(e)}")
            return None
    
    def cache_results(self, query: str, results: List[Dict[str, Any]]) -> None:
        """
        検索結果をキャッシュに保存
        
        Args:
            query: 検索クエリ
            results: 検索結果
        """
        try:
            query_hash = self._generate_query_hash(query)
            current_time = datetime.now()
            
            # TTLを計算
            ttl_hours = self.cache_config["ttl_hours"]
            expires_at = current_time + timedelta(hours=ttl_hours)
            
            results_json = json.dumps(results, ensure_ascii=False)
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # 既存のキャッシュを更新または新規作成
                cursor.execute('''
                    INSERT OR REPLACE INTO search_cache 
                    (query_hash, original_query, results, created_at, expires_at, result_count)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    query_hash,
                    query,
                    results_json,
                    current_time.isoformat(),
                    expires_at.isoformat(),
                    len(results)
                ))
                
                conn.commit()
                
            logger.info(f"キャッシュ保存: '{query}' -> {len(results)}件 (TTL: {ttl_hours}時間)")
            
        except Exception as e:
            logger.error(f"キャッシュ保存エラー: {str(e)}")
            raise CacheError(f"キャッシュ保存に失敗しました: {str(e)}")
    
    def _generate_query_hash(self, query: str) -> str:
        """
        クエリのハッシュ値を生成
        
        Args:
            query: 検索クエリ
            
        Returns:
            ハッシュ値（16進数文字列）
        """
        # クエリを正規化（小文字、空白除去）
        normalized_query = query.lower().strip()
        
        # SHA256ハッシュを生成
        hash_obj = hashlib.sha256(normalized_query.encode('utf-8'))
        return hash_obj.hexdigest()
    
    def is_cached(self, query: str) -> bool:
        """
        クエリがキャッシュされているかチェック
        
        Args:
            query: 検索クエリ
            
        Returns:
            キャッシュされている場合True
        """
        return self.get_cached_results(query) is not None
    
    def invalidate_cache(self, query: str) -> bool:
        """
        特定クエリのキャッシュを無効化
        
        Args:
            query: 検索クエリ
            
        Returns:
            削除成功時True
        """
        try:
            query_hash = self._generate_query_hash(query)
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    DELETE FROM search_cache WHERE query_hash = ?
                ''', (query_hash,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
            if deleted_count > 0:
                logger.info(f"キャッシュ無効化: '{query}'")
                return True
            else:
                logger.debug(f"キャッシュ無効化対象なし: '{query}'")
                return False
                
        except Exception as e:
            logger.error(f"キャッシュ無効化エラー: {str(e)}")
            return False
    
    def clear_all_cache(self) -> int:
        """
        全キャッシュを削除
        
        Returns:
            削除されたレコード数
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM search_cache')
                deleted_count = cursor.rowcount
                conn.commit()
                
            logger.info(f"全キャッシュクリア: {deleted_count}件削除")
            return deleted_count
            
        except Exception as e:
            logger.error(f"キャッシュクリアエラー: {str(e)}")
            raise CacheError(f"キャッシュクリアに失敗しました: {str(e)}")
    
    def cleanup_expired_cache(self) -> int:
        """
        期限切れキャッシュをクリーンアップ
        
        Returns:
            削除されたレコード数
        """
        return self.db_manager.cleanup_expired_cache()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        キャッシュ統計情報を取得
        
        Returns:
            統計情報辞書
        """
        try:
            db_stats = self.db_manager.get_database_stats()
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # 最近のキャッシュアクティビティ
                cursor.execute('''
                    SELECT COUNT(*) FROM search_cache 
                    WHERE created_at > ?
                ''', ((datetime.now() - timedelta(hours=24)).isoformat(),))
                recent_cache_count = cursor.fetchone()[0]
                
                # 平均結果数
                cursor.execute('''
                    SELECT AVG(result_count) FROM search_cache 
                    WHERE expires_at > ?
                ''', (datetime.now().isoformat(),))
                avg_result_count = cursor.fetchone()[0] or 0
            
            cache_stats = {
                "ttl_hours": self.cache_config["ttl_hours"],
                "max_results": self.cache_config["max_results"],
                "recent_cache_entries_24h": recent_cache_count,
                "average_result_count": round(avg_result_count, 1)
            }
            
            # データベース統計と結合
            cache_stats.update(db_stats)
            
            return cache_stats
            
        except Exception as e:
            logger.error(f"キャッシュ統計取得エラー: {str(e)}")
            return {"error": str(e)}
    
    def get_recent_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        最近のクエリ一覧を取得
        
        Args:
            limit: 取得件数上限
            
        Returns:
            最近のクエリ情報のリスト
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT original_query, created_at, result_count, expires_at
                    FROM search_cache 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (limit,))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        "query": row['original_query'],
                        "created_at": row['created_at'],
                        "result_count": row['result_count'],
                        "expires_at": row['expires_at'],
                        "is_expired": row['expires_at'] < datetime.now().isoformat()
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"最近のクエリ取得エラー: {str(e)}")
            return []