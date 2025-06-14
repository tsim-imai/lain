"""
政治データベース管理
政治関連データの永続化・検索・管理を提供
"""
import logging
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from ..utils.config import ConfigManager

logger = logging.getLogger(__name__)


@dataclass
class Politician:
    """政治家データクラス"""
    id: Optional[int]
    name: str
    reading: str  # ふりがな
    party_id: Optional[int]
    position: str
    constituency: str
    birth_date: Optional[str]
    career: str
    ideology_score: Optional[float]  # イデオロギースコア（-1.0〜1.0）
    active: bool
    created_at: str
    updated_at: str


@dataclass
class Party:
    """政党データクラス"""
    id: Optional[int]
    name: str
    short_name: str
    leader: str
    founded_date: Optional[str]
    ideology_score: float  # イデオロギースコア（-1.0:左派 〜 1.0:右派）
    seat_count_house: int  # 衆議院議席数
    seat_count_council: int  # 参議院議席数
    coalition_status: str  # 与党/野党/中立
    active: bool
    created_at: str
    updated_at: str


@dataclass
class Election:
    """選挙データクラス"""
    id: Optional[int]
    election_type: str  # 衆議院/参議院/統一地方選挙等
    election_date: str
    region: str
    constituency: str
    candidate_name: str
    party_name: str
    votes: int
    is_elected: bool
    vote_share: float
    turnout_rate: Optional[float]
    created_at: str


@dataclass
class Poll:
    """世論調査データクラス"""
    id: Optional[int]
    pollster: str  # 調査機関
    poll_date: str
    question_type: str  # 内閣支持率/政党支持率/選挙予測等
    target: str  # 対象（内閣/政党名/候補者名）
    support_rate: float
    sample_size: int
    methodology: str  # 調査方法
    reliability_score: float
    created_at: str


class PoliticalDatabaseManager:
    """政治データベース管理クラス"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
        """
        self.config_manager = config_manager
        self.db_path = Path("data/political.db")
        self.db_path.parent.mkdir(exist_ok=True)
        
        self._initialize_database()
        logger.info(f"政治データベースを初期化: {self.db_path}")
    
    def _initialize_database(self):
        """データベーステーブルを初期化"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 政治家マスタテーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS politicians (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    reading TEXT NOT NULL,
                    party_id INTEGER,
                    position TEXT,
                    constituency TEXT,
                    birth_date TEXT,
                    career TEXT,
                    ideology_score REAL,
                    active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (party_id) REFERENCES parties (id)
                )
            ''')
            
            # 政党マスタテーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS parties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    short_name TEXT,
                    leader TEXT,
                    founded_date TEXT,
                    ideology_score REAL DEFAULT 0.0,
                    seat_count_house INTEGER DEFAULT 0,
                    seat_count_council INTEGER DEFAULT 0,
                    coalition_status TEXT DEFAULT '野党',
                    active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 選挙データテーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS elections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    election_type TEXT NOT NULL,
                    election_date TEXT NOT NULL,
                    region TEXT,
                    constituency TEXT,
                    candidate_name TEXT,
                    party_name TEXT,
                    votes INTEGER,
                    is_elected BOOLEAN,
                    vote_share REAL,
                    turnout_rate REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 世論調査データテーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS polls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pollster TEXT NOT NULL,
                    poll_date TEXT NOT NULL,
                    question_type TEXT,
                    target TEXT,
                    support_rate REAL,
                    sample_size INTEGER,
                    methodology TEXT,
                    reliability_score REAL DEFAULT 0.5,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # インデックス作成
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_politicians_name ON politicians(name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_politicians_party ON politicians(party_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_elections_date ON elections(election_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_polls_date ON polls(poll_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_polls_target ON polls(target)')
            
            conn.commit()
    
    def add_politician(self, politician: Politician) -> int:
        """
        政治家を追加
        
        Args:
            politician: 政治家データ
            
        Returns:
            追加された政治家のID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO politicians (
                    name, reading, party_id, position, constituency,
                    birth_date, career, ideology_score, active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                politician.name, politician.reading, politician.party_id,
                politician.position, politician.constituency, politician.birth_date,
                politician.career, politician.ideology_score, politician.active
            ))
            politician_id = cursor.lastrowid
            conn.commit()
            
        logger.info(f"政治家を追加: {politician.name} (ID: {politician_id})")
        return politician_id
    
    def add_party(self, party: Party) -> int:
        """
        政党を追加
        
        Args:
            party: 政党データ
            
        Returns:
            追加された政党のID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO parties (
                    name, short_name, leader, founded_date, ideology_score,
                    seat_count_house, seat_count_council, coalition_status, active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                party.name, party.short_name, party.leader, party.founded_date,
                party.ideology_score, party.seat_count_house, party.seat_count_council,
                party.coalition_status, party.active
            ))
            party_id = cursor.lastrowid
            conn.commit()
            
        logger.info(f"政党を追加: {party.name} (ID: {party_id})")
        return party_id
    
    def get_politician_by_name(self, name: str) -> Optional[Politician]:
        """名前で政治家を検索"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM politicians WHERE name = ? AND active = 1
            ''', (name,))
            
            row = cursor.fetchone()
            if row:
                return self._row_to_politician(row)
        
        return None
    
    def get_party_by_name(self, name: str) -> Optional[Party]:
        """名前で政党を検索"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM parties WHERE (name = ? OR short_name = ?) AND active = 1
            ''', (name, name))
            
            row = cursor.fetchone()
            if row:
                return self._row_to_party(row)
        
        return None
    
    def get_politicians_by_party(self, party_name: str) -> List[Politician]:
        """政党名で政治家を検索"""
        party = self.get_party_by_name(party_name)
        if not party:
            return []
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM politicians WHERE party_id = ? AND active = 1
                ORDER BY position, name
            ''', (party.id,))
            
            return [self._row_to_politician(row) for row in cursor.fetchall()]
    
    def get_latest_polls(self, target: str, limit: int = 10) -> List[Poll]:
        """最新の世論調査データを取得"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM polls WHERE target = ?
                ORDER BY poll_date DESC LIMIT ?
            ''', (target, limit))
            
            return [self._row_to_poll(row) for row in cursor.fetchall()]
    
    def get_election_results(self, election_type: str, election_date: str) -> List[Election]:
        """選挙結果を取得"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM elections 
                WHERE election_type = ? AND election_date = ?
                ORDER BY votes DESC
            ''', (election_type, election_date))
            
            return [self._row_to_election(row) for row in cursor.fetchall()]
    
    def search_politicians(self, keyword: str) -> List[Politician]:
        """キーワードで政治家を検索"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM politicians 
                WHERE (name LIKE ? OR reading LIKE ? OR position LIKE ? OR constituency LIKE ?)
                AND active = 1
                ORDER BY name
            ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
            
            return [self._row_to_politician(row) for row in cursor.fetchall()]
    
    def _row_to_politician(self, row: tuple) -> Politician:
        """データベース行を政治家オブジェクトに変換"""
        return Politician(
            id=row[0], name=row[1], reading=row[2], party_id=row[3],
            position=row[4], constituency=row[5], birth_date=row[6],
            career=row[7], ideology_score=row[8], active=bool(row[9]),
            created_at=row[10], updated_at=row[11]
        )
    
    def _row_to_party(self, row: tuple) -> Party:
        """データベース行を政党オブジェクトに変換"""
        return Party(
            id=row[0], name=row[1], short_name=row[2], leader=row[3],
            founded_date=row[4], ideology_score=row[5], seat_count_house=row[6],
            seat_count_council=row[7], coalition_status=row[8], active=bool(row[9]),
            created_at=row[10], updated_at=row[11]
        )
    
    def _row_to_election(self, row: tuple) -> Election:
        """データベース行を選挙オブジェクトに変換"""
        return Election(
            id=row[0], election_type=row[1], election_date=row[2], region=row[3],
            constituency=row[4], candidate_name=row[5], party_name=row[6],
            votes=row[7], is_elected=bool(row[8]), vote_share=row[9],
            turnout_rate=row[10], created_at=row[11]
        )
    
    def _row_to_poll(self, row: tuple) -> Poll:
        """データベース行を世論調査オブジェクトに変換"""
        return Poll(
            id=row[0], pollster=row[1], poll_date=row[2], question_type=row[3],
            target=row[4], support_rate=row[5], sample_size=row[6],
            methodology=row[7], reliability_score=row[8], created_at=row[9]
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """データベース統計情報を取得"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 各テーブルのレコード数を取得
            stats = {}
            
            cursor.execute('SELECT COUNT(*) FROM politicians WHERE active = 1')
            stats['active_politicians'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM parties WHERE active = 1')
            stats['active_parties'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM elections')
            stats['election_records'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM polls')
            stats['poll_records'] = cursor.fetchone()[0]
            
            return stats
    
    def test_connection(self) -> bool:
        """データベース接続テスト"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1')
                result = cursor.fetchone()
                return result is not None
        except Exception as e:
            logger.error(f"データベース接続テスト失敗: {str(e)}")
            return False