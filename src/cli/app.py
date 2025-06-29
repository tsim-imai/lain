"""
メインアプリケーション
"""
import logging
import sys
from typing import Dict, Any, List, Optional, Callable
from tqdm import tqdm
import time
from ..llm.services import LLMService
from ..scraper.services import ScraperService
from ..cache.services import CacheService
from ..cache.chat_manager import ChatHistoryManager
from ..utils.config import ConfigManager
from ..utils.exceptions import LainError
from ..utils.colors import ColorPrinter, success, error, warning, info, highlight, progress_color

logger = logging.getLogger(__name__)


class LainApp:
    """メインアプリケーションクラス"""
    
    def __init__(self, config_manager: ConfigManager, enable_color: bool = True):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
            enable_color: カラー出力を有効にするか
        """
        self.config_manager = config_manager
        self.color_printer = ColorPrinter(enable_color)
        
        # 各サービスを初期化
        self.llm_service = LLMService(config_manager)
        self.scraper_service = ScraperService(config_manager)
        self.cache_service = CacheService(config_manager)
        self.chat_manager = ChatHistoryManager(config_manager)
        
        logger.info("lainアプリケーションを初期化")
    
    def process_query(
        self,
        query: str,
        force_refresh: bool = False,
        max_results: int = 10,
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        クエリを処理してAI応答を生成
        
        Args:
            query: ユーザーの質問
            force_refresh: キャッシュを無視して強制検索
            max_results: 最大検索結果数
            show_progress: 進捗バーを表示するか
            
        Returns:
            処理結果辞書
        """
        start_time = time.time()
        
        try:
            # 進捗バーの初期化
            if show_progress:
                if self.color_printer.color_enabled:
                    progress = tqdm(
                        total=4, 
                        desc="🔄 処理中", 
                        unit="step",
                        bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}',
                        colour='cyan',
                        leave=False  # 完了後にプログレスバーを消去
                    )
                else:
                    progress = tqdm(
                        total=4, 
                        desc="🔄 処理中", 
                        unit="step",
                        bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}',
                        leave=False  # 完了後にプログレスバーを消去
                    )
            
            # ステップ1: 検索判断
            if show_progress:
                progress.set_description("🤔 検索の必要性を判断中")
                progress.update(1)
            
            should_search = self.llm_service.should_search(query)
            logger.info(f"検索判断: {'必要' if should_search else '不要'}")
            
            if not should_search:
                # ステップ2-4をスキップして直接回答
                if show_progress:
                    progress.set_description("🤖 AIが直接回答中")
                    progress.update(3)
                
                response = self.llm_service.direct_answer(query)
                
                if show_progress:
                    progress.close()
                
                return {
                    "query": query,
                    "search_performed": False,
                    "response": response,
                    "processing_time": time.time() - start_time,
                    "search_results": []
                }
            
            # ステップ2: 検索クエリ生成
            if show_progress:
                progress.set_description("📝 検索クエリを生成中")
                progress.update(1)
            
            search_query = self.llm_service.generate_search_query(query)
            logger.info(f"生成された検索クエリ: '{search_query}'")
            
            # ステップ3: Web検索（キャッシュ付き）
            if show_progress:
                progress.set_description("🌐 Web検索を実行中")
                progress.update(1)
            
            search_results = self.cache_service.get_or_cache_results(
                search_query,
                lambda q: self.scraper_service.search(q, max_results),
                force_refresh
            )
            
            logger.info(f"検索結果: {len(search_results)}件取得")
            
            # ステップ4: 結果要約
            if show_progress:
                progress.set_description("📊 検索結果を要約中")
                progress.update(1)
            
            if search_results:
                response = self.llm_service.summarize_results(query, search_results)
            else:
                response = "申し訳ございませんが、関連する情報を見つけることができませんでした。"
            
            if show_progress:
                progress.close()
            
            return {
                "query": query,
                "search_query": search_query,
                "search_performed": True,
                "response": response,
                "search_results": search_results,
                "processing_time": time.time() - start_time,
                "result_count": len(search_results)
            }
            
        except Exception as e:
            if show_progress and 'progress' in locals():
                progress.close()
            
            logger.error(f"クエリ処理エラー: {str(e)}")
            
            # エラー時はLLMによる直接回答を試行
            try:
                response = self.llm_service.direct_answer(query)
                return {
                    "query": query,
                    "search_performed": False,
                    "response": f"検索中にエラーが発生しました。以下は直接回答です：\n\n{response}",
                    "error": str(e),
                    "processing_time": time.time() - start_time,
                    "search_results": []
                }
            except Exception as fallback_error:
                logger.error(f"フォールバック回答エラー: {str(fallback_error)}")
                return {
                    "query": query,
                    "search_performed": False,
                    "response": "申し訳ございませんが、処理中にエラーが発生し、回答を生成できませんでした。",
                    "error": str(e),
                    "fallback_error": str(fallback_error),
                    "processing_time": time.time() - start_time,
                    "search_results": []
                }
    
    def search(self, query: str, show_progress: bool = True, **kwargs) -> str:
        """
        カラー出力対応の検索実行
        
        Args:
            query: 検索クエリ
            show_progress: プログレス表示
            **kwargs: process_queryへの追加引数
            
        Returns:
            検索結果テキスト
        """
        try:
            # ヘッダー表示
            self.color_printer.print_header(f"lain検索: {query}")
            
            # 処理実行
            result = self.process_query(query, show_progress=show_progress, **kwargs)
            
            # 結果表示
            if result.get("search_performed"):
                self.color_printer.print_info(f"検索実行: {len(result.get('search_results', []))}件の結果を取得")
                # 使用した検索クエリを表示
                if "search_query" in result:
                    self.color_printer.print_info(f"使用クエリ: {result['search_query']}")
                if result.get("from_cache"):
                    self.color_printer.print_info("キャッシュから取得")
            else:
                self.color_printer.print_info("検索をスキップして直接回答")
            
            # 処理時間表示
            processing_time = result.get("processing_time", 0)
            self.color_printer.print_info(f"処理時間: {processing_time:.2f}秒")
            
            # エラーがある場合
            if "error" in result:
                self.color_printer.print_warning("処理中に問題が発生しました")
            
            # 回答表示
            print()  # 空行
            print(highlight("🤖 AI回答:"))
            print(result["response"])
            
            return result["response"]
            
        except Exception as e:
            self.color_printer.print_error(f"検索エラー: {str(e)}")
            return f"エラーが発生しました: {str(e)}"
    
    def search_stream(self, query: str, show_progress: bool = True, **kwargs) -> str:
        """
        ストリーミング対応の検索実行
        
        Args:
            query: 検索クエリ
            show_progress: プログレス表示
            **kwargs: process_queryへの追加引数
            
        Returns:
            検索結果テキスト
        """
        try:
            # ヘッダー表示
            self.color_printer.print_header(f"lain検索: {query}")
            
            start_time = time.time()
            
            # 進捗バーの初期化
            if show_progress:
                if self.color_printer.color_enabled:
                    progress = tqdm(
                        total=4, 
                        desc="🔄 処理中", 
                        unit="step",
                        bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}',
                        colour='cyan',
                        leave=False
                    )
                else:
                    progress = tqdm(
                        total=4, 
                        desc="🔄 処理中", 
                        unit="step",
                        bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}',
                        leave=False
                    )
            
            # ステップ1: 検索判断
            if show_progress:
                progress.set_description("🤔 検索の必要性を判断中")
                progress.update(1)
            
            should_search = self.llm_service.should_search(query)
            logger.info(f"検索判断: {'必要' if should_search else '不要'}")
            
            if not should_search:
                # 直接回答をストリーミング表示
                if show_progress:
                    progress.set_description("🤖 AIが直接回答中")
                    progress.update(3)
                    progress.close()
                
                # 回答表示開始
                print()
                print(highlight("🤖 AI回答:"), end=" ", flush=True)
                
                # ストリーミング回答の収集
                complete_response = ""
                for chunk in self.llm_service.direct_answer_stream(query):
                    print(chunk, end="", flush=True)
                    complete_response += chunk
                
                print()  # 改行
                
                # 処理時間表示
                processing_time = time.time() - start_time
                self.color_printer.print_info(f"処理時間: {processing_time:.2f}秒")
                self.color_printer.print_info("検索をスキップして直接回答")
                
                return complete_response.strip()
            
            # ステップ2: 検索クエリ生成
            if show_progress:
                progress.set_description("📝 検索クエリを生成中")
                progress.update(1)
            
            search_query = self.llm_service.generate_search_query(query)
            logger.info(f"生成された検索クエリ: '{search_query}'")
            
            # ステップ3: Web検索（キャッシュ付き）
            if show_progress:
                progress.set_description("🌐 Web検索を実行中")
                progress.update(1)
            
            search_results = self.cache_service.get_or_cache_results(
                search_query,
                lambda q: self.scraper_service.search(q, kwargs.get('max_results', 10)),
                kwargs.get('force_refresh', False)
            )
            
            logger.info(f"検索結果: {len(search_results)}件取得")
            
            # ステップ4: 結果要約をストリーミング表示
            if show_progress:
                progress.set_description("📊 検索結果を要約中")
                progress.update(1)
                progress.close()
            
            if search_results:
                # 回答表示開始
                print()
                print(highlight("🤖 AI回答:"), end=" ", flush=True)
                
                # ストリーミング要約の収集
                complete_response = ""
                for chunk in self.llm_service.summarize_results_stream(query, search_results):
                    print(chunk, end="", flush=True)
                    complete_response += chunk
                
                print()  # 改行
                response = complete_response.strip()
            else:
                response = "申し訳ございませんが、関連する情報を見つけることができませんでした。"
                print()
                print(highlight("🤖 AI回答:"))
                print(response)
            
            # 結果表示
            self.color_printer.print_info(f"検索実行: {len(search_results)}件の結果を取得")
            if search_query:
                self.color_printer.print_info(f"使用クエリ: {search_query}")
            
            # 処理時間表示
            processing_time = time.time() - start_time
            self.color_printer.print_info(f"処理時間: {processing_time:.2f}秒")
            
            return response
            
        except Exception as e:
            if show_progress and 'progress' in locals():
                progress.close()
            
            self.color_printer.print_error(f"検索エラー: {str(e)}")
            return f"エラーが発生しました: {str(e)}"
    
    def test_llm_connection(self) -> bool:
        """
        LLM接続テスト
        
        Returns:
            接続成功時True
        """
        try:
            return self.llm_service.test_connection()
        except Exception as e:
            logger.error(f"LLM接続テストエラー: {str(e)}")
            return False
    
    def test_scraper_connection(self) -> bool:
        """
        スクレイパー接続テスト
        
        Returns:
            接続成功時True
        """
        try:
            return self.scraper_service.test_connection()
        except Exception as e:
            logger.error(f"スクレイパー接続テストエラー: {str(e)}")
            return False
    
    def test_cache_system(self) -> Dict[str, Any]:
        """
        キャッシュシステムテスト
        
        Returns:
            ヘルスチェック結果
        """
        try:
            return self.cache_service.health_check()
        except Exception as e:
            logger.error(f"キャッシュシステムテストエラー: {str(e)}")
            return {"status": "unhealthy", "error": str(e)}
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        キャッシュ統計情報を取得
        
        Returns:
            統計情報辞書
        """
        return self.cache_service.get_cache_statistics()
    
    def get_recent_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        最近のクエリ一覧を取得
        
        Args:
            limit: 取得件数上限
            
        Returns:
            最近のクエリ情報のリスト
        """
        return self.cache_service.get_recent_queries(limit)
    
    def clear_all_cache(self) -> int:
        """
        全キャッシュを削除
        
        Returns:
            削除されたレコード数
        """
        return self.cache_service.clear_all_cache()
    
    def cleanup_expired_cache(self) -> int:
        """
        期限切れキャッシュをクリーンアップ
        
        Returns:
            削除されたレコード数
        """
        return self.cache_service.cleanup_expired_cache()
    
    def optimize_cache(self) -> None:
        """
        キャッシュを最適化
        """
        self.cache_service.optimize_cache()
    
    def process_chat_query(
        self,
        query: str,
        session_id: str,
        force_refresh: bool = False,
        max_results: int = 10,
        show_progress: bool = True,
        history_limit: int = 5
    ) -> Dict[str, Any]:
        """
        チャットクエリを処理してAI応答を生成（履歴考慮）
        
        Args:
            query: ユーザーの質問
            session_id: チャットセッションID
            force_refresh: キャッシュを無視して強制検索
            max_results: 最大検索結果数
            show_progress: 進捗バーを表示するか
            history_limit: 考慮する履歴の最大数
            
        Returns:
            処理結果辞書
        """
        start_time = time.time()
        
        try:
            # チャット履歴を取得
            history = self.chat_manager.format_history_for_llm(session_id, history_limit)
            
            # 進捗バーの初期化
            if show_progress:
                if self.color_printer.color_enabled:
                    progress = tqdm(
                        total=4, 
                        desc="🔄 処理中", 
                        unit="step",
                        bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}',
                        colour='cyan',
                        leave=False
                    )
                else:
                    progress = tqdm(
                        total=4, 
                        desc="🔄 処理中", 
                        unit="step",
                        bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}',
                        leave=False
                    )
            
            # ステップ1: 検索判断
            if show_progress:
                progress.set_description("🤔 検索の必要性を判断中")
                progress.update(1)
            
            should_search = self.llm_service.should_search(query)
            logger.info(f"検索判断: {'必要' if should_search else '不要'}")
            
            if not should_search:
                # 履歴を考慮して直接回答
                if show_progress:
                    progress.set_description("🤖 AIが直接回答中")
                    progress.update(3)
                
                response = self.llm_service.direct_answer(query, history)
                
                if show_progress:
                    progress.close()
                
                # チャット履歴に保存
                self.chat_manager.save_chat_entry(
                    session_id, query, response, False
                )
                
                return {
                    "query": query,
                    "session_id": session_id,
                    "search_performed": False,
                    "response": response,
                    "processing_time": time.time() - start_time,
                    "search_results": [],
                    "history_used": bool(history)
                }
            
            # ステップ2: 検索クエリ生成
            if show_progress:
                progress.set_description("📝 検索クエリを生成中")
                progress.update(1)
            
            search_query = self.llm_service.generate_search_query(query)
            logger.info(f"生成された検索クエリ: '{search_query}'")
            
            # ステップ3: Web検索（キャッシュ付き）
            if show_progress:
                progress.set_description("🌐 Web検索を実行中")
                progress.update(1)
            
            search_results = self.cache_service.get_or_cache_results(
                search_query,
                lambda q: self.scraper_service.search(q, max_results),
                force_refresh
            )
            
            logger.info(f"検索結果: {len(search_results)}件取得")
            
            # ステップ4: 結果要約（履歴考慮）
            if show_progress:
                progress.set_description("📊 検索結果を要約中")
                progress.update(1)
            
            if search_results:
                response = self.llm_service.summarize_results(query, search_results, history)
            else:
                response = "申し訳ございませんが、関連する情報を見つけることができませんでした。"
            
            if show_progress:
                progress.close()
            
            # チャット履歴に保存
            self.chat_manager.save_chat_entry(
                session_id, query, response, True, search_query
            )
            
            return {
                "query": query,
                "session_id": session_id,
                "search_query": search_query,
                "search_performed": True,
                "response": response,
                "search_results": search_results,
                "processing_time": time.time() - start_time,
                "result_count": len(search_results),
                "history_used": bool(history)
            }
            
        except Exception as e:
            if show_progress and 'progress' in locals():
                progress.close()
            
            logger.error(f"チャットクエリ処理エラー: {str(e)}")
            
            # エラー時もLLMによる直接回答を試行
            try:
                response = self.llm_service.direct_answer(query, history)
                
                # エラー情報も含めて履歴に保存
                error_response = f"検索中にエラーが発生しました。以下は直接回答です：\n\n{response}"
                self.chat_manager.save_chat_entry(
                    session_id, query, error_response, False
                )
                
                return {
                    "query": query,
                    "session_id": session_id,
                    "search_performed": False,
                    "response": error_response,
                    "error": str(e),
                    "processing_time": time.time() - start_time,
                    "search_results": [],
                    "history_used": bool(history)
                }
            except Exception as fallback_error:
                logger.error(f"フォールバック回答エラー: {str(fallback_error)}")
                
                error_response = "申し訳ございませんが、処理中にエラーが発生し、回答を生成できませんでした。"
                self.chat_manager.save_chat_entry(
                    session_id, query, error_response, False
                )
                
                return {
                    "query": query,
                    "session_id": session_id,
                    "search_performed": False,
                    "response": error_response,
                    "error": str(e),
                    "fallback_error": str(fallback_error),
                    "processing_time": time.time() - start_time,
                    "search_results": [],
                    "history_used": bool(history)
                }
    
    def start_chat_session(self) -> str:
        """
        新しいチャットセッションを開始
        
        Returns:
            セッションID
        """
        return self.chat_manager.create_session()
    
    def get_chat_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        チャット履歴を取得
        
        Args:
            session_id: セッションID
            limit: 取得件数
            
        Returns:
            チャット履歴のリスト
        """
        return self.chat_manager.get_session_history(session_id, limit)
    
    def clear_chat_session(self, session_id: str) -> int:
        """
        チャットセッションをクリア
        
        Args:
            session_id: セッションID
            
        Returns:
            削除されたレコード数
        """
        return self.chat_manager.clear_session_history(session_id)
    
    def get_recent_chat_sessions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        最近のチャットセッション一覧を取得
        
        Args:
            limit: 取得件数
            
        Returns:
            セッション情報のリスト
        """
        return self.chat_manager.get_recent_sessions(limit)
    
    def process_chat_query_stream(
        self,
        query: str,
        session_id: str,
        force_refresh: bool = False,
        max_results: int = 10,
        show_progress: bool = True,
        history_limit: int = 5,
        stream_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        チャットクエリをストリーミング処理してAI応答を生成（履歴考慮）
        
        Args:
            query: ユーザーの質問
            session_id: チャットセッションID
            force_refresh: キャッシュを無視して強制検索
            max_results: 最大検索結果数
            show_progress: 進捗バーを表示するか
            history_limit: 考慮する履歴の最大数
            stream_callback: ストリーミング出力のコールバック関数
            
        Returns:
            処理結果辞書
        """
        start_time = time.time()
        
        try:
            # チャット履歴を取得
            history = self.chat_manager.format_history_for_llm(session_id, history_limit)
            
            # 進捗バーの初期化
            if show_progress:
                if self.color_printer.color_enabled:
                    progress = tqdm(
                        total=4, 
                        desc="🔄 処理中", 
                        unit="step",
                        bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}',
                        colour='cyan',
                        leave=False
                    )
                else:
                    progress = tqdm(
                        total=4, 
                        desc="🔄 処理中", 
                        unit="step",
                        bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}',
                        leave=False
                    )
            
            # ステップ1: 検索判断
            if show_progress:
                progress.set_description("🤔 検索の必要性を判断中")
                progress.update(1)
            
            should_search = self.llm_service.should_search(query)
            logger.info(f"検索判断: {'必要' if should_search else '不要'}")
            
            if not should_search:
                # 履歴を考慮してストリーミング直接回答
                if show_progress:
                    progress.set_description("🤖 AIが直接回答中")
                    progress.update(3)
                    progress.close()
                
                # ストリーミング応答を収集
                complete_response = ""
                for chunk in self.llm_service.direct_answer_stream(query, history, stream_callback):
                    complete_response += chunk
                
                response = complete_response.strip()
                
                # チャット履歴に保存
                self.chat_manager.save_chat_entry(
                    session_id, query, response, False
                )
                
                return {
                    "query": query,
                    "session_id": session_id,
                    "search_performed": False,
                    "response": response,
                    "processing_time": time.time() - start_time,
                    "search_results": [],
                    "history_used": bool(history),
                    "streamed": True
                }
            
            # ステップ2: 検索クエリ生成
            if show_progress:
                progress.set_description("📝 検索クエリを生成中")
                progress.update(1)
            
            search_query = self.llm_service.generate_search_query(query)
            logger.info(f"生成された検索クエリ: '{search_query}'")
            
            # ステップ3: Web検索（キャッシュ付き）
            if show_progress:
                progress.set_description("🌐 Web検索を実行中")
                progress.update(1)
            
            search_results = self.cache_service.get_or_cache_results(
                search_query,
                lambda q: self.scraper_service.search(q, max_results),
                force_refresh
            )
            
            logger.info(f"検索結果: {len(search_results)}件取得")
            
            # ステップ4: 結果要約（履歴考慮、ストリーミング）
            if show_progress:
                progress.set_description("📊 検索結果を要約中")
                progress.update(1)
                progress.close()
            
            if search_results:
                # ストリーミング要約を収集
                complete_response = ""
                for chunk in self.llm_service.summarize_results_stream(
                    query, search_results, history, stream_callback
                ):
                    complete_response += chunk
                response = complete_response.strip()
            else:
                response = "申し訳ございませんが、関連する情報を見つけることができませんでした。"
                if stream_callback:
                    stream_callback(response)
            
            # チャット履歴に保存
            self.chat_manager.save_chat_entry(
                session_id, query, response, True, search_query
            )
            
            return {
                "query": query,
                "session_id": session_id,
                "search_query": search_query,
                "search_performed": True,
                "response": response,
                "search_results": search_results,
                "processing_time": time.time() - start_time,
                "result_count": len(search_results),
                "history_used": bool(history),
                "streamed": True
            }
            
        except Exception as e:
            if show_progress and 'progress' in locals():
                progress.close()
            
            logger.error(f"チャットクエリストリーミング処理エラー: {str(e)}")
            
            # エラー時もLLMによる直接回答を試行
            try:
                complete_response = ""
                for chunk in self.llm_service.direct_answer_stream(query, history, stream_callback):
                    complete_response += chunk
                response = complete_response.strip()
                
                # エラー情報も含めて履歴に保存
                error_response = f"検索中にエラーが発生しました。以下は直接回答です：\n\n{response}"
                self.chat_manager.save_chat_entry(
                    session_id, query, error_response, False
                )
                
                return {
                    "query": query,
                    "session_id": session_id,
                    "search_performed": False,
                    "response": error_response,
                    "error": str(e),
                    "processing_time": time.time() - start_time,
                    "search_results": [],
                    "history_used": bool(history),
                    "streamed": True
                }
            except Exception as fallback_error:
                logger.error(f"フォールバック回答エラー: {str(fallback_error)}")
                
                error_response = "申し訳ございませんが、処理中にエラーが発生し、回答を生成できませんでした。"
                if stream_callback:
                    stream_callback(error_response)
                    
                self.chat_manager.save_chat_entry(
                    session_id, query, error_response, False
                )
                
                return {
                    "query": query,
                    "session_id": session_id,
                    "search_performed": False,
                    "response": error_response,
                    "error": str(e),
                    "fallback_error": str(fallback_error),
                    "processing_time": time.time() - start_time,
                    "search_results": [],
                    "history_used": bool(history),
                    "streamed": True
                }
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        システム情報を取得
        
        Returns:
            システム情報辞書
        """
        try:
            llm_config = self.config_manager.get_llm_config()
            scraper_config = self.config_manager.get_scraper_config()
            cache_stats = self.get_cache_statistics()
            chat_stats = self.chat_manager.get_chat_statistics()
            
            return {
                "llm": {
                    "base_url": llm_config["lm_studio"]["base_url"],
                    "model": llm_config["lm_studio"]["model_name"],
                    "connected": self.test_llm_connection()
                },
                "scraper": {
                    "engine": "bing",
                    "rate_limit": scraper_config["bing"]["rate_limit"]["requests_per_second"],
                    "connected": self.test_scraper_connection()
                },
                "cache": cache_stats,
                "chat": chat_stats
            }
        except Exception as e:
            logger.error(f"システム情報取得エラー: {str(e)}")
            return {"error": str(e)}