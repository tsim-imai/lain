"""
立候補者データベース管理システム
2025年選挙候補者の詳細プロフィール・政策・支援基盤を管理
"""
import logging
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json

from ..utils.config import ConfigManager
from ..utils.exceptions import AnalysisError

logger = logging.getLogger(__name__)


@dataclass
class Candidate:
    """候補者データクラス"""
    id: Optional[int]
    name: str
    reading: str  # ふりがな
    party: str
    constituency_id: str
    status: str  # 現職/元職/新人
    age: int
    gender: str
    education: str
    career: List[str]
    policy_positions: Dict[str, str]
    support_organizations: List[str]
    past_elections: List[Dict[str, Any]]
    recognition_rate: float
    support_rate: float
    fundraising_amount: Optional[int]
    social_media: Dict[str, str]
    strengths: List[str]
    weaknesses: List[str]
    created_at: str
    updated_at: str


@dataclass
class PolicyPosition:
    """政策立場データクラス"""
    candidate_id: int
    policy_area: str
    position: str
    priority: int  # 1-10
    details: str
    source_url: Optional[str]
    last_updated: str


@dataclass
class CampaignData:
    """選挙活動データクラス"""
    candidate_id: int
    activity_date: str
    activity_type: str  # 演説/街頭活動/政策発表/討論会等
    location: str
    attendance: Optional[int]
    media_coverage: bool
    key_messages: List[str]
    public_reaction: str


class CandidateDatabase:
    """立候補者データベース管理クラス"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
        """
        self.config_manager = config_manager
        self.db_path = Path("data/candidates_2025.db")
        self.db_path.parent.mkdir(exist_ok=True)
        
        self._initialize_database()
        
        # 主要政策分野
        self.policy_areas = [
            "経済政策", "外交・安全保障", "社会保障", "教育", "環境・エネルギー",
            "地方創生", "憲法", "労働政策", "子育て支援", "高齢者対策",
            "デジタル政策", "科学技術", "農業", "中小企業支援", "税制"
        ]
        
        logger.info(f"候補者データベースを初期化: {self.db_path}")
    
    def _initialize_database(self):
        """データベーステーブルを初期化"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 候補者基本情報テーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    reading TEXT NOT NULL,
                    party TEXT NOT NULL,
                    constituency_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    age INTEGER,
                    gender TEXT,
                    education TEXT,
                    career TEXT, -- JSON format
                    support_organizations TEXT, -- JSON format
                    past_elections TEXT, -- JSON format
                    recognition_rate REAL DEFAULT 0.0,
                    support_rate REAL DEFAULT 0.0,
                    fundraising_amount INTEGER,
                    social_media TEXT, -- JSON format
                    strengths TEXT, -- JSON format
                    weaknesses TEXT, -- JSON format
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 政策立場テーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS policy_positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    candidate_id INTEGER NOT NULL,
                    policy_area TEXT NOT NULL,
                    position TEXT NOT NULL,
                    priority INTEGER DEFAULT 5,
                    details TEXT,
                    source_url TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (candidate_id) REFERENCES candidates (id)
                )
            ''')
            
            # 選挙活動データテーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS campaign_activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    candidate_id INTEGER NOT NULL,
                    activity_date DATE NOT NULL,
                    activity_type TEXT NOT NULL,
                    location TEXT,
                    attendance INTEGER,
                    media_coverage BOOLEAN DEFAULT 0,
                    key_messages TEXT, -- JSON format
                    public_reaction TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (candidate_id) REFERENCES candidates (id)
                )
            ''')
            
            # 支持基盤分析テーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS support_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    candidate_id INTEGER NOT NULL,
                    support_segment TEXT NOT NULL, -- 年代/職業/地域等
                    support_rate REAL,
                    confidence_level REAL,
                    analysis_date DATE,
                    source TEXT,
                    notes TEXT,
                    FOREIGN KEY (candidate_id) REFERENCES candidates (id)
                )
            ''')
            
            # 対立候補比較テーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS candidate_comparisons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    constituency_id TEXT NOT NULL,
                    candidate1_id INTEGER NOT NULL,
                    candidate2_id INTEGER NOT NULL,
                    comparison_category TEXT NOT NULL,
                    candidate1_score REAL,
                    candidate2_score REAL,
                    analysis_notes TEXT,
                    comparison_date DATE,
                    FOREIGN KEY (candidate1_id) REFERENCES candidates (id),
                    FOREIGN KEY (candidate2_id) REFERENCES candidates (id)
                )
            ''')
            
            # インデックス作成
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_candidates_constituency ON candidates(constituency_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_candidates_party ON candidates(party)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_policy_positions_candidate ON policy_positions(candidate_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_campaign_activities_candidate ON campaign_activities(candidate_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_support_analysis_candidate ON support_analysis(candidate_id)')
            
            conn.commit()
    
    def add_candidate(self, candidate: Candidate) -> int:
        """
        候補者を追加
        
        Args:
            candidate: 候補者データ
            
        Returns:
            追加された候補者のID
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO candidates (
                        name, reading, party, constituency_id, status, age, gender, education,
                        career, support_organizations, past_elections, recognition_rate,
                        support_rate, fundraising_amount, social_media, strengths, weaknesses
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    candidate.name, candidate.reading, candidate.party, candidate.constituency_id,
                    candidate.status, candidate.age, candidate.gender, candidate.education,
                    json.dumps(candidate.career, ensure_ascii=False),
                    json.dumps(candidate.support_organizations, ensure_ascii=False),
                    json.dumps(candidate.past_elections, ensure_ascii=False),
                    candidate.recognition_rate, candidate.support_rate, candidate.fundraising_amount,
                    json.dumps(candidate.social_media, ensure_ascii=False),
                    json.dumps(candidate.strengths, ensure_ascii=False),
                    json.dumps(candidate.weaknesses, ensure_ascii=False)
                ))
                
                candidate_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"候補者を追加: {candidate.name} ({candidate.party}) - ID: {candidate_id}")
                return candidate_id
                
        except Exception as e:
            logger.error(f"候補者追加エラー: {str(e)}")
            raise AnalysisError(f"候補者追加に失敗しました: {str(e)}")
    
    def get_candidates_by_constituency(self, constituency_id: str) -> List[Candidate]:
        """
        選挙区別候補者一覧を取得
        
        Args:
            constituency_id: 選挙区ID
            
        Returns:
            候補者リスト
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM candidates WHERE constituency_id = ?
                    ORDER BY party, support_rate DESC
                ''', (constituency_id,))
                
                candidates = []
                for row in cursor.fetchall():
                    candidate = self._row_to_candidate(row)
                    candidates.append(candidate)
                
                logger.info(f"選挙区候補者取得: {constituency_id} - {len(candidates)}名")
                return candidates
                
        except Exception as e:
            logger.error(f"選挙区候補者取得エラー ({constituency_id}): {str(e)}")
            return []
    
    def add_policy_position(self, policy: PolicyPosition) -> int:
        """
        政策立場を追加
        
        Args:
            policy: 政策立場データ
            
        Returns:
            追加された政策立場のID
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO policy_positions (
                        candidate_id, policy_area, position, priority, details, source_url
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    policy.candidate_id, policy.policy_area, policy.position,
                    policy.priority, policy.details, policy.source_url
                ))
                
                policy_id = cursor.lastrowid
                conn.commit()
                
                logger.debug(f"政策立場を追加: 候補者ID {policy.candidate_id} - {policy.policy_area}")
                return policy_id
                
        except Exception as e:
            logger.error(f"政策立場追加エラー: {str(e)}")
            raise AnalysisError(f"政策立場追加に失敗しました: {str(e)}")
    
    def get_candidate_policies(self, candidate_id: int) -> List[PolicyPosition]:
        """
        候補者の政策立場を取得
        
        Args:
            candidate_id: 候補者ID
            
        Returns:
            政策立場リスト
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM policy_positions WHERE candidate_id = ?
                    ORDER BY priority DESC, policy_area
                ''', (candidate_id,))
                
                policies = []
                for row in cursor.fetchall():
                    policy = PolicyPosition(
                        candidate_id=row[1], policy_area=row[2], position=row[3],
                        priority=row[4], details=row[5], source_url=row[6],
                        last_updated=row[7]
                    )
                    policies.append(policy)
                
                return policies
                
        except Exception as e:
            logger.error(f"候補者政策取得エラー ({candidate_id}): {str(e)}")
            return []
    
    def add_campaign_activity(self, activity: CampaignData) -> int:
        """
        選挙活動データを追加
        
        Args:
            activity: 選挙活動データ
            
        Returns:
            追加された活動のID
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO campaign_activities (
                        candidate_id, activity_date, activity_type, location, attendance,
                        media_coverage, key_messages, public_reaction
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    activity.candidate_id, activity.activity_date, activity.activity_type,
                    activity.location, activity.attendance, activity.media_coverage,
                    json.dumps(activity.key_messages, ensure_ascii=False), activity.public_reaction
                ))
                
                activity_id = cursor.lastrowid
                conn.commit()
                
                logger.debug(f"選挙活動を追加: 候補者ID {activity.candidate_id} - {activity.activity_type}")
                return activity_id
                
        except Exception as e:
            logger.error(f"選挙活動追加エラー: {str(e)}")
            raise AnalysisError(f"選挙活動追加に失敗しました: {str(e)}")
    
    def analyze_candidate_strengths(self, candidate_id: int) -> Dict[str, Any]:
        """
        候補者の強み・弱み分析
        
        Args:
            candidate_id: 候補者ID
            
        Returns:
            強み・弱み分析結果
        """
        try:
            candidate = self.get_candidate_by_id(candidate_id)
            if not candidate:
                return {"error": "候補者が見つかりません"}
            
            policies = self.get_candidate_policies(candidate_id)
            activities = self.get_campaign_activities(candidate_id, days=30)
            
            analysis = {
                "candidate_name": candidate.name,
                "party": candidate.party,
                "overall_assessment": {
                    "recognition_rate": candidate.recognition_rate,
                    "support_rate": candidate.support_rate,
                    "status_advantage": candidate.status,
                    "experience_score": self._calculate_experience_score(candidate)
                },
                "policy_strength": {
                    "policy_count": len(policies),
                    "priority_policies": [p for p in policies if p.priority >= 8],
                    "policy_coverage": len(set(p.policy_area for p in policies)) / len(self.policy_areas)
                },
                "campaign_activity": {
                    "activity_frequency": len(activities) / 30,
                    "media_exposure": sum(1 for a in activities if a.media_coverage) / max(len(activities), 1),
                    "public_engagement": self._assess_public_engagement(activities)
                },
                "competitive_position": self._analyze_competitive_position(candidate_id),
                "key_strengths": candidate.strengths,
                "key_weaknesses": candidate.weaknesses,
                "recommendations": self._generate_campaign_recommendations(candidate, policies, activities)
            }
            
            logger.info(f"候補者分析完了: {candidate.name}")
            return analysis
            
        except Exception as e:
            logger.error(f"候補者分析エラー ({candidate_id}): {str(e)}")
            return {"error": str(e)}
    
    def compare_candidates(self, candidate1_id: int, candidate2_id: int) -> Dict[str, Any]:
        """
        候補者間比較分析
        
        Args:
            candidate1_id: 候補者1のID
            candidate2_id: 候補者2のID
            
        Returns:
            比較分析結果
        """
        try:
            candidate1 = self.get_candidate_by_id(candidate1_id)
            candidate2 = self.get_candidate_by_id(candidate2_id)
            
            if not candidate1 or not candidate2:
                return {"error": "候補者が見つかりません"}
            
            comparison = {
                "candidates": {
                    "candidate1": {"name": candidate1.name, "party": candidate1.party},
                    "candidate2": {"name": candidate2.name, "party": candidate2.party}
                },
                "basic_comparison": {
                    "recognition_rate": {
                        "candidate1": candidate1.recognition_rate,
                        "candidate2": candidate2.recognition_rate,
                        "advantage": "candidate1" if candidate1.recognition_rate > candidate2.recognition_rate else "candidate2"
                    },
                    "support_rate": {
                        "candidate1": candidate1.support_rate,
                        "candidate2": candidate2.support_rate,
                        "advantage": "candidate1" if candidate1.support_rate > candidate2.support_rate else "candidate2"
                    },
                    "experience": {
                        "candidate1": self._calculate_experience_score(candidate1),
                        "candidate2": self._calculate_experience_score(candidate2)
                    }
                },
                "policy_comparison": self._compare_policies(candidate1_id, candidate2_id),
                "demographic_appeal": self._compare_demographic_appeal(candidate1, candidate2),
                "campaign_effectiveness": self._compare_campaign_effectiveness(candidate1_id, candidate2_id),
                "overall_assessment": {
                    "competitive_balance": "均衡" if abs(candidate1.support_rate - candidate2.support_rate) < 0.05 else "一方優勢",
                    "key_battleground": self._identify_key_battleground(candidate1, candidate2)
                },
                "analysis_date": datetime.now().isoformat()
            }
            
            # 比較結果をデータベースに保存
            self._save_comparison_result(candidate1.constituency_id, candidate1_id, candidate2_id, comparison)
            
            logger.info(f"候補者比較完了: {candidate1.name} vs {candidate2.name}")
            return comparison
            
        except Exception as e:
            logger.error(f"候補者比較エラー: {str(e)}")
            return {"error": str(e)}
    
    def get_candidate_by_id(self, candidate_id: int) -> Optional[Candidate]:
        """IDで候補者を取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM candidates WHERE id = ?', (candidate_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_candidate(row)
                return None
                
        except Exception as e:
            logger.error(f"候補者取得エラー ({candidate_id}): {str(e)}")
            return None
    
    def search_candidates(self, 
                         party: Optional[str] = None,
                         status: Optional[str] = None,
                         constituency: Optional[str] = None,
                         min_support: Optional[float] = None) -> List[Candidate]:
        """
        条件で候補者を検索
        
        Args:
            party: 政党名
            status: 候補者ステータス
            constituency: 選挙区
            min_support: 最小支持率
            
        Returns:
            条件に合致する候補者リスト
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                conditions = []
                params = []
                
                if party:
                    conditions.append("party = ?")
                    params.append(party)
                if status:
                    conditions.append("status = ?")
                    params.append(status)
                if constituency:
                    conditions.append("constituency_id = ?")
                    params.append(constituency)
                if min_support:
                    conditions.append("support_rate >= ?")
                    params.append(min_support)
                
                where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
                query = f"SELECT * FROM candidates{where_clause} ORDER BY support_rate DESC"
                
                cursor.execute(query, params)
                
                candidates = []
                for row in cursor.fetchall():
                    candidate = self._row_to_candidate(row)
                    candidates.append(candidate)
                
                logger.info(f"候補者検索完了: {len(candidates)}名")
                return candidates
                
        except Exception as e:
            logger.error(f"候補者検索エラー: {str(e)}")
            return []
    
    def get_campaign_activities(self, candidate_id: int, days: int = 7) -> List[CampaignData]:
        """候補者の選挙活動を取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM campaign_activities 
                    WHERE candidate_id = ? AND activity_date >= date('now', '-{} days')
                    ORDER BY activity_date DESC
                '''.format(days), (candidate_id,))
                
                activities = []
                for row in cursor.fetchall():
                    activity = CampaignData(
                        candidate_id=row[1], activity_date=row[2], activity_type=row[3],
                        location=row[4], attendance=row[5], media_coverage=bool(row[6]),
                        key_messages=json.loads(row[7]) if row[7] else [],
                        public_reaction=row[8]
                    )
                    activities.append(activity)
                
                return activities
                
        except Exception as e:
            logger.error(f"選挙活動取得エラー ({candidate_id}): {str(e)}")
            return []
    
    def _row_to_candidate(self, row: tuple) -> Candidate:
        """データベース行を候補者オブジェクトに変換"""
        return Candidate(
            id=row[0], name=row[1], reading=row[2], party=row[3], constituency_id=row[4],
            status=row[5], age=row[6], gender=row[7], education=row[8],
            career=json.loads(row[9]) if row[9] else [],
            policy_positions={},  # 別途取得
            support_organizations=json.loads(row[10]) if row[10] else [],
            past_elections=json.loads(row[11]) if row[11] else [],
            recognition_rate=row[12], support_rate=row[13], fundraising_amount=row[14],
            social_media=json.loads(row[15]) if row[15] else {},
            strengths=json.loads(row[16]) if row[16] else [],
            weaknesses=json.loads(row[17]) if row[17] else [],
            created_at=row[18], updated_at=row[19]
        )
    
    def _calculate_experience_score(self, candidate: Candidate) -> float:
        """候補者の経験値スコア計算"""
        score = 0.0
        
        # 現職ボーナス
        if candidate.status == "現職":
            score += 0.4
        elif candidate.status == "元職":
            score += 0.2
        
        # 過去選挙経験
        score += min(0.3, len(candidate.past_elections) * 0.1)
        
        # 年齢・キャリア
        if candidate.age >= 50:
            score += 0.2
        
        score += min(0.1, len(candidate.career) * 0.02)
        
        return min(1.0, score)
    
    def _assess_public_engagement(self, activities: List[CampaignData]) -> float:
        """公的関与度評価"""
        if not activities:
            return 0.0
        
        total_attendance = sum(a.attendance or 0 for a in activities)
        avg_attendance = total_attendance / len(activities)
        
        # 正規化（1000人平均を1.0とする）
        return min(1.0, avg_attendance / 1000)
    
    def _analyze_competitive_position(self, candidate_id: int) -> Dict[str, Any]:
        """競争ポジション分析"""
        candidate = self.get_candidate_by_id(candidate_id)
        if not candidate:
            return {}
        
        # 同選挙区の他候補取得
        other_candidates = self.get_candidates_by_constituency(candidate.constituency_id)
        other_candidates = [c for c in other_candidates if c.id != candidate_id]
        
        if not other_candidates:
            return {"status": "単独立候補"}
        
        # 支持率ランキング
        all_candidates = [candidate] + other_candidates
        all_candidates.sort(key=lambda x: x.support_rate, reverse=True)
        
        position = next(i for i, c in enumerate(all_candidates) if c.id == candidate_id) + 1
        
        return {
            "ranking": position,
            "total_candidates": len(all_candidates),
            "support_rate_gap": candidate.support_rate - (other_candidates[0].support_rate if other_candidates else 0),
            "competitive_status": "優勢" if position == 1 else "劣勢" if position > 2 else "競合"
        }
    
    def _generate_campaign_recommendations(self, candidate: Candidate, policies: List[PolicyPosition], activities: List[CampaignData]) -> List[str]:
        """選挙戦略推奨"""
        recommendations = []
        
        # 認知度が低い場合
        if candidate.recognition_rate < 0.6:
            recommendations.append("知名度向上のための露出増加が必要")
        
        # 政策が少ない場合
        if len(policies) < 10:
            recommendations.append("政策立場の明確化と発信強化")
        
        # 活動頻度が低い場合
        if len(activities) < 15:  # 月15回未満
            recommendations.append("選挙活動の頻度増加")
        
        # 支持率が低い場合
        if candidate.support_rate < 0.3:
            recommendations.append("支援組織との連携強化")
        
        return recommendations
    
    def _compare_policies(self, candidate1_id: int, candidate2_id: int) -> Dict[str, Any]:
        """政策比較"""
        policies1 = self.get_candidate_policies(candidate1_id)
        policies2 = self.get_candidate_policies(candidate2_id)
        
        areas1 = set(p.policy_area for p in policies1)
        areas2 = set(p.policy_area for p in policies2)
        
        return {
            "policy_coverage": {
                "candidate1": len(areas1),
                "candidate2": len(areas2)
            },
            "common_areas": list(areas1 & areas2),
            "unique_to_candidate1": list(areas1 - areas2),
            "unique_to_candidate2": list(areas2 - areas1)
        }
    
    def _compare_demographic_appeal(self, candidate1: Candidate, candidate2: Candidate) -> Dict[str, Any]:
        """有権者層アピール比較"""
        return {
            "age_appeal": {
                "candidate1": "高齢者" if candidate1.age > 55 else "若年層",
                "candidate2": "高齢者" if candidate2.age > 55 else "若年層"
            },
            "gender_appeal": {
                "candidate1": candidate1.gender,
                "candidate2": candidate2.gender
            },
            "career_appeal": {
                "candidate1": candidate1.career[:2],  # 主要キャリア
                "candidate2": candidate2.career[:2]
            }
        }
    
    def _compare_campaign_effectiveness(self, candidate1_id: int, candidate2_id: int) -> Dict[str, Any]:
        """選挙戦効果比較"""
        activities1 = self.get_campaign_activities(candidate1_id, 30)
        activities2 = self.get_campaign_activities(candidate2_id, 30)
        
        return {
            "activity_frequency": {
                "candidate1": len(activities1),
                "candidate2": len(activities2)
            },
            "media_coverage": {
                "candidate1": sum(1 for a in activities1 if a.media_coverage),
                "candidate2": sum(1 for a in activities2 if a.media_coverage)
            }
        }
    
    def _identify_key_battleground(self, candidate1: Candidate, candidate2: Candidate) -> List[str]:
        """主要争点特定"""
        battlegrounds = []
        
        # 年代別争い
        if abs(candidate1.age - candidate2.age) > 15:
            battlegrounds.append("世代間アピール")
        
        # 経験差
        if candidate1.status != candidate2.status:
            battlegrounds.append("経験vs新鮮さ")
        
        # 政党色
        if candidate1.party in ["自由民主党", "公明党"] and candidate2.party not in ["自由民主党", "公明党"]:
            battlegrounds.append("与野党対決")
        
        return battlegrounds
    
    def _save_comparison_result(self, constituency_id: str, candidate1_id: int, candidate2_id: int, comparison: Dict[str, Any]):
        """比較結果をデータベースに保存"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 主要カテゴリごとに保存
                categories = ["recognition_rate", "support_rate", "experience", "policy_coverage"]
                
                for category in categories:
                    if category in comparison.get("basic_comparison", {}):
                        data = comparison["basic_comparison"][category]
                        cursor.execute('''
                            INSERT INTO candidate_comparisons (
                                constituency_id, candidate1_id, candidate2_id, comparison_category,
                                candidate1_score, candidate2_score, analysis_notes, comparison_date
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            constituency_id, candidate1_id, candidate2_id, category,
                            data.get("candidate1", 0), data.get("candidate2", 0),
                            data.get("advantage", ""), datetime.now().date()
                        ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"比較結果保存エラー: {str(e)}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """データベース統計情報を取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                cursor.execute('SELECT COUNT(*) FROM candidates')
                stats['total_candidates'] = cursor.fetchone()[0]
                
                cursor.execute('SELECT party, COUNT(*) FROM candidates GROUP BY party')
                stats['candidates_by_party'] = dict(cursor.fetchall())
                
                cursor.execute('SELECT status, COUNT(*) FROM candidates GROUP BY status')
                stats['candidates_by_status'] = dict(cursor.fetchall())
                
                cursor.execute('SELECT COUNT(*) FROM policy_positions')
                stats['total_policy_positions'] = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM campaign_activities')
                stats['total_campaign_activities'] = cursor.fetchone()[0]
                
                return stats
                
        except Exception as e:
            logger.error(f"統計情報取得エラー: {str(e)}")
            return {}
    
    def test_connection(self) -> bool:
        """データベース接続テスト"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM candidates')
                cursor.fetchone()
                return True
        except Exception as e:
            logger.error(f"候補者DB接続テスト失敗: {str(e)}")
            return False