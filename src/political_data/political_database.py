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
import json
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


# === 学習データ用データクラス ===

@dataclass
class PoliticalNews:
    """政治ニュース記事データクラス"""
    id: Optional[int]
    title: str
    content: Optional[str]
    summary: Optional[str]
    url: Optional[str]
    source_name: str
    published_at: Optional[str]
    collected_at: str
    reliability_score: float
    political_bias: float
    topic_category: Optional[str]
    sentiment_score: float
    entity_mentions: Dict[str, Any]
    keywords: List[str]


@dataclass  
class SocialPost:
    """SNS投稿データクラス"""
    id: Optional[int]
    platform: str
    account_name: Optional[str]
    account_type: str  # politician/influencer/general
    content: str
    posted_at: Optional[str]
    collected_at: str
    engagement_data: Dict[str, Any]
    sentiment_score: float
    reliability_score: float
    hashtags: Optional[str]
    mentioned_entities: Dict[str, Any]
    political_topics: List[str]


@dataclass
class GovernmentAnnouncement:
    """政府発表データクラス"""
    id: Optional[int]
    agency: str
    title: str
    content: Optional[str]
    announced_at: Optional[str]
    collected_at: str
    category: Optional[str]
    importance_level: int
    related_policies: Dict[str, Any]
    implementation_date: Optional[str]
    url: Optional[str]
    document_type: str


@dataclass
class OpinionPoll:
    """拡張世論調査データクラス"""
    id: Optional[int]
    organization: str
    poll_date: Optional[str]
    sample_size: Optional[int]
    methodology: Optional[str]
    questions: Dict[str, Any]
    results: Dict[str, Any]
    reliability_score: float
    collected_at: str
    margin_of_error: Optional[float]
    response_rate: Optional[float]
    demographic_breakdown: Dict[str, Any]


@dataclass
class ElectionData:
    """拡張選挙データクラス"""
    id: Optional[int]
    election_type: str
    election_date: Optional[str]
    region: Optional[str]
    constituency: Optional[str]
    candidates: Dict[str, Any]
    results: Dict[str, Any]
    turnout_rate: Optional[float]
    predictions: Dict[str, Any]
    collected_at: str
    total_voters: Optional[int]
    valid_votes: Optional[int]
    invalid_votes: Optional[int]


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
            
            # === 学習データ用テーブル ===
            
            # 政治ニュース記事テーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS political_news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT,
                    summary TEXT,
                    url TEXT UNIQUE,
                    source_name TEXT,
                    published_at TIMESTAMP,
                    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reliability_score REAL DEFAULT 0.5,
                    political_bias REAL DEFAULT 0.0,
                    topic_category TEXT,
                    sentiment_score REAL DEFAULT 0.0,
                    entity_mentions TEXT, -- JSON format
                    keywords TEXT -- comma separated
                )
            ''')
            
            # SNS投稿データテーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS social_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    account_name TEXT,
                    account_type TEXT, -- politician/influencer/general
                    content TEXT NOT NULL,
                    posted_at TIMESTAMP,
                    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    engagement_data TEXT, -- JSON format (likes, retweets, etc.)
                    sentiment_score REAL DEFAULT 0.0,
                    reliability_score REAL DEFAULT 0.5,
                    hashtags TEXT,
                    mentioned_entities TEXT, -- JSON format
                    political_topics TEXT -- JSON format
                )
            ''')
            
            # 政府発表データテーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS government_announcements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agency TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT,
                    announced_at TIMESTAMP,
                    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    category TEXT,
                    importance_level INTEGER DEFAULT 5, -- 1-10
                    related_policies TEXT, -- JSON format
                    implementation_date TIMESTAMP,
                    url TEXT,
                    document_type TEXT -- press_release/cabinet_decision/etc
                )
            ''')
            
            # 拡張世論調査データテーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS opinion_polls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    organization TEXT NOT NULL,
                    poll_date TIMESTAMP,
                    sample_size INTEGER,
                    methodology TEXT,
                    questions TEXT, -- JSON format
                    results TEXT, -- JSON format
                    reliability_score REAL DEFAULT 0.5,
                    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    margin_of_error REAL,
                    response_rate REAL,
                    demographic_breakdown TEXT -- JSON format
                )
            ''')
            
            # 拡張選挙データテーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS election_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    election_type TEXT NOT NULL,
                    election_date DATE,
                    region TEXT,
                    constituency TEXT,
                    candidates TEXT, -- JSON format
                    results TEXT, -- JSON format
                    turnout_rate REAL,
                    predictions TEXT, -- JSON format
                    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_voters INTEGER,
                    valid_votes INTEGER,
                    invalid_votes INTEGER
                )
            ''')
            
            # データ品質管理テーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS data_quality (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT NOT NULL,
                    record_id INTEGER NOT NULL,
                    quality_score REAL DEFAULT 0.5,
                    completeness REAL DEFAULT 0.5,
                    accuracy REAL DEFAULT 0.5,
                    timeliness REAL DEFAULT 0.5,
                    verification_status TEXT DEFAULT 'unverified',
                    last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT
                )
            ''')
            
            # インデックス作成
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_politicians_name ON politicians(name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_politicians_party ON politicians(party_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_elections_date ON elections(election_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_polls_date ON polls(poll_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_polls_target ON polls(target)')
            
            # 学習データ用インデックス
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_political_news_date ON political_news(published_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_political_news_source ON political_news(source_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_political_news_topic ON political_news(topic_category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_social_posts_date ON social_posts(posted_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_social_posts_platform ON social_posts(platform)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_government_announcements_date ON government_announcements(announced_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_government_announcements_agency ON government_announcements(agency)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_opinion_polls_date ON opinion_polls(poll_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_election_data_date ON election_data(election_date)')
            
            # 全文検索用仮想テーブル
            cursor.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS news_fts USING fts5(
                    title, content, 
                    content='political_news', 
                    content_rowid='id'
                )
            ''')
            
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
    
    # === 学習データ保存メソッド ===
    
    def save_political_news(self, news: PoliticalNews) -> Optional[int]:
        """
        政治ニュース記事を保存
        
        Args:
            news: 政治ニュース記事データ
            
        Returns:
            保存されたニュースのID（重複の場合はNone）
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 重複チェック（URL）
                if news.url:
                    cursor.execute('SELECT id FROM political_news WHERE url = ?', (news.url,))
                    if cursor.fetchone():
                        logger.debug(f"重複ニュースをスキップ: {news.url}")
                        return None
                
                cursor.execute('''
                    INSERT INTO political_news (
                        title, content, summary, url, source_name, published_at,
                        reliability_score, political_bias, topic_category, sentiment_score,
                        entity_mentions, keywords
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    news.title, news.content, news.summary, news.url, news.source_name,
                    news.published_at, news.reliability_score, news.political_bias,
                    news.topic_category, news.sentiment_score,
                    json.dumps(news.entity_mentions, ensure_ascii=False),
                    ','.join(news.keywords) if news.keywords else ''
                ))
                
                news_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"政治ニュースを保存: {news.title[:30]}... (ID: {news_id})")
                return news_id
                
        except Exception as e:
            logger.error(f"政治ニュース保存エラー: {str(e)}")
            return None
    
    def save_social_post(self, post: SocialPost) -> Optional[int]:
        """
        SNS投稿を保存
        
        Args:
            post: SNS投稿データ
            
        Returns:
            保存された投稿のID（重複の場合はNone）
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 重複チェック（同一アカウント・同一内容・同一時刻）
                cursor.execute('''
                    SELECT id FROM social_posts 
                    WHERE account_name = ? AND content = ? AND posted_at = ?
                ''', (post.account_name, post.content, post.posted_at))
                
                if cursor.fetchone():
                    logger.debug(f"重複SNS投稿をスキップ: {post.account_name}")
                    return None
                
                cursor.execute('''
                    INSERT INTO social_posts (
                        platform, account_name, account_type, content, posted_at,
                        engagement_data, sentiment_score, reliability_score, hashtags,
                        mentioned_entities, political_topics
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    post.platform, post.account_name, post.account_type, post.content,
                    post.posted_at, json.dumps(post.engagement_data, ensure_ascii=False),
                    post.sentiment_score, post.reliability_score, post.hashtags,
                    json.dumps(post.mentioned_entities, ensure_ascii=False),
                    json.dumps(post.political_topics, ensure_ascii=False)
                ))
                
                post_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"SNS投稿を保存: {post.platform}@{post.account_name} (ID: {post_id})")
                return post_id
                
        except Exception as e:
            logger.error(f"SNS投稿保存エラー: {str(e)}")
            return None
    
    def save_government_announcement(self, announcement: GovernmentAnnouncement) -> Optional[int]:
        """
        政府発表を保存
        
        Args:
            announcement: 政府発表データ
            
        Returns:
            保存された発表のID（重複の場合はNone）
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 重複チェック（機関・タイトル・発表日時）
                cursor.execute('''
                    SELECT id FROM government_announcements
                    WHERE agency = ? AND title = ? AND announced_at = ?
                ''', (announcement.agency, announcement.title, announcement.announced_at))
                
                if cursor.fetchone():
                    logger.debug(f"重複政府発表をスキップ: {announcement.title[:30]}...")
                    return None
                
                cursor.execute('''
                    INSERT INTO government_announcements (
                        agency, title, content, announced_at, category, importance_level,
                        related_policies, implementation_date, url, document_type
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    announcement.agency, announcement.title, announcement.content,
                    announcement.announced_at, announcement.category, announcement.importance_level,
                    json.dumps(announcement.related_policies, ensure_ascii=False),
                    announcement.implementation_date, announcement.url, announcement.document_type
                ))
                
                announcement_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"政府発表を保存: {announcement.agency} - {announcement.title[:30]}... (ID: {announcement_id})")
                return announcement_id
                
        except Exception as e:
            logger.error(f"政府発表保存エラー: {str(e)}")
            return None
    
    def save_opinion_poll(self, poll: OpinionPoll) -> Optional[int]:
        """
        世論調査データを保存
        
        Args:
            poll: 世論調査データ
            
        Returns:
            保存された調査のID（重複の場合はNone）
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 重複チェック（調査機関・調査日）
                cursor.execute('''
                    SELECT id FROM opinion_polls
                    WHERE organization = ? AND poll_date = ?
                ''', (poll.organization, poll.poll_date))
                
                if cursor.fetchone():
                    logger.debug(f"重複世論調査をスキップ: {poll.organization} {poll.poll_date}")
                    return None
                
                cursor.execute('''
                    INSERT INTO opinion_polls (
                        organization, poll_date, sample_size, methodology, questions, results,
                        reliability_score, margin_of_error, response_rate, demographic_breakdown
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    poll.organization, poll.poll_date, poll.sample_size, poll.methodology,
                    json.dumps(poll.questions, ensure_ascii=False),
                    json.dumps(poll.results, ensure_ascii=False),
                    poll.reliability_score, poll.margin_of_error, poll.response_rate,
                    json.dumps(poll.demographic_breakdown, ensure_ascii=False)
                ))
                
                poll_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"世論調査を保存: {poll.organization} {poll.poll_date} (ID: {poll_id})")
                return poll_id
                
        except Exception as e:
            logger.error(f"世論調査保存エラー: {str(e)}")
            return None
    
    def save_election_data(self, election: ElectionData) -> Optional[int]:
        """
        選挙データを保存
        
        Args:
            election: 選挙データ
            
        Returns:
            保存された選挙のID（重複の場合はNone）
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 重複チェック（選挙種別・選挙日・地域）
                cursor.execute('''
                    SELECT id FROM election_data
                    WHERE election_type = ? AND election_date = ? AND region = ?
                ''', (election.election_type, election.election_date, election.region))
                
                if cursor.fetchone():
                    logger.debug(f"重複選挙データをスキップ: {election.election_type} {election.election_date}")
                    return None
                
                cursor.execute('''
                    INSERT INTO election_data (
                        election_type, election_date, region, constituency, candidates, results,
                        turnout_rate, predictions, total_voters, valid_votes, invalid_votes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    election.election_type, election.election_date, election.region,
                    election.constituency, json.dumps(election.candidates, ensure_ascii=False),
                    json.dumps(election.results, ensure_ascii=False), election.turnout_rate,
                    json.dumps(election.predictions, ensure_ascii=False),
                    election.total_voters, election.valid_votes, election.invalid_votes
                ))
                
                election_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"選挙データを保存: {election.election_type} {election.election_date} (ID: {election_id})")
                return election_id
                
        except Exception as e:
            logger.error(f"選挙データ保存エラー: {str(e)}")
            return None
    
    # === 学習データ検索メソッド ===
    
    def search_political_news(self, 
                            keyword: Optional[str] = None,
                            source: Optional[str] = None,
                            topic: Optional[str] = None,
                            days_back: int = 30,
                            limit: int = 100) -> List[PoliticalNews]:
        """政治ニュースを検索"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                conditions = ["published_at >= date('now', '-{} days')".format(days_back)]
                params = []
                
                if keyword:
                    conditions.append("(title LIKE ? OR content LIKE ?)")
                    params.extend([f'%{keyword}%', f'%{keyword}%'])
                
                if source:
                    conditions.append("source_name = ?")
                    params.append(source)
                
                if topic:
                    conditions.append("topic_category = ?")
                    params.append(topic)
                
                query = f'''
                    SELECT * FROM political_news
                    WHERE {' AND '.join(conditions)}
                    ORDER BY published_at DESC
                    LIMIT ?
                '''
                params.append(limit)
                
                cursor.execute(query, params)
                return [self._row_to_political_news(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"政治ニュース検索エラー: {str(e)}")
            return []
    
    def get_latest_social_posts(self, 
                              platform: Optional[str] = None,
                              account_type: Optional[str] = None,
                              days_back: int = 7,
                              limit: int = 50) -> List[SocialPost]:
        """最新のSNS投稿を取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                conditions = ["posted_at >= date('now', '-{} days')".format(days_back)]
                params = []
                
                if platform:
                    conditions.append("platform = ?")
                    params.append(platform)
                
                if account_type:
                    conditions.append("account_type = ?")
                    params.append(account_type)
                
                query = f'''
                    SELECT * FROM social_posts
                    WHERE {' AND '.join(conditions)}
                    ORDER BY posted_at DESC
                    LIMIT ?
                '''
                params.append(limit)
                
                cursor.execute(query, params)
                return [self._row_to_social_post(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"SNS投稿取得エラー: {str(e)}")
            return []
    
    def get_cache_status(self, query: str, hours: int = 24) -> Dict[str, Any]:
        """キャッシュ状況をチェック"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 指定時間内のデータ件数を確認
                cutoff_time = f"datetime('now', '-{hours} hours')"
                
                cursor.execute(f'''
                    SELECT COUNT(*) FROM political_news 
                    WHERE (title LIKE ? OR content LIKE ?) AND collected_at >= {cutoff_time}
                ''', (f'%{query}%', f'%{query}%'))
                news_count = cursor.fetchone()[0]
                
                cursor.execute(f'''
                    SELECT COUNT(*) FROM social_posts 
                    WHERE content LIKE ? AND collected_at >= {cutoff_time}
                ''', (f'%{query}%',))
                social_count = cursor.fetchone()[0]
                
                return {
                    "query": query,
                    "hours": hours,
                    "news_count": news_count,
                    "social_count": social_count,
                    "has_fresh_data": (news_count + social_count) > 0,
                    "last_update": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"キャッシュ状況確認エラー: {str(e)}")
            return {"has_fresh_data": False, "error": str(e)}
    
    def _row_to_political_news(self, row: tuple) -> PoliticalNews:
        """データベース行を政治ニュースオブジェクトに変換"""
        return PoliticalNews(
            id=row[0], title=row[1], content=row[2], summary=row[3], url=row[4],
            source_name=row[5], published_at=row[6], collected_at=row[7],
            reliability_score=row[8], political_bias=row[9], topic_category=row[10],
            sentiment_score=row[11],
            entity_mentions=json.loads(row[12]) if row[12] else {},
            keywords=row[13].split(',') if row[13] else []
        )
    
    def _row_to_social_post(self, row: tuple) -> SocialPost:
        """データベース行をSNS投稿オブジェクトに変換"""
        return SocialPost(
            id=row[0], platform=row[1], account_name=row[2], account_type=row[3],
            content=row[4], posted_at=row[5], collected_at=row[6],
            engagement_data=json.loads(row[7]) if row[7] else {},
            sentiment_score=row[8], reliability_score=row[9], hashtags=row[10],
            mentioned_entities=json.loads(row[11]) if row[11] else {},
            political_topics=json.loads(row[12]) if row[12] else []
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
            
            # 学習データ統計
            cursor.execute('SELECT COUNT(*) FROM political_news')
            stats['political_news'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM social_posts')
            stats['social_posts'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM government_announcements')
            stats['government_announcements'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM opinion_polls')
            stats['opinion_polls'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM election_data')
            stats['election_data'] = cursor.fetchone()[0]
            
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