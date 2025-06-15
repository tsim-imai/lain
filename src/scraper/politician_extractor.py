#!/usr/bin/env python3
"""
政治家情報抽出モジュール
"""
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, date

logger = logging.getLogger(__name__)


class PoliticianExtractor:
    """政治家情報抽出クラス"""
    
    def __init__(self):
        """初期化"""
        # 政党名パターン
        self.party_patterns = [
            r'自由民主党|自民党',
            r'立憲民主党',
            r'国民民主党', 
            r'日本維新の会|維新の会|維新',
            r'公明党',
            r'日本共産党|共産党',
            r'れいわ新選組',
            r'社会民主党|社民党',
            r'NHK党',
            r'参政党',
            r'無所属'
        ]
        
        # 役職パターン
        self.position_patterns = [
            r'総理大臣|首相',
            r'副総理',
            r'官房長官',
            r'外務大臣',
            r'財務大臣',
            r'防衛大臣',
            r'厚生労働大臣',
            r'経済産業大臣',
            r'国土交通大臣',
            r'文部科学大臣',
            r'法務大臣',
            r'農林水産大臣',
            r'環境大臣',
            r'内閣府特命担当大臣',
            r'国務大臣',
            r'副大臣',
            r'政務官',
            r'党首|総裁|代表',
            r'幹事長|事務局長',
            r'政調会長',
            r'国対委員長',
            r'選対委員長'
        ]
        
        # 学歴パターン  
        self.education_patterns = [
            r'東京大学|東大',
            r'京都大学|京大',
            r'早稲田大学|早大',
            r'慶應義塾大学|慶大',
            r'一橋大学',
            r'東京工業大学|東工大',
            r'大阪大学|阪大',
            r'名古屋大学|名大',
            r'九州大学|九大',
            r'北海道大学|北大',
            r'東北大学',
            r'筑波大学',
            r'神戸大学',
            r'広島大学',
            r'千葉大学',
            r'横浜国立大学',
            r'上智大学',
            r'明治大学',
            r'青山学院大学',
            r'立教大学',
            r'中央大学',
            r'法政大学',
            r'関西大学',
            r'関西学院大学',
            r'同志社大学',
            r'立命館大学',
            r'日本大学|日大',
            r'専修大学',
            r'駒澤大学',
            r'東洋大学'
        ]
        
        logger.info("政治家情報抽出器を初期化")
    
    def extract_politician_info(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        コンテンツから政治家情報を抽出
        
        Args:
            content_data: URLスクレイパーからの結果辞書
            
        Returns:
            抽出された政治家情報辞書
        """
        try:
            text = content_data.get('text_content', '')
            title = content_data.get('title', '')
            url = content_data.get('url', '')
            
            # 基本情報を抽出
            name = self._extract_name(title, text)
            age = self._extract_age(text)
            birth_date = self._extract_birth_date(text)
            
            # 政治情報を抽出
            current_party = self._extract_current_party(text)
            party_history = self._extract_party_history(text)
            positions = self._extract_positions(text)
            
            # 学歴・経歴を抽出
            education = self._extract_education(text)
            career = self._extract_career(text)
            
            # 選挙区情報を抽出
            constituency = self._extract_constituency(text)
            
            result = {
                'name': name,
                'age': age,
                'birth_date': birth_date,
                'current_party': current_party,
                'party_history': party_history,
                'positions': positions,
                'education': education,
                'career': career,
                'constituency': constituency,
                'source_url': url,
                'source_title': title,
                'extracted_at': datetime.now().isoformat(),
                'confidence_score': self._calculate_confidence_score(text, name, current_party)
            }
            
            logger.info(f"政治家情報抽出完了: {name}")
            return result
            
        except Exception as e:
            logger.error(f"政治家情報抽出エラー: {str(e)}")
            return {
                'name': '',
                'age': None,
                'birth_date': '',
                'current_party': '',
                'party_history': [],
                'positions': [],
                'education': [],
                'career': [],
                'constituency': '',
                'source_url': content_data.get('url', ''),
                'source_title': content_data.get('title', ''),
                'extracted_at': datetime.now().isoformat(),
                'confidence_score': 0.0,
                'error': str(e)
            }
    
    def _extract_name(self, title: str, text: str) -> str:
        """名前を抽出"""
        # タイトルから名前を抽出（Wikipedia形式）
        if 'Wikipedia' in title:
            name_match = re.search(r'([^\s\-｜|]+(?:\s+[^\s\-｜|]+)*)\s*[-｜|]', title)
            if name_match:
                return name_match.group(1).strip()
        
        # タイトルから政治家名を推定
        title_parts = re.split(r'[-｜|・]', title)
        if title_parts:
            potential_name = title_parts[0].strip()
            # 日本人名パターンでチェック
            if re.search(r'^[ぁ-ん一-龯]{2,6}$', potential_name):
                return potential_name
        
        # テキストから候補者名を抽出
        name_patterns = [
            r'([一-龯ぁ-んァ-ン]{2,4})\s*([一-龯ぁ-んァ-ン]{1,3})',  # 姓名パターン
            r'議員\s*([一-龯ぁ-んァ-ン]{2,6})',
            r'代表\s*([一-龯ぁ-んァ-ン]{2,6})',
            r'([一-龯ぁ-んァ-ン]{2,6})\s*(?:氏|議員|代表|総裁|党首)'
        ]
        
        for pattern in name_patterns:
            matches = re.findall(pattern, text[:1000])  # 最初の1000文字から抽出
            if matches:
                if isinstance(matches[0], tuple):
                    return ''.join(matches[0])
                else:
                    return matches[0]
        
        return ""
    
    def _extract_age(self, text: str) -> Optional[int]:
        """年齢を抽出"""
        age_patterns = [
            r'(?:年齢|歳|才)\s*[:：]?\s*(\d{1,3})',
            r'(\d{1,3})\s*(?:歳|才)',
            r'(?:現在|今年で)\s*(\d{1,3})\s*(?:歳|才)'
        ]
        
        for pattern in age_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                age = int(match)
                if 20 <= age <= 100:  # 妥当な年齢範囲
                    return age
        
        return None
    
    def _extract_birth_date(self, text: str) -> str:
        """生年月日を抽出"""
        birth_patterns = [
            r'(\d{4})年(\d{1,2})月(\d{1,2})日\s*(?:生まれ|生)',
            r'生年月日\s*[:：]?\s*(\d{4})年(\d{1,2})月(\d{1,2})日',
            r'(?:昭和|平成|令和)(\d{1,2})年(\d{1,2})月(\d{1,2})日\s*(?:生まれ|生)'
        ]
        
        for pattern in birth_patterns:
            match = re.search(pattern, text)
            if match:
                if len(match.groups()) == 3:
                    year, month, day = match.groups()
                    return f"{year}年{month}月{day}日"
        
        return ""
    
    def _extract_current_party(self, text: str) -> str:
        """現在の所属政党を抽出"""
        # 現在形の表現で政党を探す
        current_patterns = [
            r'(?:所属|現在|現職)\s*[:：]?\s*(' + '|'.join(self.party_patterns) + ')',
            r'(' + '|'.join(self.party_patterns) + ')\s*(?:所属|議員|党員)',
            r'(' + '|'.join(self.party_patterns) + ')\s*から\s*(?:出馬|立候補)'
        ]
        
        for pattern in current_patterns:
            match = re.search(pattern, text[:2000])  # 最初の2000文字で探す
            if match:
                return match.group(1)
        
        return ""
    
    def _extract_party_history(self, text: str) -> List[str]:
        """政党履歴を抽出"""
        parties = []
        
        # 時系列順に政党移籍を探す
        history_patterns = [
            r'(\d{4})年.*?(' + '|'.join(self.party_patterns) + ')',
            r'(' + '|'.join(self.party_patterns) + ').*?から.*?(' + '|'.join(self.party_patterns) + ')',
            r'離党.*?(' + '|'.join(self.party_patterns) + ')',
            r'入党.*?(' + '|'.join(self.party_patterns) + ')'
        ]
        
        for pattern in history_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                party = match if isinstance(match, str) else match[-1]  # 最後の要素を取得
                if party not in parties:
                    parties.append(party)
        
        return parties
    
    def _extract_positions(self, text: str) -> List[str]:
        """歴任した役職を抽出"""
        positions = []
        
        for pattern in self.position_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if match not in positions:
                    positions.append(match)
        
        return positions
    
    def _extract_education(self, text: str) -> List[str]:
        """学歴を抽出"""
        education = []
        
        education_patterns = [
            r'(' + '|'.join(self.education_patterns) + ')\s*(?:卒業|修了|中退)',
            r'(?:卒業|修了|中退)\s*[:：]?\s*(' + '|'.join(self.education_patterns) + ')',
            r'学歴\s*[:：]?\s*([^。\n]*(?:' + '|'.join(self.education_patterns) + ')[^。\n]*)'
        ]
        
        for pattern in education_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if match not in education:
                    education.append(match)
        
        return education
    
    def _extract_career(self, text: str) -> List[str]:
        """経歴を抽出"""
        career = []
        
        career_patterns = [
            r'(?:経歴|職歴)\s*[:：]?\s*([^。\n]{10,100})',
            r'(\d{4})年\s*([^。\n]{5,50})',
            r'(?:勤務|就職|転職)\s*[:：]?\s*([^。\n]{5,50})',
            r'([^。\n]{5,50})\s*(?:勤務|就職|入社)'
        ]
        
        for pattern in career_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                career_item = match if isinstance(match, str) else ' '.join(match)
                if len(career_item) > 3 and career_item not in career:
                    career.append(career_item)
        
        return career[:10]  # 最大10件
    
    def _extract_constituency(self, text: str) -> str:
        """選挙区を抽出"""
        constituency_patterns = [
            r'([^。\n]*(?:選挙区|区|県|府|都|道))',
            r'選挙区\s*[:：]?\s*([^。\n]+)',
            r'([一-龯]+(?:県|府|都|道)).*?(?:選挙区|区)',
            r'([一-龯]+(?:市|区|町|村)).*?選挙区'
        ]
        
        for pattern in constituency_patterns:
            match = re.search(pattern, text)
            if match:
                constituency = match.group(1).strip()
                if len(constituency) < 20:  # 適切な長さかチェック
                    return constituency
        
        return ""
    
    def _calculate_confidence_score(self, text: str, name: str, party: str) -> float:
        """抽出の信頼度スコアを計算"""
        score = 0.0
        
        # 名前が抽出できている
        if name:
            score += 0.3
        
        # 政党が抽出できている
        if party:
            score += 0.2
        
        # 政治関連キーワードの出現数
        political_keywords = ['議員', '政治', '選挙', '国会', '政党', '内閣', '大臣']
        keyword_count = sum(1 for keyword in political_keywords if keyword in text)
        score += min(keyword_count * 0.05, 0.3)
        
        # テキスト長による信頼度
        if len(text) > 1000:
            score += 0.2
        elif len(text) > 500:
            score += 0.1
        
        return min(score, 1.0)