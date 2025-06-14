"""
政治専門スクレイピングサービス
政府・政党データの統合収集サービス
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from ..utils.config import ConfigManager
from ..utils.exceptions import ScraperError
from .government_scraper import GovernmentScraper
from .party_scraper import PartyScraper
from .media_scraper import MediaScraper
from .social_scraper import SocialScraper
from .political_search_engine import PoliticalSearchEngine

logger = logging.getLogger(__name__)


class PoliticalScraperService:
    """政治専門スクレイピングサービスクラス"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
        """
        self.config_manager = config_manager
        self.government_scraper = GovernmentScraper(config_manager)
        self.party_scraper = PartyScraper(config_manager)
        self.media_scraper = MediaScraper(config_manager)
        self.social_scraper = SocialScraper(config_manager)
        self.political_search_engine = PoliticalSearchEngine(config_manager)
        
        # 政治的意図別の検索戦略
        self.search_strategies = {
            "support_rating": self._search_support_rating,
            "election_prediction": self._search_election_data,
            "policy_analysis": self._search_policy_data,
            "political_news": self._search_political_news,
            "politician_info": self._search_politician_info,
            "party_info": self._search_party_info,
            "political_scandal": self._search_scandal_info,
            "coalition_analysis": self._search_coalition_info,
            "general_political": self._search_general_political
        }
        
        logger.info("政治専門スクレイピングサービスを初期化")
    
    def search_by_political_intent(self, 
                                  query: str,
                                  intent: str,
                                  max_results: int = 10) -> List[Dict[str, Any]]:
        """
        政治的意図に基づくデータ検索
        
        Args:
            query: 検索クエリ
            intent: 政治的意図
            max_results: 最大取得件数
            
        Returns:
            検索結果のリスト
        """
        try:
            # 政治特化検索エンジンを使用
            search_results = self.political_search_engine.search_political_content(
                query, intent, max_results
            )
            
            # 既存のスクレイピング戦略と統合
            strategy_func = self.search_strategies.get(intent, self._search_general_political)
            scraped_results = strategy_func(query, max_results // 2)
            
            # 結果を統合
            all_results = search_results + scraped_results
            
            # 重複除去と最終ランキング
            final_results = self._merge_and_rank_results(all_results, intent)
            
            logger.info(f"政治意図別検索完了 ({intent}): {len(final_results)}件")
            return final_results[:max_results]
            
        except Exception as e:
            logger.error(f"政治意図別検索エラー ({intent}): {str(e)}")
            return []
    
    def _search_support_rating(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """支持率関連データを検索"""
        results = []
        
        try:
            # 政府発表データを優先
            gov_data = self.government_scraper.scrape_kantei_news(max_results // 2)
            for item in gov_data:
                if any(keyword in item.get("title", "") for keyword in ["支持率", "世論調査", "内閣"]):
                    item["relevance_score"] = 0.9
                    results.append(item)
            
            # 政党のコメント・声明
            major_parties = ["自由民主党", "立憲民主党", "公明党"]
            for party in major_parties:
                party_statements = self.party_scraper.scrape_party_statements(party, 3)
                for item in party_statements:
                    if any(keyword in item.get("title", "") for keyword in ["支持率", "世論", "内閣"]):
                        item["relevance_score"] = 0.7
                        results.append(item)
            
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"支持率検索エラー: {str(e)}")
            return results
    
    def _search_election_data(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """選挙関連データを検索"""
        results = []
        
        try:
            # 政府の選挙関連発表
            gov_data = self.government_scraper.scrape_kantei_news(max_results // 2)
            for item in gov_data:
                if any(keyword in item.get("title", "") for keyword in ["選挙", "衆議院", "参議院", "解散"]):
                    item["relevance_score"] = 0.95
                    results.append(item)
            
            # 各政党の選挙関連ニュース
            all_parties = list(self.party_scraper.party_sites.keys())
            for party in all_parties[:4]:  # 主要4党
                party_news = self.party_scraper.scrape_party_news(party, 3)
                for item in party_news:
                    if any(keyword in item.get("title", "") for keyword in ["選挙", "候補", "公約"]):
                        item["relevance_score"] = 0.8
                        results.append(item)
            
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"選挙データ検索エラー: {str(e)}")
            return results
    
    def _search_policy_data(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """政策関連データを検索"""
        results = []
        
        try:
            # 政府の政策文書
            policy_docs = self.government_scraper.scrape_policy_documents()
            for item in policy_docs:
                item["relevance_score"] = 1.0
                results.append(item)
            
            # 閣議決定
            cabinet_decisions = self.government_scraper.scrape_cabinet_decisions(max_results // 3)
            for item in cabinet_decisions:
                item["relevance_score"] = 0.95
                results.append(item)
            
            # 政党の政策
            major_parties = ["自由民主党", "立憲民主党", "日本維新の会"]
            for party in major_parties:
                party_policies = self.party_scraper.scrape_party_policies(party, 3)
                for item in party_policies:
                    item["relevance_score"] = 0.85
                    results.append(item)
            
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"政策データ検索エラー: {str(e)}")
            return results
    
    def _search_political_news(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """政治ニュースを検索"""
        results = []
        
        try:
            # 政府ニュース
            gov_news = self.government_scraper.scrape_kantei_news(max_results // 2)
            for item in gov_news:
                item["relevance_score"] = 0.9
                results.append(item)
            
            # 全政党のニュース
            all_party_news = self.party_scraper.get_all_party_news(2)
            for party_name, news_list in all_party_news.items():
                for item in news_list:
                    item["relevance_score"] = 0.8
                    results.append(item)
            
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"政治ニュース検索エラー: {str(e)}")
            return results
    
    def _search_politician_info(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """政治家情報を検索"""
        results = []
        
        try:
            # 政治家名を含む政府発表
            gov_data = self.government_scraper.scrape_kantei_news(max_results // 2)
            for item in gov_data:
                # 政治家名のキーワードチェック（簡略版）
                politician_keywords = ["岸田", "総理", "大臣", "議員"]
                if any(keyword in item.get("title", "") for keyword in politician_keywords):
                    item["relevance_score"] = 0.9
                    results.append(item)
            
            # 政党からの政治家関連情報
            major_parties = ["自由民主党", "立憲民主党"]
            for party in major_parties:
                party_news = self.party_scraper.scrape_party_news(party, 3)
                for item in party_news:
                    item["relevance_score"] = 0.7
                    results.append(item)
            
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"政治家情報検索エラー: {str(e)}")
            return results
    
    def _search_party_info(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """政党情報を検索"""
        results = []
        
        try:
            # クエリから政党名を推定
            target_parties = []
            for party_name in self.party_scraper.party_sites.keys():
                if party_name in query or any(alias in query for alias in [party_name[:2], party_name[-2:]]):
                    target_parties.append(party_name)
            
            # 対象政党が見つからない場合は主要政党を対象
            if not target_parties:
                target_parties = ["自由民主党", "立憲民主党", "日本維新の会", "公明党"]
            
            # 対象政党の包括的データ取得
            for party in target_parties[:3]:  # 最大3政党
                party_data = self.party_scraper.get_comprehensive_party_data(party, 3)
                
                for category, items in party_data.items():
                    for item in items:
                        item["relevance_score"] = 0.9 if party in query else 0.7
                        item["data_category"] = category
                        results.append(item)
            
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"政党情報検索エラー: {str(e)}")
            return results
    
    def _search_scandal_info(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """スキャンダル関連情報を検索"""
        results = []
        
        try:
            # 政府の説明・対応
            gov_data = self.government_scraper.scrape_kantei_news(max_results // 2)
            for item in gov_data:
                scandal_keywords = ["説明", "調査", "責任", "疑惑", "問題"]
                if any(keyword in item.get("title", "") for keyword in scandal_keywords):
                    item["relevance_score"] = 0.8
                    results.append(item)
            
            # 野党の追及・声明
            opposition_parties = ["立憲民主党", "日本共産党", "日本維新の会"]
            for party in opposition_parties:
                party_statements = self.party_scraper.scrape_party_statements(party, 2)
                for item in party_statements:
                    item["relevance_score"] = 0.7
                    results.append(item)
            
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"スキャンダル情報検索エラー: {str(e)}")
            return results
    
    def _search_coalition_info(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """連立政権関連情報を検索"""
        results = []
        
        try:
            # 与党（自民・公明）の情報
            coalition_parties = ["自由民主党", "公明党"]
            for party in coalition_parties:
                party_data = self.party_scraper.get_comprehensive_party_data(party, 3)
                
                for category, items in party_data.items():
                    for item in items:
                        if any(keyword in item.get("title", "") for keyword in ["連立", "協力", "合意"]):
                            item["relevance_score"] = 0.9
                            results.append(item)
            
            # 政府の連立関連発表
            gov_data = self.government_scraper.scrape_kantei_news(max_results // 2)
            for item in gov_data:
                item["relevance_score"] = 0.8
                results.append(item)
            
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"連立情報検索エラー: {str(e)}")
            return results
    
    def _search_general_political(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """一般的な政治情報を検索"""
        results = []
        
        try:
            # 政府データ
            gov_data = self.government_scraper.get_comprehensive_government_data(2)
            for category, items in gov_data.items():
                for item in items:
                    item["relevance_score"] = 0.8
                    item["source_category"] = category
                    results.append(item)
            
            # 主要政党データ
            major_parties = ["自由民主党", "立憲民主党"]
            for party in major_parties:
                party_news = self.party_scraper.scrape_party_news(party, 3)
                for item in party_news:
                    item["relevance_score"] = 0.7
                    results.append(item)
            
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"一般政治情報検索エラー: {str(e)}")
            return results
    
    def get_realtime_political_updates(self, max_results: int = 20) -> Dict[str, List[Dict[str, Any]]]:
        """
        リアルタイム政治情報を取得
        
        Args:
            max_results: 最大取得件数
            
        Returns:
            カテゴリ別政治情報辞書
        """
        political_updates = {}
        
        try:
            # 並行処理で複数ソースからデータ取得
            with ThreadPoolExecutor(max_workers=4) as executor:
                # 政府データ取得タスク
                gov_future = executor.submit(
                    self.government_scraper.get_comprehensive_government_data, 3
                )
                
                # 主要政党データ取得タスク
                party_futures = {}
                major_parties = ["自由民主党", "立憲民主党", "日本維新の会"]
                for party in major_parties:
                    party_futures[party] = executor.submit(
                        self.party_scraper.get_comprehensive_party_data, party, 2
                    )
                
                # 結果収集
                political_updates["government"] = gov_future.result()
                
                for party, future in party_futures.items():
                    political_updates[f"party_{party}"] = future.result()
            
            # 統計情報
            total_items = 0
            for category, data in political_updates.items():
                if isinstance(data, dict):
                    total_items += sum(len(items) for items in data.values())
                else:
                    total_items += len(data)
            
            logger.info(f"リアルタイム政治情報取得完了: 総計{total_items}件")
            
            return political_updates
            
        except Exception as e:
            logger.error(f"リアルタイム政治情報取得エラー: {str(e)}")
            return political_updates
    
    def test_all_connections(self) -> Dict[str, bool]:
        """全スクレイパーの接続テスト"""
        test_results = {}
        
        try:
            test_results["government"] = self.government_scraper.test_connection()
            test_results["party"] = self.party_scraper.test_connection()
            
            overall_status = all(test_results.values())
            test_results["overall"] = overall_status
            
            logger.info(f"政治スクレイパー接続テスト完了: {test_results}")
            return test_results
            
        except Exception as e:
            logger.error(f"接続テストエラー: {str(e)}")
            return {"overall": False, "error": str(e)}
    
    def _merge_and_rank_results(self, results: List[Dict[str, Any]], intent: str) -> List[Dict[str, Any]]:
        """結果を統合し最終ランキングを適用"""
        try:
            # URL重複除去
            seen_urls = set()
            unique_results = []
            
            for result in results:
                url = result.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_results.append(result)
            
            # 最終スコア計算
            for result in unique_results:
                final_score = 0.0
                
                # 既存スコアがある場合は使用
                if "final_political_score" in result:
                    final_score += result["final_political_score"] * 0.6
                
                # 信頼性スコア
                reliability = result.get("reliability_score", 0.5)
                final_score += reliability * 0.3
                
                # 関連性スコア
                relevance = result.get("relevance_score", 0.5)
                final_score += relevance * 0.1
                
                result["final_score"] = final_score
            
            # 最終スコア順でソート
            ranked_results = sorted(unique_results, key=lambda x: x.get("final_score", 0), reverse=True)
            
            return ranked_results
            
        except Exception as e:
            logger.error(f"結果統合エラー: {str(e)}")
            return results
    
    def search_comprehensive_political_data(self, 
                                          query: str, 
                                          max_results: int = 20) -> Dict[str, List[Dict[str, Any]]]:
        """
        包括的な政治データ検索
        
        Args:
            query: 検索クエリ
            max_results: 最大取得件数
            
        Returns:
            ソース別政治データ辞書
        """
        try:
            comprehensive_data = {}
            
            # 並行処理で各ソースから取得
            with ThreadPoolExecutor(max_workers=6) as executor:
                # 検索エンジン結果
                search_future = executor.submit(
                    self.political_search_engine.search_political_content,
                    query, "general_political", max_results // 4
                )
                
                # 政府データ
                gov_future = executor.submit(
                    self.government_scraper.get_comprehensive_government_data, 3
                )
                
                # 政党データ（主要政党）
                party_future = executor.submit(
                    self.party_scraper.get_all_party_news, 2
                )
                
                # メディアデータ
                media_future = executor.submit(
                    self.media_scraper.scrape_political_headlines, 3
                )
                
                # SNSデータ
                social_future = executor.submit(
                    self.social_scraper.monitor_political_twitter, max_results // 4
                )
                
                # 政府専用検索
                gov_search_future = executor.submit(
                    self.political_search_engine.search_government_sources,
                    query, max_results // 4
                )
                
                # 結果収集
                try:
                    comprehensive_data["search_results"] = search_future.result()
                except Exception as e:
                    logger.warning(f"検索結果取得エラー: {str(e)}")
                    comprehensive_data["search_results"] = []
                
                try:
                    comprehensive_data["government_data"] = gov_future.result()
                except Exception as e:
                    logger.warning(f"政府データ取得エラー: {str(e)}")
                    comprehensive_data["government_data"] = {}
                
                try:
                    comprehensive_data["party_data"] = party_future.result()
                except Exception as e:
                    logger.warning(f"政党データ取得エラー: {str(e)}")
                    comprehensive_data["party_data"] = {}
                
                try:
                    comprehensive_data["media_data"] = media_future.result()
                except Exception as e:
                    logger.warning(f"メディアデータ取得エラー: {str(e)}")
                    comprehensive_data["media_data"] = {}
                
                try:
                    comprehensive_data["social_data"] = social_future.result()
                except Exception as e:
                    logger.warning(f"SNSデータ取得エラー: {str(e)}")
                    comprehensive_data["social_data"] = []
                
                try:
                    comprehensive_data["government_search"] = gov_search_future.result()
                except Exception as e:
                    logger.warning(f"政府検索結果取得エラー: {str(e)}")
                    comprehensive_data["government_search"] = []
            
            # 統計情報
            total_items = 0
            for key, data in comprehensive_data.items():
                if isinstance(data, list):
                    total_items += len(data)
                elif isinstance(data, dict):
                    total_items += sum(len(items) if isinstance(items, list) else 1 
                                     for items in data.values())
            
            comprehensive_data["meta"] = {
                "query": query,
                "total_items": total_items,
                "search_timestamp": datetime.now().isoformat(),
                "sources": list(comprehensive_data.keys())
            }
            
            logger.info(f"包括的政治データ検索完了: 総計{total_items}件")
            return comprehensive_data
            
        except Exception as e:
            logger.error(f"包括的政治データ検索エラー: {str(e)}")
            return {"error": str(e)}