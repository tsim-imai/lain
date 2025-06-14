"""
政治特化LLMサービス
日本政治に特化したLLM処理の統合サービス
"""
import logging
from typing import Optional, List, Dict, Any, Iterator, Callable
from enum import Enum

from ..llm.client import LLMClient
from ..utils.config import ConfigManager
from ..utils.exceptions import LLMError
from .political_prompts import PoliticalPromptManager
from .entity_recognizer import PoliticalEntityRecognizer
from .bias_detector import PoliticalBiasDetector

logger = logging.getLogger(__name__)


class PoliticalQueryIntent(Enum):
    """政治クエリの意図分類"""
    SUPPORT_RATING = "support_rating"           # 支持率関連
    ELECTION_PREDICTION = "election_prediction" # 選挙予測
    POLICY_ANALYSIS = "policy_analysis"         # 政策分析
    POLITICAL_NEWS = "political_news"           # 政治ニュース
    POLITICIAN_INFO = "politician_info"         # 政治家情報
    PARTY_INFO = "party_info"                   # 政党情報
    POLITICAL_SCANDAL = "political_scandal"     # 政治スキャンダル
    COALITION_ANALYSIS = "coalition_analysis"   # 連立分析
    GENERAL_POLITICAL = "general_political"     # 一般政治質問


class PoliticalResponse:
    """政治分析応答データクラス"""
    
    def __init__(self, 
                 query: str,
                 intent: PoliticalQueryIntent,
                 response: str,
                 entities: List[str],
                 sentiment_score: Optional[float] = None,
                 reliability_score: Optional[float] = None,
                 bias_score: Optional[float] = None,
                 sources: Optional[List[str]] = None):
        self.query = query
        self.intent = intent
        self.response = response
        self.entities = entities
        self.sentiment_score = sentiment_score
        self.reliability_score = reliability_score
        self.bias_score = bias_score
        self.sources = sources or []


class PoliticalLLMService:
    """政治特化LLMサービスクラス"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
        """
        self.config_manager = config_manager
        self.client = LLMClient(config_manager)
        self.prompt_manager = PoliticalPromptManager(config_manager)
        self.entity_recognizer = PoliticalEntityRecognizer()
        self.bias_detector = PoliticalBiasDetector()
        
        logger.info("政治特化LLMサービスを初期化")
    
    def analyze_political_query(self, query: str) -> PoliticalQueryIntent:
        """
        政治クエリの意図を詳細分析
        
        Args:
            query: ユーザーの政治関連質問
            
        Returns:
            政治クエリの意図分類
        """
        try:
            prompt = self.prompt_manager.get_query_intent_analysis_prompt(query)
            response = self.client.generate_response(prompt, max_tokens=50)
            
            # 応答から意図を抽出
            intent = self._extract_intent_from_response(response)
            
            logger.info(f"政治クエリ意図分析: '{query}' -> {intent.value}")
            return intent
            
        except Exception as e:
            logger.error(f"政治クエリ意図分析エラー: {str(e)}")
            return PoliticalQueryIntent.GENERAL_POLITICAL
    
    def _extract_intent_from_response(self, response: str) -> PoliticalQueryIntent:
        """LLM応答から意図を抽出"""
        response_lower = response.lower()
        
        if "支持率" in response or "support_rating" in response_lower:
            return PoliticalQueryIntent.SUPPORT_RATING
        elif "選挙" in response or "election" in response_lower:
            return PoliticalQueryIntent.ELECTION_PREDICTION
        elif "政策" in response or "policy" in response_lower:
            return PoliticalQueryIntent.POLICY_ANALYSIS
        elif "ニュース" in response or "news" in response_lower:
            return PoliticalQueryIntent.POLITICAL_NEWS
        elif "政治家" in response or "politician" in response_lower:
            return PoliticalQueryIntent.POLITICIAN_INFO
        elif "政党" in response or "party" in response_lower:
            return PoliticalQueryIntent.PARTY_INFO
        elif "スキャンダル" in response or "scandal" in response_lower:
            return PoliticalQueryIntent.POLITICAL_SCANDAL
        elif "連立" in response or "coalition" in response_lower:
            return PoliticalQueryIntent.COALITION_ANALYSIS
        else:
            return PoliticalQueryIntent.GENERAL_POLITICAL
    
    def generate_political_search_queries(self, intent: PoliticalQueryIntent, original_query: str) -> List[str]:
        """
        政治意図に基づく最適化された検索クエリ生成
        
        Args:
            intent: 政治クエリ意図
            original_query: 元のクエリ
            
        Returns:
            最適化された検索クエリのリスト
        """
        try:
            prompt = self.prompt_manager.get_search_query_generation_prompt(intent, original_query)
            response = self.client.generate_response(prompt, max_tokens=200)
            
            # 複数のクエリを抽出
            queries = self._extract_queries_from_response(response)
            
            logger.info(f"政治検索クエリ生成: {intent.value} -> {len(queries)}件")
            return queries
            
        except Exception as e:
            logger.error(f"政治検索クエリ生成エラー: {str(e)}")
            return [original_query]
    
    def _extract_queries_from_response(self, response: str) -> List[str]:
        """LLM応答から検索クエリを抽出"""
        queries = []
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            # 番号付きリストから抽出
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
                # 番号や記号を除去
                clean_query = line.lstrip('0123456789.-* ').strip().strip('"\'')
                if clean_query:
                    queries.append(clean_query)
            elif line and not line.startswith('検索クエリ'):
                # 単純なクエリの場合
                clean_query = line.strip().strip('"\'')
                if clean_query:
                    queries.append(clean_query)
        
        return queries[:5]  # 最大5件まで
    
    def synthesize_political_response(self,
                                    query: str,
                                    intent: PoliticalQueryIntent,
                                    search_results: List[Dict[str, Any]],
                                    history: str = "") -> PoliticalResponse:
        """
        政治データの統合的分析・回答生成
        
        Args:
            query: ユーザーの質問
            intent: 政治クエリ意図
            search_results: 検索結果データ
            history: 過去の会話履歴
            
        Returns:
            政治分析応答
        """
        try:
            # エンティティ認識
            entities = self.entity_recognizer.extract_political_entities(query)
            
            # 政治特化プロンプトで応答生成
            prompt = self.prompt_manager.get_political_response_prompt(
                query, intent, search_results, history
            )
            
            response = self.client.generate_response(prompt)
            
            # バイアス検知
            bias_score = self.bias_detector.detect_bias(response)
            
            # 信頼性スコア（仮実装）
            reliability_score = self._calculate_reliability_score(search_results)
            
            political_response = PoliticalResponse(
                query=query,
                intent=intent,
                response=response,
                entities=entities,
                bias_score=bias_score,
                reliability_score=reliability_score,
                sources=[result.get('url', '') for result in search_results]
            )
            
            logger.info(f"政治応答生成完了: {intent.value}, エンティティ{len(entities)}件")
            return political_response
            
        except Exception as e:
            logger.error(f"政治応答生成エラー: {str(e)}")
            raise LLMError(f"政治応答の生成に失敗しました: {str(e)}")
    
    def _calculate_reliability_score(self, search_results: List[Dict[str, Any]]) -> float:
        """検索結果の信頼性スコアを算出（仮実装）"""
        if not search_results:
            return 0.0
        
        total_score = 0.0
        for result in search_results:
            url = result.get('url', '')
            # 政府・公式サイト判定
            if any(domain in url for domain in ['go.jp', 'kantei', 'soumu']):
                total_score += 1.0
            elif any(domain in url for domain in ['nhk.or.jp', 'asahi.com', 'yomiuri.co.jp']):
                total_score += 0.9
            else:
                total_score += 0.5
        
        return min(total_score / len(search_results), 1.0)
    
    def test_connection(self) -> bool:
        """政治LLMサービス接続テスト"""
        try:
            test_query = "岸田内閣の支持率について教えてください"
            intent = self.analyze_political_query(test_query)
            return intent is not None
        except Exception as e:
            logger.error(f"政治LLMサービス接続テスト失敗: {str(e)}")
            return False
    
    def get_llm_response(self, prompt: str, **kwargs) -> str:
        """
        LLMからの応答を取得
        
        Args:
            prompt: プロンプトテキスト
            **kwargs: 追加パラメータ
            
        Returns:
            LLMからの応答文字列
        """
        try:
            return self.client.generate_response(prompt, **kwargs)
        except Exception as e:
            logger.error(f"LLM応答生成エラー: {str(e)}")
            raise LLMError(f"LLM応答の生成に失敗しました: {str(e)}")