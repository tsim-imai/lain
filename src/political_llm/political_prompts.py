"""
政治専門プロンプト管理
日本政治に特化したプロンプトテンプレートを提供
"""
import logging
from typing import Dict, Any, List
from enum import Enum

from ..utils.config import ConfigManager

logger = logging.getLogger(__name__)


class PoliticalPromptManager:
    """政治専門プロンプト管理クラス"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
        """
        self.config_manager = config_manager
        self._load_political_prompts()
        logger.info("政治専門プロンプト管理を初期化")
    
    def _load_political_prompts(self):
        """政治専門プロンプトテンプレートを読み込み"""
        self.prompts = {
            # クエリ意図分析プロンプト
            "query_intent_analysis": """
あなたは日本政治の専門アナリストです。以下の質問の政治的意図を分析してください。

質問: {query}

以下のカテゴリから最も適切なものを1つ選んでください：
- support_rating: 支持率に関する質問
- election_prediction: 選挙予測に関する質問  
- policy_analysis: 政策分析に関する質問
- political_news: 政治ニュースに関する質問
- politician_info: 政治家の情報に関する質問
- party_info: 政党の情報に関する質問
- political_scandal: 政治スキャンダルに関する質問
- coalition_analysis: 連立政権分析に関する質問
- general_political: 一般的な政治質問

回答は選択したカテゴリ名のみを返してください。
""",
            
            # 検索クエリ生成プロンプト
            "search_query_generation": """
あなたは日本政治の検索専門家です。以下の政治質問に対して、最適な検索クエリを3-5個生成してください。

質問: {original_query}
意図: {intent}

検索クエリは以下の条件を満たしてください：
1. 日本語で具体的なキーワードを含む
2. 政治家名、政党名、政策名を正確に含む
3. 最新情報を取得できるような時事性のあるキーワード
4. 信頼できる情報源から情報を取得できるキーワード

検索クエリのみを番号付きリストで返してください。
例：
1. 岸田内閣 支持率 最新
2. 自民党 世論調査 2024年
3. 内閣支持率 推移 グラフ
""",
            
            # 政治応答生成プロンプト
            "political_response": """
あなたは日本政治の専門アナリストです。以下の情報を基に、客観的で正確な政治分析を行ってください。

【質問】: {query}
【政治的意図】: {intent}
【検索結果】: {search_results}
{history_section}

以下の観点で分析してください：
1. 事実に基づく客観的な情報整理
2. 複数の情報源からの総合的な判断
3. 政治的偏向を避けた中立的な分析
4. 不確実な情報については明確に注記
5. 情報の信頼性と時事性の考慮

回答は以下の構造で記述してください：
【概要】: 質問に対する簡潔な回答
【詳細分析】: 検索結果に基づく詳細な分析
【注意事項】: 情報の限界や不確実性について
""",
            
            # 選挙予測プロンプト
            "election_prediction": """
あなたは日本の選挙予測の専門家です。以下の情報を基に客観的な選挙分析を行ってください：

【分析対象】: {target}
【過去選挙データ】: {past_data}
【現在の世論調査】: {current_polls}
【政治情勢】: {political_situation}

以下の観点で分析してください：
1. 投票率予測とその根拠
2. 各政党・候補の得票率予測
3. 勝敗予測とその確度
4. 不確定要素とリスク要因
5. 過去データとの比較分析

注意：予測には必ず不確実性が伴うことを明記し、複数のシナリオを提示してください。
""",
            
            # 感情分析プロンプト
            "sentiment_analysis": """
以下のテキストについて、{political_entity}に対する政治的感情を分析してください：

【対象テキスト】: {text}
【分析対象】: {political_entity}

以下のスコアで評価してください（0-100）：
- ポジティブ度: 支持・好意的な内容
- ネガティブ度: 批判・否定的な内容  
- 中立度: 客観的・事実報道の内容
- 信頼度: 情報の信頼性・正確性

回答は数値のみで記述してください：
ポジティブ度: XX
ネガティブ度: XX
中立度: XX
信頼度: XX
""",
            
            # 信頼性評価プロンプト
            "reliability_assessment": """
以下の政治情報の信頼性を評価してください：

【情報源】: {source}
【内容】: {content}
【発信者】: {author}

評価観点：
1. 情報源の権威性・公式性
2. 内容の事実性・検証可能性
3. 偏向・バイアスの有無
4. 情報の新しさ・時事性
5. 他の情報源との整合性

信頼性スコア（0-100）とその根拠を記述してください。
"""
        }
    
    def get_query_intent_analysis_prompt(self, query: str) -> str:
        """クエリ意図分析プロンプトを取得"""
        return self.prompts["query_intent_analysis"].format(query=query)
    
    def get_search_query_generation_prompt(self, intent, original_query: str) -> str:
        """検索クエリ生成プロンプトを取得"""
        return self.prompts["search_query_generation"].format(
            original_query=original_query,
            intent=intent.value if hasattr(intent, 'value') else str(intent)
        )
    
    def get_political_response_prompt(self, 
                                    query: str, 
                                    intent, 
                                    search_results: List[Dict[str, Any]], 
                                    history: str = "") -> str:
        """政治応答生成プロンプトを取得"""
        # 検索結果をフォーマット
        formatted_results = self._format_search_results(search_results)
        
        # 履歴セクション
        history_section = ""
        if history:
            history_section = f"【過去の会話履歴】: {history}"
        
        return self.prompts["political_response"].format(
            query=query,
            intent=intent.value if hasattr(intent, 'value') else str(intent),
            search_results=formatted_results,
            history_section=history_section
        )
    
    def get_election_prediction_prompt(self, 
                                     target: str,
                                     past_data: str,
                                     current_polls: str,
                                     political_situation: str) -> str:
        """選挙予測プロンプトを取得"""
        return self.prompts["election_prediction"].format(
            target=target,
            past_data=past_data,
            current_polls=current_polls,
            political_situation=political_situation
        )
    
    def get_sentiment_analysis_prompt(self, text: str, political_entity: str) -> str:
        """感情分析プロンプトを取得"""
        return self.prompts["sentiment_analysis"].format(
            text=text,
            political_entity=political_entity
        )
    
    def get_reliability_assessment_prompt(self, 
                                        source: str,
                                        content: str,
                                        author: str = "") -> str:
        """信頼性評価プロンプトを取得"""
        return self.prompts["reliability_assessment"].format(
            source=source,
            content=content,
            author=author
        )
    
    def _format_search_results(self, search_results: List[Dict[str, Any]]) -> str:
        """検索結果をLLM用にフォーマット"""
        if not search_results:
            return "検索結果が見つかりませんでした。"
        
        formatted_parts = []
        for i, result in enumerate(search_results, 1):
            title = result.get('title', 'タイトルなし')
            snippet = result.get('snippet', '内容なし')
            url = result.get('url', '')
            
            formatted_part = f"{i}. {title}\n   内容: {snippet}\n   URL: {url}\n"
            formatted_parts.append(formatted_part)
        
        return "\n".join(formatted_parts)