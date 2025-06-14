"""
政治エンティティ管理
政治家・政党データの管理とマスタデータ初期化
"""
import logging
from typing import List, Dict, Any, Optional
from .political_database import PoliticalDatabaseManager, Politician, Party
from ..utils.config import ConfigManager

logger = logging.getLogger(__name__)


class PoliticalEntityManager:
    """政治エンティティ管理クラス"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
        """
        self.config_manager = config_manager
        self.db_manager = PoliticalDatabaseManager(config_manager)
        logger.info("政治エンティティ管理を初期化")
    
    def initialize_master_data(self):
        """マスタデータを初期化"""
        logger.info("政治マスタデータの初期化を開始")
        
        # 政党マスタの初期化
        self._initialize_parties()
        
        # 政治家マスタの初期化
        self._initialize_politicians()
        
        logger.info("政治マスタデータの初期化が完了")
    
    def _initialize_parties(self):
        """政党マスタデータを初期化"""
        logger.info("政党マスタデータを初期化中...")
        
        parties_data = [
            # 与党
            {
                "name": "自由民主党",
                "short_name": "自民党",
                "leader": "岸田文雄",
                "founded_date": "1955-11-15",
                "ideology_score": 0.6,  # 右派・保守
                "seat_count_house": 261,  # 2021年衆院選後
                "seat_count_council": 119,  # 2022年参院選後
                "coalition_status": "与党",
                "active": True
            },
            {
                "name": "公明党",
                "short_name": "公明",
                "leader": "山口那津男",
                "founded_date": "1964-11-17",
                "ideology_score": 0.2,  # 中道右派
                "seat_count_house": 32,
                "seat_count_council": 27,
                "coalition_status": "与党",
                "active": True
            },
            
            # 野党
            {
                "name": "立憲民主党",
                "short_name": "立憲",
                "leader": "泉健太",
                "founded_date": "2017-10-03",
                "ideology_score": -0.4,  # 中道左派
                "seat_count_house": 96,
                "seat_count_council": 39,
                "coalition_status": "野党",
                "active": True
            },
            {
                "name": "日本維新の会",
                "short_name": "維新",
                "leader": "馬場伸幸",
                "founded_date": "2012-09-28",
                "ideology_score": 0.3,  # 中道右派
                "seat_count_house": 41,
                "seat_count_council": 21,
                "coalition_status": "野党",
                "active": True
            },
            {
                "name": "日本共産党",
                "short_name": "共産",
                "leader": "志位和夫",
                "founded_date": "1922-07-15",
                "ideology_score": -0.8,  # 左派
                "seat_count_house": 10,
                "seat_count_council": 11,
                "coalition_status": "野党",
                "active": True
            },
            {
                "name": "国民民主党",
                "short_name": "国民",
                "leader": "玉木雄一郎",
                "founded_date": "2018-05-07",
                "ideology_score": -0.1,  # 中道
                "seat_count_house": 11,
                "seat_count_council": 16,
                "coalition_status": "野党",
                "active": True
            },
            {
                "name": "れいわ新選組",
                "short_name": "れいわ",
                "leader": "山本太郎",
                "founded_date": "2019-04-01",
                "ideology_score": -0.7,  # 左派
                "seat_count_house": 3,
                "seat_count_council": 2,
                "coalition_status": "野党",
                "active": True
            },
            {
                "name": "社会民主党",
                "short_name": "社民",
                "leader": "福島みずほ",
                "founded_date": "1996-01-19",
                "ideology_score": -0.6,  # 左派
                "seat_count_house": 1,
                "seat_count_council": 1,
                "coalition_status": "野党",
                "active": True
            },
            {
                "name": "参政党",
                "short_name": "参政",
                "leader": "神谷宗幣",
                "founded_date": "2020-04-14",
                "ideology_score": 0.5,  # 右派
                "seat_count_house": 0,
                "seat_count_council": 1,
                "coalition_status": "野党",
                "active": True
            },
            {
                "name": "NHK党",
                "short_name": "NHK党",
                "leader": "立花孝志",
                "founded_date": "2013-06-17",
                "ideology_score": 0.0,  # 中立（単一争点政党）
                "seat_count_house": 0,
                "seat_count_council": 1,
                "coalition_status": "野党",
                "active": True
            },
            
            # 歴史的政党（非現役）
            {
                "name": "民主党",
                "short_name": "民主",
                "leader": "",
                "founded_date": "1998-04-27",
                "ideology_score": -0.3,
                "seat_count_house": 0,
                "seat_count_council": 0,
                "coalition_status": "解党",
                "active": False
            }
        ]
        
        for party_data in parties_data:
            # 既存チェック
            existing_party = self.db_manager.get_party_by_name(party_data["name"])
            if not existing_party:
                party = Party(
                    id=None,
                    name=party_data["name"],
                    short_name=party_data["short_name"],
                    leader=party_data["leader"],
                    founded_date=party_data["founded_date"],
                    ideology_score=party_data["ideology_score"],
                    seat_count_house=party_data["seat_count_house"],
                    seat_count_council=party_data["seat_count_council"],
                    coalition_status=party_data["coalition_status"],
                    active=party_data["active"],
                    created_at="",
                    updated_at=""
                )
                self.db_manager.add_party(party)
                logger.info(f"政党を追加: {party_data['name']}")
    
    def _initialize_politicians(self):
        """政治家マスタデータを初期化"""
        logger.info("政治家マスタデータを初期化中...")
        
        # 主要政治家データ
        politicians_data = [
            # 自民党
            {
                "name": "岸田文雄",
                "reading": "きしだ ふみお",
                "party": "自由民主党",
                "position": "内閣総理大臣",
                "constituency": "広島1区",
                "birth_date": "1957-07-29",
                "career": "元外務大臣、元政調会長",
                "ideology_score": 0.4,
                "active": True
            },
            {
                "name": "茂木敏充",
                "reading": "もてぎ としみつ",
                "party": "自由民主党", 
                "position": "幹事長",
                "constituency": "栃木5区",
                "birth_date": "1955-10-07",
                "career": "元外務大臣、元経済産業大臣",
                "ideology_score": 0.5,
                "active": True
            },
            {
                "name": "林芳正",
                "reading": "はやし よしまさ",
                "party": "自由民主党",
                "position": "外務大臣",
                "constituency": "参議院山口県",
                "birth_date": "1961-01-19",
                "career": "元文部科学大臣、元農林水産大臣",
                "ideology_score": 0.3,
                "active": True
            },
            {
                "name": "鈴木俊一",
                "reading": "すずき しゅんいち",
                "party": "自由民主党",
                "position": "財務大臣",
                "constituency": "岩手2区",
                "birth_date": "1953-04-13",
                "career": "元環境大臣、元五輪担当大臣",
                "ideology_score": 0.4,
                "active": True
            },
            {
                "name": "松野博一",
                "reading": "まつの ひろかず",
                "party": "自由民主党",
                "position": "官房長官",
                "constituency": "千葉3区",
                "birth_date": "1962-09-13",
                "career": "元文部科学大臣",
                "ideology_score": 0.5,
                "active": True
            },
            {
                "name": "安倍晋三",
                "reading": "あべ しんぞう",
                "party": "自由民主党",
                "position": "元内閣総理大臣",
                "constituency": "山口4区",
                "birth_date": "1954-09-21",
                "career": "第90・96・97・98代内閣総理大臣",
                "ideology_score": 0.7,
                "active": False  # 2022年逝去
            },
            {
                "name": "菅義偉",
                "reading": "すが よしひで",
                "party": "自由民主党",
                "position": "元内閣総理大臣",
                "constituency": "神奈川2区",
                "birth_date": "1948-12-06",
                "career": "第99代内閣総理大臣、元官房長官",
                "ideology_score": 0.4,
                "active": True
            },
            {
                "name": "麻生太郎",
                "reading": "あそう たろう",
                "party": "自由民主党",
                "position": "副総裁",
                "constituency": "福岡8区",
                "birth_date": "1940-09-20",
                "career": "第92代内閣総理大臣、元財務大臣",
                "ideology_score": 0.6,
                "active": True
            },
            
            # 公明党
            {
                "name": "山口那津男",
                "reading": "やまぐち なつお",
                "party": "公明党",
                "position": "代表",
                "constituency": "参議院東京都",
                "birth_date": "1952-07-12",
                "career": "公明党代表、元国土交通大臣",
                "ideology_score": 0.2,
                "active": True
            },
            
            # 立憲民主党
            {
                "name": "泉健太",
                "reading": "いずみ けんた",
                "party": "立憲民主党",
                "position": "代表",
                "constituency": "京都3区",
                "birth_date": "1974-07-29",
                "career": "元国土交通副大臣",
                "ideology_score": -0.4,
                "active": True
            },
            {
                "name": "枝野幸男",
                "reading": "えだの ゆきお",
                "party": "立憲民主党",
                "position": "前代表",
                "constituency": "埼玉5区",
                "birth_date": "1964-05-31",
                "career": "立憲民主党創設者、元官房長官",
                "ideology_score": -0.5,
                "active": True
            },
            {
                "name": "蓮舫",
                "reading": "れんほう",
                "party": "立憲民主党",
                "position": "参議院議員",
                "constituency": "参議院東京都",
                "birth_date": "1967-11-28",
                "career": "元民主党代表代行、元行政刷新担当大臣",
                "ideology_score": -0.6,
                "active": True
            },
            
            # 日本維新の会
            {
                "name": "馬場伸幸",
                "reading": "ばば のぶゆき",
                "party": "日本維新の会",
                "position": "代表",
                "constituency": "大阪17区",
                "birth_date": "1965-02-13",
                "career": "維新政調会長",
                "ideology_score": 0.3,
                "active": True
            },
            {
                "name": "吉村洋文",
                "reading": "よしむら ひろふみ",
                "party": "日本維新の会",
                "position": "副代表",
                "constituency": "大阪府知事",
                "birth_date": "1975-06-17",
                "career": "大阪府知事、元大阪市長",
                "ideology_score": 0.4,
                "active": True
            },
            
            # 日本共産党
            {
                "name": "志位和夫",
                "reading": "しい かずお",
                "party": "日本共産党",
                "position": "委員長",
                "constituency": "比例南関東",
                "birth_date": "1954-07-29",
                "career": "共産党委員長",
                "ideology_score": -0.8,
                "active": True
            },
            
            # 国民民主党
            {
                "name": "玉木雄一郎",
                "reading": "たまき ゆういちろう",
                "party": "国民民主党",
                "position": "代表",
                "constituency": "香川2区",
                "birth_date": "1969-05-01",
                "career": "元民進党政調会長",
                "ideology_score": -0.1,
                "active": True
            },
            
            # れいわ新選組
            {
                "name": "山本太郎",
                "reading": "やまもと たろう",
                "party": "れいわ新選組",
                "position": "代表",
                "constituency": "比例東京",
                "birth_date": "1974-11-24",
                "career": "元俳優、れいわ新選組創設者",
                "ideology_score": -0.7,
                "active": True
            },
            
            # 社会民主党
            {
                "name": "福島みずほ",
                "reading": "ふくしま みずほ",
                "party": "社会民主党",
                "position": "党首",
                "constituency": "参議院比例",
                "birth_date": "1955-12-24",
                "career": "元少子化担当大臣、弁護士",
                "ideology_score": -0.6,
                "active": True
            }
        ]
        
        for politician_data in politicians_data:
            # 既存チェック
            existing_politician = self.db_manager.get_politician_by_name(politician_data["name"])
            if not existing_politician:
                # 政党IDを取得
                party = self.db_manager.get_party_by_name(politician_data["party"])
                party_id = party.id if party else None
                
                politician = Politician(
                    id=None,
                    name=politician_data["name"],
                    reading=politician_data["reading"],
                    party_id=party_id,
                    position=politician_data["position"],
                    constituency=politician_data["constituency"],
                    birth_date=politician_data["birth_date"],
                    career=politician_data["career"],
                    ideology_score=politician_data["ideology_score"],
                    active=politician_data["active"],
                    created_at="",
                    updated_at=""
                )
                self.db_manager.add_politician(politician)
                logger.info(f"政治家を追加: {politician_data['name']}")
    
    def get_politician_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        政治家情報を取得
        
        Args:
            name: 政治家名
            
        Returns:
            政治家情報辞書
        """
        politician = self.db_manager.get_politician_by_name(name)
        if not politician:
            return None
        
        # 政党情報も取得
        party = None
        if politician.party_id:
            with self.db_manager.db_path.open() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM parties WHERE id = ?', (politician.party_id,))
                party_row = cursor.fetchone()
                if party_row:
                    party = self.db_manager._row_to_party(party_row)
        
        return {
            "politician": politician,
            "party": party
        }
    
    def search_politicians(self, keyword: str) -> List[Dict[str, Any]]:
        """
        政治家を検索
        
        Args:
            keyword: 検索キーワード
            
        Returns:
            検索結果のリスト
        """
        politicians = self.db_manager.search_politicians(keyword)
        results = []
        
        for politician in politicians:
            party = None
            if politician.party_id:
                # 政党情報を取得（簡略版）
                party_name = "政党情報取得中"  # 実装簡略化
            
            results.append({
                "politician": politician,
                "party_name": party_name if politician.party_id else "無所属"
            })
        
        return results
    
    def get_party_members(self, party_name: str) -> List[Politician]:
        """
        政党のメンバーを取得
        
        Args:
            party_name: 政党名
            
        Returns:
            政党メンバーのリスト
        """
        return self.db_manager.get_politicians_by_party(party_name)
    
    def get_statistics(self) -> Dict[str, Any]:
        """エンティティ統計情報を取得"""
        return self.db_manager.get_statistics()