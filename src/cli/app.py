"""
メインアプリケーション
"""
import logging
from typing import Dict, Any, List, Optional
from tqdm import tqdm
import time
from ..llm.services import LLMService
from ..scraper.services import ScraperService
from ..cache.services import CacheService
from ..utils.config import ConfigManager
from ..utils.exceptions import LainError

logger = logging.getLogger(__name__)


class LainApp:
    """メインアプリケーションクラス"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
        """
        self.config_manager = config_manager
        
        # 各サービスを初期化
        self.llm_service = LLMService(config_manager)
        self.scraper_service = ScraperService(config_manager)
        self.cache_service = CacheService(config_manager)
        
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
                progress = tqdm(total=4, desc="処理中", unit="step")
            
            # ステップ1: 検索判断
            if show_progress:
                progress.set_description("検索の必要性を判断中")
                progress.update(1)
            
            should_search = self.llm_service.should_search(query)
            logger.info(f"検索判断: {'必要' if should_search else '不要'}")
            
            if not should_search:
                # ステップ2-4をスキップして直接回答
                if show_progress:
                    progress.set_description("AIが直接回答中")
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
                progress.set_description("検索クエリを生成中")
                progress.update(1)
            
            search_query = self.llm_service.generate_search_query(query)
            logger.info(f"生成された検索クエリ: '{search_query}'")
            
            # ステップ3: Web検索（キャッシュ付き）
            if show_progress:
                progress.set_description("Web検索を実行中")
                progress.update(1)
            
            search_results = self.cache_service.get_or_cache_results(
                search_query,
                lambda q: self.scraper_service.search(q, max_results),
                force_refresh
            )
            
            logger.info(f"検索結果: {len(search_results)}件取得")
            
            # ステップ4: 結果要約
            if show_progress:
                progress.set_description("検索結果を要約中")
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
                "cache": cache_stats
            }
        except Exception as e:
            logger.error(f"システム情報取得エラー: {str(e)}")
            return {"error": str(e)}