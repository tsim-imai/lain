"""
スクレイパーサービス層 - 検索機能の統合管理
"""
import logging
from typing import List, Dict, Any, Optional
from .bing_scraper import BingScraper
from ..utils.config import ConfigManager
from ..utils.exceptions import ScraperError

logger = logging.getLogger(__name__)


class ScraperService:
    """スクレイパーサービスクラス - 検索機能の統合管理"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
        """
        self.config_manager = config_manager
        self.bing_scraper = BingScraper(config_manager)
        self.scraper_config = config_manager.get_scraper_config()
        
        logger.info("スクレイパーサービスを初期化")
    
    def search(self, query: str, max_results: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Web検索を実行
        
        Args:
            query: 検索クエリ
            max_results: 最大取得結果数（Noneの場合は設定値を使用）
            
        Returns:
            検索結果のリスト
            
        Raises:
            ScraperError: 検索エラー時
        """
        if max_results is None:
            max_results = self.scraper_config["cache"]["max_results"]
        
        try:
            logger.info(f"Web検索開始: '{query}' (最大{max_results}件)")
            
            # Bing検索を実行
            results = self.bing_scraper.search(query, max_results)
            
            # 結果をフィルタリング・クリーンアップ
            cleaned_results = self._clean_search_results(results)
            
            logger.info(f"Web検索完了: {len(cleaned_results)}件の有効な結果")
            return cleaned_results
            
        except Exception as e:
            logger.error(f"Web検索エラー: {str(e)}")
            raise ScraperError(f"Web検索に失敗しました: {str(e)}")
    
    def _clean_search_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        検索結果をクリーンアップ
        
        Args:
            results: 生の検索結果
            
        Returns:
            クリーンアップされた検索結果
        """
        cleaned_results = []
        
        for result in results:
            try:
                # 必須フィールドをチェック
                if not result.get('title') or not result.get('snippet'):
                    continue
                
                # タイトルとスニペットをクリーンアップ
                cleaned_result = {
                    'title': self._clean_text(result['title']),
                    'url': result.get('url', ''),
                    'snippet': self._clean_text(result['snippet']),
                    'source': result.get('source', 'unknown')
                }
                
                # 空の結果は除外
                if cleaned_result['title'] and cleaned_result['snippet']:
                    cleaned_results.append(cleaned_result)
                    
            except Exception as e:
                logger.warning(f"検索結果クリーンアップエラー: {str(e)}")
                continue
        
        return cleaned_results
    
    def _clean_text(self, text: str) -> str:
        """
        テキストをクリーンアップ
        
        Args:
            text: 入力テキスト
            
        Returns:
            クリーンアップされたテキスト
        """
        if not text:
            return ""
        
        # 改行と余分な空白を除去
        cleaned = " ".join(text.split())
        
        # 特殊文字を除去（必要に応じて）
        # cleaned = re.sub(r'[^\w\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', '', cleaned)
        
        return cleaned.strip()
    
    def search_multiple_queries(self, queries: List[str], max_results_per_query: int = 5) -> List[Dict[str, Any]]:
        """
        複数のクエリで検索を実行
        
        Args:
            queries: 検索クエリのリスト
            max_results_per_query: クエリごとの最大結果数
            
        Returns:
            統合された検索結果
        """
        all_results = []
        
        for query in queries:
            try:
                results = self.search(query, max_results_per_query)
                all_results.extend(results)
                logger.info(f"クエリ '{query}': {len(results)}件取得")
                
            except Exception as e:
                logger.error(f"クエリ '{query}' の検索エラー: {str(e)}")
                continue
        
        # 重複を除去（URLベース）
        unique_results = self._remove_duplicates(all_results)
        
        logger.info(f"複数クエリ検索完了: {len(unique_results)}件の一意な結果")
        return unique_results
    
    def _remove_duplicates(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        重複する検索結果を除去
        
        Args:
            results: 検索結果のリスト
            
        Returns:
            重複除去後の検索結果
        """
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results
    
    def test_connection(self) -> bool:
        """
        スクレイパー接続テスト
        
        Returns:
            接続成功時True
        """
        try:
            return self.bing_scraper.test_connection()
        except Exception as e:
            logger.error(f"スクレイパー接続テスト失敗: {str(e)}")
            return False
    
    def get_scraper_stats(self) -> Dict[str, Any]:
        """
        スクレイパーの統計情報を取得
        
        Returns:
            統計情報辞書
        """
        return {
            "available_scrapers": ["bing"],
            "rate_limit": self.scraper_config["bing"]["rate_limit"],
            "max_results": self.scraper_config["cache"]["max_results"]
        }