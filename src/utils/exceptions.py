"""
カスタム例外クラス定義
"""


class LainError(Exception):
    """lainプロジェクトの基底例外クラス"""
    pass


class LLMError(LainError):
    """LLM関連のエラー"""
    pass


class ScraperError(LainError):
    """スクレイピング関連のエラー"""
    pass


class CacheError(LainError):
    """キャッシュ関連のエラー"""
    pass


class ConfigError(LainError):
    """設定関連のエラー"""
    pass


class NetworkError(LainError):
    """ネットワーク関連のエラー"""
    pass


class ValidationError(LainError):
    """データ検証関連のエラー"""
    pass


class AnalysisError(LainError):
    """分析処理関連のエラー"""
    pass


class PoliticalDataError(LainError):
    """政治データ関連のエラー"""
    pass