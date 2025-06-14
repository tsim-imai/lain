"""
カラー出力ユーティリティ
"""
import sys
import os
from typing import Optional
from colorama import Fore, Back, Style, init

# coloramaの初期化（Windows対応）
init(autoreset=True)


class Colors:
    """カラー出力クラス"""
    
    # 基本色
    RED = Fore.RED
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    BLUE = Fore.BLUE
    MAGENTA = Fore.MAGENTA
    CYAN = Fore.CYAN
    WHITE = Fore.WHITE
    
    # スタイル
    BRIGHT = Style.BRIGHT
    DIM = Style.DIM
    RESET = Style.RESET_ALL
    
    # 背景色
    BG_RED = Back.RED
    BG_GREEN = Back.GREEN
    BG_YELLOW = Back.YELLOW
    BG_BLUE = Back.BLUE
    
    @staticmethod
    def is_color_supported() -> bool:
        """
        カラー出力がサポートされているかチェック
        
        Returns:
            カラー出力可能な場合True
        """
        # Windows CMD、PowerShell、Unix系ターミナルで動作確認
        return (
            hasattr(sys.stdout, 'isatty') and sys.stdout.isatty() and
            sys.platform != 'win32' or 
            'ANSICON' in os.environ or 
            'WT_SESSION' in os.environ or  # Windows Terminal
            'TERM_PROGRAM' in os.environ   # VS Code Terminal等
        )


def colorize(text: str, color: str = "", style: str = "", bg_color: str = "") -> str:
    """
    テキストをカラー化
    
    Args:
        text: カラー化するテキスト
        color: 文字色（Colors.REDなど）
        style: スタイル（Colors.BRIGHTなど）
        bg_color: 背景色（Colors.BG_REDなど）
        
    Returns:
        カラー化されたテキスト
    """
    if not Colors.is_color_supported():
        return text
    
    return f"{style}{color}{bg_color}{text}{Colors.RESET}"


def success(text: str) -> str:
    """成功メッセージ（緑色）"""
    return colorize(f"✅ {text}", Colors.GREEN, Colors.BRIGHT)


def error(text: str) -> str:
    """エラーメッセージ（赤色）"""
    return colorize(f"❌ {text}", Colors.RED, Colors.BRIGHT)


def warning(text: str) -> str:
    """警告メッセージ（黄色）"""
    return colorize(f"⚠️ {text}", Colors.YELLOW, Colors.BRIGHT)


def info(text: str) -> str:
    """情報メッセージ（青色）"""
    return colorize(f"ℹ️ {text}", Colors.BLUE, Colors.BRIGHT)


def highlight(text: str) -> str:
    """ハイライト（マゼンタ色）"""
    return colorize(text, Colors.MAGENTA, Colors.BRIGHT)


def dim(text: str) -> str:
    """薄く表示（グレー）"""
    return colorize(text, Colors.WHITE, Colors.DIM)


def progress_color(text: str) -> str:
    """プログレス表示（シアン色）"""
    return colorize(text, Colors.CYAN, Colors.BRIGHT)


def header(text: str) -> str:
    """ヘッダー表示（背景付き）"""
    return colorize(f" {text} ", Colors.WHITE, Colors.BRIGHT, Colors.BG_BLUE)




def result_highlight(text: str) -> str:
    """検索結果のハイライト（緑背景）"""
    return colorize(f" {text} ", Colors.WHITE, Colors.BRIGHT, Colors.BG_GREEN)


class ColorPrinter:
    """カラー対応のプリンタークラス"""
    
    def __init__(self, enable_color: Optional[bool] = None):
        """
        初期化
        
        Args:
            enable_color: カラー出力を強制的に有効/無効化（Noneで自動判定）
        """
        if enable_color is None:
            self.color_enabled = Colors.is_color_supported()
        else:
            self.color_enabled = enable_color
    
    def print_success(self, message: str) -> None:
        """成功メッセージを出力"""
        if self.color_enabled:
            print(success(message))
        else:
            print(f"✅ {message}")
    
    def print_error(self, message: str) -> None:
        """エラーメッセージを出力"""
        if self.color_enabled:
            print(error(message))
        else:
            print(f"❌ {message}")
    
    def print_warning(self, message: str) -> None:
        """警告メッセージを出力"""
        if self.color_enabled:
            print(warning(message))
        else:
            print(f"⚠️ {message}")
    
    def print_info(self, message: str) -> None:
        """情報メッセージを出力"""
        if self.color_enabled:
            print(info(message))
        else:
            print(f"ℹ️ {message}")
    
    def print_header(self, message: str) -> None:
        """ヘッダーメッセージを出力"""
        if self.color_enabled:
            print(header(message))
        else:
            print(f"=== {message} ===")
    
    
    def print_result(self, title: str, content: str) -> None:
        """検索結果を整形して出力"""
        if self.color_enabled:
            print(f"{highlight(title)}: {content}")
        else:
            print(f"{title}: {content}")
    
    def print_progress(self, message: str) -> None:
        """プログレス情報を出力"""
        if self.color_enabled:
            print(progress_color(f"🔄 {message}"))
        else:
            print(f"🔄 {message}")


# グローバルなカラープリンターインスタンス
printer = ColorPrinter()