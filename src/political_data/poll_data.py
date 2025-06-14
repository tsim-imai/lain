"""
世論調査データ管理
内閣支持率・政党支持率・世論調査データの管理
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from .political_database import PoliticalDatabaseManager, Poll
from ..utils.config import ConfigManager

logger = logging.getLogger(__name__)


class PollDataManager:
    """世論調査データ管理クラス"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
        """
        self.config_manager = config_manager
        self.db_manager = PoliticalDatabaseManager(config_manager)
        
        # 世論調査機関の信頼性重み
        self.pollster_weights = {
            "NHK": 1.0,
            "共同通信": 0.95,
            "時事通信": 0.9,
            "朝日新聞": 0.85,
            "読売新聞": 0.85,
            "毎日新聞": 0.8,
            "産経新聞": 0.8,
            "日本経済新聞": 0.85,
            "JNN": 0.8,
            "FNN": 0.8,
            "ANN": 0.75,
            "NNN": 0.75
        }
        
        logger.info("世論調査データ管理を初期化")
    
    def add_poll_data(self, poll_data: Dict[str, Any]) -> int:
        """
        世論調査データを追加
        
        Args:
            poll_data: 世論調査データ辞書
            
        Returns:
            追加されたレコードのID
        """
        # 信頼性スコアを計算
        reliability_score = self._calculate_reliability_score(
            poll_data.get("pollster", ""),
            poll_data.get("sample_size", 0),
            poll_data.get("methodology", "")
        )
        
        poll = Poll(
            id=None,
            pollster=poll_data["pollster"],
            poll_date=poll_data["poll_date"],
            question_type=poll_data.get("question_type", ""),
            target=poll_data.get("target", ""),
            support_rate=poll_data.get("support_rate", 0.0),
            sample_size=poll_data.get("sample_size", 0),
            methodology=poll_data.get("methodology", ""),
            reliability_score=reliability_score,
            created_at=""
        )
        
        logger.info(f"世論調査データを追加: {poll_data.get('pollster', 'N/A')} - {poll_data.get('target', 'N/A')}")
        return 1  # 仮のID
    
    def get_latest_cabinet_support(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        最新の内閣支持率を取得
        
        Args:
            limit: 取得件数上限
            
        Returns:
            内閣支持率データのリスト
        """
        # 最新の内閣支持率データ（サンプル）
        cabinet_support_data = [
            {
                "poll_date": "2024-06-15",
                "pollster": "NHK",
                "support_rate": 32.5,
                "opposition_rate": 55.2,
                "undecided": 12.3,
                "sample_size": 1208,
                "methodology": "RDD（固定・携帯）",
                "reliability_score": 1.0,
                "previous_month_change": -2.1
            },
            {
                "poll_date": "2024-06-12",
                "pollster": "共同通信",
                "support_rate": 30.8,
                "opposition_rate": 57.4,
                "undecided": 11.8,
                "sample_size": 1006,
                "methodology": "電話調査",
                "reliability_score": 0.95,
                "previous_month_change": -1.8
            },
            {
                "poll_date": "2024-06-10",
                "pollster": "朝日新聞",
                "support_rate": 29.2,
                "opposition_rate": 59.1,
                "undecided": 11.7,
                "sample_size": 1523,
                "methodology": "電話調査（RDD）",
                "reliability_score": 0.85,
                "previous_month_change": -3.2
            },
            {
                "poll_date": "2024-06-08",
                "pollster": "読売新聞",
                "support_rate": 34.1,
                "opposition_rate": 53.8,
                "undecided": 12.1,
                "sample_size": 1055,
                "methodology": "電話調査",
                "reliability_score": 0.85,
                "previous_month_change": -1.5
            }
        ]
        
        return cabinet_support_data[:limit]
    
    def get_party_support_trends(self, party_name: str, months: int = 12) -> List[Dict[str, Any]]:
        """
        政党支持率トレンドを取得
        
        Args:
            party_name: 政党名
            months: 取得月数
            
        Returns:
            政党支持率トレンドデータ
        """
        # 自民党支持率トレンド（サンプル）
        if "自民" in party_name or "自由民主党" in party_name:
            return [
                {"poll_date": "2024-06-15", "support_rate": 28.5, "pollster": "NHK"},
                {"poll_date": "2024-05-15", "support_rate": 30.2, "pollster": "NHK"},
                {"poll_date": "2024-04-15", "support_rate": 32.1, "pollster": "NHK"},
                {"poll_date": "2024-03-15", "support_rate": 33.8, "pollster": "NHK"},
                {"poll_date": "2024-02-15", "support_rate": 31.9, "pollster": "NHK"},
                {"poll_date": "2024-01-15", "support_rate": 35.2, "pollster": "NHK"}
            ]
        
        # 立憲民主党支持率トレンド
        elif "立憲" in party_name:
            return [
                {"poll_date": "2024-06-15", "support_rate": 7.8, "pollster": "NHK"},
                {"poll_date": "2024-05-15", "support_rate": 8.2, "pollster": "NHK"},
                {"poll_date": "2024-04-15", "support_rate": 7.5, "pollster": "NHK"},
                {"poll_date": "2024-03-15", "support_rate": 8.9, "pollster": "NHK"},
                {"poll_date": "2024-02-15", "support_rate": 9.1, "pollster": "NHK"},
                {"poll_date": "2024-01-15", "support_rate": 8.7, "pollster": "NHK"}
            ]
        
        return []
    
    def get_weighted_average_support(self, target: str, days: int = 30) -> Optional[Dict[str, Any]]:
        """
        信頼性重み付き平均支持率を計算
        
        Args:
            target: 対象（内閣/政党名）
            days: 集計期間（日数）
            
        Returns:
            重み付き平均支持率データ
        """
        if target == "内閣":
            # 過去30日の内閣支持率データを取得（サンプル）
            recent_polls = [
                {"pollster": "NHK", "support_rate": 32.5, "weight": 1.0},
                {"pollster": "共同通信", "support_rate": 30.8, "weight": 0.95},
                {"pollster": "朝日新聞", "support_rate": 29.2, "weight": 0.85},
                {"pollster": "読売新聞", "support_rate": 34.1, "weight": 0.85},
                {"pollster": "毎日新聞", "support_rate": 28.7, "weight": 0.8}
            ]
            
            # 重み付き平均を計算
            weighted_sum = sum(poll["support_rate"] * poll["weight"] for poll in recent_polls)
            total_weight = sum(poll["weight"] for poll in recent_polls)
            
            if total_weight > 0:
                weighted_average = weighted_sum / total_weight
                
                return {
                    "target": target,
                    "weighted_average": round(weighted_average, 1),
                    "period_days": days,
                    "polls_count": len(recent_polls),
                    "polls_used": recent_polls,
                    "calculation_date": datetime.now().isoformat()
                }
        
        return None
    
    def analyze_support_volatility(self, target: str, months: int = 6) -> Dict[str, Any]:
        """
        支持率変動分析
        
        Args:
            target: 分析対象
            months: 分析期間（月数）
            
        Returns:
            変動分析結果
        """
        if target == "内閣":
            # 過去6ヶ月の内閣支持率（サンプル）
            monthly_data = [
                32.5, 30.2, 32.1, 33.8, 31.9, 35.2
            ]
            
            # 統計計算
            average = sum(monthly_data) / len(monthly_data)
            variance = sum((x - average) ** 2 for x in monthly_data) / len(monthly_data)
            std_deviation = variance ** 0.5
            
            max_rate = max(monthly_data)
            min_rate = min(monthly_data)
            volatility_range = max_rate - min_rate
            
            # トレンド分析
            trend = "下降" if monthly_data[-1] < monthly_data[0] else "上昇"
            
            return {
                "target": target,
                "period_months": months,
                "average_support": round(average, 1),
                "standard_deviation": round(std_deviation, 1),
                "max_support": max_rate,
                "min_support": min_rate,
                "volatility_range": volatility_range,
                "trend": trend,
                "stability_score": round(max(0, 100 - volatility_range * 2), 1),
                "monthly_data": monthly_data
            }
        
        return {}
    
    def predict_support_trend(self, target: str, forecast_months: int = 3) -> Dict[str, Any]:
        """
        支持率トレンド予測
        
        Args:
            target: 予測対象
            forecast_months: 予測期間（月数）
            
        Returns:
            支持率予測結果
        """
        if target == "内閣":
            # 現在の支持率とトレンド
            current_support = 32.5
            monthly_change = -0.8  # 月次変化率
            
            # 単純線形予測
            predictions = []
            for i in range(1, forecast_months + 1):
                predicted_rate = current_support + (monthly_change * i)
                # 現実的な範囲に制限
                predicted_rate = max(5, min(80, predicted_rate))
                
                predictions.append({
                    "month": f"2024-{6+i:02d}",
                    "predicted_support": round(predicted_rate, 1),
                    "confidence_lower": round(predicted_rate - 3, 1),
                    "confidence_upper": round(predicted_rate + 3, 1)
                })
            
            return {
                "target": target,
                "current_support": current_support,
                "forecast_months": forecast_months,
                "predictions": predictions,
                "methodology": "線形トレンド予測",
                "confidence_level": 0.7,
                "factors": [
                    "経済状況の変化",
                    "政治スキャンダルの影響",
                    "国際情勢の変化",
                    "政策実施の成果"
                ]
            }
        
        return {}
    
    def _calculate_reliability_score(self, pollster: str, sample_size: int, methodology: str) -> float:
        """
        世論調査の信頼性スコアを計算
        
        Args:
            pollster: 調査機関
            sample_size: サンプルサイズ
            methodology: 調査手法
            
        Returns:
            信頼性スコア（0.0-1.0）
        """
        # 調査機関の基本信頼性
        base_score = self.pollster_weights.get(pollster, 0.5)
        
        # サンプルサイズによる補正
        if sample_size >= 1000:
            size_modifier = 1.0
        elif sample_size >= 500:
            size_modifier = 0.9
        elif sample_size >= 300:
            size_modifier = 0.8
        else:
            size_modifier = 0.6
        
        # 調査手法による補正
        if "RDD" in methodology:
            method_modifier = 1.0
        elif "電話" in methodology:
            method_modifier = 0.9
        elif "ネット" in methodology:
            method_modifier = 0.7
        else:
            method_modifier = 0.8
        
        final_score = base_score * size_modifier * method_modifier
        return min(1.0, final_score)
    
    def get_pollster_comparison(self, target: str = "内閣") -> Dict[str, Any]:
        """
        調査機関別の支持率比較
        
        Args:
            target: 比較対象
            
        Returns:
            調査機関別比較データ
        """
        if target == "内閣":
            comparison_data = {
                "NHK": {"support_rate": 32.5, "reliability": 1.0, "date": "2024-06-15"},
                "共同通信": {"support_rate": 30.8, "reliability": 0.95, "date": "2024-06-12"},
                "朝日新聞": {"support_rate": 29.2, "reliability": 0.85, "date": "2024-06-10"},
                "読売新聞": {"support_rate": 34.1, "reliability": 0.85, "date": "2024-06-08"},
                "毎日新聞": {"support_rate": 28.7, "reliability": 0.8, "date": "2024-06-05"},
                "産経新聞": {"support_rate": 35.3, "reliability": 0.8, "date": "2024-06-03"}
            }
            
            # 統計情報を計算
            support_rates = [data["support_rate"] for data in comparison_data.values()]
            average = sum(support_rates) / len(support_rates)
            max_diff = max(support_rates) - min(support_rates)
            
            return {
                "target": target,
                "pollster_data": comparison_data,
                "statistics": {
                    "average": round(average, 1),
                    "max_difference": round(max_diff, 1),
                    "pollster_count": len(comparison_data)
                },
                "analysis_date": datetime.now().isoformat()
            }
        
        return {}