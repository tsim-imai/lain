"""
設定管理ユーティリティ
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
from .exceptions import ConfigError

logger = logging.getLogger(__name__)


class ConfigManager:
    """設定ファイル管理クラス"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        初期化
        
        Args:
            config_dir: 設定ファイルディレクトリのパス
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # プロジェクトルートのconfigディレクトリを使用
            project_root = Path(__file__).parent.parent.parent
            self.config_dir = project_root / "config"
        
        self._llm_config = None
        self._scraper_config = None
        self._logging_config = None
        
        logger.info(f"設定管理を初期化: {self.config_dir}")
    
    def get_llm_config(self) -> Dict[str, Any]:
        """
        LLM設定を取得
        
        Returns:
            LLM設定辞書
            
        Raises:
            ConfigError: 設定ファイル読み込みエラー時
        """
        if self._llm_config is None:
            self._llm_config = self._load_config("llm_config.json")
        return self._llm_config
    
    def get_scraper_config(self) -> Dict[str, Any]:
        """
        スクレイパー設定を取得
        
        Returns:
            スクレイパー設定辞書
            
        Raises:
            ConfigError: 設定ファイル読み込みエラー時
        """
        if self._scraper_config is None:
            self._scraper_config = self._load_config("scraper_config.json")
        return self._scraper_config
    
    def get_logging_config(self) -> Dict[str, Any]:
        """
        ログ設定を取得
        
        Returns:
            ログ設定辞書
            
        Raises:
            ConfigError: 設定ファイル読み込みエラー時
        """
        if self._logging_config is None:
            self._logging_config = self._load_config("logging_config.json")
        return self._logging_config
    
    def _load_config(self, filename: str) -> Dict[str, Any]:
        """
        設定ファイルを読み込み
        
        Args:
            filename: 設定ファイル名
            
        Returns:
            設定辞書
            
        Raises:
            ConfigError: ファイル読み込みエラー時
        """
        config_path = self.config_dir / filename
        
        if not config_path.exists():
            raise ConfigError(f"設定ファイルが見つかりません: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            logger.debug(f"設定ファイル読み込み成功: {filename}")
            return config
            
        except json.JSONDecodeError as e:
            raise ConfigError(f"JSON解析エラー in {filename}: {str(e)}")
        except Exception as e:
            raise ConfigError(f"設定ファイル読み込みエラー {filename}: {str(e)}")
    
    def update_config(self, config_type: str, updates: Dict[str, Any]) -> None:
        """
        設定を更新
        
        Args:
            config_type: 設定タイプ ("llm", "scraper", "logging")
            updates: 更新する設定項目
            
        Raises:
            ConfigError: 設定更新エラー時
        """
        if config_type == "llm":
            if self._llm_config is None:
                self._llm_config = self.get_llm_config()
            self._llm_config.update(updates)
            self._save_config("llm_config.json", self._llm_config)
            
        elif config_type == "scraper":
            if self._scraper_config is None:
                self._scraper_config = self.get_scraper_config()
            self._scraper_config.update(updates)
            self._save_config("scraper_config.json", self._scraper_config)
            
        elif config_type == "logging":
            if self._logging_config is None:
                self._logging_config = self.get_logging_config()
            self._logging_config.update(updates)
            self._save_config("logging_config.json", self._logging_config)
            
        else:
            raise ConfigError(f"不明な設定タイプ: {config_type}")
    
    def _save_config(self, filename: str, config: Dict[str, Any]) -> None:
        """
        設定ファイルを保存
        
        Args:
            filename: 設定ファイル名
            config: 設定辞書
            
        Raises:
            ConfigError: ファイル保存エラー時
        """
        config_path = self.config_dir / filename
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            logger.info(f"設定ファイル保存成功: {filename}")
            
        except Exception as e:
            raise ConfigError(f"設定ファイル保存エラー {filename}: {str(e)}")
    
    def validate_config(self) -> bool:
        """
        全設定ファイルの妥当性をチェック
        
        Returns:
            全設定が有効な場合True
        """
        try:
            self.get_llm_config()
            self.get_scraper_config()
            self.get_logging_config()
            
            # 必須設定項目のチェック
            llm_config = self.get_llm_config()
            if "lm_studio" not in llm_config or "base_url" not in llm_config["lm_studio"]:
                logger.error("LM Studio設定が不完全です")
                return False
            
            scraper_config = self.get_scraper_config()
            if "bing" not in scraper_config:
                logger.error("Bing設定が不完全です")
                return False
            
            logger.info("全設定ファイルの妥当性チェック完了")
            return True
            
        except Exception as e:
            logger.error(f"設定妥当性チェックエラー: {str(e)}")
            return False