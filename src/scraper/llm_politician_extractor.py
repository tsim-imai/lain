#!/usr/bin/env python3
"""
LLM活用政治家情報抽出モジュール
"""
import logging
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..llm.client import LLMClient

logger = logging.getLogger(__name__)


class LLMPoliticianExtractor:
    """LLM活用政治家情報抽出クラス"""
    
    def __init__(self, llm_client: LLMClient):
        """
        初期化
        
        Args:
            llm_client: LLM クライアント
        """
        self.llm_client = llm_client
        
        # 抽出用プロンプトテンプレート
        self.extraction_prompt = """
あなたは政治家の情報を正確に抽出する専門家です。
与えられたWebページのテキストから、以下の情報を抽出してください。

情報が見つからない場合は空文字や null を返してください。
推測や憶測は避け、テキストに明確に書かれている情報のみを抽出してください。

テキスト:
{text}

以下のJSON形式で情報を抽出してください：

```json
{{
  "name": "政治家の氏名（フルネーム）",
  "reading": "氏名の読み方（ひらがな）",
  "age": 年齢（数値、わからない場合はnull）,
  "birth_date": "生年月日（YYYY年MM月DD日形式）",
  "birth_place": "出身地",
  "current_party": "現在の所属政党",
  "party_history": ["政党履歴1", "政党履歴2", ...],
  "positions": ["現在または過去の役職1", "役職2", ...],
  "education": ["学歴1", "学歴2", ...],
  "career": ["経歴1", "経歴2", ...],
  "constituency": "選挙区",
  "election_type": "選挙種別（衆議院・参議院など）",
  "election_history": ["当選回数や選挙履歴"],
  "family": "家族構成の情報",
  "hobbies": ["趣味1", "趣味2", ...],
  "special_notes": "特記事項や重要な情報"
}}
```

重要：
- JSONのみを返答してください（説明文は不要）
- 情報が不明な場合は空文字 "" や null を使用
- 推測ではなく、テキストに明記されている事実のみを抽出
- 日付は可能な限り「YYYY年MM月DD日」形式に統一
"""

        # 統合用プロンプトテンプレート
        self.integration_prompt = """
複数のWebページから抽出された政治家の情報を統合して、最も正確で完全な情報を作成してください。

抽出された情報一覧:
{extracted_data}

以下のルールに従って統合してください：
1. 同じ情報が複数ある場合、最も詳細で正確なものを選択
2. 矛盾する情報がある場合、より信頼できるソース（公式サイト、Wikipedia等）を優先
3. 空の情報は他のソースで補完
4. リスト項目は重複を排除して統合

統合結果を以下のJSON形式で返してください：

```json
{{
  "name": "統合された氏名",
  "reading": "統合された読み方",
  "age": 統合された年齢,
  "birth_date": "統合された生年月日",
  "birth_place": "統合された出身地",
  "current_party": "統合された現在の政党",
  "party_history": ["統合された政党履歴"],
  "positions": ["統合された役職"],
  "education": ["統合された学歴"],
  "career": ["統合された経歴"],
  "constituency": "統合された選挙区",
  "election_type": "統合された選挙種別",
  "election_history": ["統合された選挙履歴"],
  "family": "統合された家族情報",
  "hobbies": ["統合された趣味"],
  "special_notes": "統合された特記事項",
  "sources": ["情報源URL1", "情報源URL2", ...],
  "confidence_level": "high/medium/low（情報の信頼度）",
  "integration_notes": "統合時の特記事項"
}}
```

重要：
- JSONのみを返答してください
- 矛盾する情報がある場合は integration_notes に記載
- 信頼度は情報の完全性と一貫性で判定
"""

        logger.info("LLM政治家情報抽出器を初期化")
    
    def extract_politician_info(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        LLMを使用してコンテンツから政治家情報を抽出
        
        Args:
            content_data: URLスクレイパーからの結果辞書
            
        Returns:
            抽出された政治家情報辞書
        """
        try:
            text = content_data.get('text_content', '')
            title = content_data.get('title', '')
            url = content_data.get('url', '')
            
            # テキストが短すぎる場合はスキップ
            if len(text) < 100:
                logger.warning(f"テキストが短すぎます: {url}")
                return self._create_empty_result(url, title, "テキストが短すぎます")
            
            # テキストが長すぎる場合は切り詰め
            max_length = 8000  # LLMのコンテキスト制限を考慮
            if len(text) > max_length:
                text = text[:max_length] + "..."
                logger.info(f"テキストを{max_length}文字に切り詰めました: {url}")
            
            # LLMにプロンプトを送信
            prompt = self.extraction_prompt.format(text=text)
            
            logger.info(f"LLM抽出開始: {url}")
            response = self.llm_client.generate_response(prompt)
            
            # JSONレスポンスをパース
            extracted_info = self._parse_llm_response(response)
            
            # メタデータを追加
            extracted_info.update({
                'source_url': url,
                'source_title': title,
                'source_domain': content_data.get('domain', ''),
                'extracted_at': datetime.now().isoformat(),
                'extraction_method': 'llm',
                'text_length': len(content_data.get('text_content', ''))
            })
            
            logger.info(f"LLM抽出完了: {url} - {extracted_info.get('name', '名前未抽出')}")
            return extracted_info
            
        except Exception as e:
            logger.error(f"LLM政治家情報抽出エラー: {url} - {str(e)}")
            return self._create_empty_result(
                content_data.get('url', ''),
                content_data.get('title', ''),
                str(e)
            )
    
    def integrate_multiple_extractions(self, extractions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        複数の抽出結果をLLMで統合
        
        Args:
            extractions: 複数の抽出結果リスト
            
        Returns:
            統合された政治家情報
        """
        try:
            if not extractions:
                return self._create_empty_result("", "", "抽出結果がありません")
            
            # 有効な抽出結果のみをフィルタリング
            valid_extractions = [
                ext for ext in extractions 
                if ext.get('name') and ext.get('name') != '' and 'error' not in ext
            ]
            
            if not valid_extractions:
                logger.warning("有効な抽出結果がありません")
                return extractions[0] if extractions else self._create_empty_result("", "", "有効な抽出結果なし")
            
            if len(valid_extractions) == 1:
                logger.info("抽出結果が1件のため統合をスキップ")
                return valid_extractions[0]
            
            # 統合用プロンプトを作成
            extraction_summary = []
            for i, ext in enumerate(valid_extractions, 1):
                summary = {
                    'source': i,
                    'url': ext.get('source_url', ''),
                    'data': {k: v for k, v in ext.items() 
                           if k not in ['source_url', 'source_title', 'source_domain', 
                                      'extracted_at', 'extraction_method', 'text_length']}
                }
                extraction_summary.append(summary)
            
            prompt = self.integration_prompt.format(
                extracted_data=json.dumps(extraction_summary, ensure_ascii=False, indent=2)
            )
            
            logger.info(f"LLM統合開始: {len(valid_extractions)}件の結果を統合")
            response = self.llm_client.generate_response(prompt)
            
            # 統合結果をパース
            integrated_info = self._parse_llm_response(response)
            
            # メタデータを追加
            integrated_info.update({
                'integrated_at': datetime.now().isoformat(),
                'integration_method': 'llm',
                'source_count': len(valid_extractions),
                'sources': [ext.get('source_url', '') for ext in valid_extractions]
            })
            
            logger.info(f"LLM統合完了: {integrated_info.get('name', '名前未統合')}")
            return integrated_info
            
        except Exception as e:
            logger.error(f"LLM統合エラー: {str(e)}")
            # エラー時は最初の有効な結果を返す
            return valid_extractions[0] if valid_extractions else self._create_empty_result("", "", str(e))
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """LLMレスポンスをJSONとしてパース"""
        try:
            # JSONブロックを抽出
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # JSONブロックがない場合、レスポンス全体をJSONとして解釈
                json_str = response.strip()
            
            # JSONをパース
            result = json.loads(json_str)
            
            # 基本的な検証
            if not isinstance(result, dict):
                raise ValueError("レスポンスが辞書形式ではありません")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON パースエラー: {str(e)}")
            logger.debug(f"パース失敗レスポンス: {response[:500]}...")
            return self._create_empty_result("", "", f"JSON パースエラー: {str(e)}")
        
        except Exception as e:
            logger.error(f"レスポンス処理エラー: {str(e)}")
            return self._create_empty_result("", "", f"レスポンス処理エラー: {str(e)}")
    
    def _create_empty_result(self, url: str, title: str, error_msg: str) -> Dict[str, Any]:
        """空の結果辞書を作成"""
        return {
            'name': '',
            'reading': '',
            'age': None,
            'birth_date': '',
            'birth_place': '',
            'current_party': '',
            'party_history': [],
            'positions': [],
            'education': [],
            'career': [],
            'constituency': '',
            'election_type': '',
            'election_history': [],
            'family': '',
            'hobbies': [],
            'special_notes': '',
            'source_url': url,
            'source_title': title,
            'extracted_at': datetime.now().isoformat(),
            'extraction_method': 'llm',
            'error': error_msg
        }
    
    def extract_multiple_politicians(self, content_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        複数のコンテンツから政治家情報を抽出
        
        Args:
            content_list: URLスクレイピング結果のリスト
            
        Returns:
            抽出された政治家情報のリスト
        """
        results = []
        
        for i, content in enumerate(content_list, 1):
            try:
                logger.info(f"政治家情報抽出 {i}/{len(content_list)}: {content.get('url', 'Unknown')}")
                result = self.extract_politician_info(content)
                results.append(result)
                
            except Exception as e:
                logger.error(f"抽出エラー {i}/{len(content_list)}: {str(e)}")
                error_result = self._create_empty_result(
                    content.get('url', ''),
                    content.get('title', ''),
                    str(e)
                )
                results.append(error_result)
        
        return results