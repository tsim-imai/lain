"""
LM Studio API接続クライアント
"""
import json
import logging
from typing import Optional, Dict, Any, Iterator, Callable
from openai import OpenAI
from ..utils.config import ConfigManager
from ..utils.exceptions import LLMError

logger = logging.getLogger(__name__)


class LLMClient:
    """LM Studio API接続クライアント"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
        """
        self.config_manager = config_manager
        self.llm_config = config_manager.get_llm_config()
        
        # OpenAI互換クライアントを初期化
        self.client = OpenAI(
            base_url=self.llm_config["lm_studio"]["base_url"],
            api_key=self.llm_config["lm_studio"]["api_key"]
        )
        
        logger.info(f"LM Studio接続を初期化: {self.llm_config['lm_studio']['base_url']}")
    
    def generate_response(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        timeout: Optional[int] = None
    ) -> str:
        """
        LLMから応答を生成
        
        Args:
            prompt: 入力プロンプト
            max_tokens: 最大トークン数
            temperature: 温度パラメータ
            timeout: タイムアウト（秒）
            
        Returns:
            LLMの応答テキスト
            
        Raises:
            LLMError: LLM処理エラー時
        """
        try:
            # パラメータの設定（デフォルト値を使用）
            request_params = {
                "model": self.llm_config["lm_studio"]["model_name"],
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens or self.llm_config["lm_studio"]["max_tokens"],
                "temperature": temperature or self.llm_config["lm_studio"]["temperature"]
            }
            
            logger.debug(f"LLMリクエスト送信: {request_params}")
            
            # API呼び出し
            response = self.client.chat.completions.create(**request_params)
            
            # 応答の取得
            if response.choices and len(response.choices) > 0:
                result = response.choices[0].message.content
                logger.debug(f"LLM応答受信: {result[:100]}...")
                return result.strip()
            else:
                raise LLMError("LLMから有効な応答を取得できませんでした")
                
        except Exception as e:
            logger.error(f"LLM処理エラー: {str(e)}")
            raise LLMError(f"LLM処理に失敗しました: {str(e)}")
    
    def generate_response_stream(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        timeout: Optional[int] = None,
        callback: Optional[Callable[[str], None]] = None
    ) -> Iterator[str]:
        """
        LLMからストリーミング応答を生成
        
        Args:
            prompt: 入力プロンプト
            max_tokens: 最大トークン数
            temperature: 温度パラメータ
            timeout: タイムアウト（秒）
            callback: チャンクごとのコールバック関数
            
        Yields:
            LLMの応答テキストチャンク
            
        Raises:
            LLMError: LLM処理エラー時
        """
        try:
            # パラメータの設定（デフォルト値を使用）
            request_params = {
                "model": self.llm_config["lm_studio"]["model_name"],
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens or self.llm_config["lm_studio"]["max_tokens"],
                "temperature": temperature or self.llm_config["lm_studio"]["temperature"],
                "stream": True  # ストリーミングを有効化
            }
            
            logger.debug(f"LLMストリーミングリクエスト送信: {request_params}")
            
            # ストリーミングAPI呼び出し
            response_stream = self.client.chat.completions.create(**request_params)
            
            for chunk in response_stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        content = delta.content
                        
                        # コールバック関数があれば呼び出し
                        if callback:
                            callback(content)
                        
                        yield content
                        
        except Exception as e:
            logger.error(f"LLMストリーミング処理エラー: {str(e)}")
            raise LLMError(f"LLMストリーミング処理に失敗しました: {str(e)}")
    
    def generate_response_stream_complete(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        timeout: Optional[int] = None,
        callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        ストリーミング応答を完全に受信して文字列として返す
        
        Args:
            prompt: 入力プロンプト
            max_tokens: 最大トークン数
            temperature: 温度パラメータ
            timeout: タイムアウト（秒）
            callback: チャンクごとのコールバック関数
            
        Returns:
            完全なLLM応答テキスト
            
        Raises:
            LLMError: LLM処理エラー時
        """
        complete_response = ""
        try:
            for chunk in self.generate_response_stream(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout,
                callback=callback
            ):
                complete_response += chunk
            
            logger.debug(f"LLMストリーミング応答完了: {complete_response[:100]}...")
            return complete_response.strip()
            
        except Exception as e:
            logger.error(f"LLMストリーミング完了処理エラー: {str(e)}")
            raise LLMError(f"LLMストリーミング完了処理に失敗しました: {str(e)}")

    def test_connection(self) -> bool:
        """
        LM Studio接続テスト
        
        Returns:
            接続成功時True、失敗時False
        """
        try:
            test_prompt = "こんにちは"
            response = self.generate_response(test_prompt, max_tokens=10)
            logger.info("LM Studio接続テスト成功")
            return True
        except Exception as e:
            logger.error(f"LM Studio接続テスト失敗: {str(e)}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        使用中のモデル情報を取得
        
        Returns:
            モデル情報辞書
        """
        try:
            models = self.client.models.list()
            return {
                "models": [model.id for model in models.data],
                "current_model": self.llm_config["lm_studio"]["model_name"]
            }
        except Exception as e:
            logger.error(f"モデル情報取得エラー: {str(e)}")
            return {"error": str(e)}