"""
政治特化CLI メインエントリーポイント
"""
import sys
import logging
from .political_commands import political_cli


def main():
    """
    メイン関数 - 政治特化CLIアプリケーションのエントリーポイント
    """
    try:
        political_cli()
    except KeyboardInterrupt:
        print("\n処理が中断されました。")
        sys.exit(130)  # SIGINT
    except Exception as e:
        logging.error(f"予期しないエラー: {str(e)}")
        print(f"エラーが発生しました: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()