"""
政治特化検索エンジン
既存検索エンジンに政治専門の検索戦略・フィルタリング・ランキングを追加
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..scraper.services import ScraperService
from ..utils.config import ConfigManager
from ..utils.exceptions import ScraperError

logger = logging.getLogger(__name__)


class PoliticalSearchEngine:
    """政治特化検索エンジンクラス"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
        """
        self.config_manager = config_manager
        self.base_scraper = ScraperService(config_manager)
        
        # 政治専門サイトの優先度設定
        self.political_site_weights = {
            # 政府公式サイト - 最高優先度
            "kantei.go.jp": 1.0,
            "gov.go.jp": 1.0,
            "soumu.go.jp": 0.95,
            "mof.go.jp": 0.95,
            "mofa.go.jp": 0.95,
            
            # 主要メディア - 高優先度
            "nhk.or.jp": 0.9,
            "kyodo.co.jp": 0.9,
            "jiji.com": 0.9,
            "asahi.com": 0.85,
            "yomiuri.co.jp": 0.85,
            "mainichi.jp": 0.8,
            "sankei.com": 0.8,
            "nikkei.com": 0.85,
            
            # 政党公式サイト - 高優先度
            "jimin.jp": 0.9,
            "cdp-japan.jp": 0.9,
            "o-ishin.jp": 0.85,
            "komei.or.jp": 0.85,
            "jcp.or.jp": 0.85,
            
            # 政治専門メディア - 中高優先度
            "seijiyama.jp": 0.8,
            "go2senkyo.com": 0.8,
            "blogos.com": 0.7,
            
            # 国会・公的機関
            "kokkai.ndl.go.jp": 0.95,
            "senkyo.go.jp": 0.9,
            
            # 一般メディア - 中優先度
            "yahoo.co.jp": 0.6,
            "google.com": 0.5,
            
            # SNS・個人ブログ - 低優先度
            "twitter.com": 0.4,
            "facebook.com": 0.4,
            "note.com": 0.5,
            "ameblo.jp": 0.3
        }
        
        # 政治専門キーワード重み付け
        self.political_keyword_weights = {
            # 高重要度キーワード
            "内閣総理大臣": 1.0,
            "総理大臣": 1.0,
            "首相": 1.0,
            "内閣支持率": 1.0,
            "世論調査": 0.9,
            "衆議院選挙": 1.0,
            "参議院選挙": 1.0,
            "総選挙": 1.0,
            "国会": 0.9,
            "政府": 0.8,
            "閣議決定": 0.9,
            
            # 政党関連
            "自由民主党": 0.9,
            "立憲民主党": 0.9,
            "日本維新の会": 0.8,
            "公明党": 0.8,
            "日本共産党": 0.8,
            
            # 政治家名
            "岸田文雄": 1.0,
            "泉健太": 0.8,
            "志位和夫": 0.8,
            "馬場伸幸": 0.7,
            
            # 政策分野
            "経済政策": 0.8,
            "外交政策": 0.8,
            "安全保障": 0.8,
            "憲法改正": 0.9,
            "消費税": 0.7,
            "年金": 0.7,
            "医療": 0.7,
            
            # 政治プロセス
            "法案": 0.8,
            "予算": 0.8,
            "政策": 0.7,
            "選挙": 0.9,
            "投票": 0.7
        }
        
        # 除外キーワード（政治と無関係な内容）
        self.exclusion_keywords = [
            "スポーツ", "芸能", "エンタメ", "ゲーム", "アニメ",
            "料理", "レシピ", "ファッション", "美容", "旅行",
            "映画", "音楽", "小説", "漫画", "天気", "占い"
        ]
        
        logger.info("政治特化検索エンジンを初期化")
    
    def search_political_content(self, 
                                query: str,
                                political_intent: str = "general_political",
                                max_results: int = 10,
                                time_filter: str = "all") -> List[Dict[str, Any]]:
        """
        政治特化検索を実行
        
        Args:
            query: 検索クエリ
            political_intent: 政治的意図
            max_results: 最大取得件数
            time_filter: 時間フィルタ (recent, week, month, all)
            
        Returns:
            政治関連検索結果のリスト
        """
        try:
            # 政治意図に基づくクエリ拡張
            enhanced_queries = self._enhance_query_for_political_intent(query, political_intent)
            
            # 複数クエリで並行検索
            all_results = []
            with ThreadPoolExecutor(max_workers=3) as executor:
                future_to_query = {}
                
                for enhanced_query in enhanced_queries[:3]:  # 最大3つのクエリ
                    future = executor.submit(
                        self._search_with_political_filtering,
                        enhanced_query,
                        max_results * 2  # 多めに取得してフィルタリング
                    )
                    future_to_query[future] = enhanced_query
                
                for future in as_completed(future_to_query):
                    enhanced_query = future_to_query[future]
                    try:
                        results = future.result()
                        all_results.extend(results)
                    except Exception as e:
                        logger.warning(f"拡張クエリ検索エラー ({enhanced_query}): {str(e)}")
            
            # 重複除去
            unique_results = self._remove_duplicates(all_results)
            
            # 政治関連性フィルタリング
            political_results = self._filter_political_relevance(unique_results)
            
            # 時間フィルタリング
            time_filtered_results = self._apply_time_filter(political_results, time_filter)
            
            # 政治特化ランキング
            ranked_results = self._rank_political_results(time_filtered_results, query, political_intent)
            
            logger.info(f"政治特化検索完了: {len(ranked_results)}件")
            return ranked_results[:max_results]
            
        except Exception as e:
            logger.error(f"政治特化検索エラー: {str(e)}")
            return []
    
    def _enhance_query_for_political_intent(self, query: str, political_intent: str) -> List[str]:
        """政治意図に基づくクエリ拡張"""
        enhanced_queries = [query]  # 元のクエリは常に含める
        
        intent_enhancements = {
            "support_rating": [
                f"{query} 支持率",
                f"{query} 世論調査",
                f"内閣支持率 {query}"
            ],
            "election_prediction": [
                f"{query} 選挙",
                f"{query} 選挙予測",
                f"衆議院選挙 {query}",
                f"参議院選挙 {query}"
            ],
            "policy_analysis": [
                f"{query} 政策",
                f"{query} 法案",
                f"政府 {query} 政策",
                f"{query} 施策"
            ],
            "political_news": [
                f"{query} 政治",
                f"{query} 国会",
                f"政府 {query}",
                f"{query} ニュース"
            ],
            "politician_info": [
                f"{query} 経歴",
                f"{query} 発言",
                f"{query} 政治家",
                f"{query} 略歴"
            ],
            "party_info": [
                f"{query} 政党",
                f"{query} 公約",
                f"{query} マニフェスト",
                f"{query} 党"
            ],
            "political_scandal": [
                f"{query} 疑惑",
                f"{query} 説明責任",
                f"{query} 問題",
                f"{query} 追及"
            ],
            "coalition_analysis": [
                f"{query} 連立",
                f"{query} 与党",
                f"自民公明 {query}",
                f"{query} 協力"
            ]
        }
        
        enhancements = intent_enhancements.get(political_intent, [f"{query} 政治"])
        enhanced_queries.extend(enhancements)
        
        return enhanced_queries
    
    def _search_with_political_filtering(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """政治フィルタリング付き検索"""
        try:
            # 基本検索実行
            results = self.base_scraper.search(query, max_results)
            
            # 各結果に政治関連スコアを付与
            for result in results:
                result["political_relevance_score"] = self._calculate_political_relevance(result)
                result["site_weight"] = self._get_site_weight(result.get("url", ""))
                result["political_keyword_score"] = self._calculate_keyword_score(result, query)
            
            return results
            
        except Exception as e:
            logger.error(f"政治フィルタリング検索エラー: {str(e)}")
            return []
    
    def _calculate_political_relevance(self, result: Dict[str, Any]) -> float:
        """政治関連性スコアを計算"""
        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()
        url = result.get("url", "").lower()
        
        relevance_score = 0.0
        
        # タイトルでの政治キーワードマッチ（高重要度）
        for keyword, weight in self.political_keyword_weights.items():
            if keyword.lower() in title:
                relevance_score += weight * 0.4  # タイトルは重要度高
        
        # スニペットでの政治キーワードマッチ（中重要度）
        for keyword, weight in self.political_keyword_weights.items():
            if keyword.lower() in snippet:
                relevance_score += weight * 0.2  # スニペットは中重要度
        
        # URLでの政治サイトマッチ
        site_weight = self._get_site_weight(url)
        relevance_score += site_weight * 0.3
        
        # 除外キーワードペナルティ
        for exclusion_keyword in self.exclusion_keywords:
            if exclusion_keyword.lower() in title + snippet:
                relevance_score -= 0.5
        
        return max(0.0, min(1.0, relevance_score))
    
    def _get_site_weight(self, url: str) -> float:
        """サイト重み付けを取得"""
        url_lower = url.lower()
        
        for domain, weight in self.political_site_weights.items():
            if domain in url_lower:
                return weight
        
        # 未知のサイトは中程度の重み
        return 0.5
    
    def _calculate_keyword_score(self, result: Dict[str, Any], query: str) -> float:
        """キーワードマッチングスコアを計算"""
        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()
        query_lower = query.lower()
        
        keyword_score = 0.0
        
        # 完全一致ボーナス
        if query_lower in title:
            keyword_score += 0.5
        if query_lower in snippet:
            keyword_score += 0.3
        
        # 部分一致
        query_words = query_lower.split()
        for word in query_words:
            if word in title:
                keyword_score += 0.2
            if word in snippet:
                keyword_score += 0.1
        
        return min(1.0, keyword_score)
    
    def _filter_political_relevance(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """政治関連性でフィルタリング"""
        # 政治関連性スコアが閾値以上の結果のみ残す
        threshold = 0.3
        filtered_results = [
            result for result in results 
            if result.get("political_relevance_score", 0) >= threshold
        ]
        
        logger.info(f"政治関連性フィルタリング: {len(results)} -> {len(filtered_results)}件")
        return filtered_results
    
    def _apply_time_filter(self, results: List[Dict[str, Any]], time_filter: str) -> List[Dict[str, Any]]:
        """時間フィルタを適用"""
        if time_filter == "all":
            return results
        
        # 時間フィルタリングの実装（簡略版）
        # 実際の実装では、検索結果の日付を解析して フィルタリング
        
        time_keywords = {
            "recent": ["今日", "昨日", "最新", "速報"],
            "week": ["今週", "先週", "週間"],
            "month": ["今月", "先月", "月間"]
        }
        
        if time_filter in time_keywords:
            keywords = time_keywords[time_filter]
            filtered_results = []
            
            for result in results:
                title_snippet = result.get("title", "") + " " + result.get("snippet", "")
                if any(keyword in title_snippet for keyword in keywords):
                    result["time_relevance"] = 1.0
                    filtered_results.append(result)
                else:
                    result["time_relevance"] = 0.5
                    filtered_results.append(result)
            
            return filtered_results
        
        return results
    
    def _rank_political_results(self, 
                               results: List[Dict[str, Any]], 
                               query: str, 
                               political_intent: str) -> List[Dict[str, Any]]:
        """政治特化ランキングを適用"""
        
        # 意図別重み調整
        intent_weights = {
            "support_rating": {"government": 1.2, "media": 1.0, "party": 0.8},
            "election_prediction": {"media": 1.1, "government": 1.0, "party": 0.9},
            "policy_analysis": {"government": 1.3, "party": 1.0, "media": 0.9},
            "political_news": {"media": 1.2, "government": 1.0, "party": 0.8},
            "politician_info": {"government": 1.1, "party": 1.0, "media": 1.0},
            "party_info": {"party": 1.3, "government": 0.9, "media": 1.0},
            "political_scandal": {"media": 1.2, "government": 0.8, "party": 0.7},
            "coalition_analysis": {"government": 1.1, "party": 1.1, "media": 1.0}
        }
        
        weights = intent_weights.get(political_intent, {"government": 1.0, "media": 1.0, "party": 1.0})
        
        for result in results:
            # 基本スコア計算
            base_score = (
                result.get("political_relevance_score", 0) * 0.4 +
                result.get("site_weight", 0.5) * 0.3 +
                result.get("political_keyword_score", 0) * 0.2 +
                result.get("time_relevance", 0.5) * 0.1
            )
            
            # サイト種別による重み調整
            url = result.get("url", "").lower()
            site_type_weight = 1.0
            
            if any(domain in url for domain in ["go.jp", "kantei", "gov"]):
                site_type_weight = weights.get("government", 1.0)
            elif any(domain in url for domain in ["jimin.jp", "cdp-japan.jp", "o-ishin.jp"]):
                site_type_weight = weights.get("party", 1.0)
            elif any(domain in url for domain in ["nhk.or.jp", "asahi.com", "yomiuri.co.jp"]):
                site_type_weight = weights.get("media", 1.0)
            
            # 最終スコア
            result["final_political_score"] = base_score * site_type_weight
        
        # スコア順でソート
        ranked_results = sorted(results, key=lambda x: x.get("final_political_score", 0), reverse=True)
        
        logger.info(f"政治特化ランキング完了: トップスコア={ranked_results[0].get('final_political_score', 0):.2f}")
        return ranked_results
    
    def _remove_duplicates(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """重複結果を除去"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get("url", "")
            if url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        logger.info(f"重複除去: {len(results)} -> {len(unique_results)}件")
        return unique_results
    
    def search_government_sources(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """政府ソース限定検索"""
        try:
            # 政府サイト限定検索クエリ
            gov_queries = [
                f"site:kantei.go.jp {query}",
                f"site:gov.go.jp {query}",
                f"site:soumu.go.jp {query}",
                f"site:mof.go.jp {query}",
                f"site:mofa.go.jp {query}"
            ]
            
            all_results = []
            for gov_query in gov_queries:
                try:
                    results = self.base_scraper.search(gov_query, max_results // len(gov_queries))
                    all_results.extend(results)
                except Exception as e:
                    logger.warning(f"政府サイト検索エラー ({gov_query}): {str(e)}")
            
            # 政府ソース専用ランキング
            for result in all_results:
                result["government_relevance"] = 1.0
                result["final_political_score"] = self._calculate_political_relevance(result)
            
            ranked_results = sorted(all_results, key=lambda x: x.get("final_political_score", 0), reverse=True)
            
            logger.info(f"政府ソース検索完了: {len(ranked_results)}件")
            return ranked_results[:max_results]
            
        except Exception as e:
            logger.error(f"政府ソース検索エラー: {str(e)}")
            return []
    
    def search_media_sources(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """メディアソース限定検索"""
        try:
            # 主要メディアサイト限定検索
            media_queries = [
                f"site:nhk.or.jp {query}",
                f"site:asahi.com {query}",
                f"site:yomiuri.co.jp {query}",
                f"site:mainichi.jp {query}",
                f"site:kyodo.co.jp {query}"
            ]
            
            all_results = []
            for media_query in media_queries:
                try:
                    results = self.base_scraper.search(media_query, max_results // len(media_queries))
                    all_results.extend(results)
                except Exception as e:
                    logger.warning(f"メディア検索エラー ({media_query}): {str(e)}")
            
            # メディアバイアス情報を付与
            for result in all_results:
                result["media_bias"] = self._get_media_bias(result.get("url", ""))
                result["final_political_score"] = self._calculate_political_relevance(result)
            
            ranked_results = sorted(all_results, key=lambda x: x.get("final_political_score", 0), reverse=True)
            
            logger.info(f"メディアソース検索完了: {len(ranked_results)}件")
            return ranked_results[:max_results]
            
        except Exception as e:
            logger.error(f"メディアソース検索エラー: {str(e)}")
            return []
    
    def _get_media_bias(self, url: str) -> float:
        """メディアの政治的バイアスを取得"""
        media_bias_map = {
            "sankei.com": 0.4,      # 右派
            "yomiuri.co.jp": 0.2,   # やや右派
            "nikkei.com": 0.1,      # やや右派
            "nhk.or.jp": 0.0,       # 中立
            "kyodo.co.jp": 0.0,     # 中立
            "jiji.com": 0.0,        # 中立
            "mainichi.jp": -0.2,    # やや左派
            "asahi.com": -0.3       # 左派
        }
        
        url_lower = url.lower()
        for domain, bias in media_bias_map.items():
            if domain in url_lower:
                return bias
        
        return 0.0  # 未知のメディアは中立扱い
    
    def get_political_search_suggestions(self, query: str) -> List[str]:
        """政治検索の候補を生成"""
        try:
            suggestions = []
            
            # 基本的な政治関連拡張
            base_suggestions = [
                f"{query} 政策",
                f"{query} 支持率",
                f"{query} 選挙",
                f"{query} 国会",
                f"{query} 法案"
            ]
            suggestions.extend(base_suggestions)
            
            # 政治家名を含む場合の拡張
            politician_keywords = ["岸田", "泉", "志位", "馬場", "玉木", "山本"]
            if any(name in query for name in politician_keywords):
                politician_suggestions = [
                    f"{query} 発言",
                    f"{query} 経歴",
                    f"{query} 政治活動"
                ]
                suggestions.extend(politician_suggestions)
            
            # 政党名を含む場合の拡張
            party_keywords = ["自民", "立憲", "維新", "公明", "共産"]
            if any(party in query for party in party_keywords):
                party_suggestions = [
                    f"{query} 公約",
                    f"{query} マニフェスト",
                    f"{query} 党首"
                ]
                suggestions.extend(party_suggestions)
            
            return suggestions[:10]  # 最大10件
            
        except Exception as e:
            logger.error(f"検索候補生成エラー: {str(e)}")
            return []
    
    def test_political_search(self) -> bool:
        """政治特化検索機能のテスト"""
        try:
            test_query = "岸田内閣"
            results = self.search_political_content(test_query, max_results=5)
            return len(results) > 0
        except Exception as e:
            logger.error(f"政治検索テスト失敗: {str(e)}")
            return False