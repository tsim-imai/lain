"""
政治特化システム統合テスト
全コンポーネントの統合テストとベンチマーク
"""
import logging
import time
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..utils.config import ConfigManager
from ..utils.colors import ColorPrinter
from .political_app import PoliticalLainApp

logger = logging.getLogger(__name__)


class PoliticalSystemIntegrationTest:
    """政治システム統合テストクラス"""
    
    def __init__(self, config_manager: ConfigManager, enable_color: bool = True):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
            enable_color: カラー出力有効化
        """
        self.config_manager = config_manager
        self.color_printer = ColorPrinter(enable_color)
        self.app = PoliticalLainApp(config_manager, enable_color)
        self.test_results = {}
        
        logger.info("政治システム統合テスト初期化完了")
    
    def run_all_tests(self, save_report: bool = True) -> Dict[str, Any]:
        """
        全統合テスト実行
        
        Args:
            save_report: テストレポート保存
            
        Returns:
            統合テスト結果
        """
        start_time = time.time()
        
        self.color_printer.print_header("政治システム統合テスト開始")
        
        # テスト実行
        test_suite = [
            ("基本接続テスト", self._test_basic_connections),
            ("感情分析テスト", self._test_sentiment_analysis),
            ("信頼性評価テスト", self._test_reliability_scoring),
            ("支持率予測テスト", self._test_support_prediction),
            ("選挙予測テスト", self._test_election_prediction),
            ("包括的分析テスト", self._test_comprehensive_analysis),
            ("パフォーマンステスト", self._test_performance),
            ("データ品質テスト", self._test_data_quality),
            ("エラーハンドリングテスト", self._test_error_handling)
        ]
        
        for test_name, test_func in test_suite:
            try:
                self.color_printer.print_progress(f"実行中: {test_name}")
                result = test_func()
                self.test_results[test_name] = result
                
                if result.get("success", False):
                    self.color_printer.print_success(f"{test_name}: 成功")
                else:
                    self.color_printer.print_error(f"{test_name}: 失敗")
                    
            except Exception as e:
                logger.error(f"{test_name}エラー: {str(e)}")
                self.test_results[test_name] = {"success": False, "error": str(e)}
                self.color_printer.print_error(f"{test_name}: エラー - {str(e)}")
        
        # 総合結果
        total_time = time.time() - start_time
        success_count = sum(1 for result in self.test_results.values() if result.get("success", False))
        total_count = len(self.test_results)
        
        overall_result = {
            "test_timestamp": datetime.now().isoformat(),
            "total_execution_time": total_time,
            "tests_passed": success_count,
            "tests_total": total_count,
            "success_rate": success_count / total_count if total_count > 0 else 0,
            "individual_results": self.test_results
        }
        
        # 結果表示
        self.color_printer.print_header("統合テスト結果サマリー")
        self.color_printer.print_result("実行時間", f"{total_time:.2f}秒")
        self.color_printer.print_result("成功率", f"{overall_result['success_rate']:.1%}")
        self.color_printer.print_result("成功テスト", f"{success_count}/{total_count}")
        
        if overall_result['success_rate'] >= 0.8:
            self.color_printer.print_success("統合テスト: 全体的に良好")
        elif overall_result['success_rate'] >= 0.6:
            self.color_printer.print_warning("統合テスト: 一部問題あり")
        else:
            self.color_printer.print_error("統合テスト: 重大な問題あり")
        
        # レポート保存
        if save_report:
            report_file = f"integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(overall_result, f, ensure_ascii=False, indent=2)
            self.color_printer.print_info(f"テストレポート保存: {report_file}")
        
        return overall_result
    
    def _test_basic_connections(self) -> Dict[str, Any]:
        """基本接続テスト"""
        try:
            results = self.app.test_all_systems()
            
            return {
                "success": results.get("overall", False),
                "component_results": results,
                "test_time": time.time()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_sentiment_analysis(self) -> Dict[str, Any]:
        """感情分析テスト"""
        try:
            test_cases = [
                {
                    "content": "岸田内閣の支持率が上昇し、経済政策に対する評価が高まっています。",
                    "expected_sentiment": "positive",
                    "source_type": "news"
                },
                {
                    "content": "政府の対応に批判が集まり、野党は責任追及を強めています。",
                    "expected_sentiment": "negative", 
                    "source_type": "news"
                },
                {
                    "content": "政府は本日、新たな政策について検討していることを発表しました。",
                    "expected_sentiment": "neutral",
                    "source_type": "official"
                }
            ]
            
            results = []
            for test_case in test_cases:
                start_time = time.time()
                
                result = self.app.analyze_political_sentiment(
                    test_case["content"], 
                    test_case["source_type"]
                )
                
                execution_time = time.time() - start_time
                
                # 結果評価
                sentiment_score = result.get("final_sentiment_score", 0.0)
                expected = test_case["expected_sentiment"]
                
                if expected == "positive":
                    correct = sentiment_score > 0.1
                elif expected == "negative":
                    correct = sentiment_score < -0.1
                else:  # neutral
                    correct = abs(sentiment_score) <= 0.1
                
                results.append({
                    "test_case": test_case["content"][:50] + "...",
                    "expected": expected,
                    "sentiment_score": sentiment_score,
                    "correct": correct,
                    "execution_time": execution_time,
                    "confidence": result.get("confidence_level", 0.0)
                })
            
            success_count = sum(1 for r in results if r["correct"])
            avg_time = sum(r["execution_time"] for r in results) / len(results)
            
            return {
                "success": success_count >= len(results) * 0.7,  # 70%以上正解
                "test_cases": results,
                "accuracy": success_count / len(results),
                "average_execution_time": avg_time
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_reliability_scoring(self) -> Dict[str, Any]:
        """信頼性評価テスト"""
        try:
            test_cases = [
                {
                    "url": "https://www.kantei.go.jp/jp/news/",
                    "expected_level": "very_high",
                    "description": "政府公式サイト"
                },
                {
                    "url": "https://www.nhk.or.jp/politics/",
                    "expected_level": "high",
                    "description": "NHK政治ニュース"
                },
                {
                    "url": "https://twitter.com/user/status",
                    "expected_level": "low",
                    "description": "SNS投稿"
                }
            ]
            
            results = []
            for test_case in test_cases:
                start_time = time.time()
                
                result = self.app.evaluate_source_reliability(test_case["url"])
                
                execution_time = time.time() - start_time
                
                # 結果評価
                source_eval = result.get("source_evaluation", {})
                reliability_level = source_eval.get("reliability_level", "unknown")
                reliability_score = source_eval.get("final_reliability_score", 0.0)
                
                # 期待レベルとの比較
                level_scores = {
                    "very_low": 0.2, "low": 0.4, "medium": 0.6, 
                    "high": 0.8, "very_high": 0.9
                }
                expected_score = level_scores.get(test_case["expected_level"], 0.5)
                score_diff = abs(reliability_score - expected_score)
                correct = score_diff < 0.3  # 30%以内の誤差を許容
                
                results.append({
                    "url": test_case["url"],
                    "description": test_case["description"],
                    "expected_level": test_case["expected_level"],
                    "actual_level": reliability_level,
                    "reliability_score": reliability_score,
                    "correct": correct,
                    "execution_time": execution_time
                })
            
            success_count = sum(1 for r in results if r["correct"])
            avg_time = sum(r["execution_time"] for r in results) / len(results)
            
            return {
                "success": success_count >= len(results) * 0.7,
                "test_cases": results,
                "accuracy": success_count / len(results),
                "average_execution_time": avg_time
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_support_prediction(self) -> Dict[str, Any]:
        """支持率予測テスト"""
        try:
            # テスト用データ
            test_data = {
                "current_support_rate": 0.45,
                "sentiment_data": {"average_sentiment": 0.1, "volatility": 0.3},
                "media_data": {"coverage_volume": 0.6, "average_sentiment": 0.05},
                "government_data": {"policy_success_rate": 0.7, "announcement_frequency": 0.5},
                "social_data": {"engagement_level": 0.5, "average_sentiment": 0.0}
            }
            
            start_time = time.time()
            result = self.app.predict_support_rating(test_data, prediction_days=30)
            execution_time = time.time() - start_time
            
            # 結果検証
            predicted_rate = result.get("predicted_support_rate", 0)
            confidence = result.get("confidence_score", 0)
            
            # 基本的な妥当性チェック
            valid_prediction = (
                0.1 <= predicted_rate <= 0.9 and  # 10%-90%の範囲内
                confidence >= 0.3 and  # 最低限の信頼度
                "impact_breakdown" in result  # 影響度分析が含まれる
            )
            
            return {
                "success": valid_prediction,
                "predicted_support_rate": predicted_rate,
                "confidence_score": confidence,
                "execution_time": execution_time,
                "has_breakdown": "impact_breakdown" in result
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_election_prediction(self) -> Dict[str, Any]:
        """選挙予測テスト"""
        try:
            # テスト用データ
            test_data = {
                "party_support": {
                    "自由民主党": 0.35,
                    "立憲民主党": 0.18,
                    "日本維新の会": 0.12,
                    "公明党": 0.08,
                    "その他": 0.27
                },
                "sentiment_data": {"average_sentiment": 0.0},
                "media_data": {"coverage_intensity": 0.6}
            }
            
            start_time = time.time()
            result = self.app.predict_election_outcome(test_data, prediction_days=90)
            execution_time = time.time() - start_time
            
            # 結果検証
            predicted_support = result.get("predicted_party_support", {})
            seat_distribution = result.get("predicted_seat_distribution", {})
            confidence = result.get("confidence_score", 0)
            
            # 基本的な妥当性チェック
            valid_prediction = (
                len(predicted_support) >= 4 and  # 主要政党をカバー
                abs(sum(predicted_support.values()) - 1.0) < 0.01 and  # 合計が1.0
                sum(seat_distribution.values()) == 465 and  # 総議席数が正しい
                confidence >= 0.3
            )
            
            return {
                "success": valid_prediction,
                "predicted_parties": len(predicted_support),
                "total_support": sum(predicted_support.values()),
                "total_seats": sum(seat_distribution.values()),
                "confidence_score": confidence,
                "execution_time": execution_time
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_comprehensive_analysis(self) -> Dict[str, Any]:
        """包括的分析テスト"""
        try:
            test_query = "岸田内閣"
            
            start_time = time.time()
            result = self.app.analyze_comprehensive_political_data(test_query, max_results=10)
            execution_time = time.time() - start_time
            
            # 結果検証
            has_raw_data = "raw_data" in result and result["raw_data"]
            has_sentiment = "sentiment_analysis" in result
            has_reliability = "reliability_analysis" in result
            
            valid_analysis = has_raw_data and has_sentiment and has_reliability
            
            return {
                "success": valid_analysis,
                "query": test_query,
                "has_raw_data": has_raw_data,
                "has_sentiment_analysis": has_sentiment,
                "has_reliability_analysis": has_reliability,
                "execution_time": execution_time
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_performance(self) -> Dict[str, Any]:
        """パフォーマンステスト"""
        try:
            test_cases = [
                ("短文感情分析", lambda: self.app.analyze_political_sentiment("政府の政策")),
                ("URL信頼性評価", lambda: self.app.evaluate_source_reliability("https://www.kantei.go.jp")),
                ("簡易予測", lambda: self.app.predict_support_rating({"current_support_rate": 0.45}, 7))
            ]
            
            results = []
            for test_name, test_func in test_cases:
                times = []
                errors = 0
                
                # 3回実行して平均を取る
                for _ in range(3):
                    try:
                        start_time = time.time()
                        test_func()
                        execution_time = time.time() - start_time
                        times.append(execution_time)
                    except Exception:
                        errors += 1
                
                if times:
                    avg_time = sum(times) / len(times)
                    results.append({
                        "test_name": test_name,
                        "average_time": avg_time,
                        "min_time": min(times),
                        "max_time": max(times),
                        "errors": errors
                    })
            
            # パフォーマンス判定
            avg_execution_time = sum(r["average_time"] for r in results) / len(results)
            performance_good = avg_execution_time < 10.0  # 10秒以内
            
            return {
                "success": performance_good,
                "average_execution_time": avg_execution_time,
                "performance_results": results,
                "performance_level": "good" if performance_good else "slow"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_data_quality(self) -> Dict[str, Any]:
        """データ品質テスト"""
        try:
            # データ収集テスト
            test_query = "政治"
            
            start_time = time.time()
            result = self.app.analyze_comprehensive_political_data(test_query, max_results=5)
            execution_time = time.time() - start_time
            
            # データ品質評価
            raw_data = result.get("raw_data", {})
            
            quality_metrics = {
                "data_sources": len(raw_data),
                "total_items": 0,
                "non_empty_items": 0,
                "avg_content_length": 0
            }
            
            all_items = []
            for source, data in raw_data.items():
                if isinstance(data, list):
                    quality_metrics["total_items"] += len(data)
                    for item in data:
                        if isinstance(item, dict):
                            content = str(item.get("title", "")) + str(item.get("content", ""))
                            if content.strip():
                                quality_metrics["non_empty_items"] += 1
                                all_items.append(len(content))
            
            if all_items:
                quality_metrics["avg_content_length"] = sum(all_items) / len(all_items)
            
            # 品質判定
            data_quality_good = (
                quality_metrics["data_sources"] >= 2 and
                quality_metrics["total_items"] >= 3 and
                quality_metrics["non_empty_items"] >= 2
            )
            
            return {
                "success": data_quality_good,
                "quality_metrics": quality_metrics,
                "execution_time": execution_time
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_error_handling(self) -> Dict[str, Any]:
        """エラーハンドリングテスト"""
        try:
            error_scenarios = [
                ("空文字列感情分析", lambda: self.app.analyze_political_sentiment("")),
                ("無効URL信頼性評価", lambda: self.app.evaluate_source_reliability("invalid-url")),
                ("不正データ予測", lambda: self.app.predict_support_rating({"invalid": "data"}))
            ]
            
            handled_errors = 0
            total_scenarios = len(error_scenarios)
            
            for scenario_name, error_func in error_scenarios:
                try:
                    result = error_func()
                    # エラーが発生せずに結果が返された場合も適切な処理とみなす
                    if result and "error" not in result:
                        handled_errors += 1
                except Exception:
                    # 例外がキャッチされた場合も適切な処理
                    handled_errors += 1
            
            error_handling_rate = handled_errors / total_scenarios
            
            return {
                "success": error_handling_rate >= 0.8,  # 80%以上適切に処理
                "error_handling_rate": error_handling_rate,
                "handled_scenarios": handled_errors,
                "total_scenarios": total_scenarios
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


def run_integration_test(config_dir: Optional[str] = None, enable_color: bool = True) -> Dict[str, Any]:
    """
    統合テスト実行関数
    
    Args:
        config_dir: 設定ディレクトリ
        enable_color: カラー出力有効化
        
    Returns:
        テスト結果
    """
    try:
        config_manager = ConfigManager(config_dir)
        tester = PoliticalSystemIntegrationTest(config_manager, enable_color)
        return tester.run_all_tests()
        
    except Exception as e:
        logger.error(f"統合テスト実行エラー: {str(e)}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # スタンドアロン実行
    import sys
    
    config_dir = sys.argv[1] if len(sys.argv) > 1 else None
    result = run_integration_test(config_dir)
    
    if not result.get("success", False):
        sys.exit(1)