"""
チャット履歴管理 - チャット履歴の保存・取得・管理
"""
import logging
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from .database import DatabaseManager
from ..utils.config import ConfigManager
from ..utils.exceptions import CacheError

logger = logging.getLogger(__name__)


class ChatHistoryManager:
    """チャット履歴管理クラス"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
        """
        self.config_manager = config_manager
        self.db_manager = DatabaseManager(config_manager)
        
        logger.info("チャット履歴管理を初期化")
    
    def create_session(self) -> str:
        """
        新しいチャットセッションを作成
        
        Returns:
            セッションID
        """
        session_id = str(uuid.uuid4())
        logger.info(f"新しいチャットセッション作成: {session_id}")
        return session_id
    
    def save_chat_entry(
        self,
        session_id: str,
        user_query: str,
        llm_response: str,
        search_performed: bool = False,
        search_query: Optional[str] = None
    ) -> None:
        """
        チャットエントリを保存
        
        Args:
            session_id: セッションID
            user_query: ユーザーの質問
            llm_response: LLMの回答
            search_performed: 検索が実行されたか
            search_query: 検索クエリ（検索実行時のみ）
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO chat_history 
                    (session_id, user_query, llm_response, search_performed, search_query, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    session_id,
                    user_query,
                    llm_response,
                    search_performed,
                    search_query,
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                logger.debug(f"チャットエントリ保存: セッション={session_id}")
                
        except Exception as e:
            logger.error(f"チャットエントリ保存エラー: {str(e)}")
            raise CacheError(f"チャットエントリ保存に失敗しました: {str(e)}")
    
    def get_session_history(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        セッションの履歴を取得
        
        Args:
            session_id: セッションID
            limit: 取得する履歴の最大数
            
        Returns:
            履歴エントリのリスト（時系列順）
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT 
                        user_query,
                        llm_response,
                        search_performed,
                        search_query,
                        created_at
                    FROM chat_history 
                    WHERE session_id = ?
                    ORDER BY created_at ASC
                    LIMIT ?
                ''', (session_id, limit))
                
                rows = cursor.fetchall()
                
                history = []
                for row in rows:
                    history.append({
                        "user_query": row["user_query"],
                        "llm_response": row["llm_response"],
                        "search_performed": bool(row["search_performed"]),
                        "search_query": row["search_query"],
                        "created_at": row["created_at"]
                    })
                
                logger.debug(f"セッション履歴取得: {len(history)}件")
                return history
                
        except Exception as e:
            logger.error(f"セッション履歴取得エラー: {str(e)}")
            raise CacheError(f"セッション履歴取得に失敗しました: {str(e)}")
    
    def get_recent_sessions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        最近のセッション一覧を取得
        
        Args:
            limit: 取得するセッション数
            
        Returns:
            セッション情報のリスト
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT 
                        session_id,
                        COUNT(*) as message_count,
                        MIN(created_at) as first_message,
                        MAX(created_at) as last_message
                    FROM chat_history 
                    GROUP BY session_id
                    ORDER BY last_message DESC
                    LIMIT ?
                ''', (limit,))
                
                rows = cursor.fetchall()
                
                sessions = []
                for row in rows:
                    sessions.append({
                        "session_id": row["session_id"],
                        "message_count": row["message_count"],
                        "first_message": row["first_message"],
                        "last_message": row["last_message"]
                    })
                
                return sessions
                
        except Exception as e:
            logger.error(f"最近のセッション取得エラー: {str(e)}")
            return []
    
    def clear_session_history(self, session_id: str) -> int:
        """
        特定セッションの履歴を削除
        
        Args:
            session_id: セッションID
            
        Returns:
            削除されたレコード数
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    DELETE FROM chat_history 
                    WHERE session_id = ?
                ''', (session_id,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"セッション履歴削除: {deleted_count}件")
                return deleted_count
                
        except Exception as e:
            logger.error(f"セッション履歴削除エラー: {str(e)}")
            raise CacheError(f"セッション履歴削除に失敗しました: {str(e)}")
    
    def clear_all_chat_history(self) -> int:
        """
        全チャット履歴を削除
        
        Returns:
            削除されたレコード数
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM chat_history')
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"全チャット履歴削除: {deleted_count}件")
                return deleted_count
                
        except Exception as e:
            logger.error(f"全チャット履歴削除エラー: {str(e)}")
            raise CacheError(f"全チャット履歴削除に失敗しました: {str(e)}")
    
    def get_chat_statistics(self) -> Dict[str, Any]:
        """
        チャット統計情報を取得
        
        Returns:
            統計情報辞書
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # 総メッセージ数
                cursor.execute('SELECT COUNT(*) FROM chat_history')
                total_messages = cursor.fetchone()[0]
                
                # セッション数
                cursor.execute('SELECT COUNT(DISTINCT session_id) FROM chat_history')
                total_sessions = cursor.fetchone()[0]
                
                # 検索実行数
                cursor.execute('SELECT COUNT(*) FROM chat_history WHERE search_performed = 1')
                search_count = cursor.fetchone()[0]
                
                return {
                    "total_messages": total_messages,
                    "total_sessions": total_sessions,
                    "search_performed_count": search_count,
                    "average_messages_per_session": total_messages / max(total_sessions, 1)
                }
                
        except Exception as e:
            logger.error(f"チャット統計取得エラー: {str(e)}")
            return {"error": str(e)}
    
    def format_history_for_llm(
        self,
        session_id: str,
        limit: int = 5
    ) -> str:
        """
        LLMに渡すためのフォーマット済み履歴文字列を生成
        
        Args:
            session_id: セッションID
            limit: 取得する履歴の最大数
            
        Returns:
            フォーマット済み履歴文字列
        """
        try:
            history = self.get_session_history(session_id, limit)
            
            if not history:
                return ""
            
            formatted_history = []
            for entry in history:
                formatted_history.append(f"ユーザー: {entry['user_query']}")
                formatted_history.append(f"AI: {entry['llm_response']}")
            
            return "\n\n".join(formatted_history)
            
        except Exception as e:
            logger.error(f"履歴フォーマットエラー: {str(e)}")
            return ""