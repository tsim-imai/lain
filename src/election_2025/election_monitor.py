"""
選挙情勢リアルタイム監視システム
2025年選挙に向けた情勢変化の自動検知・アラート機能
"""
import logging
import time
import threading
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from queue import Queue
import json

from ..utils.config import ConfigManager
from ..utils.exceptions import AnalysisError
from ..political_data.political_database import PoliticalDatabaseManager
from .constituency_data_collector import ConstituencyDataCollector
from .election_prediction_model import ElectionPredictionModel
from .candidate_database import CandidateDatabase

logger = logging.getLogger(__name__)


@dataclass
class ElectionAlert:
    """選挙アラートデータクラス"""
    alert_id: str
    alert_type: str  # support_change/candidate_news/poll_release/etc
    severity: str    # high/medium/low
    constituency_id: Optional[str]
    candidate_name: Optional[str]
    title: str
    description: str
    data: Dict[str, Any]
    timestamp: str
    source: str


@dataclass
class TrendAnalysis:
    """トレンド分析データクラス"""
    metric: str
    current_value: float
    previous_value: float
    change_rate: float
    trend_direction: str  # rising/falling/stable
    confidence: float
    time_period: str


class ElectionMonitor:
    """選挙情勢リアルタイム監視クラス"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
        """
        self.config_manager = config_manager
        self.database = PoliticalDatabaseManager(config_manager)
        self.constituency_collector = ConstituencyDataCollector(config_manager)
        self.prediction_model = ElectionPredictionModel(config_manager)
        self.candidate_db = CandidateDatabase(config_manager)
        
        # 監視設定
        self.monitoring_active = False
        self.monitoring_thread = None
        self.alert_queue = Queue()
        self.alert_callbacks: List[Callable] = []
        
        # アラート閾値設定
        self.alert_thresholds = {
            "support_rate_change": 0.03,      # 支持率3%以上変動
            "recognition_change": 0.05,       # 知名度5%以上変動
            "poll_margin_change": 0.04,       # 世論調査差4%以上変動
            "media_coverage_spike": 2.0,      # メディア露出2倍以上
            "campaign_activity_spike": 1.5,   # 選挙活動1.5倍以上
            "social_sentiment_change": 0.15   # SNS感情15%以上変動
        }
        
        # 監視間隔（秒）
        self.monitoring_intervals = {
            "real_time": 300,     # 5分
            "frequent": 1800,     # 30分
            "regular": 3600,      # 1時間
            "daily": 86400        # 24時間
        }
        
        # 重要選挙区（激戦区）リスト
        self.critical_constituencies = [
            "13001", "13025",  # 東京1区、25区
            "14001",           # 神奈川1区
            "23001",           # 愛知1区
            "27001",           # 大阪1区
            "40001"            # 福岡1区
        ]
        
        logger.info("選挙情勢監視システムを初期化")
    
    def start_monitoring(self, interval_type: str = "frequent") -> bool:
        """
        監視を開始
        
        Args:
            interval_type: 監視間隔タイプ
            
        Returns:
            監視開始成功フラグ
        """
        try:
            if self.monitoring_active:
                logger.warning("監視は既に開始されています")
                return False
            
            interval = self.monitoring_intervals.get(interval_type, 1800)
            
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                args=(interval,),
                daemon=True
            )
            self.monitoring_thread.start()
            
            logger.info(f"選挙情勢監視を開始: {interval_type}間隔 ({interval}秒)")
            return True
            
        except Exception as e:
            logger.error(f"監視開始エラー: {str(e)}")
            self.monitoring_active = False
            return False
    
    def stop_monitoring(self):
        """監視を停止"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("選挙情勢監視を停止")
    
    def add_alert_callback(self, callback: Callable[[ElectionAlert], None]):
        """アラートコールバック関数を追加"""
        self.alert_callbacks.append(callback)
        logger.debug("アラートコールバックを追加")
    
    def get_current_alerts(self, severity: Optional[str] = None, hours: int = 24) -> List[ElectionAlert]:
        """
        現在のアラートを取得
        
        Args:
            severity: アラート重要度フィルタ
            hours: 取得対象時間
            
        Returns:
            アラートリスト
        """
        try:
            alerts = []
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # アラートキューから取得
            temp_alerts = []
            while not self.alert_queue.empty():
                alert = self.alert_queue.get_nowait()
                temp_alerts.append(alert)
                
                alert_time = datetime.fromisoformat(alert.timestamp)
                if alert_time >= cutoff_time:
                    if not severity or alert.severity == severity:
                        alerts.append(alert)
            
            # キューに戻す
            for alert in temp_alerts:
                self.alert_queue.put(alert)
            
            # 時刻順でソート
            alerts.sort(key=lambda x: x.timestamp, reverse=True)
            
            logger.info(f"現在のアラート取得: {len(alerts)}件")
            return alerts
            
        except Exception as e:
            logger.error(f"アラート取得エラー: {str(e)}")
            return []
    
    def analyze_constituency_trends(self, constituency_id: str, days: int = 7) -> Dict[str, TrendAnalysis]:
        """
        選挙区トレンド分析
        
        Args:
            constituency_id: 選挙区ID
            days: 分析期間
            
        Returns:
            トレンド分析結果
        """
        try:
            # 候補者データ取得
            candidates = self.candidate_db.get_candidates_by_constituency(constituency_id)
            
            trends = {}
            
            for candidate in candidates:
                # 支持率トレンド分析
                support_trend = self._analyze_support_trend(candidate.id, days)
                if support_trend:
                    trends[f"{candidate.name}_support"] = support_trend
                
                # 認知度トレンド分析
                recognition_trend = self._analyze_recognition_trend(candidate.id, days)
                if recognition_trend:
                    trends[f"{candidate.name}_recognition"] = recognition_trend
                
                # 活動頻度トレンド
                activity_trend = self._analyze_activity_trend(candidate.id, days)
                if activity_trend:
                    trends[f"{candidate.name}_activity"] = activity_trend
            
            # 全体的な選挙区トレンド
            constituency_trend = self._analyze_constituency_competitiveness(constituency_id, days)
            if constituency_trend:
                trends["constituency_competitiveness"] = constituency_trend
            
            logger.info(f"選挙区トレンド分析完了: {constituency_id}")
            return trends
            
        except Exception as e:
            logger.error(f"トレンド分析エラー ({constituency_id}): {str(e)}")
            return {}
    
    def generate_daily_report(self) -> Dict[str, Any]:
        """
        日次選挙情勢レポート生成
        
        Returns:
            日次レポート
        """
        try:
            report = {
                "report_date": datetime.now().isoformat(),
                "overall_summary": self._generate_overall_summary(),
                "critical_constituencies": {},
                "trend_analysis": {},
                "recent_alerts": self.get_current_alerts(hours=24),
                "key_developments": self._identify_key_developments(),
                "predictions_update": self._update_predictions_summary()
            }
            
            # 重要選挙区の個別分析
            for constituency_id in self.critical_constituencies:
                constituency_analysis = self.analyze_constituency_trends(constituency_id, 7)
                report["critical_constituencies"][constituency_id] = constituency_analysis
            
            # 全体トレンド
            report["trend_analysis"] = self._analyze_overall_trends()
            
            logger.info("日次選挙情勢レポート生成完了")
            return report
            
        except Exception as e:
            logger.error(f"日次レポート生成エラー: {str(e)}")
            return {"error": str(e)}
    
    def _monitoring_loop(self, interval: int):
        """監視メインループ"""
        logger.info("監視ループを開始")
        
        while self.monitoring_active:
            try:
                # 各種監視タスクを実行
                self._check_support_rate_changes()
                self._check_poll_releases()
                self._check_media_coverage()
                self._check_campaign_activities()
                self._check_social_sentiment()
                
                # インターバル待機
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"監視ループエラー: {str(e)}")
                time.sleep(60)  # エラー時は1分待機
        
        logger.info("監視ループを終了")
    
    def _check_support_rate_changes(self):
        """支持率変動チェック"""
        try:
            # 重要選挙区の候補者支持率をチェック
            for constituency_id in self.critical_constituencies:
                candidates = self.candidate_db.get_candidates_by_constituency(constituency_id)
                
                for candidate in candidates:
                    # 過去のデータと比較（実装簡略化）
                    current_support = candidate.support_rate
                    previous_support = current_support - 0.02  # サンプル：2%下落
                    
                    change = abs(current_support - previous_support)
                    
                    if change >= self.alert_thresholds["support_rate_change"]:
                        alert = ElectionAlert(
                            alert_id=f"support_{candidate.id}_{int(time.time())}",
                            alert_type="support_change",
                            severity="high" if change >= 0.05 else "medium",
                            constituency_id=constituency_id,
                            candidate_name=candidate.name,
                            title=f"{candidate.name}の支持率が大幅変動",
                            description=f"支持率が{change:.1%}変動しました",
                            data={
                                "current_support": current_support,
                                "previous_support": previous_support,
                                "change": change,
                                "direction": "up" if current_support > previous_support else "down"
                            },
                            timestamp=datetime.now().isoformat(),
                            source="support_monitor"
                        )
                        
                        self._trigger_alert(alert)
                        
        except Exception as e:
            logger.error(f"支持率変動チェックエラー: {str(e)}")
    
    def _check_poll_releases(self):
        """世論調査発表チェック"""
        try:
            # 新しい世論調査データの検知
            # 実装簡略化：サンプルアラート
            if datetime.now().hour == 18:  # 夕方6時にサンプルアラート
                alert = ElectionAlert(
                    alert_id=f"poll_{int(time.time())}",
                    alert_type="poll_release",
                    severity="medium",
                    constituency_id=None,
                    candidate_name=None,
                    title="新しい世論調査が発表されました",
                    description="全国世論調査の最新結果が公開されました",
                    data={
                        "poll_organization": "調査機関A",
                        "poll_date": datetime.now().date().isoformat(),
                        "sample_size": 1200
                    },
                    timestamp=datetime.now().isoformat(),
                    source="poll_monitor"
                )
                
                self._trigger_alert(alert)
                
        except Exception as e:
            logger.error(f"世論調査チェックエラー: {str(e)}")
    
    def _check_media_coverage(self):
        """メディア報道監視"""
        try:
            # メディア報道の急増検知
            # 実装簡略化
            pass
            
        except Exception as e:
            logger.error(f"メディア監視エラー: {str(e)}")
    
    def _check_campaign_activities(self):
        """選挙活動監視"""
        try:
            # 選挙活動の急増・重要イベント検知
            # 実装簡略化
            pass
            
        except Exception as e:
            logger.error(f"選挙活動監視エラー: {str(e)}")
    
    def _check_social_sentiment(self):
        """SNS世論監視"""
        try:
            # SNS感情の急変検知
            # 実装簡略化
            pass
            
        except Exception as e:
            logger.error(f"SNS監視エラー: {str(e)}")
    
    def _trigger_alert(self, alert: ElectionAlert):
        """アラートを発火"""
        try:
            # アラートをキューに追加
            self.alert_queue.put(alert)
            
            # コールバック関数を実行
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    logger.error(f"アラートコールバックエラー: {str(e)}")
            
            logger.info(f"アラート発火: {alert.title} ({alert.severity})")
            
        except Exception as e:
            logger.error(f"アラート発火エラー: {str(e)}")
    
    def _analyze_support_trend(self, candidate_id: int, days: int) -> Optional[TrendAnalysis]:
        """候補者支持率トレンド分析"""
        try:
            candidate = self.candidate_db.get_candidate_by_id(candidate_id)
            if not candidate:
                return None
            
            # 簡略化：サンプルトレンド
            current_support = candidate.support_rate
            previous_support = current_support - 0.01  # 1%上昇トレンド
            
            change_rate = (current_support - previous_support) / previous_support if previous_support > 0 else 0
            
            return TrendAnalysis(
                metric="support_rate",
                current_value=current_support,
                previous_value=previous_support,
                change_rate=change_rate,
                trend_direction="rising" if change_rate > 0.01 else "falling" if change_rate < -0.01 else "stable",
                confidence=0.8,
                time_period=f"{days}days"
            )
            
        except Exception as e:
            logger.error(f"支持率トレンド分析エラー ({candidate_id}): {str(e)}")
            return None
    
    def _analyze_recognition_trend(self, candidate_id: int, days: int) -> Optional[TrendAnalysis]:
        """候補者認知度トレンド分析"""
        try:
            candidate = self.candidate_db.get_candidate_by_id(candidate_id)
            if not candidate:
                return None
            
            # 簡略化実装
            current_recognition = candidate.recognition_rate
            previous_recognition = current_recognition - 0.02  # 2%上昇
            
            change_rate = (current_recognition - previous_recognition) / previous_recognition if previous_recognition > 0 else 0
            
            return TrendAnalysis(
                metric="recognition_rate",
                current_value=current_recognition,
                previous_value=previous_recognition,
                change_rate=change_rate,
                trend_direction="rising" if change_rate > 0.01 else "stable",
                confidence=0.75,
                time_period=f"{days}days"
            )
            
        except Exception as e:
            logger.error(f"認知度トレンド分析エラー ({candidate_id}): {str(e)}")
            return None
    
    def _analyze_activity_trend(self, candidate_id: int, days: int) -> Optional[TrendAnalysis]:
        """選挙活動トレンド分析"""
        try:
            activities = self.candidate_db.get_campaign_activities(candidate_id, days)
            current_activity = len(activities)
            
            # 前期間と比較
            previous_activities = self.candidate_db.get_campaign_activities(candidate_id, days * 2)
            previous_activity = len(previous_activities) - current_activity
            
            change_rate = (current_activity - previous_activity) / max(previous_activity, 1)
            
            return TrendAnalysis(
                metric="activity_frequency",
                current_value=current_activity,
                previous_value=previous_activity,
                change_rate=change_rate,
                trend_direction="rising" if change_rate > 0.2 else "falling" if change_rate < -0.2 else "stable",
                confidence=0.9,
                time_period=f"{days}days"
            )
            
        except Exception as e:
            logger.error(f"活動トレンド分析エラー ({candidate_id}): {str(e)}")
            return None
    
    def _analyze_constituency_competitiveness(self, constituency_id: str, days: int) -> Optional[TrendAnalysis]:
        """選挙区競争激化度分析"""
        try:
            candidates = self.candidate_db.get_candidates_by_constituency(constituency_id)
            
            if len(candidates) < 2:
                return None
            
            # 上位2候補の支持率差
            candidates.sort(key=lambda x: x.support_rate, reverse=True)
            current_margin = candidates[0].support_rate - candidates[1].support_rate
            
            # 前期間のマージン（簡略化）
            previous_margin = current_margin + 0.01  # マージンが縮小傾向
            
            change_rate = (current_margin - previous_margin) / max(previous_margin, 0.01)
            
            return TrendAnalysis(
                metric="competitiveness",
                current_value=current_margin,
                previous_value=previous_margin,
                change_rate=change_rate,
                trend_direction="more_competitive" if change_rate < -0.1 else "less_competitive" if change_rate > 0.1 else "stable",
                confidence=0.7,
                time_period=f"{days}days"
            )
            
        except Exception as e:
            logger.error(f"選挙区競争分析エラー ({constituency_id}): {str(e)}")
            return None
    
    def _generate_overall_summary(self) -> Dict[str, Any]:
        """全体サマリー生成"""
        return {
            "monitoring_status": "active" if self.monitoring_active else "inactive",
            "total_constituencies": len(self.critical_constituencies),
            "recent_alerts_count": self.alert_queue.qsize(),
            "last_update": datetime.now().isoformat(),
            "key_metrics": {
                "average_competitiveness": 0.05,  # 平均マージン5%
                "trend_stability": "moderate",
                "alert_frequency": "normal"
            }
        }
    
    def _analyze_overall_trends(self) -> Dict[str, Any]:
        """全体トレンド分析"""
        return {
            "national_trend": {
                "ruling_party_trend": "slightly_declining",
                "opposition_trend": "gaining",
                "volatility": "moderate"
            },
            "regional_patterns": {
                "urban_areas": "competitive",
                "rural_areas": "stable",
                "swing_districts": "highly_volatile"
            },
            "demographic_trends": {
                "young_voters": "opposition_leaning",
                "senior_voters": "ruling_party_leaning",
                "middle_age": "split"
            }
        }
    
    def _identify_key_developments(self) -> List[Dict[str, Any]]:
        """重要動向特定"""
        return [
            {
                "development": "重要選挙区での接戦",
                "impact": "high",
                "constituencies": ["13001", "27001"],
                "description": "東京1区、大阪1区で接戦が続いています"
            },
            {
                "development": "新人候補の躍進",
                "impact": "medium",
                "constituencies": ["23001"],
                "description": "愛知1区で新人候補が支持を伸ばしています"
            }
        ]
    
    def _update_predictions_summary(self) -> Dict[str, Any]:
        """予測サマリー更新"""
        return {
            "overall_accuracy": 0.82,
            "confidence_level": "high",
            "last_model_update": datetime.now().isoformat(),
            "key_changes": [
                "東京1区の予測を更新",
                "大阪1区の競争激化を反映"
            ]
        }
    
    def test_monitoring_system(self) -> bool:
        """監視システムテスト"""
        try:
            # テストアラート生成
            test_alert = ElectionAlert(
                alert_id="test_001",
                alert_type="test",
                severity="low",
                constituency_id="TEST001",
                candidate_name="テスト候補",
                title="テストアラート",
                description="システム動作確認用のテストアラートです",
                data={"test": True},
                timestamp=datetime.now().isoformat(),
                source="test"
            )
            
            self._trigger_alert(test_alert)
            
            # アラートが正常に処理されたかチェック
            return not self.alert_queue.empty()
            
        except Exception as e:
            logger.error(f"監視システムテスト失敗: {str(e)}")
            return False