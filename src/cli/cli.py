"""
CLI インターフェース
"""
import click
import logging
import sys
from pathlib import Path
from typing import Optional
from ..utils.config import ConfigManager
from ..utils.exceptions import ConfigError
from ..utils.colors import ColorPrinter, success, error, warning, info, highlight
from .app import LainApp

logger = logging.getLogger(__name__)


@click.group()
@click.option('--config-dir', type=click.Path(exists=True), help='設定ファイルディレクトリのパス')
@click.option('--verbose', '-v', is_flag=True, help='詳細ログを有効化')
@click.option('--debug', is_flag=True, help='デバッグモードを有効化')
@click.option('--no-color', is_flag=True, help='カラー出力を無効化')
@click.pass_context
def cli(ctx, config_dir: Optional[str], verbose: bool, debug: bool, no_color: bool):
    """
    lain - ローカルLLMを使用したWeb検索・要約システム
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


@cli.command()
@click.argument('query', required=True)
@click.option('--no-cache', is_flag=True, help='キャッシュを使用せずに検索')
@click.option('--max-results', type=int, default=10, help='最大検索結果数')
@click.option('--output-format', type=click.Choice(['text', 'json']), default='text', help='出力形式')
@click.pass_context
def search(ctx, query: str, no_cache: bool, max_results: int, output_format: str):
    """
    検索クエリを実行
    
    QUERY: 検索したい内容（自然言語）
    """
    try:
        config_manager = ctx.obj['config_manager']
        enable_color = ctx.obj['enable_color']
        color_printer = ctx.obj['color_printer']
        
        app = LainApp(config_manager, enable_color=enable_color)
        
        # JSON出力の場合はカラー出力を無効化
        if output_format == 'json':
            result = app.process_query(
                query=query,
                force_refresh=no_cache,
                max_results=max_results
            )
            import json
            click.echo(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            # カラー出力対応の検索実行
            app.search(
                query=query,
                force_refresh=no_cache,
                max_results=max_results
            )
            
    except Exception as e:
        if ctx.obj['enable_color']:
            click.echo(error(f"検索エラー: {str(e)}"), err=True)
        else:
            click.echo(f"❌ 検索エラー: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def test(ctx):
    """
    システム接続テスト
    """
    try:
        config_manager = ctx.obj['config_manager']
        enable_color = ctx.obj['enable_color']
        color_printer = ctx.obj['color_printer']
        
        app = LainApp(config_manager, enable_color=enable_color)
        
        color_printer.print_header("システム接続テスト")
        
        # LLM接続テスト
        color_printer.print_progress("LM Studio接続テスト中...")
        if app.test_llm_connection():
            color_printer.print_success("LM Studio接続テスト成功")
        else:
            color_printer.print_error("LM Studio接続テスト失敗")
        
        # スクレイパー接続テスト
        color_printer.print_progress("Webスクレイパー接続テスト中...")
        if app.test_scraper_connection():
            color_printer.print_success("Webスクレイパー接続テスト成功")
        else:
            color_printer.print_error("Webスクレイパー接続テスト失敗")
        
        # キャッシュシステムテスト
        color_printer.print_progress("キャッシュシステムテスト中...")
        cache_health = app.test_cache_system()
        if cache_health['status'] == 'healthy':
            color_printer.print_success("キャッシュシステムテスト成功")
        else:
            color_printer.print_error("キャッシュシステムテスト失敗")
        
        color_printer.print_info("全テスト完了")
        
    except Exception as e:
        if ctx.obj['enable_color']:
            click.echo(error(f"テストエラー: {str(e)}"), err=True)
        else:
            click.echo(f"❌ テストエラー: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--stats', is_flag=True, help='統計情報を表示')
@click.option('--recent', type=int, default=10, help='最近のクエリ数')
@click.pass_context
def cache(ctx, stats: bool, recent: int):
    """
    キャッシュ管理
    """
    try:
        config_manager = ctx.obj['config_manager']
        app = LainApp(config_manager)
        
        if stats:
            # キャッシュ統計を表示
            cache_stats = app.get_cache_statistics()
            
            click.echo("=== キャッシュ統計 ===")
            click.echo(f"有効なキャッシュエントリ: {cache_stats.get('valid_cache_entries', 0)}")
            click.echo(f"期限切れエントリ: {cache_stats.get('expired_cache_entries', 0)}")
            click.echo(f"TTL設定: {cache_stats.get('ttl_hours', 0)}時間")
            click.echo(f"データベースサイズ: {cache_stats.get('database_size_bytes', 0)} bytes")
            
            # 最近のクエリを表示
            recent_queries = app.get_recent_queries(recent)
            if recent_queries:
                click.echo(f"\n=== 最近のクエリ（{len(recent_queries)}件）===")
                for query_info in recent_queries:
                    status = "期限切れ" if query_info['is_expired'] else "有効"
                    click.echo(f"  {query_info['query'][:50]}... ({query_info['result_count']}件, {status})")
        
    except Exception as e:
        click.echo(f"キャッシュ管理エラー: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--clear-cache', is_flag=True, help='全キャッシュを削除')
@click.option('--cleanup', is_flag=True, help='期限切れキャッシュを削除')
@click.option('--optimize', is_flag=True, help='データベースを最適化')
@click.pass_context
def maintenance(ctx, clear_cache: bool, cleanup: bool, optimize: bool):
    """
    システムメンテナンス
    """
    try:
        config_manager = ctx.obj['config_manager']
        app = LainApp(config_manager)
        
        if clear_cache:
            click.confirm('全キャッシュを削除しますか？', abort=True)
            deleted_count = app.clear_all_cache()
            click.echo(f"キャッシュクリア完了: {deleted_count}件削除")
        
        if cleanup:
            deleted_count = app.cleanup_expired_cache()
            click.echo(f"期限切れキャッシュクリーンアップ完了: {deleted_count}件削除")
        
        if optimize:
            app.optimize_cache()
            click.echo("データベース最適化完了")
        
        if not any([clear_cache, cleanup, optimize]):
            click.echo("メンテナンス操作が指定されていません。--help を参照してください。")
        
    except Exception as e:
        click.echo(f"メンテナンスエラー: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def config(ctx):
    """
    設定情報を表示
    """
    try:
        config_manager = ctx.obj['config_manager']
        
        click.echo("=== LM Studio設定 ===")
        llm_config = config_manager.get_llm_config()
        click.echo(f"接続先: {llm_config['lm_studio']['base_url']}")
        click.echo(f"モデル: {llm_config['lm_studio']['model_name']}")
        click.echo(f"最大トークン: {llm_config['lm_studio']['max_tokens']}")
        
        click.echo("\n=== スクレイパー設定 ===")
        scraper_config = config_manager.get_scraper_config()
        click.echo(f"検索エンジン: Bing")
        click.echo(f"レート制限: {scraper_config['bing']['rate_limit']['requests_per_second']}req/s")
        click.echo(f"キャッシュTTL: {scraper_config['cache']['ttl_hours']}時間")
        
    except Exception as e:
        click.echo(f"設定表示エラー: {str(e)}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()