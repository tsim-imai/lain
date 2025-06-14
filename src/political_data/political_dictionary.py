"""
政治専門辞書システム
政治用語・人名・組織名の包括的辞書を提供
"""
import logging
import json
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from ..utils.config import ConfigManager

logger = logging.getLogger(__name__)


@dataclass
class DictionaryEntry:
    """辞書エントリデータクラス"""
    term: str
    reading: str
    category: str
    definition: str
    synonyms: List[str]
    related_terms: List[str]
    importance_score: float  # 0.0-1.0
    active: bool


class PoliticalDictionary:
    """政治専門辞書クラス"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
        """
        self.config_manager = config_manager
        self.dictionary_path = Path("data/political_dictionary.json")
        self.dictionary_path.parent.mkdir(exist_ok=True)
        
        self.entries: Dict[str, DictionaryEntry] = {}
        self._load_dictionary()
        
        if not self.entries:
            self._initialize_dictionary()
            self._save_dictionary()
        
        logger.info(f"政治専門辞書を初期化: {len(self.entries)}件のエントリ")
    
    def _initialize_dictionary(self):
        """政治専門辞書を初期化"""
        logger.info("政治専門辞書の初期データを作成中...")
        
        # 政治家辞書エントリ
        politicians_entries = [
            {
                "term": "岸田文雄",
                "reading": "きしだ ふみお",
                "category": "政治家",
                "definition": "第100・101代内閣総理大臣。自由民主党総裁。広島県出身。",
                "synonyms": ["岸田総理", "岸田首相", "総理大臣岸田文雄"],
                "related_terms": ["自由民主党", "内閣総理大臣", "新しい資本主義"],
                "importance_score": 1.0,
                "active": True
            },
            {
                "term": "安倍晋三",
                "reading": "あべ しんぞう", 
                "category": "政治家",
                "definition": "第90・96・97・98代内閣総理大臣。2022年7月8日逝去。",
                "synonyms": ["安倍元総理", "安倍元首相"],
                "related_terms": ["自由民主党", "アベノミクス", "集団的自衛権"],
                "importance_score": 1.0,
                "active": False
            },
            {
                "term": "菅義偉",
                "reading": "すが よしひで",
                "category": "政治家", 
                "definition": "第99代内閣総理大臣。自由民主党所属。元官房長官。",
                "synonyms": ["菅元総理", "菅元首相"],
                "related_terms": ["自由民主党", "デジタル庁", "携帯料金値下げ"],
                "importance_score": 0.9,
                "active": True
            },
            {
                "term": "泉健太",
                "reading": "いずみ けんた",
                "category": "政治家",
                "definition": "立憲民主党代表。京都府出身。",
                "synonyms": ["泉代表", "立憲代表"],
                "related_terms": ["立憲民主党", "野党"],
                "importance_score": 0.8,
                "active": True
            },
            {
                "term": "志位和夫", 
                "reading": "しい かずお",
                "category": "政治家",
                "definition": "日本共産党委員長。千葉県出身。",
                "synonyms": ["志位委員長", "共産党委員長"],
                "related_terms": ["日本共産党", "野党共闘"],
                "importance_score": 0.7,
                "active": True
            }
        ]
        
        # 政党辞書エントリ
        party_entries = [
            {
                "term": "自由民主党",
                "reading": "じゆうみんしゅとう",
                "category": "政党",
                "definition": "1955年設立の保守政党。現在の与党。略称は自民党。",
                "synonyms": ["自民党", "自民", "LDP"],
                "related_terms": ["与党", "保守", "岸田文雄"],
                "importance_score": 1.0,
                "active": True
            },
            {
                "term": "立憲民主党",
                "reading": "りっけんみんしゅとう",
                "category": "政党",
                "definition": "2017年設立のリベラル政党。現在の野党第一党。略称は立憲。",
                "synonyms": ["立憲", "立民"],
                "related_terms": ["野党", "リベラル", "泉健太"],
                "importance_score": 0.9,
                "active": True
            },
            {
                "term": "公明党",
                "reading": "こうめいとう",
                "category": "政党",
                "definition": "1964年設立の中道政党。自民党との連立与党。",
                "synonyms": ["公明"],
                "related_terms": ["与党", "連立政権", "創価学会"],
                "importance_score": 0.8,
                "active": True
            },
            {
                "term": "日本維新の会",
                "reading": "にっぽんいしんのかい",
                "category": "政党",
                "definition": "2012年設立の改革政党。大阪を基盤とする。略称は維新。",
                "synonyms": ["維新", "維新の会"],
                "related_terms": ["改革", "大阪", "身を切る改革"],
                "importance_score": 0.7,
                "active": True
            },
            {
                "term": "日本共産党",
                "reading": "にっぽんきょうさんとう",
                "category": "政党",
                "definition": "1922年設立の左派政党。略称は共産党。",
                "synonyms": ["共産党", "共産"],
                "related_terms": ["左派", "革新", "志位和夫"],
                "importance_score": 0.7,
                "active": True
            }
        ]
        
        # 政治制度・役職辞書エントリ
        institution_entries = [
            {
                "term": "内閣総理大臣",
                "reading": "ないかくそうりだいじん",
                "category": "政治制度",
                "definition": "日本の行政府の長。国会議員の中から国会で指名される。",
                "synonyms": ["総理大臣", "総理", "首相", "PM"],
                "related_terms": ["内閣", "行政府", "国会"],
                "importance_score": 1.0,
                "active": True
            },
            {
                "term": "官房長官", 
                "reading": "かんぼうちょうかん",
                "category": "政治制度",
                "definition": "内閣官房の長。政府のスポークスマン的役割。",
                "synonyms": ["内閣官房長官"],
                "related_terms": ["内閣", "政府発表", "記者会見"],
                "importance_score": 0.9,
                "active": True
            },
            {
                "term": "衆議院",
                "reading": "しゅうぎいん",
                "category": "政治制度",
                "definition": "国会の下院。任期4年、定数465名。",
                "synonyms": ["下院"],
                "related_terms": ["国会", "参議院", "衆議院選挙"],
                "importance_score": 1.0,
                "active": True
            },
            {
                "term": "参議院",
                "reading": "さんぎいん", 
                "category": "政治制度",
                "definition": "国会の上院。任期6年、定数248名。",
                "synonyms": ["上院"],
                "related_terms": ["国会", "衆議院", "参議院選挙"],
                "importance_score": 1.0,
                "active": True
            }
        ]
        
        # 政策・イシュー辞書エントリ
        policy_entries = [
            {
                "term": "アベノミクス",
                "reading": "あべのみくす",
                "category": "経済政策",
                "definition": "安倍政権の経済政策。三本の矢（金融緩和・財政出動・成長戦略）。",
                "synonyms": ["三本の矢"],
                "related_terms": ["安倍晋三", "経済政策", "金融緩和"],
                "importance_score": 0.9,
                "active": True
            },
            {
                "term": "新しい資本主義",
                "reading": "あたらしいしほんしゅぎ",
                "category": "経済政策",
                "definition": "岸田政権の経済政策。成長と分配の好循環を目指す。",
                "synonyms": ["新資本主義"],
                "related_terms": ["岸田文雄", "成長と分配", "分配政策"],
                "importance_score": 0.8,
                "active": True
            },
            {
                "term": "憲法改正",
                "reading": "けんぽうかいせい",
                "category": "憲法問題",
                "definition": "日本国憲法の改正。特に9条改正が争点。",
                "synonyms": ["改憲"],
                "related_terms": ["憲法9条", "自衛隊", "国民投票"],
                "importance_score": 1.0,
                "active": True
            },
            {
                "term": "集団的自衛権",
                "reading": "しゅうだんてきじえいけん",
                "category": "安全保障",
                "definition": "他国への攻撃を自国への攻撃とみなして反撃する権利。2015年に行使容認。",
                "synonyms": ["集団的自衛権の行使"],
                "related_terms": ["安全保障", "自衛隊", "日米同盟"],
                "importance_score": 0.9,
                "active": True
            }
        ]
        
        # 選挙・政治プロセス辞書エントリ
        election_entries = [
            {
                "term": "衆議院選挙",
                "reading": "しゅうぎいんせんきょ",
                "category": "選挙",
                "definition": "衆議院議員を選出する選挙。任期満了または解散により実施。",
                "synonyms": ["衆院選", "総選挙"],
                "related_terms": ["選挙", "小選挙区", "比例代表"],
                "importance_score": 1.0,
                "active": True
            },
            {
                "term": "参議院選挙",
                "reading": "さんぎいんせんきょ",
                "category": "選挙",
                "definition": "参議院議員を選出する選挙。3年ごとに半数改選。",
                "synonyms": ["参院選"],
                "related_terms": ["選挙", "選挙区", "比例代表"],
                "importance_score": 1.0,
                "active": True
            },
            {
                "term": "小選挙区制",
                "reading": "しょうせんきょくせい",
                "category": "選挙制度",
                "definition": "1つの選挙区から1名を選出する選挙制度。",
                "synonyms": ["小選挙区"],
                "related_terms": ["選挙制度", "比例代表制", "死票"],
                "importance_score": 0.8,
                "active": True
            }
        ]
        
        # 全エントリを統合
        all_entries = (politicians_entries + party_entries + 
                      institution_entries + policy_entries + election_entries)
        
        # 辞書に追加
        for entry_data in all_entries:
            entry = DictionaryEntry(**entry_data)
            self.entries[entry.term] = entry
    
    def _load_dictionary(self):
        """辞書ファイルを読み込み"""
        if self.dictionary_path.exists():
            try:
                with open(self.dictionary_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for term, entry_data in data.items():
                    self.entries[term] = DictionaryEntry(**entry_data)
                    
                logger.info(f"政治辞書を読み込み: {len(self.entries)}件")
            except Exception as e:
                logger.error(f"辞書読み込みエラー: {str(e)}")
    
    def _save_dictionary(self):
        """辞書をファイルに保存"""
        try:
            data = {}
            for term, entry in self.entries.items():
                data[term] = asdict(entry)
            
            with open(self.dictionary_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"政治辞書を保存: {len(self.entries)}件")
        except Exception as e:
            logger.error(f"辞書保存エラー: {str(e)}")
    
    def search_term(self, query: str) -> List[DictionaryEntry]:
        """
        用語を検索
        
        Args:
            query: 検索クエリ
            
        Returns:
            マッチしたエントリのリスト
        """
        results = []
        query_lower = query.lower()
        
        for entry in self.entries.values():
            # 完全一致
            if entry.term == query or query in entry.synonyms:
                results.append(entry)
                continue
            
            # 部分一致
            if (query in entry.term or 
                query_lower in entry.reading or
                any(query in synonym for synonym in entry.synonyms)):
                results.append(entry)
        
        # 重要度順にソート
        results.sort(key=lambda x: x.importance_score, reverse=True)
        return results
    
    def get_term_definition(self, term: str) -> Optional[str]:
        """
        用語の定義を取得
        
        Args:
            term: 用語
            
        Returns:
            定義文字列
        """
        entry = self.entries.get(term)
        if entry:
            return entry.definition
        
        # 同義語でも検索
        for entry in self.entries.values():
            if term in entry.synonyms:
                return entry.definition
        
        return None
    
    def get_related_terms(self, term: str) -> List[str]:
        """
        関連用語を取得
        
        Args:
            term: 用語
            
        Returns:
            関連用語のリスト
        """
        entry = self.entries.get(term)
        if entry:
            return entry.related_terms
        
        # 同義語でも検索
        for entry in self.entries.values():
            if term in entry.synonyms:
                return entry.related_terms
        
        return []
    
    def get_terms_by_category(self, category: str) -> List[DictionaryEntry]:
        """
        カテゴリ別に用語を取得
        
        Args:
            category: カテゴリ名
            
        Returns:
            該当カテゴリのエントリリスト
        """
        results = []
        for entry in self.entries.values():
            if entry.category == category and entry.active:
                results.append(entry)
        
        # 重要度順にソート
        results.sort(key=lambda x: x.importance_score, reverse=True)
        return results
    
    def add_term(self, entry: DictionaryEntry) -> bool:
        """
        新しい用語を追加
        
        Args:
            entry: 辞書エントリ
            
        Returns:
            追加成功時True
        """
        try:
            self.entries[entry.term] = entry
            self._save_dictionary()
            logger.info(f"用語を追加: {entry.term}")
            return True
        except Exception as e:
            logger.error(f"用語追加エラー: {str(e)}")
            return False
    
    def update_term(self, term: str, **kwargs) -> bool:
        """
        用語を更新
        
        Args:
            term: 更新する用語
            **kwargs: 更新フィールド
            
        Returns:
            更新成功時True
        """
        if term not in self.entries:
            return False
        
        try:
            entry = self.entries[term]
            for key, value in kwargs.items():
                if hasattr(entry, key):
                    setattr(entry, key, value)
            
            self._save_dictionary()
            logger.info(f"用語を更新: {term}")
            return True
        except Exception as e:
            logger.error(f"用語更新エラー: {str(e)}")
            return False
    
    def get_categories(self) -> List[str]:
        """全カテゴリを取得"""
        categories = set()
        for entry in self.entries.values():
            categories.add(entry.category)
        return sorted(list(categories))
    
    def get_statistics(self) -> Dict[str, Any]:
        """辞書統計情報を取得"""
        total_entries = len(self.entries)
        active_entries = sum(1 for entry in self.entries.values() if entry.active)
        categories = self.get_categories()
        
        category_counts = {}
        for category in categories:
            category_counts[category] = len(self.get_terms_by_category(category))
        
        return {
            "total_entries": total_entries,
            "active_entries": active_entries,
            "categories": categories,
            "category_counts": category_counts
        }