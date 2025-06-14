"""
政治特化Lainアプリケーション
政治分析・予測に特化したメインアプリケーションクラス
"""
import logging
import time
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..utils.config import ConfigManager
from ..utils.exceptions import ConfigError, LLMError, ScraperError, AnalysisError
from ..political_llm.political_service import PoliticalLLMService
from ..political_data.political_database import PoliticalDatabaseManager
from ..political_scraper.political_scraper_service import PoliticalScraperService
from ..political_analysis.political_sentiment_analyzer import PoliticalSentimentAnalyzer
from ..political_analysis.political_reliability_scorer import PoliticalReliabilityScorer
from ..political_analysis.political_prediction_engine import PoliticalPredictionEngine
from ..utils.colors import ColorPrinter

logger = logging.getLogger(__name__)


class PoliticalLainApp:
    """政治特化Lainアプリケーションクラス"""
    
    def __init__(self, config_manager: ConfigManager, enable_color: bool = True):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
            enable_color: カラー出力有効化
        """
        self.config_manager = config_manager
        self.color_printer = ColorPrinter(enable_color)
        
        # コアサービス初期化
        try:
            self.llm_service = PoliticalLLMService(config_manager)
            self.database = PoliticalDatabaseManager(config_manager)
            self.scraper_service = PoliticalScraperService(config_manager)
            
            # 分析エンジン初期化
            self.sentiment_analyzer = PoliticalSentimentAnalyzer(config_manager, self.llm_service)
            self.reliability_scorer = PoliticalReliabilityScorer(config_manager, self.llm_service)
            self.prediction_engine = PoliticalPredictionEngine(
                config_manager, self.llm_service, 
                self.sentiment_analyzer, self.reliability_scorer
            )
            
            logger.info("政治特化Lainアプリケーション初期化完了")
            
        except Exception as e:
            logger.error(f"アプリケーション初期化エラー: {str(e)}")
            raise ConfigError(f"アプリケーション初期化に失敗しました: {str(e)}")
    
    def analyze_political_sentiment(self, 
                                  content: str, 
                                  source_type: str = "news",
                                  verbose: bool = False) -> Dict[str, Any]:
        """
        政治感情分析実行
        
        Args:
            content: 分析対象コンテンツ
            source_type: ソースタイプ
            verbose: 詳細表示
            
        Returns:
            感情分析結果
        """
        try:
            start_time = time.time()
            
            if verbose:
                self.color_printer.print_progress("政治感情分析を実行中...")
            
            result = self.sentiment_analyzer.analyze_political_sentiment(
                content, source_type
            )
            
            processing_time = time.time() - start_time
            result["processing_time"] = processing_time
            
            if verbose:
                self._display_sentiment_result(result)
            
            return result
            
        except Exception as e:
            logger.error(f"政治感情分析エラー: {str(e)}")
            raise AnalysisError(f"感情分析に失敗しました: {str(e)}")
    
    def evaluate_source_reliability(self, 
                                   source_url: str,
                                   content: Optional[str] = None,
                                   verbose: bool = False) -> Dict[str, Any]:
        """
        ソース信頼性評価実行
        
        Args:
            source_url: ソースURL
            content: コンテンツ（オプション）
            verbose: 詳細表示
            
        Returns:
            信頼性評価結果
        """
        try:
            start_time = time.time()
            
            if verbose:
                self.color_printer.print_progress("ソース信頼性評価を実行中...")
            
            # ソース評価
            source_result = self.reliability_scorer.evaluate_source_reliability(source_url)
            
            # コンテンツ評価（提供されている場合）
            content_result = None
            if content:
                content_result = self.reliability_scorer.evaluate_content_reliability(
                    content, source_result
                )
            
            processing_time = time.time() - start_time
            
            result = {
                "source_evaluation": source_result,
                "content_evaluation": content_result,
                "processing_time": processing_time
            }
            
            if verbose:
                self._display_reliability_result(result)
            
            return result
            
        except Exception as e:
            logger.error(f"信頼性評価エラー: {str(e)}")
            raise AnalysisError(f"信頼性評価に失敗しました: {str(e)}")
    
    def predict_support_rating(self, 
                             current_data: Optional[Dict] = None,
                             prediction_days: int = 30,
                             verbose: bool = False) -> Dict[str, Any]:
        """
        支持率予測実行
        
        Args:
            current_data: 現在のデータ（なければ収集）
            prediction_days: 予測期間
            verbose: 詳細表示
            
        Returns:
            支持率予測結果
        """
        try:
            start_time = time.time()
            
            if verbose:
                self.color_printer.print_progress("支持率予測を実行中...")
            
            # データ収集（提供されていない場合）
            if not current_data:
                current_data = self._collect_current_political_data()
            
            # 予測実行
            result = self.prediction_engine.predict_support_rating(
                current_data, prediction_days
            )
            
            processing_time = time.time() - start_time
            result["processing_time"] = processing_time
            
            if verbose:
                self._display_prediction_result(result, "支持率予測")
            
            return result
            
        except Exception as e:
            logger.error(f"支持率予測エラー: {str(e)}")
            raise AnalysisError(f"支持率予測に失敗しました: {str(e)}")
    
    def predict_election_outcome(self, 
                               current_data: Optional[Dict] = None,
                               prediction_days: int = 90,
                               verbose: bool = False) -> Dict[str, Any]:
        """
        選挙結果予測実行
        
        Args:
            current_data: 現在のデータ（なければ収集）
            prediction_days: 予測期間
            verbose: 詳細表示
            
        Returns:
            選挙結果予測
        """
        try:
            start_time = time.time()
            
            if verbose:
                self.color_printer.print_progress("選挙結果予測を実行中...")
            
            # データ収集（提供されていない場合）
            if not current_data:
                current_data = self._collect_current_political_data()
            
            # 予測実行
            result = self.prediction_engine.predict_election_outcome(
                current_data, prediction_days
            )
            
            processing_time = time.time() - start_time
            result["processing_time"] = processing_time
            
            if verbose:
                self._display_election_prediction(result)
            
            return result
            
        except Exception as e:
            logger.error(f"選挙結果予測エラー: {str(e)}")
            raise AnalysisError(f"選挙結果予測に失敗しました: {str(e)}")
    
    def analyze_comprehensive_political_data(self, 
                                          query: str,
                                          max_results: int = 20,
                                          verbose: bool = False) -> Dict[str, Any]:
        """
        包括的政治データ分析
        
        Args:
            query: 分析クエリ
            max_results: 最大取得件数
            verbose: 詳細表示
            
        Returns:
            包括的分析結果
        """
        try:
            start_time = time.time()
            
            if verbose:
                self.color_printer.print_progress(f"包括的政治データ分析を実行中: {query}")
            
            # データ収集
            comprehensive_data = self.scraper_service.search_comprehensive_political_data(
                query, max_results
            )
            
            # 各データソースの感情分析
            sentiment_results = {}
            for source, data in comprehensive_data.items():
                if isinstance(data, list) and data:
                    # 各データの感情分析
                    source_sentiments = []
                    for item in data[:5]:  # 最大5件
                        content = item.get("title", "") + " " + item.get("content", "")
                        if content.strip():
                            sentiment = self.sentiment_analyzer.analyze_political_sentiment(
                                content, self._classify_source_type(source)
                            )
                            source_sentiments.append(sentiment["final_sentiment_score"])
                    
                    if source_sentiments:
                        sentiment_results[source] = {
                            "average_sentiment": sum(source_sentiments) / len(source_sentiments),
                            "sentiment_count": len(source_sentiments)
                        }
            
            # 信頼性評価
            reliability_results = {}
            for source, data in comprehensive_data.items():
                if isinstance(data, list) and data:
                    # 代表的なデータの信頼性評価
                    sample_item = data[0]
                    if "url" in sample_item:
                        reliability = self.reliability_scorer.evaluate_source_reliability(
                            sample_item["url"]
                        )
                        reliability_results[source] = reliability["final_reliability_score"]
            
            processing_time = time.time() - start_time
            
            result = {
                "query": query,
                "raw_data": comprehensive_data,
                "sentiment_analysis": sentiment_results,
                "reliability_analysis": reliability_results,
                "processing_time": processing_time,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            if verbose:
                self._display_comprehensive_analysis(result)
            
            return result
            
        except Exception as e:
            logger.error(f"包括的政治データ分析エラー: {str(e)}")
            raise AnalysisError(f"包括的分析に失敗しました: {str(e)}")
    
    def generate_political_forecast(self, 
                                  forecast_days: int = 90,
                                  verbose: bool = False) -> Dict[str, Any]:
        """
        政治予測レポート生成
        
        Args:
            forecast_days: 予測期間
            verbose: 詳細表示
            
        Returns:
            包括的政治予測レポート
        """
        try:
            start_time = time.time()
            
            if verbose:
                self.color_printer.print_progress("包括的政治予測レポートを生成中...")
            
            # 現在の政治データ収集
            comprehensive_data = self._collect_comprehensive_political_data()
            
            # 包括的予測実行
            forecast = self.prediction_engine.generate_comprehensive_political_forecast(
                comprehensive_data, forecast_days
            )
            
            processing_time = time.time() - start_time
            forecast["processing_time"] = processing_time
            
            if verbose:
                self._display_forecast_report(forecast)
            
            return forecast
            
        except Exception as e:
            logger.error(f"政治予測レポート生成エラー: {str(e)}")
            raise AnalysisError(f"予測レポート生成に失敗しました: {str(e)}")
    
    def test_all_systems(self) -> Dict[str, bool]:
        """全システム接続テスト"""
        test_results = {}
        
        try:
            # LLMサービステスト
            self.color_printer.print_progress("LLMサービステスト中...")
            test_results["llm_service"] = self.llm_service.test_connection()
            
            # データベーステスト
            self.color_printer.print_progress("データベーステスト中...")
            test_results["database"] = self.database.test_connection()
            
            # スクレイパーサービステスト
            self.color_printer.print_progress("スクレイパーサービステスト中...")
            test_results["scraper_service"] = self.scraper_service.test_all_connections()["overall"]
            
            # 感情分析エンジンテスト
            self.color_printer.print_progress("感情分析エンジンテスト中...")
            test_results["sentiment_analyzer"] = self.sentiment_analyzer.test_sentiment_analysis()
            
            # 信頼性評価エンジンテスト
            self.color_printer.print_progress("信頼性評価エンジンテスト中...")
            test_results["reliability_scorer"] = self.reliability_scorer.test_reliability_scoring()
            
            # 予測エンジンテスト
            self.color_printer.print_progress("予測エンジンテスト中...")
            test_results["prediction_engine"] = self.prediction_engine.test_prediction_engine()
            
            # 総合判定
            test_results["overall"] = all(test_results.values())
            
            return test_results
            
        except Exception as e:
            logger.error(f"システムテストエラー: {str(e)}")
            test_results["overall"] = False
            test_results["error"] = str(e)
            return test_results
    
    def _collect_current_political_data(self) -> Dict[str, Any]:
        """現在の政治データ収集"""
        try:
            # リアルタイム政治データ取得
            political_updates = self.scraper_service.get_realtime_political_updates(15)
            
            # データを分析用形式に変換
            current_data = {
                "current_support_rate": 0.45,  # デフォルト値
                "government_data": political_updates.get("government", {}),
                "party_data": {},
                "media_data": {},
                "social_data": {},
                "timestamp": datetime.now().isoformat()
            }
            
            # 政党データの統合
            for key, value in political_updates.items():
                if key.startswith("party_"):
                    current_data["party_data"][key] = value
            
            return current_data
            
        except Exception as e:
            logger.warning(f"政治データ収集エラー: {str(e)}")
            # フォールバックデータ
            return {
                "current_support_rate": 0.45,
                "timestamp": datetime.now().isoformat(),
                "error": "データ収集に失敗しました"
            }
    
    def _collect_comprehensive_political_data(self) -> Dict[str, Any]:
        """包括的政治データ収集"""
        try:
            # 現在の政治状況を複数ソースから収集
            general_data = self.scraper_service.search_comprehensive_political_data("日本政治", 30)
            support_data = self.scraper_service.search_comprehensive_political_data("内閣支持率", 20)
            election_data = self.scraper_service.search_comprehensive_political_data("選挙", 15)
            
            return {
                "general_political_data": general_data,
                "support_rating_data": support_data,
                "election_data": election_data,
                "collection_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.warning(f"包括的データ収集エラー: {str(e)}")
            return {"error": "包括的データ収集に失敗しました"}
    
    def _classify_source_type(self, source: str) -> str:
        """ソースタイプ分類"""
        source_lower = source.lower()
        
        if "government" in source_lower or "search_results" in source_lower:
            return "news"
        elif "party" in source_lower:
            return "statement"
        elif "media" in source_lower:
            return "news"
        elif "social" in source_lower:
            return "social"
        else:
            return "news"
    
    def _display_sentiment_result(self, result: Dict[str, Any]):
        """感情分析結果表示"""
        self.color_printer.print_header("政治感情分析結果")
        
        score = result.get("final_sentiment_score", 0.0)
        confidence = result.get("confidence_level", 0.0)
        
        self.color_printer.print_result("感情スコア", f"{score:.2f}")
        self.color_printer.print_result("信頼度", f"{confidence:.2f}")
        
        if "basic_sentiment" in result:
            basic = result["basic_sentiment"]
            self.color_printer.print_result("基本感情", basic.get("dominant_sentiment", "unknown"))
        
        if "political_bias" in result:
            bias = result["political_bias"]
            self.color_printer.print_result("政治的バイアス", bias.get("dominant_bias", "neutral"))
    
    def _display_reliability_result(self, result: Dict[str, Any]):
        """信頼性評価結果表示"""
        self.color_printer.print_header("信頼性評価結果")
        
        if "source_evaluation" in result:
            source_eval = result["source_evaluation"]
            self.color_printer.print_result("ソース信頼性", f"{source_eval.get('final_reliability_score', 0):.2f}")
            self.color_printer.print_result("信頼性レベル", source_eval.get("reliability_level", "unknown"))
        
        if "content_evaluation" in result and result["content_evaluation"]:
            content_eval = result["content_evaluation"]
            self.color_printer.print_result("コンテンツ信頼性", f"{content_eval.get('overall_reliability_score', 0):.2f}")
            self.color_printer.print_result("信頼性グレード", content_eval.get("reliability_grade", "unknown"))
    
    def _display_prediction_result(self, result: Dict[str, Any], prediction_type: str):
        """予測結果表示"""
        self.color_printer.print_header(f"{prediction_type}結果")
        
        if "predicted_support_rate" in result:
            current = result.get("current_support_rate", 0)
            predicted = result.get("predicted_support_rate", 0)
            change = result.get("prediction_change", 0)
            
            self.color_printer.print_result("現在の支持率", f"{current:.1%}")
            self.color_printer.print_result("予測支持率", f"{predicted:.1%}")
            self.color_printer.print_result("変化", f"{change:+.1%}")
        
        confidence = result.get("confidence_score", 0)
        self.color_printer.print_result("予測信頼度", f"{confidence:.2f}")
        self.color_printer.print_result("信頼度レベル", result.get("confidence_level", "unknown"))
    
    def _display_election_prediction(self, result: Dict[str, Any]):
        """選挙予測結果表示"""
        self.color_printer.print_header("選挙結果予測")
        
        if "predicted_party_support" in result:
            support = result["predicted_party_support"]
            self.color_printer.print_info("政党支持率予測:")
            for party, rate in support.items():
                self.color_printer.print_result(party, f"{rate:.1%}")
        
        if "predicted_seat_distribution" in result:
            seats = result["predicted_seat_distribution"]
            self.color_printer.print_info("\n議席配分予測:")
            for party, seat_count in seats.items():
                self.color_printer.print_result(party, f"{seat_count}議席")
        
        confidence = result.get("confidence_score", 0)
        self.color_printer.print_result("\n予測信頼度", f"{confidence:.2f}")
    
    def _display_comprehensive_analysis(self, result: Dict[str, Any]):
        """包括的分析結果表示"""
        self.color_printer.print_header(f"包括的政治分析: {result.get('query', 'Unknown')}")
        
        if "sentiment_analysis" in result:
            self.color_printer.print_info("ソース別感情分析:")
            for source, sentiment in result["sentiment_analysis"].items():
                avg_sentiment = sentiment.get("average_sentiment", 0)
                self.color_printer.print_result(source, f"{avg_sentiment:.2f}")
        
        if "reliability_analysis" in result:
            self.color_printer.print_info("\nソース別信頼性:")
            for source, reliability in result["reliability_analysis"].items():
                self.color_printer.print_result(source, f"{reliability:.2f}")
    
    def _display_forecast_report(self, forecast: Dict[str, Any]):
        """予測レポート表示"""
        self.color_printer.print_header("包括的政治予測レポート")
        
        period = forecast.get("forecast_period_days", 0)
        self.color_printer.print_info(f"予測期間: {period}日")
        
        if "executive_summary" in forecast:
            summary = forecast["executive_summary"]
            self.color_printer.print_info("要約:")
            for point in summary:
                self.color_printer.print_result("•", point)
        
        if "support_rating_forecast" in forecast:
            support_forecast = forecast["support_rating_forecast"]
            predicted = support_forecast.get("predicted_support_rate", 0)
            self.color_printer.print_result("支持率予測", f"{predicted:.1%}")
        
        if "overall_risk_assessment" in forecast:
            risk = forecast["overall_risk_assessment"]
            self.color_printer.print_result("リスク評価", risk.get("overall_risk_level", "unknown"))