"""
政治特化CLIコマンド
政治分析・予測システム専用のコマンドライン インターフェース
"""
import click
import json
import sys
import logging
from pathlib import Path
from typing import Optional

from ..utils.config import ConfigManager
from ..utils.exceptions import ConfigError, AnalysisError
from ..utils.colors import ColorPrinter, success, error, warning, info, highlight
from .political_app import PoliticalLainApp

logger = logging.getLogger(__name__)


@click.group()
@click.option('--config-dir', type=click.Path(exists=True), help='設定ファイルディレクトリのパス')
@click.option('--verbose', '-v', is_flag=True, help='詳細ログを有効化')
@click.option('--debug', is_flag=True, help='デバッグモードを有効化')
@click.option('--no-color', is_flag=True, help='カラー出力を無効化')
@click.pass_context
def political_cli(ctx, config_dir: Optional[str], verbose: bool, debug: bool, no_color: bool):
    """
    lain-politics - 日本政治予測システム
    
    政治データ収集・感情分析・信頼性評価・予測を統合した専門システム
    """
    # コンテキストオブジェクトを初期化
    ctx.ensure_object(dict)
    
    # ログレベルを設定
    if debug:
        log_level = logging.DEBUG
    elif verbose:
        log_level = logging.INFO
    else:
        log_level = logging.WARNING
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    
    try:
        # 設定管理を初期化
        config_manager = ConfigManager(config_dir)
        if not config_manager.validate_config():
            click.echo("設定ファイルに問題があります。設定を確認してください。", err=True)
            sys.exit(1)
        
        ctx.obj['config_manager'] = config_manager
        ctx.obj['verbose'] = verbose
        ctx.obj['debug'] = debug
        ctx.obj['enable_color'] = not no_color
        ctx.obj['color_printer'] = ColorPrinter(not no_color)
        
    except ConfigError as e:
        click.echo(f"設定エラー: {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"初期化エラー: {str(e)}", err=True)
        sys.exit(1)


@political_cli.command()
@click.argument('content', required=True)
@click.option('--source-type', type=click.Choice(['news', 'social', 'official', 'statement']), 
              default='news', help='ソースタイプ')
@click.option('--output-format', type=click.Choice(['text', 'json']), default='text', help='出力形式')
@click.pass_context
def sentiment(ctx, content: str, source_type: str, output_format: str):
    """
    政治感情分析を実行
    
    CONTENT: 分析対象のテキスト
    """
    try:
        config_manager = ctx.obj['config_manager']
        enable_color = ctx.obj['enable_color']
        verbose = ctx.obj['verbose']
        
        app = PoliticalLainApp(config_manager, enable_color=enable_color)
        
        result = app.analyze_political_sentiment(
            content=content,
            source_type=source_type,
            verbose=(output_format == 'text' and verbose)
        )
        
        if output_format == 'json':
            click.echo(json.dumps(result, ensure_ascii=False, indent=2))
        elif not verbose:
            # 簡潔な結果表示
            score = result.get("final_sentiment_score", 0.0)
            confidence = result.get("confidence_level", 0.0)
            bias = result.get("political_bias", {}).get("dominant_bias", "neutral")
            
            click.echo(f"感情スコア: {score:.2f}")
            click.echo(f"信頼度: {confidence:.2f}")
            click.echo(f"政治的バイアス: {bias}")
        
    except Exception as e:
        if ctx.obj['enable_color']:
            click.echo(error(f"感情分析エラー: {str(e)}"), err=True)
        else:
            click.echo(f"❌ 感情分析エラー: {str(e)}", err=True)
        sys.exit(1)


@political_cli.command()
@click.argument('source_url', required=True)
@click.option('--content', type=str, help='評価対象コンテンツ（オプション）')
@click.option('--output-format', type=click.Choice(['text', 'json']), default='text', help='出力形式')
@click.pass_context
def reliability(ctx, source_url: str, content: Optional[str], output_format: str):
    """
    ソース・コンテンツ信頼性評価を実行
    
    SOURCE_URL: 評価対象のソースURL
    """
    try:
        config_manager = ctx.obj['config_manager']
        enable_color = ctx.obj['enable_color']
        verbose = ctx.obj['verbose']
        
        app = PoliticalLainApp(config_manager, enable_color=enable_color)
        
        result = app.evaluate_source_reliability(
            source_url=source_url,
            content=content,
            verbose=(output_format == 'text' and verbose)
        )
        
        if output_format == 'json':
            click.echo(json.dumps(result, ensure_ascii=False, indent=2))
        elif not verbose:
            # 簡潔な結果表示
            source_score = result.get("source_evaluation", {}).get("final_reliability_score", 0)
            source_level = result.get("source_evaluation", {}).get("reliability_level", "unknown")
            
            click.echo(f"ソース信頼性: {source_score:.2f} ({source_level})")
            
            if result.get("content_evaluation"):
                content_score = result["content_evaluation"].get("overall_reliability_score", 0)
                content_grade = result["content_evaluation"].get("reliability_grade", "unknown")
                click.echo(f"コンテンツ信頼性: {content_score:.2f} (グレード: {content_grade})")
        
    except Exception as e:
        if ctx.obj['enable_color']:
            click.echo(error(f"信頼性評価エラー: {str(e)}"), err=True)
        else:
            click.echo(f"❌ 信頼性評価エラー: {str(e)}", err=True)
        sys.exit(1)


@political_cli.command()
@click.option('--prediction-days', type=int, default=30, help='予測期間（日数）')
@click.option('--data-file', type=click.Path(exists=True), help='入力データファイル（JSON）')
@click.option('--output-format', type=click.Choice(['text', 'json']), default='text', help='出力形式')
@click.pass_context
def support_rating(ctx, prediction_days: int, data_file: Optional[str], output_format: str):
    """
    内閣支持率予測を実行
    """
    try:
        config_manager = ctx.obj['config_manager']
        enable_color = ctx.obj['enable_color']
        verbose = ctx.obj['verbose']
        
        app = PoliticalLainApp(config_manager, enable_color=enable_color)
        
        # 入力データ読み込み
        current_data = None
        if data_file:
            with open(data_file, 'r', encoding='utf-8') as f:
                current_data = json.load(f)
        
        result = app.predict_support_rating(
            current_data=current_data,
            prediction_days=prediction_days,
            verbose=(output_format == 'text' and verbose)
        )
        
        if output_format == 'json':
            click.echo(json.dumps(result, ensure_ascii=False, indent=2))
        elif not verbose:
            # 簡潔な結果表示
            current = result.get("current_support_rate", 0)
            predicted = result.get("predicted_support_rate", 0)
            change = result.get("prediction_change", 0)
            confidence = result.get("confidence_score", 0)
            
            click.echo(f"現在の支持率: {current:.1%}")
            click.echo(f"予測支持率 ({prediction_days}日後): {predicted:.1%}")
            click.echo(f"変化: {change:+.1%}")
            click.echo(f"予測信頼度: {confidence:.2f}")
        
    except Exception as e:
        if ctx.obj['enable_color']:
            click.echo(error(f"支持率予測エラー: {str(e)}"), err=True)
        else:
            click.echo(f"❌ 支持率予測エラー: {str(e)}", err=True)
        sys.exit(1)


@political_cli.command()
@click.option('--prediction-days', type=int, default=90, help='予測期間（日数）')
@click.option('--data-file', type=click.Path(exists=True), help='入力データファイル（JSON）')
@click.option('--output-format', type=click.Choice(['text', 'json']), default='text', help='出力形式')
@click.pass_context
def election(ctx, prediction_days: int, data_file: Optional[str], output_format: str):
    """
    選挙結果予測を実行
    """
    try:
        config_manager = ctx.obj['config_manager']
        enable_color = ctx.obj['enable_color']
        verbose = ctx.obj['verbose']
        
        app = PoliticalLainApp(config_manager, enable_color=enable_color)
        
        # 入力データ読み込み
        current_data = None
        if data_file:
            with open(data_file, 'r', encoding='utf-8') as f:
                current_data = json.load(f)
        
        result = app.predict_election_outcome(
            current_data=current_data,
            prediction_days=prediction_days,
            verbose=(output_format == 'text' and verbose)
        )
        
        if output_format == 'json':
            click.echo(json.dumps(result, ensure_ascii=False, indent=2))
        elif not verbose:
            # 簡潔な結果表示
            if "predicted_party_support" in result:
                click.echo("政党支持率予測:")
                for party, rate in result["predicted_party_support"].items():
                    click.echo(f"  {party}: {rate:.1%}")
            
            if "predicted_seat_distribution" in result:
                click.echo("\n議席配分予測:")
                for party, seats in result["predicted_seat_distribution"].items():
                    click.echo(f"  {party}: {seats}議席")
            
            confidence = result.get("confidence_score", 0)
            click.echo(f"\n予測信頼度: {confidence:.2f}")
        
    except Exception as e:
        if ctx.obj['enable_color']:
            click.echo(error(f"選挙予測エラー: {str(e)}"), err=True)
        else:
            click.echo(f"❌ 選挙予測エラー: {str(e)}", err=True)
        sys.exit(1)


@political_cli.command()
@click.argument('query', required=True)
@click.option('--max-results', type=int, default=20, help='最大取得件数')
@click.option('--output-format', type=click.Choice(['text', 'json']), default='text', help='出力形式')
@click.pass_context
def analyze(ctx, query: str, max_results: int, output_format: str):
    """
    包括的政治データ分析を実行
    
    QUERY: 分析対象クエリ
    """
    try:
        config_manager = ctx.obj['config_manager']
        enable_color = ctx.obj['enable_color']
        verbose = ctx.obj['verbose']
        
        app = PoliticalLainApp(config_manager, enable_color=enable_color)
        
        result = app.analyze_comprehensive_political_data(
            query=query,
            max_results=max_results,
            verbose=(output_format == 'text' and verbose)
        )
        
        if output_format == 'json':
            click.echo(json.dumps(result, ensure_ascii=False, indent=2))
        elif not verbose:
            # 簡潔な結果表示
            click.echo(f"分析クエリ: {query}")
            
            if "sentiment_analysis" in result:
                click.echo("\nソース別感情分析:")
                for source, sentiment in result["sentiment_analysis"].items():
                    avg_sentiment = sentiment.get("average_sentiment", 0)
                    count = sentiment.get("sentiment_count", 0)
                    click.echo(f"  {source}: {avg_sentiment:+.2f} ({count}件)")
            
            if "reliability_analysis" in result:
                click.echo("\nソース別信頼性:")
                for source, reliability in result["reliability_analysis"].items():
                    click.echo(f"  {source}: {reliability:.2f}")
        
    except Exception as e:
        if ctx.obj['enable_color']:
            click.echo(error(f"包括的分析エラー: {str(e)}"), err=True)
        else:
            click.echo(f"❌ 包括的分析エラー: {str(e)}", err=True)
        sys.exit(1)


@political_cli.command()
@click.option('--forecast-days', type=int, default=90, help='予測期間（日数）')
@click.option('--output-format', type=click.Choice(['text', 'json']), default='text', help='出力形式')
@click.option('--save-report', type=click.Path(), help='レポート保存先ファイル')
@click.pass_context
def forecast(ctx, forecast_days: int, output_format: str, save_report: Optional[str]):
    """
    包括的政治予測レポートを生成
    """
    try:
        config_manager = ctx.obj['config_manager']
        enable_color = ctx.obj['enable_color']
        verbose = ctx.obj['verbose']
        
        app = PoliticalLainApp(config_manager, enable_color=enable_color)
        
        result = app.generate_political_forecast(
            forecast_days=forecast_days,
            verbose=(output_format == 'text' and verbose)
        )
        
        # レポート保存
        if save_report:
            with open(save_report, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            click.echo(f"レポートを保存しました: {save_report}")
        
        if output_format == 'json':
            click.echo(json.dumps(result, ensure_ascii=False, indent=2))
        elif not verbose:
            # 簡潔な結果表示
            click.echo(f"予測期間: {forecast_days}日")
            
            if "executive_summary" in result:
                click.echo("\n要約:")
                for point in result["executive_summary"]:
                    click.echo(f"• {point}")
            
            if "support_rating_forecast" in result:
                support = result["support_rating_forecast"]
                predicted = support.get("predicted_support_rate", 0)
                click.echo(f"\n支持率予測: {predicted:.1%}")
            
            if "overall_risk_assessment" in result:
                risk = result["overall_risk_assessment"]
                risk_level = risk.get("overall_risk_level", "unknown")
                click.echo(f"リスク評価: {risk_level}")
        
    except Exception as e:
        if ctx.obj['enable_color']:
            click.echo(error(f"予測レポート生成エラー: {str(e)}"), err=True)
        else:
            click.echo(f"❌ 予測レポート生成エラー: {str(e)}", err=True)
        sys.exit(1)


@political_cli.command()
@click.pass_context
def test(ctx):
    """
    全システム接続テストを実行
    """
    try:
        config_manager = ctx.obj['config_manager']
        enable_color = ctx.obj['enable_color']
        color_printer = ctx.obj['color_printer']
        
        app = PoliticalLainApp(config_manager, enable_color=enable_color)
        
        color_printer.print_header("政治分析システム接続テスト")
        
        test_results = app.test_all_systems()
        
        # 結果表示
        for system, result in test_results.items():
            if system == "overall":
                continue
            elif system == "error":
                color_printer.print_error(f"エラー: {result}")
                continue
            
            if result:
                color_printer.print_success(f"{system}: 成功")
            else:
                color_printer.print_error(f"{system}: 失敗")
        
        # 総合判定
        overall_result = test_results.get("overall", False)
        if overall_result:
            color_printer.print_success("全システムテスト成功")
        else:
            color_printer.print_error("システムテストに失敗した項目があります")
            sys.exit(1)
        
    except Exception as e:
        if ctx.obj['enable_color']:
            click.echo(error(f"システムテストエラー: {str(e)}"), err=True)
        else:
            click.echo(f"❌ システムテストエラー: {str(e)}", err=True)
        sys.exit(1)


@political_cli.command()
@click.pass_context
def config(ctx):
    """
    設定情報を表示
    """
    try:
        config_manager = ctx.obj['config_manager']
        color_printer = ctx.obj['color_printer']
        
        color_printer.print_header("lain-politics 設定情報")
        
        # LLM設定
        llm_config = config_manager.get_llm_config()
        color_printer.print_info("LM Studio設定:")
        color_printer.print_result("接続先", llm_config['lm_studio']['base_url'])
        color_printer.print_result("モデル", llm_config['lm_studio']['model_name'])
        color_printer.print_result("最大トークン", str(llm_config['lm_studio']['max_tokens']))
        
        # スクレイパー設定
        scraper_config = config_manager.get_scraper_config()
        color_printer.print_info("\nスクレイパー設定:")
        color_printer.print_result("検索エンジン", "Bing")
        color_printer.print_result("レート制限", f"{scraper_config['bing']['rate_limit']['requests_per_second']}req/s")
        color_printer.print_result("キャッシュTTL", f"{scraper_config['cache']['ttl_hours']}時間")
        
        # 政治分析設定
        color_printer.print_info("\n政治分析設定:")
        color_printer.print_result("感情分析", "有効")
        color_printer.print_result("信頼性評価", "有効")
        color_printer.print_result("予測エンジン", "有効")
        
    except Exception as e:
        if ctx.obj['enable_color']:
            click.echo(error(f"設定表示エラー: {str(e)}"), err=True)
        else:
            click.echo(f"❌ 設定表示エラー: {str(e)}", err=True)
        sys.exit(1)


@political_cli.command()
@click.argument('text_file', type=click.Path(exists=True))
@click.option('--source-type', type=click.Choice(['news', 'social', 'official', 'statement']), 
              default='news', help='ソースタイプ')
@click.option('--output-file', type=click.Path(), help='結果保存先ファイル')
@click.pass_context
def batch_sentiment(ctx, text_file: str, source_type: str, output_file: Optional[str]):
    """
    バッチ感情分析を実行
    
    TEXT_FILE: 分析対象テキストファイル（1行1コンテンツ）
    """
    try:
        config_manager = ctx.obj['config_manager']
        enable_color = ctx.obj['enable_color']
        color_printer = ctx.obj['color_printer']
        
        app = PoliticalLainApp(config_manager, enable_color=enable_color)
        
        # ファイル読み込み
        with open(text_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        
        color_printer.print_progress(f"バッチ感情分析開始: {len(lines)}件")
        
        results = []
        for i, content in enumerate(lines, 1):
            try:
                result = app.analyze_political_sentiment(content, source_type)
                results.append({
                    "index": i,
                    "content": content[:100] + "..." if len(content) > 100 else content,
                    "sentiment_score": result.get("final_sentiment_score", 0.0),
                    "confidence": result.get("confidence_level", 0.0),
                    "bias": result.get("political_bias", {}).get("dominant_bias", "neutral")
                })
                
                if i % 10 == 0:
                    color_printer.print_progress(f"処理中: {i}/{len(lines)}")
                
            except Exception as e:
                color_printer.print_warning(f"エラー (行{i}): {str(e)}")
                results.append({
                    "index": i,
                    "content": content[:100] + "..." if len(content) > 100 else content,
                    "error": str(e)
                })
        
        # 結果保存
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            color_printer.print_success(f"結果を保存しました: {output_file}")
        else:
            # 簡潔な結果表示
            for result in results:
                if "error" in result:
                    click.echo(f"{result['index']}: エラー - {result['error']}")
                else:
                    click.echo(f"{result['index']}: {result['sentiment_score']:+.2f} ({result['bias']})")
        
        color_printer.print_success(f"バッチ感情分析完了: {len(results)}件")
        
    except Exception as e:
        if ctx.obj['enable_color']:
            click.echo(error(f"バッチ感情分析エラー: {str(e)}"), err=True)
        else:
            click.echo(f"❌ バッチ感情分析エラー: {str(e)}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    political_cli()