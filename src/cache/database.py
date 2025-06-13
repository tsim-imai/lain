"""
SQLiteデータベース管理
"""
import sqlite3
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from ..utils.config import ConfigManager
from ..utils.exceptions import CacheError

logger = logging.getLogger(__name__)


class DatabaseManager:
    """SQLiteデータベース管理クラス"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
        """
        self.config_manager = config_manager
        self.scraper_config = config_manager.get_scraper_config()
        
        # データベースパスを設定
        db_path = self.scraper_config["cache"]["database_path"]
        self.db_path = Path(db_path)
        
        # データディレクトリを作成
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # データベースを初期化
        self._initialize_database()
        
        logger.info(f"データベース管理を初期化: {self.db_path}")
    
    def _initialize_database(self) -> None:
        """
        データベースを初期化してテーブルを作成
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 検索キャッシュテーブル
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS search_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query_hash TEXT UNIQUE NOT NULL,
                        original_query TEXT NOT NULL,
                        results TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        expires_at TEXT NOT NULL,
                        result_count INTEGER NOT NULL DEFAULT 0
                    )
                ''')
                
                # チャット履歴テーブル（将来実装用）
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS chat_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        user_query TEXT NOT NULL,
                        llm_response TEXT NOT NULL,
                        search_performed BOOLEAN NOT NULL DEFAULT 0,
                        search_query TEXT,
                        created_at TEXT NOT NULL
                    )
                ''')
                
                # インデックスを作成
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_search_cache_query_hash 
                    ON search_cache(query_hash)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_search_cache_expires_at 
                    ON search_cache(expires_at)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_chat_history_session_id 
                    ON chat_history(session_id)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_chat_history_created_at 
                    ON chat_history(created_at)
                ''')
                
                conn.commit()
                logger.info("データベーステーブル初期化完了")
                
        except Exception as e:
            logger.error(f"データベース初期化エラー: {str(e)}")
            raise CacheError(f"データベース初期化に失敗しました: {str(e)}")
    
    def get_connection(self) -> sqlite3.Connection:
        """
        データベース接続を取得
        
        Returns:
            SQLite接続オブジェクト
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 辞書形式でアクセス可能
            return conn
        except Exception as e:
            logger.error(f"データベース接続エラー: {str(e)}")
            raise CacheError(f"データベース接続に失敗しました: {str(e)}")
    
    def cleanup_expired_cache(self) -> int:
        """
        期限切れキャッシュをクリーンアップ
        
        Returns:
            削除されたレコード数
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                current_time = datetime.now().isoformat()
                
                cursor.execute('''
                    DELETE FROM search_cache 
                    WHERE expires_at < ?
                ''', (current_time,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    logger.info(f"期限切れキャッシュ削除: {deleted_count}件")
                
                return deleted_count
                
        except Exception as e:
            logger.error(f"キャッシュクリーンアップエラー: {str(e)}")
            raise CacheError(f"キャッシュクリーンアップに失敗しました: {str(e)}")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        データベース統計情報を取得
        
        Returns:
            統計情報辞書
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 検索キャッシュ統計
                cursor.execute('SELECT COUNT(*) FROM search_cache')
                total_cache_count = cursor.fetchone()[0]
                
                cursor.execute('''
                    SELECT COUNT(*) FROM search_cache 
                    WHERE expires_at > ?
                ''', (datetime.now().isoformat(),))
                valid_cache_count = cursor.fetchone()[0]
                
                # チャット履歴統計
                cursor.execute('SELECT COUNT(*) FROM chat_history')
                chat_history_count = cursor.fetchone()[0]
                
                # データベースサイズ
                db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
                
                return {
                    "database_path": str(self.db_path),
                    "database_size_bytes": db_size,
                    "total_cache_entries": total_cache_count,
                    "valid_cache_entries": valid_cache_count,
                    "expired_cache_entries": total_cache_count - valid_cache_count,
                    "chat_history_entries": chat_history_count
                }
                
        except Exception as e:
            logger.error(f"データベース統計取得エラー: {str(e)}")
            return {"error": str(e)}
    
    def vacuum_database(self) -> None:
        """
        データベースを最適化（VACUUM）
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('VACUUM')
                logger.info("データベース最適化完了")
                
        except Exception as e:
            logger.error(f"データベース最適化エラー: {str(e)}")
            raise CacheError(f"データベース最適化に失敗しました: {str(e)}")
    
    def backup_database(self, backup_path: str) -> None:
        """
        データベースをバックアップ
        
        Args:
            backup_path: バックアップファイルパス
        """
        try:
            backup_path_obj = Path(backup_path)
            backup_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            with sqlite3.connect(self.db_path) as source:
                with sqlite3.connect(backup_path) as backup:
                    source.backup(backup)
            
            logger.info(f"データベースバックアップ完了: {backup_path}")
            
        except Exception as e:
            logger.error(f"データベースバックアップエラー: {str(e)}")
            raise CacheError(f"データベースバックアップに失敗しました: {str(e)}")