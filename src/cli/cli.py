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
@click.option('--stream', is_flag=True, help='ストリーミング表示を有効化')
@click.pass_context
def search(ctx, query: str, no_cache: bool, max_results: int, output_format: str, stream: bool):
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
            # ストリーミング検索実行
            if stream:
                app.search_stream(
                    query=query,
                    force_refresh=no_cache,
                    max_results=max_results
                )
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
@click.option('--session-id', type=str, help='既存のセッションIDを指定（新規作成する場合は省略）')
@click.option('--no-cache', is_flag=True, help='キャッシュを使用せずに検索')
@click.option('--max-results', type=int, default=10, help='最大検索結果数')
@click.option('--history-limit', type=int, default=5, help='考慮する履歴の最大数')
@click.option('--no-stream', is_flag=True, help='ストリーミング表示を無効化')
@click.pass_context
def chat(ctx, session_id: Optional[str], no_cache: bool, max_results: int, history_limit: int, no_stream: bool):
    """
    インタラクティブなチャットモード
    """
    try:
        config_manager = ctx.obj['config_manager']
        enable_color = ctx.obj['enable_color']
        color_printer = ctx.obj['color_printer']
        
        app = LainApp(config_manager, enable_color=enable_color)
        
        # セッション管理
        if session_id:
            current_session = session_id
            color_printer.print_info(f"既存セッションを使用: {session_id[:8]}...")
        else:
            current_session = app.start_chat_session()
            color_printer.print_success(f"新しいチャットセッション開始: {current_session[:8]}...")
        
        color_printer.print_header("lain チャットモード")
        color_printer.print_info("'exit' または 'quit' で終了")
        color_printer.print_info("'history' で履歴表示")
        color_printer.print_info("'clear' でセッションクリア")
        print()
        
        message_count = 0
        
        while True:
            try:
                # ユーザー入力を取得
                if enable_color:
                    user_input = input(f"{highlight('あなた:')} ")
                else:
                    user_input = input("あなた: ")
                
                # 特殊コマンドの処理
                if user_input.lower() in ['exit', 'quit']:
                    color_printer.print_info("チャットを終了します")
                    break
                elif user_input.lower() == 'history':
                    history = app.get_chat_history(current_session, 10)
                    if history:
                        color_printer.print_header("チャット履歴")
                        for i, entry in enumerate(history, 1):
                            print(f"{i}. ユーザー: {entry['user_query']}")
                            print(f"   AI: {entry['llm_response'][:100]}...")
                            print()
                    else:
                        color_printer.print_info("履歴がありません")
                    continue
                elif user_input.lower() == 'clear':
                    deleted_count = app.clear_chat_session(current_session)
                    color_printer.print_success(f"セッション履歴を削除しました: {deleted_count}件")
                    continue
                elif not user_input.strip():
                    continue
                
                # チャット処理
                if no_stream:
                    # 従来の非ストリーミング処理
                    result = app.process_chat_query(
                        query=user_input,
                        session_id=current_session,
                        force_refresh=no_cache,
                        max_results=max_results,
                        history_limit=history_limit
                    )
                else:
                    # ストリーミング処理
                    print()  # 回答開始前の空行
                    if enable_color:
                        print(f"{highlight('AI:')} ", end="", flush=True)
                    else:
                        print("AI: ", end="", flush=True)
                    
                    # ストリーミングコールバック関数
                    def stream_callback(chunk: str):
                        print(chunk, end="", flush=True)
                    
                    result = app.process_chat_query_stream(
                        query=user_input,
                        session_id=current_session,
                        force_refresh=no_cache,
                        max_results=max_results,
                        history_limit=history_limit,
                        stream_callback=stream_callback
                    )
                
                message_count += 1
                
                # ストリーミング後の追加情報表示
                if result.get("streamed"):
                    print()  # ストリーミング終了後の空行
                
                # 結果表示
                if result.get("search_performed"):
                    color_printer.print_info(f"検索実行: {len(result.get('search_results', []))}件の結果を取得")
                    if "search_query" in result:
                        color_printer.print_info(f"使用クエリ: {result['search_query']}")
                
                if result.get("history_used"):
                    color_printer.print_info("過去の会話履歴を考慮")
                
                # 処理時間表示
                processing_time = result.get("processing_time", 0)
                color_printer.print_info(f"処理時間: {processing_time:.2f}秒")
                
                # エラーがある場合
                if "error" in result:
                    color_printer.print_warning("処理中に問題が発生しました")
                
                # 非ストリーミングの場合のみ回答表示
                if not result.get("streamed"):
                    print()
                    if enable_color:
                        print(f"{highlight('AI:')} {result['response']}")
                    else:
                        print(f"AI: {result['response']}")
                
                print()
                
            except KeyboardInterrupt:
                color_printer.print_info("\nチャットを終了します")
                break
            except Exception as e:
                color_printer.print_error(f"エラー: {str(e)}")
                continue
        
        # セッション統計
        if message_count > 0:
            color_printer.print_info(f"総メッセージ数: {message_count}")
            color_printer.print_info(f"セッションID: {current_session}")
        
    except Exception as e:
        if ctx.obj['enable_color']:
            click.echo(error(f"チャットエラー: {str(e)}"), err=True)
        else:
            click.echo(f"❌ チャットエラー: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--sessions', is_flag=True, help='最近のセッション一覧を表示')
@click.option('--stats', is_flag=True, help='チャット統計を表示')
@click.option('--clear-all', is_flag=True, help='全チャット履歴を削除')
@click.pass_context
def chat_history(ctx, sessions: bool, stats: bool, clear_all: bool):
    """
    チャット履歴管理
    """
    try:
        config_manager = ctx.obj['config_manager']
        enable_color = ctx.obj['enable_color']
        color_printer = ctx.obj['color_printer']
        
        app = LainApp(config_manager, enable_color=enable_color)
        
        if sessions:
            # 最近のセッション一覧を表示
            recent_sessions = app.get_recent_chat_sessions(10)
            if recent_sessions:
                color_printer.print_header("最近のチャットセッション")
                for session in recent_sessions:
                    session_id_short = session['session_id'][:8]
                    color_printer.print_result(
                        f"セッション {session_id_short}",
                        f"{session['message_count']}メッセージ ({session['last_message'][:19]})"
                    )
            else:
                color_printer.print_info("チャットセッションがありません")
        
        if stats:
            # チャット統計を表示
            chat_stats = app.chat_manager.get_chat_statistics()
            color_printer.print_header("チャット統計")
            color_printer.print_result("総メッセージ数", str(chat_stats.get('total_messages', 0)))
            color_printer.print_result("総セッション数", str(chat_stats.get('total_sessions', 0)))
            color_printer.print_result("検索実行数", str(chat_stats.get('search_performed_count', 0)))
            color_printer.print_result("平均メッセージ/セッション", f"{chat_stats.get('average_messages_per_session', 0):.1f}")
        
        if clear_all:
            click.confirm('全チャット履歴を削除しますか？', abort=True)
            deleted_count = app.chat_manager.clear_all_chat_history()
            color_printer.print_success(f"全チャット履歴を削除しました: {deleted_count}件")
        
        if not any([sessions, stats, clear_all]):
            color_printer.print_info("オプションを指定してください。--help を参照してください。")
        
    except Exception as e:
        if ctx.obj['enable_color']:
            click.echo(error(f"チャット履歴エラー: {str(e)}"), err=True)
        else:
            click.echo(f"❌ チャット履歴エラー: {str(e)}", err=True)
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