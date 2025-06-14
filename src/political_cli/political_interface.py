"""
政治特化インターフェース
政治分析システムの統合インターフェースとユーティリティ
"""
import logging
import time
import json
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from pathlib import Path

from ..utils.config import ConfigManager
from ..utils.colors import ColorPrinter
from .political_app import PoliticalLainApp

logger = logging.getLogger(__name__)


class PoliticalInterface:
    """政治分析システム統合インターフェースクラス"""
    
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
        
        logger.info("政治インターフェース初期化完了")
    
    def interactive_sentiment_analysis(self):
        """インタラクティブ感情分析モード"""
        self.color_printer.print_header("政治感情分析 - インタラクティブモード")
        self.color_printer.print_info("'exit' で終了、'help' でヘルプ表示")
        print()
        
        while True:
            try:
                # ユーザー入力
                content = input("分析するテキストを入力: ").strip()
                
                if not content:
                    continue
                elif content.lower() == 'exit':
                    self.color_printer.print_info("感情分析モードを終了します")
                    break
                elif content.lower() == 'help':
                    self._show_sentiment_help()
                    continue
                
                # ソースタイプ選択
                source_type = self._get_source_type_input()
                
                # 感情分析実行
                self.color_printer.print_progress("感情分析実行中...")
                result = self.app.analyze_political_sentiment(content, source_type, verbose=True)
                
                # 詳細表示オプション
                if self._ask_yes_no("詳細情報を表示しますか？"):
                    self._show_detailed_sentiment_result(result)
                
                print()
                
            except KeyboardInterrupt:
                self.color_printer.print_info("\n感情分析モードを終了します")
                break
            except Exception as e:
                self.color_printer.print_error(f"エラー: {str(e)}")
                continue
    
    def interactive_reliability_evaluation(self):
        """インタラクティブ信頼性評価モード"""
        self.color_printer.print_header("信頼性評価 - インタラクティブモード")
        self.color_printer.print_info("'exit' で終了、'help' でヘルプ表示")
        print()
        
        while True:
            try:
                # URL入力
                url = input("評価するURLを入力: ").strip()
                
                if not url:
                    continue
                elif url.lower() == 'exit':
                    self.color_printer.print_info("信頼性評価モードを終了します")
                    break
                elif url.lower() == 'help':
                    self._show_reliability_help()
                    continue
                
                # コンテンツ入力（オプション）
                content = None
                if self._ask_yes_no("コンテンツも評価しますか？"):
                    content = input("コンテンツを入力: ").strip()
                
                # 信頼性評価実行
                self.color_printer.print_progress("信頼性評価実行中...")
                result = self.app.evaluate_source_reliability(url, content, verbose=True)
                
                # 詳細表示オプション
                if self._ask_yes_no("詳細情報を表示しますか？"):
                    self._show_detailed_reliability_result(result)
                
                print()
                
            except KeyboardInterrupt:
                self.color_printer.print_info("\n信頼性評価モードを終了します")
                break
            except Exception as e:
                self.color_printer.print_error(f"エラー: {str(e)}")
                continue
    
    def interactive_prediction_mode(self):
        """インタラクティブ予測モード"""
        self.color_printer.print_header("政治予測 - インタラクティブモード")
        self.color_printer.print_info("予測タイプを選択してください")
        print()
        
        while True:
            try:
                # 予測タイプ選択
                prediction_type = self._get_prediction_type_input()
                
                if prediction_type == 'exit':
                    self.color_printer.print_info("予測モードを終了します")
                    break
                elif prediction_type == 'support_rating':
                    self._interactive_support_prediction()
                elif prediction_type == 'election':
                    self._interactive_election_prediction()
                elif prediction_type == 'comprehensive':
                    self._interactive_comprehensive_forecast()
                
                print()
                
            except KeyboardInterrupt:
                self.color_printer.print_info("\n予測モードを終了します")
                break
            except Exception as e:
                self.color_printer.print_error(f"エラー: {str(e)}")
                continue
    
    def batch_process_files(self, 
                          input_dir: str, 
                          output_dir: str,
                          process_type: str = "sentiment",
                          file_pattern: str = "*.txt") -> Dict[str, Any]:
        """
        ファイルのバッチ処理
        
        Args:
            input_dir: 入力ディレクトリ
            output_dir: 出力ディレクトリ
            process_type: 処理タイプ（sentiment, reliability, analysis）
            file_pattern: ファイルパターン
            
        Returns:
            処理結果サマリー
        """
        try:
            input_path = Path(input_dir)
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # ファイル一覧取得
            files = list(input_path.glob(file_pattern))
            
            if not files:
                self.color_printer.print_warning(f"処理対象ファイルが見つかりません: {input_dir}/{file_pattern}")
                return {"error": "ファイルが見つかりません"}
            
            self.color_printer.print_progress(f"バッチ処理開始: {len(files)}ファイル")
            
            results = []
            processed_count = 0
            error_count = 0
            
            for file_path in files:
                try:
                    self.color_printer.print_progress(f"処理中: {file_path.name}")
                    
                    # ファイル読み込み
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    
                    if not content:
                        continue
                    
                    # 処理実行
                    if process_type == "sentiment":
                        result = self.app.analyze_political_sentiment(content)
                    elif process_type == "reliability" and content.startswith("http"):
                        result = self.app.evaluate_source_reliability(content)
                    elif process_type == "analysis":
                        result = self.app.analyze_comprehensive_political_data(content, max_results=10)
                    else:
                        self.color_printer.print_warning(f"未対応の処理タイプ: {process_type}")
                        continue
                    
                    # 結果保存
                    output_file = output_path / f"{file_path.stem}_{process_type}_result.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    
                    results.append({
                        "input_file": str(file_path),
                        "output_file": str(output_file),
                        "status": "success"
                    })
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"ファイル処理エラー ({file_path}): {str(e)}")
                    results.append({
                        "input_file": str(file_path),
                        "status": "error",
                        "error": str(e)
                    })
                    error_count += 1
            
            # サマリー作成
            summary = {
                "total_files": len(files),
                "processed_count": processed_count,
                "error_count": error_count,
                "process_type": process_type,
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
            # サマリー保存
            summary_file = output_path / f"batch_summary_{process_type}.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            self.color_printer.print_success(f"バッチ処理完了: {processed_count}件成功, {error_count}件エラー")
            
            return summary
            
        except Exception as e:
            logger.error(f"バッチ処理エラー: {str(e)}")
            return {"error": str(e)}
    
    def generate_analysis_report(self, 
                               topics: List[str],
                               output_file: str,
                               include_forecast: bool = True) -> bool:
        """
        分析レポート生成
        
        Args:
            topics: 分析トピックリスト
            output_file: 出力ファイル
            include_forecast: 予測を含めるか
            
        Returns:
            成功フラグ
        """
        try:
            self.color_printer.print_progress("分析レポートを生成中...")
            
            report = {
                "report_title": "政治分析レポート",
                "generation_timestamp": datetime.now().isoformat(),
                "topics": topics,
                "analyses": {},
                "summary": {}
            }
            
            # 各トピックの分析
            for topic in topics:
                self.color_printer.print_progress(f"分析中: {topic}")
                
                try:
                    analysis = self.app.analyze_comprehensive_political_data(topic, max_results=15)
                    report["analyses"][topic] = analysis
                    
                    time.sleep(1)  # レート制限対応
                    
                except Exception as e:
                    logger.warning(f"トピック分析エラー ({topic}): {str(e)}")
                    report["analyses"][topic] = {"error": str(e)}
            
            # 予測情報追加
            if include_forecast:
                self.color_printer.print_progress("予測情報を追加中...")
                try:
                    forecast = self.app.generate_political_forecast(90)
                    report["forecast"] = forecast
                except Exception as e:
                    logger.warning(f"予測情報エラー: {str(e)}")
                    report["forecast"] = {"error": str(e)}
            
            # レポート保存
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            self.color_printer.print_success(f"分析レポートを保存しました: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"レポート生成エラー: {str(e)}")
            self.color_printer.print_error(f"レポート生成エラー: {str(e)}")
            return False
    
    def _get_source_type_input(self) -> str:
        """ソースタイプ入力取得"""
        while True:
            print("ソースタイプを選択:")
            print("1. ニュース (news)")
            print("2. SNS (social)")  
            print("3. 公式発表 (official)")
            print("4. 政党声明 (statement)")
            
            choice = input("選択 (1-4, デフォルト:1): ").strip()
            
            if choice == '1' or choice == '':
                return 'news'
            elif choice == '2':
                return 'social'
            elif choice == '3':
                return 'official'
            elif choice == '4':
                return 'statement'
            else:
                print("無効な選択です。1-4を入力してください。")
    
    def _get_prediction_type_input(self) -> str:
        """予測タイプ入力取得"""
        while True:
            print("予測タイプを選択:")
            print("1. 内閣支持率予測 (support_rating)")
            print("2. 選挙結果予測 (election)")
            print("3. 包括的予測レポート (comprehensive)")
            print("4. 終了 (exit)")
            
            choice = input("選択 (1-4): ").strip()
            
            if choice == '1':
                return 'support_rating'
            elif choice == '2':
                return 'election'
            elif choice == '3':
                return 'comprehensive'
            elif choice == '4':
                return 'exit'
            else:
                print("無効な選択です。1-4を入力してください。")
    
    def _ask_yes_no(self, question: str) -> bool:
        """Yes/No質問"""
        while True:
            answer = input(f"{question} (y/n): ").strip().lower()
            if answer in ['y', 'yes', 'はい']:
                return True
            elif answer in ['n', 'no', 'いいえ']:
                return False
            else:
                print("'y' または 'n' で回答してください。")
    
    def _interactive_support_prediction(self):
        """インタラクティブ支持率予測"""
        try:
            # 予測期間入力
            while True:
                try:
                    days_input = input("予測期間（日数、デフォルト30日）: ").strip()
                    if not days_input:
                        prediction_days = 30
                    else:
                        prediction_days = int(days_input)
                    break
                except ValueError:
                    print("数値を入力してください。")
            
            # 予測実行
            self.color_printer.print_progress("支持率予測実行中...")
            result = self.app.predict_support_rating(prediction_days=prediction_days, verbose=True)
            
            # 詳細表示オプション
            if self._ask_yes_no("詳細な要因分析を表示しますか？"):
                self._show_detailed_prediction_factors(result)
            
        except Exception as e:
            self.color_printer.print_error(f"支持率予測エラー: {str(e)}")
    
    def _interactive_election_prediction(self):
        """インタラクティブ選挙予測"""
        try:
            # 予測期間入力
            while True:
                try:
                    days_input = input("予測期間（日数、デフォルト90日）: ").strip()
                    if not days_input:
                        prediction_days = 90
                    else:
                        prediction_days = int(days_input)
                    break
                except ValueError:
                    print("数値を入力してください。")
            
            # 予測実行
            self.color_printer.print_progress("選挙結果予測実行中...")
            result = self.app.predict_election_outcome(prediction_days=prediction_days, verbose=True)
            
            # 詳細表示オプション
            if self._ask_yes_no("連立可能性分析を表示しますか？"):
                self._show_coalition_analysis(result)
            
        except Exception as e:
            self.color_printer.print_error(f"選挙予測エラー: {str(e)}")
    
    def _interactive_comprehensive_forecast(self):
        """インタラクティブ包括的予測"""
        try:
            # 予測期間入力
            while True:
                try:
                    days_input = input("予測期間（日数、デフォルト90日）: ").strip()
                    if not days_input:
                        forecast_days = 90
                    else:
                        forecast_days = int(days_input)
                    break
                except ValueError:
                    print("数値を入力してください。")
            
            # レポート保存オプション
            save_report = None
            if self._ask_yes_no("レポートをファイルに保存しますか？"):
                save_report = input("保存ファイル名: ").strip()
                if not save_report:
                    save_report = f"political_forecast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # 予測実行
            self.color_printer.print_progress("包括的予測レポート生成中...")
            result = self.app.generate_political_forecast(forecast_days=forecast_days, verbose=True)
            
            # レポート保存
            if save_report:
                with open(save_report, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                self.color_printer.print_success(f"レポートを保存しました: {save_report}")
            
        except Exception as e:
            self.color_printer.print_error(f"包括的予測エラー: {str(e)}")
    
    def _show_sentiment_help(self):
        """感情分析ヘルプ表示"""
        print("\n=== 政治感情分析ヘルプ ===")
        print("• 政治関連テキストの感情・論調・バイアスを分析します")
        print("• -1.0（ネガティブ）から +1.0（ポジティブ）のスコアを出力")
        print("• 政治的バイアス（左派/右派/中立）も検出")
        print("• ソースタイプにより分析方法が調整されます")
        print()
    
    def _show_reliability_help(self):
        """信頼性評価ヘルプ表示"""
        print("\n=== 信頼性評価ヘルプ ===")
        print("• URLやコンテンツの信頼性を0.0-1.0のスコアで評価")
        print("• 政府サイト、主要メディア、SNS等でスコアが異なります")
        print("• フェイクニュース、センセーショナリズムを検出")
        print("• A+からFまでのグレード評価も提供")
        print()
    
    def _show_detailed_sentiment_result(self, result: Dict[str, Any]):
        """詳細感情分析結果表示"""
        self.color_printer.print_info("\n=== 詳細感情分析結果 ===")
        
        # 基本感情分析
        if "basic_sentiment" in result:
            basic = result["basic_sentiment"]
            self.color_printer.print_result("基本感情スコア", str(basic.get("scores", {})))
            
            detected = basic.get("detected_keywords", {})
            for sentiment_type, keywords in detected.items():
                if keywords:
                    self.color_printer.print_result(f"{sentiment_type}キーワード", ", ".join(keywords[:5]))
        
        # 政治バイアス
        if "political_bias" in result:
            bias = result["political_bias"]
            self.color_printer.print_result("バイアススコア", str(bias.get("bias_scores", {})))
            
            indicators = bias.get("detected_indicators", {})
            for bias_type, words in indicators.items():
                if words:
                    self.color_printer.print_result(f"{bias_type}指標", ", ".join(words[:3]))
        
        # 感情強度
        if "emotion_intensity" in result:
            intensity = result["emotion_intensity"]
            self.color_printer.print_result("感情強度", f"{intensity.get('intensity_score', 0):.2f}")
            self.color_printer.print_result("強度レベル", intensity.get("intensity_level", "unknown"))
    
    def _show_detailed_reliability_result(self, result: Dict[str, Any]):
        """詳細信頼性評価結果表示"""
        self.color_printer.print_info("\n=== 詳細信頼性評価結果 ===")
        
        # ソース評価
        if "source_evaluation" in result:
            source = result["source_evaluation"]
            self.color_printer.print_result("ソースカテゴリ", source.get("source_category", "unknown"))
            self.color_printer.print_result("ドメイン", source.get("domain", "unknown"))
            
            characteristics = source.get("source_characteristics", {})
            for key, value in characteristics.items():
                self.color_printer.print_result(key, str(value))
        
        # コンテンツ評価
        if "content_evaluation" in result and result["content_evaluation"]:
            content = result["content_evaluation"]
            
            # 各評価項目
            factual = content.get("factual_quality", {})
            self.color_printer.print_result("事実性スコア", f"{factual.get('factual_score', 0):.2f}")
            
            misinformation = content.get("misinformation_risk", {})
            self.color_printer.print_result("偽情報リスク", misinformation.get("risk_level", "unknown"))
            
            bias = content.get("bias_assessment", {})
            self.color_printer.print_result("バイアスレベル", bias.get("bias_level", "unknown"))
    
    def _show_detailed_prediction_factors(self, result: Dict[str, Any]):
        """詳細予測要因表示"""
        self.color_printer.print_info("\n=== 予測要因詳細分析 ===")
        
        if "impact_breakdown" in result:
            breakdown = result["impact_breakdown"]
            for factor, impact in breakdown.items():
                if isinstance(impact, (int, float)):
                    self.color_printer.print_result(factor, f"{impact:+.3f}")
        
        if "factors_summary" in result:
            factors = result["factors_summary"]
            self.color_printer.print_info("\n主要要因:")
            for factor in factors:
                self.color_printer.print_result("•", factor)
        
        if "llm_analysis" in result:
            llm = result["llm_analysis"]
            if "key_factors" in llm:
                self.color_printer.print_info("\nLLM分析による要因:")
                for factor in llm["key_factors"]:
                    self.color_printer.print_result("•", factor)
    
    def _show_coalition_analysis(self, result: Dict[str, Any]):
        """連立分析表示"""
        self.color_printer.print_info("\n=== 連立可能性分析 ===")
        
        if "coalition_analysis" in result:
            coalition = result["coalition_analysis"]
            
            majority = coalition.get("majority_threshold", 0)
            self.color_printer.print_result("過半数ライン", f"{majority}議席")
            
            scenarios = coalition.get("coalition_scenarios", [])
            for i, scenario in enumerate(scenarios, 1):
                parties = " + ".join(scenario.get("coalition", []))
                seats = scenario.get("seats", 0)
                probability = scenario.get("probability", 0)
                stability = scenario.get("stability", "unknown")
                
                self.color_printer.print_info(f"\nシナリオ {i}: {parties}")
                self.color_printer.print_result("議席数", f"{seats}議席")
                self.color_printer.print_result("実現可能性", f"{probability:.1%}")
                self.color_printer.print_result("安定性", stability)