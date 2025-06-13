"""
プロンプトテンプレート管理
"""
import logging
from typing import Dict, Any
from ..utils.config import ConfigManager

logger = logging.getLogger(__name__)


class PromptManager:
    """プロンプトテンプレート管理クラス"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
        """
        self.config_manager = config_manager
        self.prompts = config_manager.get_llm_config()["prompts"]
        logger.info("プロンプトテンプレート管理を初期化")
    
    def get_search_decision_prompt(self, query: str) -> str:
        """
        検索判断用プロンプトを生成
        
        Args:
            query: ユーザーの質問
            
        Returns:
            検索判断用プロンプト
        """
        prompt_template = self.prompts["search_decision"]
        return prompt_template.format(query=query)
    
    def get_query_generation_prompt(self, query: str) -> str:
        """
        検索クエリ生成用プロンプトを生成
        
        Args:
            query: ユーザーの質問
            
        Returns:
            クエリ生成用プロンプト
        """
        prompt_template = self.prompts["query_generation"]
        return prompt_template.format(query=query)
    
    def get_result_summary_prompt(self, query: str, search_results: str) -> str:
        """
        結果要約用プロンプトを生成
        
        Args:
            query: ユーザーの質問
            search_results: 検索結果
            
        Returns:
            結果要約用プロンプト
        """
        prompt_template = self.prompts["result_summary"]
        return prompt_template.format(
            query=query,
            search_results=search_results
        )
    
    def get_custom_prompt(self, template_name: str, **kwargs) -> str:
        """
        カスタムプロンプトを生成
        
        Args:
            template_name: テンプレート名
            **kwargs: テンプレート変数
            
        Returns:
            生成されたプロンプト
            
        Raises:
            KeyError: 指定されたテンプレートが存在しない場合
        """
        if template_name not in self.prompts:
            raise KeyError(f"プロンプトテンプレート '{template_name}' が見つかりません")
        
        prompt_template = self.prompts[template_name]
        return prompt_template.format(**kwargs)
    
    def add_prompt_template(self, name: str, template: str) -> None:
        """
        新しいプロンプトテンプレートを追加
        
        Args:
            name: テンプレート名
            template: プロンプトテンプレート
        """
        self.prompts[name] = template
        logger.info(f"プロンプトテンプレート '{name}' を追加")
    
    def list_available_templates(self) -> list:
        """
        利用可能なテンプレート一覧を取得
        
        Returns:
            テンプレート名のリスト
        """
        return list(self.prompts.keys())
    
    def validate_prompt_variables(self, template_name: str, **kwargs) -> bool:
        """
        プロンプトテンプレートの変数が正しく提供されているかチェック
        
        Args:
            template_name: テンプレート名
            **kwargs: テンプレート変数
            
        Returns:
            変数が正しく提供されている場合True
        """
        try:
            self.get_custom_prompt(template_name, **kwargs)
            return True
        except (KeyError, ValueError) as e:
            logger.error(f"プロンプト変数検証エラー: {str(e)}")
            return False