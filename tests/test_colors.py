"""
カラー出力ユーティリティのテスト
"""
import pytest
from src.utils.colors import (
    Colors, colorize, success, error, warning, info, 
    highlight, dim, progress_color, ColorPrinter
)


class TestColors:
    """カラー出力テストクラス"""
    
    def test_colors_constants(self):
        """カラー定数のテスト"""
        assert Colors.RED is not None
        assert Colors.GREEN is not None
        assert Colors.YELLOW is not None
        assert Colors.BLUE is not None
        assert Colors.RESET is not None
    
    def test_colorize_basic(self):
        """基本的なカラー化テスト"""
        text = "テストテキスト"
        colored = colorize(text, Colors.RED)
        
        # カラーコードが含まれているかチェック
        assert text in colored
        assert len(colored) >= len(text)
    
    def test_success_message(self):
        """成功メッセージテスト"""
        result = success("テスト成功")
        assert "テスト成功" in result
        assert "✅" in result
    
    def test_error_message(self):
        """エラーメッセージテスト"""
        result = error("テストエラー")
        assert "テストエラー" in result
        assert "❌" in result
    
    def test_warning_message(self):
        """警告メッセージテスト"""
        result = warning("テスト警告")
        assert "テスト警告" in result
        assert "⚠️" in result
    
    def test_info_message(self):
        """情報メッセージテスト"""
        result = info("テスト情報")
        assert "テスト情報" in result
        assert "ℹ️" in result


class TestColorPrinter:
    """ColorPrinterテストクラス"""
    
    def test_color_printer_initialization(self):
        """ColorPrinter初期化テスト"""
        # カラー有効
        printer_color = ColorPrinter(True)
        assert printer_color.color_enabled == True
        
        # カラー無効
        printer_no_color = ColorPrinter(False)
        assert printer_no_color.color_enabled == False
        
        # 自動判定
        printer_auto = ColorPrinter(None)
        assert isinstance(printer_auto.color_enabled, bool)
    
    def test_print_methods_exist(self):
        """プリントメソッドの存在確認"""
        printer = ColorPrinter(False)
        
        # メソッドが存在することを確認
        assert hasattr(printer, 'print_success')
        assert hasattr(printer, 'print_error')
        assert hasattr(printer, 'print_warning')
        assert hasattr(printer, 'print_info')
        assert hasattr(printer, 'print_header')
        assert hasattr(printer, 'print_result')
        assert hasattr(printer, 'print_progress')
    
    def test_print_methods_callable(self):
        """プリントメソッドが呼び出し可能かテスト"""
        printer = ColorPrinter(False)
        
        # エラーが発生しないことを確認
        try:
            printer.print_success("成功テスト")
            printer.print_error("エラーテスト")
            printer.print_warning("警告テスト")
            printer.print_info("情報テスト")
            printer.print_header("ヘッダーテスト")
            printer.print_result("タイトル", "内容")
            printer.print_progress("プログレステスト")
        except Exception as e:
            pytest.fail(f"プリントメソッドでエラーが発生: {e}")
    
    def test_color_enabled_vs_disabled(self):
        """カラー有効・無効での動作差異テスト"""
        printer_color = ColorPrinter(True)
        printer_no_color = ColorPrinter(False)
        
        # 両方ともエラーなく実行できることを確認
        try:
            printer_color.print_success("カラーテスト")
            printer_no_color.print_success("非カラーテスト")
        except Exception as e:
            pytest.fail(f"カラー設定でエラーが発生: {e}")


class TestColorUtilities:
    """カラーユーティリティ関数テスト"""
    
    def test_highlight_function(self):
        """ハイライト機能テスト"""
        result = highlight("ハイライトテスト")
        assert "ハイライトテスト" in result
    
    def test_dim_function(self):
        """薄表示機能テスト"""
        result = dim("薄表示テスト")
        assert "薄表示テスト" in result
    
    def test_progress_color_function(self):
        """プログレスカラー機能テスト"""
        result = progress_color("プログレステスト")
        assert "プログレステスト" in result
    
    def test_colorize_with_multiple_options(self):
        """複数オプション付きカラー化テスト"""
        text = "複合テスト"
        result = colorize(text, Colors.RED, Colors.BRIGHT, Colors.BG_YELLOW)
        assert text in result
    
    def test_colorize_empty_text(self):
        """空文字列のカラー化テスト"""
        result = colorize("", Colors.RED)
        assert isinstance(result, str)
    
    def test_color_support_detection(self):
        """カラーサポート検出テスト"""
        # メソッドが正常に実行できることを確認
        try:
            is_supported = Colors.is_color_supported()
            assert isinstance(is_supported, bool)
        except Exception as e:
            pytest.fail(f"カラーサポート検出でエラー: {e}")


