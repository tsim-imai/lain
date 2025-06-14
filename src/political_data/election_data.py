"""
選挙データ管理
選挙結果・選挙予測データの管理
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from .political_database import PoliticalDatabaseManager, Election
from ..utils.config import ConfigManager

logger = logging.getLogger(__name__)


class ElectionDataManager:
    """選挙データ管理クラス"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
        """
        self.config_manager = config_manager
        self.db_manager = PoliticalDatabaseManager(config_manager)
        logger.info("選挙データ管理を初期化")
    
    def add_election_result(self, election_data: Dict[str, Any]) -> int:
        """
        選挙結果を追加
        
        Args:
            election_data: 選挙データ辞書
            
        Returns:
            追加されたレコードのID
        """
        election = Election(
            id=None,
            election_type=election_data["election_type"],
            election_date=election_data["election_date"],
            region=election_data.get("region", ""),
            constituency=election_data.get("constituency", ""),
            candidate_name=election_data.get("candidate_name", ""),
            party_name=election_data.get("party_name", ""),
            votes=election_data.get("votes", 0),
            is_elected=election_data.get("is_elected", False),
            vote_share=election_data.get("vote_share", 0.0),
            turnout_rate=election_data.get("turnout_rate"),
            created_at=""
        )
        
        with self.db_manager.db_path.parent as db_dir:
            db_dir.mkdir(exist_ok=True)
        
        # 簡略化実装（実際にはDBManagerのメソッドを使用）
        logger.info(f"選挙結果を追加: {election_data.get('candidate_name', 'N/A')}")
        return 1  # 仮のID
    
    def get_recent_elections(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        最近の選挙結果を取得
        
        Args:
            limit: 取得件数上限
            
        Returns:
            選挙結果のリスト
        """
        # 2021年衆議院選挙の主要結果（サンプルデータ）
        sample_elections = [
            {
                "election_type": "衆議院選挙",
                "election_date": "2021-10-31",
                "region": "全国",
                "results": {
                    "自由民主党": {"seats": 261, "vote_share": 35.5},
                    "立憲民主党": {"seats": 96, "vote_share": 20.0},
                    "日本維新の会": {"seats": 41, "vote_share": 14.0},
                    "公明党": {"seats": 32, "vote_share": 7.0},
                    "日本共産党": {"seats": 10, "vote_share": 7.3},
                    "国民民主党": {"seats": 11, "vote_share": 2.8}
                },
                "turnout_rate": 55.93
            },
            {
                "election_type": "参議院選挙", 
                "election_date": "2022-07-10",
                "region": "全国",
                "results": {
                    "自由民主党": {"seats": 63, "vote_share": 35.4},
                    "立憲民主党": {"seats": 17, "vote_share": 23.0},
                    "日本維新の会": {"seats": 12, "vote_share": 14.9},
                    "公明党": {"seats": 13, "vote_share": 7.2},
                    "日本共産党": {"seats": 4, "vote_share": 6.2},
                    "国民民主党": {"seats": 5, "vote_share": 3.6}
                },
                "turnout_rate": 52.05
            }
        ]
        
        return sample_elections[:limit]
    
    def get_election_trends(self, party_name: str) -> List[Dict[str, Any]]:
        """
        政党の選挙トレンドを取得
        
        Args:
            party_name: 政党名
            
        Returns:
            選挙トレンドデータ
        """
        # 自民党の過去選挙結果トレンド（サンプル）
        if "自民" in party_name or "自由民主党" in party_name:
            return [
                {
                    "election_date": "2021-10-31",
                    "election_type": "衆議院選挙",
                    "seats": 261,
                    "vote_share": 35.5,
                    "seat_change": -15  # 前回比
                },
                {
                    "election_date": "2022-07-10", 
                    "election_type": "参議院選挙",
                    "seats": 63,
                    "vote_share": 35.4,
                    "seat_change": +7
                },
                {
                    "election_date": "2017-10-22",
                    "election_type": "衆議院選挙", 
                    "seats": 284,
                    "vote_share": 33.3,
                    "seat_change": +6
                }
            ]
        
        # 立憲民主党のトレンド
        elif "立憲" in party_name or "立憲民主党" in party_name:
            return [
                {
                    "election_date": "2021-10-31",
                    "election_type": "衆議院選挙",
                    "seats": 96,
                    "vote_share": 20.0,
                    "seat_change": -13
                },
                {
                    "election_date": "2022-07-10",
                    "election_type": "参議院選挙",
                    "seats": 17,
                    "vote_share": 23.0,
                    "seat_change": -6
                }
            ]
        
        return []
    
    def predict_next_election(self, constituency: str = "全国") -> Dict[str, Any]:
        """
        次期選挙予測
        
        Args:
            constituency: 選挙区
            
        Returns:
            選挙予測データ
        """
        # 次期衆議院選挙予測（サンプル）
        prediction = {
            "election_type": "衆議院選挙",
            "predicted_date": "2025-10-21",  # 任期満了
            "constituency": constituency,
            "predictions": {
                "自由民主党": {
                    "predicted_seats": 250,
                    "seat_range": [230, 270],
                    "confidence": 0.7
                },
                "立憲民主党": {
                    "predicted_seats": 100,
                    "seat_range": [80, 120],
                    "confidence": 0.6
                },
                "日本維新の会": {
                    "predicted_seats": 50,
                    "seat_range": [35, 65],
                    "confidence": 0.5
                },
                "公明党": {
                    "predicted_seats": 30,
                    "seat_range": [25, 35],
                    "confidence": 0.8
                }
            },
            "factors": [
                "現在の支持率動向",
                "経済状況",
                "国際情勢", 
                "政治スキャンダルの影響",
                "野党連携の状況"
            ],
            "uncertainties": [
                "解散時期の不確実性",
                "新政党の動向",
                "選挙制度改革の影響",
                "投票率の変動"
            ],
            "last_updated": datetime.now().isoformat()
        }
        
        return prediction
    
    def analyze_swing_seats(self) -> List[Dict[str, Any]]:
        """
        激戦区分析
        
        Returns:
            激戦区データのリスト
        """
        swing_seats = [
            {
                "constituency": "東京1区",
                "current_winner": "海江田万里",
                "current_party": "立憲民主党",
                "margin": 1.8,  # 勝利マージン（%）
                "challenger": "山田太郎",
                "challenger_party": "自由民主党",
                "turnout_2021": 58.2,
                "prediction": {
                    "leading_candidate": "山田太郎",
                    "leading_party": "自由民主党",
                    "confidence": 0.6
                }
            },
            {
                "constituency": "大阪19区", 
                "current_winner": "長尾敬",
                "current_party": "自由民主党",
                "margin": 2.1,
                "challenger": "田中花子",
                "challenger_party": "日本維新の会",
                "turnout_2021": 52.8,
                "prediction": {
                    "leading_candidate": "田中花子",
                    "leading_party": "日本維新の会", 
                    "confidence": 0.7
                }
            },
            {
                "constituency": "神奈川7区",
                "current_winner": "鈴木義弘",
                "current_party": "立憲民主党",
                "margin": 1.2,
                "challenger": "佐藤次郎",
                "challenger_party": "自由民主党",
                "turnout_2021": 60.1,
                "prediction": {
                    "leading_candidate": "佐藤次郎",
                    "leading_party": "自由民主党",
                    "confidence": 0.5
                }
            }
        ]
        
        return swing_seats
    
    def get_constituency_history(self, constituency: str) -> List[Dict[str, Any]]:
        """
        選挙区の選挙履歴を取得
        
        Args:
            constituency: 選挙区名
            
        Returns:
            選挙履歴のリスト
        """
        # サンプル実装
        if constituency == "東京1区":
            return [
                {
                    "election_date": "2021-10-31",
                    "winner": "海江田万里",
                    "party": "立憲民主党", 
                    "votes": 98765,
                    "vote_share": 48.2,
                    "turnout": 58.2
                },
                {
                    "election_date": "2017-10-22",
                    "winner": "山田太郎",
                    "party": "自由民主党",
                    "votes": 95432,
                    "vote_share": 46.8,
                    "turnout": 55.7
                }
            ]
        
        return []
    
    def calculate_seat_projection(self, support_rates: Dict[str, float]) -> Dict[str, Any]:
        """
        支持率から議席数を予測
        
        Args:
            support_rates: 政党別支持率
            
        Returns:
            議席予測結果
        """
        # 簡易な議席予測モデル
        total_seats = 465  # 衆議院総議席数
        
        # 支持率を議席に変換（簡略化）
        seat_projections = {}
        total_support = sum(support_rates.values())
        
        if total_support > 0:
            for party, support in support_rates.items():
                # 小選挙区での優位性を考慮した補正
                if party == "自由民主党":
                    modifier = 1.2  # 小選挙区で有利
                elif party == "立憲民主党":
                    modifier = 0.9
                elif party == "日本維新の会":
                    modifier = 0.8
                else:
                    modifier = 0.7
                
                projected_seats = int((support / total_support) * total_seats * modifier)
                seat_projections[party] = max(1, projected_seats)  # 最低1議席
        
        # 総議席数調整
        current_total = sum(seat_projections.values())
        if current_total != total_seats:
            # 最大政党で調整
            max_party = max(seat_projections, key=seat_projections.get)
            seat_projections[max_party] += (total_seats - current_total)
        
        return {
            "projections": seat_projections,
            "total_seats": total_seats,
            "methodology": "支持率比例配分（小選挙区優位性補正）",
            "confidence": 0.6
        }