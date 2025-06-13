"""
CLIエントリーポイント
"""
import sys
import logging
from .cli import cli


def main():
    """
    メイン関数 - CLIアプリケーションのエントリーポイント
    """
    try:
        cli()
    except KeyboardInterrupt:
        print("\n処理が中断されました。")
        sys.exit(130)  # SIGINT
    except Exception as e:
        logging.error(f"予期しないエラー: {str(e)}")
        print(f"エラーが発生しました: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()