"""
LLMサービス層 - 各種AI機能の実装
"""
import logging
from typing import Optional, List, Dict, Any
from .client import LLMClient
from .prompts import PromptManager
from ..utils.config import ConfigManager
from ..utils.exceptions import LLMError

logger = logging.getLogger(__name__)


class LLMService:
    """LLMサービスクラス - AI機能の統合管理"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
        """
        self.config_manager = config_manager
        self.client = LLMClient(config_manager)
        self.prompt_manager = PromptManager(config_manager)
        logger.info("LLMサービスを初期化")
    
    def should_search(self, query: str) -> bool:
        """
        検索が必要かどうかを判断
        
        Args:
            query: ユーザーの質問
            
        Returns:
            検索が必要な場合True
            
        Raises:
            LLMError: LLM処理エラー時
        """
        try:
            prompt = self.prompt_manager.get_search_decision_prompt(query)
            response = self.client.generate_response(prompt, max_tokens=10)
            
            # 応答を正規化してYES/NOで判断
            response_normalized = response.upper().strip()
            
            if "YES" in response_normalized or "はい" in response or "必要" in response:
                logger.info(f"検索必要と判断: {query}")
                return True
            elif "NO" in response_normalized or "いいえ" in response or "不要" in response:
                logger.info(f"検索不要と判断: {query}")
                return False
            else:
                # 明確でない場合は検索を行う（保守的な判断）
                logger.warning(f"検索判断が不明確、検索を実行: {query} -> {response}")
                return True
                
        except Exception as e:
            logger.error(f"検索判断エラー: {str(e)}")
            # エラー時は検索を行う（保守的な判断）
            return True
    
    def generate_search_query(self, query: str) -> str:
        """
        検索クエリを生成
        
        Args:
            query: ユーザーの質問
            
        Returns:
            最適化された検索クエリ
            
        Raises:
            LLMError: LLM処理エラー時
        """
        try:
            prompt = self.prompt_manager.get_query_generation_prompt(query)
            search_query = self.client.generate_response(prompt, max_tokens=50)
            
            # 検索クエリをクリーンアップ
            search_query = search_query.strip().replace('\n', ' ')
            
            # 引用符や不要な文字を除去
            search_query = search_query.strip('"\'')
            
            logger.info(f"検索クエリ生成: '{query}' -> '{search_query}'")
            return search_query
            
        except Exception as e:
            logger.error(f"検索クエリ生成エラー: {str(e)}")
            # エラー時は元のクエリをそのまま使用
            return query
    
    def summarize_results(self, query: str, search_results: List[Dict[str, Any]]) -> str:
        """
        検索結果を要約して回答を生成
        
        Args:
            query: ユーザーの質問
            search_results: 検索結果のリスト
            
        Returns:
            要約された回答
            
        Raises:
            LLMError: LLM処理エラー時
        """
        try:
            # 検索結果を文字列形式に変換
            formatted_results = self._format_search_results(search_results)
            
            prompt = self.prompt_manager.get_result_summary_prompt(query, formatted_results)
            summary = self.client.generate_response(prompt)
            
            logger.info(f"検索結果要約完了: {len(search_results)}件の結果を要約")
            return summary
            
        except Exception as e:
            logger.error(f"検索結果要約エラー: {str(e)}")
            raise LLMError(f"検索結果の要約に失敗しました: {str(e)}")
    
    def _format_search_results(self, search_results: List[Dict[str, Any]]) -> str:
        """
        検索結果をLLM用の文字列形式に変換
        
        Args:
            search_results: 検索結果のリスト
            
        Returns:
            フォーマットされた検索結果文字列
        """
        if not search_results:
            return "検索結果が見つかりませんでした。"
        
        formatted_parts = []
        for i, result in enumerate(search_results, 1):
            title = result.get('title', 'タイトルなし')
            snippet = result.get('snippet', '内容なし')
            url = result.get('url', '')
            
            formatted_part = f"{i}. {title}\n   {snippet}\n   URL: {url}\n"
            formatted_parts.append(formatted_part)
        
        return "\n".join(formatted_parts)
    
    def direct_answer(self, query: str) -> str:
        """
        検索を行わずに直接回答を生成
        
        Args:
            query: ユーザーの質問
            
        Returns:
            LLMによる直接回答
            
        Raises:
            LLMError: LLM処理エラー時
        """
        try:
            # 直接回答用のプロンプト
            prompt = f"以下の質問に答えてください。正確でない情報は避け、知らない場合は「わかりません」と答えてください。\n\n質問: {query}"
            
            response = self.client.generate_response(prompt)
            logger.info(f"直接回答生成: {query}")
            return response
            
        except Exception as e:
            logger.error(f"直接回答エラー: {str(e)}")
            raise LLMError(f"回答の生成に失敗しました: {str(e)}")
    
    def test_connection(self) -> bool:
        """
        LLMサービス接続テスト
        
        Returns:
            接続成功時True
        """
        return self.client.test_connection()