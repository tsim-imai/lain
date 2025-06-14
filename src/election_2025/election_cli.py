"""
2025年選挙特化CLIコマンド
選挙区分析・候補者比較・情勢監視のコマンドラインインターフェース
"""
import logging
import click
import json
from typing import Optional
from datetime import datetime

from ..utils.config import ConfigManager
from ..utils.colors import ColorPrinter
from .constituency_data_collector import ConstituencyDataCollector
from .election_prediction_model import ElectionPredictionModel
from .candidate_database import CandidateDatabase, Candidate
from .election_monitor import ElectionMonitor

logger = logging.getLogger(__name__)


@click.group()
@click.pass_context
def election_2025(ctx):
    """2025年選挙分析・予測コマンド"""
    if ctx.obj is None:
        ctx.obj = {}
    
    # 設定とサービス初期化
    config_manager = ConfigManager()
    ctx.obj['config_manager'] = config_manager
    ctx.obj['color_printer'] = ColorPrinter(True)


@election_2025.command()
@click.option('--constituency-id', '-c', help='選挙区ID (例: 13001)')
@click.option('--prefecture', '-p', help='都道府県名')
@click.option('--district-type', help='選挙区タイプ (都市部/地方)')
@click.option('--competitiveness', help='競争状況 (激戦区/安定区)')
@click.option('--format', '-f', type=click.Choice(['json', 'text']), default='text', help='出力形式')
@click.pass_context
def constituency(ctx, constituency_id, prefecture, district_type, competitiveness, format):
    """選挙区情勢分析"""
    try:
        config_manager = ctx.obj['config_manager']
        color_printer = ctx.obj['color_printer']
        
        collector = ConstituencyDataCollector(config_manager)
        
        if constituency_id:
            # 特定選挙区の詳細分析
            summary = collector.get_constituency_summary(constituency_id)
            
            if not summary:
                color_printer.print_error(f"選挙区が見つかりません: {constituency_id}")
                return
            
            if format == 'json':
                click.echo(json.dumps(summary, ensure_ascii=False, indent=2))
            else:
                _display_constituency_summary(summary, color_printer)
        
        else:
            # 条件検索
            results = collector.search_constituencies(
                prefecture=prefecture,
                competitiveness=competitiveness,
                district_type=district_type
            )
            
            if format == 'json':
                click.echo(json.dumps(results, ensure_ascii=False, indent=2))
            else:
                _display_constituency_list(results, color_printer)
                
    except Exception as e:
        logger.error(f"選挙区分析エラー: {str(e)}")
        click.echo(f"エラー: {str(e)}", err=True)


@election_2025.command()
@click.option('--constituency-id', '-c', required=True, help='選挙区ID')
@click.option('--prediction-days', type=int, default=90, help='予測期間（日数）')
@click.option('--scenario', type=click.Choice(['optimistic', 'realistic', 'pessimistic']), default='realistic', help='予測シナリオ')
@click.option('--format', '-f', type=click.Choice(['json', 'text']), default='text', help='出力形式')
@click.pass_context
def predict(ctx, constituency_id, prediction_days, scenario, format):
    """選挙区別選挙予測"""
    try:
        config_manager = ctx.obj['config_manager']
        color_printer = ctx.obj['color_printer']
        
        # データ収集
        collector = ConstituencyDataCollector(config_manager)
        current_data = collector.get_constituency_summary(constituency_id)
        
        if not current_data:
            color_printer.print_error(f"選挙区データが見つかりません: {constituency_id}")
            return
        
        # 予測実行
        prediction_model = ElectionPredictionModel(config_manager)
        prediction = prediction_model.predict_constituency_election(
            constituency_id, current_data, prediction_date=datetime.now().isoformat()
        )
        
        if format == 'json':
            prediction_dict = {
                "constituency_id": prediction.constituency_id,
                "candidates": prediction.candidates,
                "prediction_date": prediction.prediction_date,
                "confidence_score": prediction.confidence_score,
                "key_factors": prediction.key_factors,
                "historical_comparison": prediction.historical_comparison
            }
            click.echo(json.dumps(prediction_dict, ensure_ascii=False, indent=2))
        else:
            _display_election_prediction(prediction, color_printer)
            
    except Exception as e:
        logger.error(f"選挙予測エラー: {str(e)}")
        click.echo(f"エラー: {str(e)}", err=True)


@election_2025.command()
@click.option('--scenario', type=click.Choice(['optimistic', 'realistic', 'pessimistic']), default='realistic', help='予測シナリオ')
@click.option('--format', '-f', type=click.Choice(['json', 'text']), default='text', help='出力形式')
@click.pass_context
def seats(ctx, scenario, format):
    """全体議席予測"""
    try:
        config_manager = ctx.obj['config_manager']
        color_printer = ctx.obj['color_printer']
        
        prediction_model = ElectionPredictionModel(config_manager)
        
        # 全体議席予測実行
        constituencies_data = {}  # 実際は全選挙区データを取得
        seat_predictions = prediction_model.predict_overall_seats(constituencies_data, scenario)
        
        if format == 'json':
            seat_dict = {}
            for party, prediction in seat_predictions.items():
                seat_dict[party] = {
                    "current_seats": prediction.current_seats,
                    "predicted_seats": prediction.predicted_seats,
                    "confidence_interval": prediction.confidence_interval,
                    "probability_distribution": prediction.probability_distribution
                }
            click.echo(json.dumps(seat_dict, ensure_ascii=False, indent=2))
        else:
            _display_seat_predictions(seat_predictions, color_printer, scenario)
            
    except Exception as e:
        logger.error(f"議席予測エラー: {str(e)}")
        click.echo(f"エラー: {str(e)}", err=True)


@election_2025.command()
@click.option('--scenario', type=click.Choice(['optimistic', 'realistic', 'pessimistic']), default='realistic', help='予測シナリオ')
@click.option('--threshold', type=int, default=233, help='過半数議席数')
@click.option('--format', '-f', type=click.Choice(['json', 'text']), default='text', help='出力形式')
@click.pass_context
def coalition(ctx, scenario, threshold, format):
    """連立政権シナリオ分析"""
    try:
        config_manager = ctx.obj['config_manager']
        color_printer = ctx.obj['color_printer']
        
        prediction_model = ElectionPredictionModel(config_manager)
        
        # 議席予測取得
        constituencies_data = {}
        seat_predictions = prediction_model.predict_overall_seats(constituencies_data, scenario)
        
        # 連立シナリオ分析
        coalition_analysis = prediction_model.analyze_coalition_scenarios(seat_predictions)
        
        if format == 'json':
            click.echo(json.dumps(coalition_analysis, ensure_ascii=False, indent=2))
        else:
            _display_coalition_analysis(coalition_analysis, color_printer, threshold)
            
    except Exception as e:
        logger.error(f"連立分析エラー: {str(e)}")
        click.echo(f"エラー: {str(e)}", err=True)


@election_2025.command()
@click.option('--constituency-id', '-c', help='選挙区ID')
@click.option('--party', '-p', help='政党名')
@click.option('--status', help='候補者ステータス (現職/元職/新人)')
@click.option('--min-support', type=float, help='最小支持率')
@click.option('--format', '-f', type=click.Choice(['json', 'text']), default='text', help='出力形式')
@click.pass_context
def candidates(ctx, constituency_id, party, status, min_support, format):
    """候補者検索・分析"""
    try:
        config_manager = ctx.obj['config_manager']
        color_printer = ctx.obj['color_printer']
        
        candidate_db = CandidateDatabase(config_manager)
        
        # 候補者検索
        candidates = candidate_db.search_candidates(
            party=party,
            status=status,
            constituency=constituency_id,
            min_support=min_support
        )
        
        if format == 'json':
            candidates_dict = []
            for candidate in candidates:
                candidates_dict.append({
                    "name": candidate.name,
                    "party": candidate.party,
                    "constituency_id": candidate.constituency_id,
                    "status": candidate.status,
                    "support_rate": candidate.support_rate,
                    "recognition_rate": candidate.recognition_rate
                })
            click.echo(json.dumps(candidates_dict, ensure_ascii=False, indent=2))
        else:
            _display_candidates_list(candidates, color_printer)
            
    except Exception as e:
        logger.error(f"候補者検索エラー: {str(e)}")
        click.echo(f"エラー: {str(e)}", err=True)


@election_2025.command()
@click.option('--candidate1-id', type=int, required=True, help='候補者1のID')
@click.option('--candidate2-id', type=int, required=True, help='候補者2のID')
@click.option('--format', '-f', type=click.Choice(['json', 'text']), default='text', help='出力形式')
@click.pass_context
def compare(ctx, candidate1_id, candidate2_id, format):
    """候補者間比較分析"""
    try:
        config_manager = ctx.obj['config_manager']
        color_printer = ctx.obj['color_printer']
        
        candidate_db = CandidateDatabase(config_manager)
        
        # 候補者比較実行
        comparison = candidate_db.compare_candidates(candidate1_id, candidate2_id)
        
        if 'error' in comparison:
            color_printer.print_error(comparison['error'])
            return
        
        if format == 'json':
            click.echo(json.dumps(comparison, ensure_ascii=False, indent=2))
        else:
            _display_candidate_comparison(comparison, color_printer)
            
    except Exception as e:
        logger.error(f"候補者比較エラー: {str(e)}")
        click.echo(f"エラー: {str(e)}", err=True)


@election_2025.command()
@click.option('--interval', type=click.Choice(['real_time', 'frequent', 'regular', 'daily']), default='frequent', help='監視間隔')
@click.option('--alerts-only', is_flag=True, help='アラートのみ表示')
@click.option('--format', '-f', type=click.Choice(['json', 'text']), default='text', help='出力形式')
@click.pass_context
def monitor(ctx, interval, alerts_only, format):
    """選挙情勢リアルタイム監視"""
    try:
        config_manager = ctx.obj['config_manager']
        color_printer = ctx.obj['color_printer']
        
        monitor = ElectionMonitor(config_manager)
        
        if alerts_only:
            # 現在のアラートのみ表示
            alerts = monitor.get_current_alerts()
            
            if format == 'json':
                alerts_dict = []
                for alert in alerts:
                    alerts_dict.append({
                        "alert_id": alert.alert_id,
                        "alert_type": alert.alert_type,
                        "severity": alert.severity,
                        "title": alert.title,
                        "timestamp": alert.timestamp
                    })
                click.echo(json.dumps(alerts_dict, ensure_ascii=False, indent=2))
            else:
                _display_alerts(alerts, color_printer)
        else:
            # 監視を開始
            color_printer.print_info(f"選挙情勢監視を開始します ({interval}間隔)")
            
            def alert_callback(alert):
                _display_single_alert(alert, color_printer)
            
            monitor.add_alert_callback(alert_callback)
            
            if monitor.start_monitoring(interval):
                color_printer.print_success("監視を開始しました。Ctrl+Cで停止できます。")
                try:
                    while True:
                        import time
                        time.sleep(1)
                except KeyboardInterrupt:
                    monitor.stop_monitoring()
                    color_printer.print_info("監視を停止しました")
            else:
                color_printer.print_error("監視の開始に失敗しました")
                
    except Exception as e:
        logger.error(f"監視エラー: {str(e)}")
        click.echo(f"エラー: {str(e)}", err=True)


@election_2025.command()
@click.option('--format', '-f', type=click.Choice(['json', 'text']), default='text', help='出力形式')
@click.pass_context
def report(ctx, format):
    """日次選挙情勢レポート"""
    try:
        config_manager = ctx.obj['config_manager']
        color_printer = ctx.obj['color_printer']
        
        monitor = ElectionMonitor(config_manager)
        
        # 日次レポート生成
        daily_report = monitor.generate_daily_report()
        
        if format == 'json':
            click.echo(json.dumps(daily_report, ensure_ascii=False, indent=2))
        else:
            _display_daily_report(daily_report, color_printer)
            
    except Exception as e:
        logger.error(f"レポート生成エラー: {str(e)}")
        click.echo(f"エラー: {str(e)}", err=True)


# 表示用ヘルパー関数

def _display_constituency_summary(summary, color_printer):
    """選挙区サマリー表示"""
    color_printer.print_header(f"選挙区情勢: {summary['basic_info']['name']}")
    
    current_situation = summary['current_situation']
    color_printer.print_result("優勢候補", current_situation['leading_candidate'])
    color_printer.print_result("政党", current_situation['leading_party'])
    color_printer.print_result("支持率", f"{current_situation['support_rate']:.1%}")
    color_printer.print_result("情勢", current_situation['competitiveness'])
    
    color_printer.print_info("\n重要要因:")
    for factor in summary['key_factors']:
        color_printer.print_result("•", factor)


def _display_constituency_list(results, color_printer):
    """選挙区リスト表示"""
    color_printer.print_header(f"選挙区検索結果: {len(results)}件")
    
    for result in results:
        color_printer.print_result(result['name'], f"{result['prefecture']} - {result['competitiveness']}")


def _display_election_prediction(prediction, color_printer):
    """選挙予測表示"""
    color_printer.print_header(f"選挙予測: {prediction.constituency_id}")
    color_printer.print_result("予測日時", prediction.prediction_date)
    color_printer.print_result("信頼度", f"{prediction.confidence_score:.2f}")
    
    color_printer.print_info("\n候補者別予測:")
    for candidate_name, candidate_data in prediction.candidates.items():
        vote_share = candidate_data.get('vote_share', 0)
        win_prob = candidate_data.get('win_probability', 0)
        color_printer.print_result(candidate_name, f"得票率 {vote_share:.1%}, 勝利確率 {win_prob:.1%}")


def _display_seat_predictions(seat_predictions, color_printer, scenario):
    """議席予測表示"""
    color_printer.print_header(f"議席予測 ({scenario}シナリオ)")
    
    for party, prediction in seat_predictions.items():
        change = prediction.predicted_seats - prediction.current_seats
        change_str = f"{change:+d}" if change != 0 else "±0"
        
        color_printer.print_result(
            party, 
            f"{prediction.predicted_seats}議席 ({change_str}) [{prediction.confidence_interval[0]}-{prediction.confidence_interval[1]}]"
        )


def _display_coalition_analysis(coalition_analysis, color_printer, threshold):
    """連立分析表示"""
    color_printer.print_header("連立政権シナリオ分析")
    
    most_likely = coalition_analysis['most_likely_outcome']
    color_printer.print_result("最有力シナリオ", most_likely['name'])
    color_printer.print_result("構成政党", ", ".join(most_likely['parties']))
    color_printer.print_result("議席数", f"{most_likely['total_seats']}議席")
    color_printer.print_result("可能性", f"{most_likely['probability']:.1%}")
    
    color_printer.print_info(f"\n過半数ライン: {threshold}議席")


def _display_candidates_list(candidates, color_printer):
    """候補者リスト表示"""
    color_printer.print_header(f"候補者検索結果: {len(candidates)}名")
    
    for candidate in candidates:
        color_printer.print_result(
            f"{candidate.name} ({candidate.party})",
            f"{candidate.constituency_id} - 支持率 {candidate.support_rate:.1%}"
        )


def _display_candidate_comparison(comparison, color_printer):
    """候補者比較表示"""
    candidates = comparison['candidates']
    color_printer.print_header(f"候補者比較: {candidates['candidate1']['name']} vs {candidates['candidate2']['name']}")
    
    basic = comparison['basic_comparison']
    
    color_printer.print_info("基本比較:")
    color_printer.print_result("支持率", f"{basic['support_rate']['candidate1']:.1%} vs {basic['support_rate']['candidate2']:.1%}")
    color_printer.print_result("知名度", f"{basic['recognition_rate']['candidate1']:.1%} vs {basic['recognition_rate']['candidate2']:.1%}")
    
    overall = comparison['overall_assessment']
    color_printer.print_result("競争状況", overall['competitive_balance'])


def _display_alerts(alerts, color_printer):
    """アラートリスト表示"""
    color_printer.print_header(f"選挙アラート: {len(alerts)}件")
    
    for alert in alerts:
        severity_color = "red" if alert.severity == "high" else "yellow" if alert.severity == "medium" else "white"
        color_printer.print_result(f"[{alert.severity.upper()}]", alert.title)
        color_printer.print_info(f"  {alert.description} ({alert.timestamp})")


def _display_single_alert(alert, color_printer):
    """単一アラート表示"""
    severity_symbol = "🚨" if alert.severity == "high" else "⚠️" if alert.severity == "medium" else "ℹ️"
    color_printer.print_info(f"{severity_symbol} [{alert.alert_type}] {alert.title}")
    color_printer.print_info(f"   {alert.description}")


def _display_daily_report(report, color_printer):
    """日次レポート表示"""
    color_printer.print_header(f"日次選挙情勢レポート ({report['report_date'][:10]})")
    
    summary = report['overall_summary']
    color_printer.print_result("監視状況", summary['monitoring_status'])
    color_printer.print_result("監視選挙区数", str(summary['total_constituencies']))
    color_printer.print_result("直近アラート数", str(summary['recent_alerts_count']))
    
    if report['key_developments']:
        color_printer.print_info("\n重要動向:")
        for dev in report['key_developments']:
            color_printer.print_result("•", f"{dev['development']} ({dev['impact']})")


if __name__ == '__main__':
    election_2025()