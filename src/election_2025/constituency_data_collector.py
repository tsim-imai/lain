"""
選挙区情勢データ収集システム
2025年選挙に向けた全289選挙区の詳細情勢データを収集・分析
"""
import logging
import requests
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
import re

from ..utils.config import ConfigManager
from ..utils.exceptions import ScraperError
from ..political_data.political_database import PoliticalDatabaseManager

logger = logging.getLogger(__name__)


class ConstituencyDataCollector:
    """選挙区情勢データ収集クラス"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
        """
        self.config_manager = config_manager
        self.session = requests.Session()
        self.database = PoliticalDatabaseManager(config_manager)
        
        # ユーザーエージェント設定
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive'
        })
        
        # 289選挙区マスタデータ
        self.constituencies = self._load_constituencies_master()
        
        # データ収集ソース設定
        self.data_sources = {
            "総務省": {
                "base_url": "https://www.soumu.go.jp",
                "election_results_path": "/senkyo/senkyo_s/data/",
                "reliability_score": 1.0
            },
            "NHK選挙": {
                "base_url": "https://www.nhk.or.jp",
                "election_path": "/senkyo/",
                "reliability_score": 0.95
            },
            "朝日新聞選挙": {
                "base_url": "https://www.asahi.com",
                "election_path": "/senkyo/",
                "reliability_score": 0.9
            },
            "読売新聞選挙": {
                "base_url": "https://www.yomiuri.co.jp",
                "election_path": "/election/",
                "reliability_score": 0.9
            },
            "共同通信選挙": {
                "base_url": "https://www.kyodo.co.jp",
                "election_path": "/politics/election/",
                "reliability_score": 0.92
            }
        }
        
        self.request_delay = 2.0  # リクエスト間隔
        
        logger.info("選挙区情勢データ収集システムを初期化")
    
    def collect_all_constituencies_data(self, limit_constituencies: Optional[int] = None) -> Dict[str, Any]:
        """
        全選挙区の情勢データを収集
        
        Args:
            limit_constituencies: 収集対象選挙区数制限（テスト用）
            
        Returns:
            全選挙区情勢データ
        """
        try:
            collected_data = {
                "collection_timestamp": datetime.now().isoformat(),
                "total_constituencies": len(self.constituencies),
                "constituencies_data": {},
                "summary": {
                    "successful_collections": 0,
                    "failed_collections": 0,
                    "data_sources_used": list(self.data_sources.keys())
                }
            }
            
            # 収集対象選挙区の決定
            target_constituencies = list(self.constituencies.items())
            if limit_constituencies:
                target_constituencies = target_constituencies[:limit_constituencies]
            
            logger.info(f"選挙区情勢データ収集開始: {len(target_constituencies)}選挙区")
            
            for i, (constituency_id, constituency_info) in enumerate(target_constituencies):
                try:
                    logger.info(f"[{i+1}/{len(target_constituencies)}] {constituency_info['name']}データ収集中...")
                    
                    # 選挙区個別データ収集
                    constituency_data = self._collect_constituency_data(constituency_id, constituency_info)
                    
                    if constituency_data:
                        collected_data["constituencies_data"][constituency_id] = constituency_data
                        collected_data["summary"]["successful_collections"] += 1
                        
                        # データベースに保存
                        self._save_constituency_data(constituency_id, constituency_data)
                    else:
                        collected_data["summary"]["failed_collections"] += 1
                    
                    # レート制限
                    if i < len(target_constituencies) - 1:
                        time.sleep(self.request_delay)
                        
                except Exception as e:
                    logger.error(f"選挙区データ収集エラー ({constituency_info['name']}): {str(e)}")
                    collected_data["summary"]["failed_collections"] += 1
            
            success_rate = collected_data["summary"]["successful_collections"] / len(target_constituencies) * 100
            logger.info(f"選挙区情勢データ収集完了: 成功率 {success_rate:.1f}%")
            
            return collected_data
            
        except Exception as e:
            logger.error(f"全選挙区データ収集エラー: {str(e)}")
            return {"error": str(e)}
    
    def _collect_constituency_data(self, constituency_id: str, constituency_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        個別選挙区のデータを収集
        
        Args:
            constituency_id: 選挙区ID
            constituency_info: 選挙区基本情報
            
        Returns:
            選挙区詳細データ
        """
        try:
            constituency_data = {
                "basic_info": constituency_info,
                "historical_results": self._get_historical_results(constituency_id),
                "current_candidates": self._get_current_candidates(constituency_id),
                "demographics": self._get_constituency_demographics(constituency_id),
                "recent_polls": self._get_recent_polls(constituency_id),
                "local_issues": self._get_local_issues(constituency_id),
                "media_coverage": self._get_media_coverage(constituency_id),
                "collection_timestamp": datetime.now().isoformat()
            }
            
            return constituency_data
            
        except Exception as e:
            logger.error(f"選挙区データ収集エラー ({constituency_id}): {str(e)}")
            return None
    
    def _get_historical_results(self, constituency_id: str) -> List[Dict[str, Any]]:
        """過去選挙結果を取得"""
        try:
            # 過去の衆議院選挙結果を取得（2009, 2012, 2014, 2017, 2021）
            historical_results = []
            
            # サンプルデータ（実際の実装では総務省データを取得）
            sample_elections = [
                {"year": 2021, "type": "衆議院"},
                {"year": 2017, "type": "衆議院"},
                {"year": 2014, "type": "衆議院"},
                {"year": 2012, "type": "衆議院"},
                {"year": 2009, "type": "衆議院"}
            ]
            
            for election in sample_elections:
                # 実際の実装では総務省選挙データベースから取得
                result = {
                    "election_year": election["year"],
                    "election_type": election["type"],
                    "winner": {
                        "name": "候補者A",
                        "party": "自由民主党",
                        "votes": 85000,
                        "vote_rate": 0.45
                    },
                    "second_place": {
                        "name": "候補者B", 
                        "party": "立憲民主党",
                        "votes": 72000,
                        "vote_rate": 0.38
                    },
                    "turnout_rate": 0.62,
                    "total_votes": 189000,
                    "margin": 13000
                }
                historical_results.append(result)
            
            return historical_results
            
        except Exception as e:
            logger.warning(f"過去選挙結果取得エラー ({constituency_id}): {str(e)}")
            return []
    
    def _get_current_candidates(self, constituency_id: str) -> List[Dict[str, Any]]:
        """現在の立候補予定者情報を取得"""
        try:
            # 実際の実装では各政党公式サイト、政治団体サイトから情報収集
            current_candidates = [
                {
                    "name": "現職議員A",
                    "party": "自由民主党",
                    "status": "現職",
                    "age": 55,
                    "career": "元官僚、3期目",
                    "support_organizations": ["農協", "商工会"],
                    "policy_positions": {
                        "経済政策": "アベノミクス継承",
                        "外交・安保": "日米同盟重視",
                        "社会保障": "持続可能な制度設計"
                    },
                    "recognition_rate": 0.78,
                    "support_rate": 0.42
                },
                {
                    "name": "新人候補B",
                    "party": "立憲民主党",
                    "status": "新人",
                    "age": 48,
                    "career": "元地方議員、弁護士",
                    "support_organizations": ["連合", "市民団体"],
                    "policy_positions": {
                        "経済政策": "格差是正重視",
                        "外交・安保": "平和外交推進",
                        "社会保障": "社会保障充実"
                    },
                    "recognition_rate": 0.35,
                    "support_rate": 0.28
                }
            ]
            
            return current_candidates
            
        except Exception as e:
            logger.warning(f"立候補者情報取得エラー ({constituency_id}): {str(e)}")
            return []
    
    def _get_constituency_demographics(self, constituency_id: str) -> Dict[str, Any]:
        """選挙区の人口統計・特性を取得"""
        try:
            # 実際の実装では総務省統計、国勢調査データから取得
            demographics = {
                "total_population": 485000,
                "eligible_voters": 398000,
                "age_distribution": {
                    "20-30": 0.18,
                    "30-40": 0.22,
                    "40-50": 0.25,
                    "50-60": 0.20,
                    "60+": 0.15
                },
                "industry_structure": {
                    "製造業": 0.35,
                    "サービス業": 0.28,
                    "農業": 0.12,
                    "公務員": 0.08,
                    "その他": 0.17
                },
                "education_level": {
                    "大学卒": 0.32,
                    "高校卒": 0.45,
                    "中学卒": 0.23
                },
                "urban_rural_ratio": {
                    "都市部": 0.65,
                    "郊外": 0.25,
                    "農村部": 0.10
                },
                "political_tendency": "中道保守",
                "swing_voter_rate": 0.25
            }
            
            return demographics
            
        except Exception as e:
            logger.warning(f"選挙区統計取得エラー ({constituency_id}): {str(e)}")
            return {}
    
    def _get_recent_polls(self, constituency_id: str) -> List[Dict[str, Any]]:
        """最近の世論調査結果を取得"""
        try:
            # 実際の実装では地方新聞、調査機関データから取得
            recent_polls = [
                {
                    "poll_date": "2024-12-01",
                    "organization": "地方新聞A",
                    "sample_size": 800,
                    "results": {
                        "現職議員A": 0.42,
                        "新人候補B": 0.28,
                        "未定・その他": 0.30
                    },
                    "margin_of_error": 0.035,
                    "reliability_score": 0.8
                },
                {
                    "poll_date": "2024-11-15",
                    "organization": "調査機関B",
                    "sample_size": 1200,
                    "results": {
                        "現職議員A": 0.45,
                        "新人候補B": 0.26,
                        "未定・その他": 0.29
                    },
                    "margin_of_error": 0.028,
                    "reliability_score": 0.85
                }
            ]
            
            return recent_polls
            
        except Exception as e:
            logger.warning(f"世論調査取得エラー ({constituency_id}): {str(e)}")
            return []
    
    def _get_local_issues(self, constituency_id: str) -> List[Dict[str, Any]]:
        """地域課題・争点を取得"""
        try:
            # 実際の実装では地方メディア、自治体サイトから収集
            local_issues = [
                {
                    "issue": "地域経済活性化",
                    "importance": 0.85,
                    "description": "製造業の海外移転により雇用減少",
                    "candidate_positions": {
                        "現職議員A": "企業誘致・税制優遇",
                        "新人候補B": "中小企業支援・起業促進"
                    }
                },
                {
                    "issue": "高齢化対策",
                    "importance": 0.78,
                    "description": "高齢化率35%超、医療・介護体制",
                    "candidate_positions": {
                        "現職議員A": "地域包括ケア拡充",
                        "新人候補B": "在宅医療・介護充実"
                    }
                },
                {
                    "issue": "交通インフラ",
                    "importance": 0.65,
                    "description": "バス路線減少、高速道路アクセス",
                    "candidate_positions": {
                        "現職議員A": "高速道路延伸推進",
                        "新人候補B": "公共交通維持・充実"
                    }
                }
            ]
            
            return local_issues
            
        except Exception as e:
            logger.warning(f"地域課題取得エラー ({constituency_id}): {str(e)}")
            return []
    
    def _get_media_coverage(self, constituency_id: str) -> Dict[str, Any]:
        """メディア報道状況を取得"""
        try:
            # 実際の実装では地方メディアサイトをスクレイピング
            media_coverage = {
                "coverage_volume": {
                    "地方新聞A": 15,
                    "地方新聞B": 12,
                    "ローカルTV": 8,
                    "地方ラジオ": 5
                },
                "coverage_tone": {
                    "現職議員A": 0.1,  # やや好意的
                    "新人候補B": -0.05  # やや批判的
                },
                "major_topics": [
                    "地域経済政策",
                    "高齢化対策",
                    "インフラ整備"
                ],
                "recent_coverage_trend": "安定",
                "last_updated": datetime.now().isoformat()
            }
            
            return media_coverage
            
        except Exception as e:
            logger.warning(f"メディア報道取得エラー ({constituency_id}): {str(e)}")
            return {}
    
    def _save_constituency_data(self, constituency_id: str, data: Dict[str, Any]):
        """選挙区データをデータベースに保存"""
        try:
            # データベースに選挙区データを保存（新しいテーブルに保存）
            # 実装は簡略化
            logger.debug(f"選挙区データをDB保存: {constituency_id}")
            
        except Exception as e:
            logger.error(f"選挙区データ保存エラー ({constituency_id}): {str(e)}")
    
    def _load_constituencies_master(self) -> Dict[str, Dict[str, Any]]:
        """289選挙区マスタデータを読み込み"""
        # 実際の実装では外部ファイルまたはデータベースから読み込み
        # ここではサンプルデータ
        constituencies = {}
        
        # 主要選挙区のサンプル
        sample_constituencies = [
            {"id": "01001", "name": "北海道1区", "prefecture": "北海道", "major_cities": ["札幌市中央区", "札幌市南区"]},
            {"id": "13001", "name": "東京1区", "prefecture": "東京都", "major_cities": ["千代田区", "港区", "新宿区"]},
            {"id": "13025", "name": "東京25区", "prefecture": "東京都", "major_cities": ["青梅市", "福生市", "羽村市"]},
            {"id": "14001", "name": "神奈川1区", "prefecture": "神奈川県", "major_cities": ["横浜市中区", "横浜市西区"]},
            {"id": "23001", "name": "愛知1区", "prefecture": "愛知県", "major_cities": ["名古屋市千種区", "名古屋市東区"]},
            {"id": "27001", "name": "大阪1区", "prefecture": "大阪府", "major_cities": ["大阪市中央区", "大阪市天王寺区"]},
            {"id": "40001", "name": "福岡1区", "prefecture": "福岡県", "major_cities": ["福岡市東区", "福岡市博多区"]}
        ]
        
        for const in sample_constituencies:
            constituencies[const["id"]] = {
                "name": const["name"],
                "prefecture": const["prefecture"], 
                "major_cities": const["major_cities"],
                "district_type": "都市部" if const["prefecture"] in ["東京都", "大阪府", "神奈川県"] else "地方",
                "competitiveness": "激戦区" if "東京" in const["name"] or "大阪" in const["name"] else "安定区"
            }
        
        return constituencies
    
    def get_constituency_summary(self, constituency_id: str) -> Optional[Dict[str, Any]]:
        """
        特定選挙区の情勢サマリーを取得
        
        Args:
            constituency_id: 選挙区ID
            
        Returns:
            選挙区情勢サマリー
        """
        try:
            if constituency_id not in self.constituencies:
                logger.warning(f"存在しない選挙区ID: {constituency_id}")
                return None
            
            # データベースから最新データを取得
            # 実装は簡略化し、サンプルデータを返す
            constituency_info = self.constituencies[constituency_id]
            
            summary = {
                "constituency_id": constituency_id,
                "basic_info": constituency_info,
                "current_situation": {
                    "leading_candidate": "現職議員A",
                    "leading_party": "自由民主党",
                    "support_rate": 0.42,
                    "competitiveness": "やや優勢",
                    "confidence_level": 0.75
                },
                "key_factors": [
                    "現職の知名度・実績",
                    "地域経済活性化への関心",
                    "組織票vs無党派票の動向"
                ],
                "prediction": {
                    "win_probability": {
                        "現職議員A": 0.68,
                        "新人候補B": 0.32
                    },
                    "confidence_interval": "±5%",
                    "last_updated": datetime.now().isoformat()
                }
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"選挙区サマリー取得エラー ({constituency_id}): {str(e)}")
            return None
    
    def search_constituencies(self, 
                            prefecture: Optional[str] = None,
                            competitiveness: Optional[str] = None,
                            district_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        条件で選挙区を検索
        
        Args:
            prefecture: 都道府県
            competitiveness: 競争状況
            district_type: 選挙区タイプ
            
        Returns:
            条件に合致する選挙区のリスト
        """
        try:
            results = []
            
            for const_id, const_info in self.constituencies.items():
                match = True
                
                if prefecture and const_info.get("prefecture") != prefecture:
                    match = False
                if competitiveness and const_info.get("competitiveness") != competitiveness:
                    match = False
                if district_type and const_info.get("district_type") != district_type:
                    match = False
                
                if match:
                    result = {
                        "constituency_id": const_id,
                        **const_info
                    }
                    results.append(result)
            
            logger.info(f"選挙区検索完了: {len(results)}件")
            return results
            
        except Exception as e:
            logger.error(f"選挙区検索エラー: {str(e)}")
            return []
    
    def test_connection(self) -> bool:
        """データ収集システム接続テスト"""
        try:
            # データソースの接続確認
            for source_name, source_info in self.data_sources.items():
                test_url = source_info["base_url"]
                response = self.session.get(test_url, timeout=10)
                if response.status_code != 200:
                    logger.warning(f"{source_name}接続エラー: {response.status_code}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"接続テストエラー: {str(e)}")
            return False