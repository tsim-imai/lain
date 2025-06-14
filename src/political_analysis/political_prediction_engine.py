"""
政治予測エンジン
感情分析・信頼性評価・データ収集を統合した日本政治予測システム
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import math
from collections import defaultdict, Counter
import statistics

from ..political_llm.political_service import PoliticalLLMService
from .political_sentiment_analyzer import PoliticalSentimentAnalyzer
from .political_reliability_scorer import PoliticalReliabilityScorer
from ..utils.config import ConfigManager
from ..utils.exceptions import AnalysisError

logger = logging.getLogger(__name__)


class PoliticalPredictionEngine:
    """政治予測エンジンクラス"""
    
    def __init__(self, 
                 config_manager: ConfigManager,
                 llm_service: PoliticalLLMService,
                 sentiment_analyzer: PoliticalSentimentAnalyzer,
                 reliability_scorer: PoliticalReliabilityScorer):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
            llm_service: 政治LLMサービスインスタンス
            sentiment_analyzer: 感情分析エンジン
            reliability_scorer: 信頼性評価エンジン
        """
        self.config_manager = config_manager
        self.llm_service = llm_service
        self.sentiment_analyzer = sentiment_analyzer
        self.reliability_scorer = reliability_scorer
        
        # 予測モデル重み設定
        self.prediction_weights = {
            "support_rating": {
                "sentiment_weight": 0.4,
                "media_weight": 0.3,
                "government_weight": 0.2,
                "social_weight": 0.1
            },
            "election_prediction": {
                "historical_weight": 0.35,
                "sentiment_weight": 0.25,
                "policy_weight": 0.2,
                "media_weight": 0.15,
                "social_weight": 0.05
            },
            "policy_analysis": {
                "government_weight": 0.4,
                "expert_weight": 0.3,
                "media_weight": 0.2,
                "public_weight": 0.1
            },
            "scandal_impact": {
                "media_weight": 0.4,
                "sentiment_weight": 0.3,
                "historical_weight": 0.2,
                "social_weight": 0.1
            }
        }
        
        # 政治イベント影響度係数
        self.event_impact_coefficients = {
            "major_policy_announcement": 1.5,
            "cabinet_reshuffle": 1.3,
            "international_crisis": 1.4,
            "economic_data_release": 1.2,
            "political_scandal": 1.6,
            "election_announcement": 1.8,
            "natural_disaster": 1.3,
            "diplomatic_meeting": 1.1
        }
        
        # 予測信頼度しきい値
        self.confidence_thresholds = {
            "very_high": 0.85,
            "high": 0.70,
            "medium": 0.55,
            "low": 0.40,
            "very_low": 0.25
        }
        
        # 予測期間別調整係数
        self.time_horizon_adjustments = {
            "short_term": {"days": 7, "accuracy_factor": 0.9},
            "medium_term": {"days": 30, "accuracy_factor": 0.75},
            "long_term": {"days": 90, "accuracy_factor": 0.6},
            "very_long_term": {"days": 365, "accuracy_factor": 0.45}
        }
        
        logger.info("政治予測エンジンを初期化")
    
    def predict_support_rating(self, 
                             current_data: Dict[str, Any],
                             prediction_horizon_days: int = 30) -> Dict[str, Any]:
        """
        内閣支持率予測
        
        Args:
            current_data: 現在のデータ（世論調査、ニュース、SNS等）
            prediction_horizon_days: 予測期間（日数）
            
        Returns:
            支持率予測結果
        """
        try:
            # 現在の支持率ベースライン
            current_support = current_data.get("current_support_rate", 0.45)
            
            # 感情分析による影響度計算
            sentiment_impact = self._calculate_sentiment_impact(
                current_data.get("sentiment_data", {}), "support_rating"
            )
            
            # メディア報道による影響度
            media_impact = self._calculate_media_impact(
                current_data.get("media_data", {}), "support_rating"
            )
            
            # 政府発表・政策による影響度
            government_impact = self._calculate_government_impact(
                current_data.get("government_data", {}), "support_rating"
            )
            
            # SNS世論による影響度
            social_impact = self._calculate_social_impact(
                current_data.get("social_data", {}), "support_rating"
            )
            
            # 外部イベント影響度
            event_impact = self._calculate_event_impact(
                current_data.get("recent_events", []), "support_rating"
            )
            
            # 重み付き影響度統合
            weights = self.prediction_weights["support_rating"]
            total_impact = (
                sentiment_impact * weights["sentiment_weight"] +
                media_impact * weights["media_weight"] +
                government_impact * weights["government_weight"] +
                social_impact * weights["social_weight"]
            ) + event_impact
            
            # 時間減衰調整
            time_adjustment = self._get_time_horizon_adjustment(prediction_horizon_days)
            adjusted_impact = total_impact * time_adjustment["accuracy_factor"]
            
            # 予測支持率計算
            predicted_support = current_support + adjusted_impact
            predicted_support = max(0.1, min(0.9, predicted_support))  # 10%-90%の範囲に制限
            
            # 予測信頼度計算
            confidence = self._calculate_prediction_confidence(
                "support_rating", current_data, adjusted_impact, prediction_horizon_days
            )
            
            # LLMによる追加分析
            llm_analysis = self._llm_prediction_analysis(
                "support_rating", current_data, predicted_support
            )
            
            prediction_result = {
                "prediction_type": "support_rating",
                "current_support_rate": current_support,
                "predicted_support_rate": predicted_support,
                "prediction_change": predicted_support - current_support,
                "prediction_horizon_days": prediction_horizon_days,
                "impact_breakdown": {
                    "sentiment_impact": sentiment_impact,
                    "media_impact": media_impact,
                    "government_impact": government_impact,
                    "social_impact": social_impact,
                    "event_impact": event_impact,
                    "total_impact": total_impact
                },
                "confidence_score": confidence,
                "confidence_level": self._categorize_confidence(confidence),
                "llm_analysis": llm_analysis,
                "prediction_timestamp": datetime.now().isoformat(),
                "factors_summary": self._generate_factors_summary("support_rating", current_data)
            }
            
            logger.info(f"支持率予測完了: {current_support:.1%} → {predicted_support:.1%}")
            return prediction_result
            
        except Exception as e:
            logger.error(f"支持率予測エラー: {str(e)}")
            return self._get_fallback_prediction("support_rating")
    
    def predict_election_outcome(self,
                               current_polling_data: Dict[str, Any],
                               prediction_horizon_days: int = 90) -> Dict[str, Any]:
        """
        選挙結果予測
        
        Args:
            current_polling_data: 現在の選挙関連データ
            prediction_horizon_days: 予測期間（日数）
            
        Returns:
            選挙結果予測
        """
        try:
            # 現在の政党支持率
            current_party_support = current_polling_data.get("party_support", {
                "自由民主党": 0.35,
                "立憲民主党": 0.18,
                "日本維新の会": 0.12,
                "公明党": 0.08,
                "その他": 0.27
            })
            
            # 歴史的データによる調整
            historical_adjustment = self._calculate_historical_election_trends(
                current_party_support, prediction_horizon_days
            )
            
            # 感情・世論による影響
            sentiment_adjustment = self._calculate_election_sentiment_impact(
                current_polling_data.get("sentiment_data", {})
            )
            
            # 政策評価による影響
            policy_adjustment = self._calculate_policy_impact_on_election(
                current_polling_data.get("policy_data", {})
            )
            
            # メディア報道による影響
            media_adjustment = self._calculate_election_media_impact(
                current_polling_data.get("media_data", {})
            )
            
            # 統合予測計算
            weights = self.prediction_weights["election_prediction"]
            predicted_support = {}
            
            for party, current_support in current_party_support.items():
                total_adjustment = (
                    historical_adjustment.get(party, 0) * weights["historical_weight"] +
                    sentiment_adjustment.get(party, 0) * weights["sentiment_weight"] +
                    policy_adjustment.get(party, 0) * weights["policy_weight"] +
                    media_adjustment.get(party, 0) * weights["media_weight"]
                )
                
                predicted_support[party] = max(0.01, min(0.8, current_support + total_adjustment))
            
            # 正規化（合計を1.0にする）
            total = sum(predicted_support.values())
            predicted_support = {party: support/total for party, support in predicted_support.items()}
            
            # 議席予測
            seat_prediction = self._predict_seat_distribution(predicted_support)
            
            # 連立可能性分析
            coalition_analysis = self._analyze_coalition_possibilities(predicted_support, seat_prediction)
            
            # 予測信頼度
            confidence = self._calculate_prediction_confidence(
                "election_prediction", current_polling_data, total_adjustment, prediction_horizon_days
            )
            
            election_prediction = {
                "prediction_type": "election_outcome",
                "current_party_support": current_party_support,
                "predicted_party_support": predicted_support,
                "predicted_seat_distribution": seat_prediction,
                "coalition_analysis": coalition_analysis,
                "prediction_horizon_days": prediction_horizon_days,
                "confidence_score": confidence,
                "confidence_level": self._categorize_confidence(confidence),
                "key_factors": {
                    "historical_trends": historical_adjustment,
                    "sentiment_impact": sentiment_adjustment,
                    "policy_impact": policy_adjustment,
                    "media_impact": media_adjustment
                },
                "prediction_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"選挙結果予測完了: 信頼度={confidence:.2f}")
            return election_prediction
            
        except Exception as e:
            logger.error(f"選挙結果予測エラー: {str(e)}")
            return self._get_fallback_prediction("election_outcome")
    
    def predict_policy_impact(self,
                            policy_proposal: Dict[str, Any],
                            prediction_horizon_days: int = 60) -> Dict[str, Any]:
        """
        政策影響予測
        
        Args:
            policy_proposal: 政策提案データ
            prediction_horizon_days: 予測期間（日数）
            
        Returns:
            政策影響予測結果
        """
        try:
            policy_title = policy_proposal.get("title", "新政策")
            policy_category = policy_proposal.get("category", "その他")
            policy_content = policy_proposal.get("content", "")
            
            # 政府・与党の立場による基本影響
            government_stance_impact = self._evaluate_government_stance_impact(policy_proposal)
            
            # 専門家・有識者の評価による影響
            expert_impact = self._evaluate_expert_opinion_impact(policy_proposal)
            
            # メディア報道予測
            media_coverage_prediction = self._predict_media_coverage_impact(policy_proposal)
            
            # 国民世論への影響予測
            public_opinion_impact = self._predict_public_opinion_impact(policy_proposal)
            
            # 政策実現可能性
            feasibility_assessment = self._assess_policy_feasibility(policy_proposal)
            
            # 統合影響度計算
            weights = self.prediction_weights["policy_analysis"]
            overall_impact = (
                government_stance_impact * weights["government_weight"] +
                expert_impact * weights["expert_weight"] +
                media_coverage_prediction * weights["media_weight"] +
                public_opinion_impact * weights["public_weight"]
            )
            
            # 支持率への影響予測
            support_rate_impact = overall_impact * self._get_policy_support_multiplier(policy_category)
            
            # LLMによる政策分析
            llm_policy_analysis = self._llm_policy_analysis(policy_proposal)
            
            # 予測信頼度
            confidence = self._calculate_prediction_confidence(
                "policy_analysis", policy_proposal, overall_impact, prediction_horizon_days
            )
            
            policy_prediction = {
                "prediction_type": "policy_impact",
                "policy_title": policy_title,
                "policy_category": policy_category,
                "overall_impact_score": overall_impact,
                "support_rate_impact": support_rate_impact,
                "impact_breakdown": {
                    "government_stance": government_stance_impact,
                    "expert_opinion": expert_impact,
                    "media_coverage": media_coverage_prediction,
                    "public_opinion": public_opinion_impact
                },
                "feasibility_assessment": feasibility_assessment,
                "llm_analysis": llm_policy_analysis,
                "prediction_horizon_days": prediction_horizon_days,
                "confidence_score": confidence,
                "confidence_level": self._categorize_confidence(confidence),
                "prediction_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"政策影響予測完了: {policy_title} - 影響度={overall_impact:.2f}")
            return policy_prediction
            
        except Exception as e:
            logger.error(f"政策影響予測エラー: {str(e)}")
            return self._get_fallback_prediction("policy_impact")
    
    def predict_scandal_impact(self,
                             scandal_data: Dict[str, Any],
                             prediction_horizon_days: int = 14) -> Dict[str, Any]:
        """
        政治スキャンダル影響予測
        
        Args:
            scandal_data: スキャンダル関連データ
            prediction_horizon_days: 予測期間（日数）
            
        Returns:
            スキャンダル影響予測結果
        """
        try:
            scandal_severity = scandal_data.get("severity", "medium")
            involved_politicians = scandal_data.get("involved_politicians", [])
            scandal_type = scandal_data.get("type", "other")
            
            # メディア報道による増幅効果
            media_amplification = self._calculate_scandal_media_amplification(scandal_data)
            
            # 感情的反応による影響
            emotional_impact = self._calculate_scandal_emotional_impact(scandal_data)
            
            # 歴史的類似事例による影響予測
            historical_pattern = self._analyze_historical_scandal_patterns(
                scandal_type, scandal_severity
            )
            
            # SNS拡散による影響
            social_amplification = self._calculate_scandal_social_amplification(scandal_data)
            
            # 統合影響度計算
            weights = self.prediction_weights["scandal_impact"]
            total_impact = (
                media_amplification * weights["media_weight"] +
                emotional_impact * weights["sentiment_weight"] +
                historical_pattern * weights["historical_weight"] +
                social_amplification * weights["social_weight"]
            )
            
            # スキャンダル深刻度による調整
            severity_multiplier = self._get_scandal_severity_multiplier(scandal_severity)
            adjusted_impact = total_impact * severity_multiplier
            
            # 支持率への具体的影響予測
            support_rate_decline = adjusted_impact * 0.15  # 最大15%の下落
            
            # 回復時期予測
            recovery_prediction = self._predict_scandal_recovery_timeline(
                scandal_data, adjusted_impact
            )
            
            # 予測信頼度
            confidence = self._calculate_prediction_confidence(
                "scandal_impact", scandal_data, adjusted_impact, prediction_horizon_days
            )
            
            scandal_prediction = {
                "prediction_type": "scandal_impact",
                "scandal_type": scandal_type,
                "scandal_severity": scandal_severity,
                "involved_politicians": involved_politicians,
                "total_impact_score": adjusted_impact,
                "predicted_support_decline": support_rate_decline,
                "impact_breakdown": {
                    "media_amplification": media_amplification,
                    "emotional_impact": emotional_impact,
                    "historical_pattern": historical_pattern,
                    "social_amplification": social_amplification
                },
                "recovery_prediction": recovery_prediction,
                "prediction_horizon_days": prediction_horizon_days,
                "confidence_score": confidence,
                "confidence_level": self._categorize_confidence(confidence),
                "prediction_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"スキャンダル影響予測完了: 影響度={adjusted_impact:.2f}")
            return scandal_prediction
            
        except Exception as e:
            logger.error(f"スキャンダル影響予測エラー: {str(e)}")
            return self._get_fallback_prediction("scandal_impact")
    
    def generate_comprehensive_political_forecast(self,
                                                comprehensive_data: Dict[str, Any],
                                                forecast_period_days: int = 90) -> Dict[str, Any]:
        """
        包括的政治予測レポート生成
        
        Args:
            comprehensive_data: 統合政治データ
            forecast_period_days: 予測期間（日数）
            
        Returns:
            包括的政治予測レポート
        """
        try:
            # 各分野の予測実行
            support_prediction = self.predict_support_rating(
                comprehensive_data, forecast_period_days
            )
            
            election_prediction = self.predict_election_outcome(
                comprehensive_data, forecast_period_days
            )
            
            # 政策影響分析（複数政策）
            policy_predictions = []
            for policy in comprehensive_data.get("upcoming_policies", []):
                policy_pred = self.predict_policy_impact(policy, forecast_period_days)
                policy_predictions.append(policy_pred)
            
            # 重要イベント影響分析
            event_impacts = []
            for event in comprehensive_data.get("upcoming_events", []):
                event_impact = self._analyze_event_political_impact(event)
                event_impacts.append(event_impact)
            
            # 総合リスク評価
            overall_risk_assessment = self._calculate_overall_political_risk(
                support_prediction, election_prediction, policy_predictions, event_impacts
            )
            
            # シナリオ分析
            scenario_analysis = self._generate_scenario_analysis(
                comprehensive_data, forecast_period_days
            )
            
            # LLMによる総合分析
            llm_comprehensive_analysis = self._llm_comprehensive_analysis(
                comprehensive_data, [support_prediction, election_prediction]
            )
            
            # 予測精度評価
            accuracy_assessment = self._assess_forecast_accuracy(
                comprehensive_data, forecast_period_days
            )
            
            comprehensive_forecast = {
                "forecast_type": "comprehensive_political_forecast",
                "forecast_period_days": forecast_period_days,
                "forecast_timestamp": datetime.now().isoformat(),
                "executive_summary": self._generate_executive_summary(
                    support_prediction, election_prediction, policy_predictions
                ),
                "support_rating_forecast": support_prediction,
                "election_forecast": election_prediction,
                "policy_impact_forecasts": policy_predictions,
                "event_impact_analysis": event_impacts,
                "overall_risk_assessment": overall_risk_assessment,
                "scenario_analysis": scenario_analysis,
                "llm_comprehensive_analysis": llm_comprehensive_analysis,
                "accuracy_assessment": accuracy_assessment,
                "key_uncertainty_factors": self._identify_key_uncertainties(comprehensive_data),
                "monitoring_recommendations": self._generate_monitoring_recommendations(comprehensive_data)
            }
            
            logger.info(f"包括的政治予測完了: 期間={forecast_period_days}日")
            return comprehensive_forecast
            
        except Exception as e:
            logger.error(f"包括的政治予測エラー: {str(e)}")
            return {"error": str(e)}
    
    # 以下、内部メソッド群
    
    def _calculate_sentiment_impact(self, sentiment_data: Dict, prediction_type: str) -> float:
        """感情分析による影響度計算"""
        if not sentiment_data:
            return 0.0
        
        avg_sentiment = sentiment_data.get("average_sentiment", 0.0)
        sentiment_volatility = sentiment_data.get("volatility", 0.3)
        
        # 感情の強度による影響度調整
        impact = avg_sentiment * (1.0 + sentiment_volatility * 0.5)
        
        # 予測タイプ別調整
        if prediction_type == "support_rating":
            impact *= 1.2  # 支持率は感情に敏感
        elif prediction_type == "election_prediction":
            impact *= 0.8  # 選挙は感情だけでは決まらない
        
        return max(-0.3, min(0.3, impact))
    
    def _calculate_media_impact(self, media_data: Dict, prediction_type: str) -> float:
        """メディア報道による影響度計算"""
        if not media_data:
            return 0.0
        
        media_sentiment = media_data.get("average_sentiment", 0.0)
        coverage_volume = media_data.get("coverage_volume", 0.5)
        media_credibility = media_data.get("average_credibility", 0.7)
        
        # 報道量と信頼性を考慮した影響度
        impact = media_sentiment * coverage_volume * media_credibility
        
        return max(-0.25, min(0.25, impact))
    
    def _calculate_government_impact(self, government_data: Dict, prediction_type: str) -> float:
        """政府発表による影響度計算"""
        if not government_data:
            return 0.0
        
        official_tone = government_data.get("official_tone", 0.0)
        announcement_frequency = government_data.get("announcement_frequency", 0.5)
        policy_success_rate = government_data.get("policy_success_rate", 0.6)
        
        impact = official_tone * announcement_frequency * policy_success_rate
        
        return max(-0.2, min(0.2, impact))
    
    def _calculate_social_impact(self, social_data: Dict, prediction_type: str) -> float:
        """SNS世論による影響度計算"""
        if not social_data:
            return 0.0
        
        social_sentiment = social_data.get("average_sentiment", 0.0)
        engagement_level = social_data.get("engagement_level", 0.5)
        
        # SNSは影響度を減衰させる（信頼性が低いため）
        impact = social_sentiment * engagement_level * 0.6
        
        return max(-0.15, min(0.15, impact))
    
    def _calculate_event_impact(self, events: List[Dict], prediction_type: str) -> float:
        """外部イベント影響度計算"""
        if not events:
            return 0.0
        
        total_impact = 0.0
        for event in events:
            event_type = event.get("type", "other")
            event_magnitude = event.get("magnitude", 0.5)
            
            coefficient = self.event_impact_coefficients.get(event_type, 1.0)
            impact = event_magnitude * coefficient * 0.1
            total_impact += impact
        
        return max(-0.4, min(0.4, total_impact))
    
    def _get_time_horizon_adjustment(self, days: int) -> Dict[str, Any]:
        """時間軸調整係数取得"""
        for horizon, config in self.time_horizon_adjustments.items():
            if days <= config["days"]:
                return config
        
        return self.time_horizon_adjustments["very_long_term"]
    
    def _calculate_prediction_confidence(self, prediction_type: str, input_data: Dict, 
                                       impact_magnitude: float, horizon_days: int) -> float:
        """予測信頼度計算"""
        base_confidence = 0.6
        
        # データ品質による調整
        data_quality = self._assess_data_quality(input_data)
        base_confidence *= data_quality
        
        # 影響度の大きさによる調整（極端すぎる予測は信頼度低下）
        if abs(impact_magnitude) > 0.5:
            base_confidence *= 0.8
        
        # 予測期間による調整
        time_adjustment = self._get_time_horizon_adjustment(horizon_days)
        base_confidence *= time_adjustment["accuracy_factor"]
        
        # 予測タイプ別調整
        type_adjustments = {
            "support_rating": 1.0,
            "election_prediction": 0.8,
            "policy_analysis": 0.9,
            "scandal_impact": 0.7
        }
        base_confidence *= type_adjustments.get(prediction_type, 0.8)
        
        return max(0.1, min(0.95, base_confidence))
    
    def _llm_prediction_analysis(self, prediction_type: str, data: Dict, prediction: float) -> Dict[str, Any]:
        """LLMによる予測分析"""
        try:
            analysis_prompt = f"""
以下の政治予測について分析してください：

【予測タイプ】: {prediction_type}
【予測結果】: {prediction}
【入力データ】: {str(data)[:300]}...

【分析項目】
1. 予測の妥当性
2. 主要影響要因
3. リスク要因
4. 代替シナリオ

JSON形式で回答してください。
"""
            
            llm_response = self.llm_service.get_llm_response(analysis_prompt)
            
            try:
                return json.loads(llm_response)
            except:
                return {
                    "validity": "moderate",
                    "key_factors": ["データ不足により詳細分析困難"],
                    "risks": ["予測精度に限界あり"],
                    "alternative_scenarios": ["現状維持シナリオ"]
                }
                
        except Exception as e:
            logger.warning(f"LLM予測分析エラー: {str(e)}")
            return {"error": "LLM分析に失敗しました"}
    
    def _categorize_confidence(self, confidence: float) -> str:
        """信頼度カテゴリ化"""
        for level, threshold in self.confidence_thresholds.items():
            if confidence >= threshold:
                return level
        return "very_low"
    
    def _generate_factors_summary(self, prediction_type: str, data: Dict) -> List[str]:
        """要因サマリー生成"""
        factors = []
        
        if prediction_type == "support_rating":
            if data.get("sentiment_data", {}).get("average_sentiment", 0) > 0.2:
                factors.append("世論の好感度上昇")
            if data.get("media_data", {}).get("coverage_volume", 0) > 0.7:
                factors.append("メディア報道の活発化")
            if data.get("government_data", {}).get("policy_success_rate", 0) > 0.7:
                factors.append("政策実行力の評価")
        
        return factors if factors else ["特定要因なし"]
    
    def _calculate_historical_election_trends(self, current_support: Dict, horizon_days: int) -> Dict[str, float]:
        """歴史的選挙トレンドによる調整"""
        # 簡略化された歴史トレンド（実際は過去データベースから取得）
        historical_adjustments = {}
        
        for party, support in current_support.items():
            if party == "自由民主党":
                # 与党は選挙時に若干低下する傾向
                historical_adjustments[party] = -0.02
            elif party == "立憲民主党":
                # 野党第一党は選挙時に微増する傾向
                historical_adjustments[party] = 0.01
            else:
                historical_adjustments[party] = 0.0
        
        return historical_adjustments
    
    def _calculate_election_sentiment_impact(self, sentiment_data: Dict) -> Dict[str, float]:
        """選挙における感情影響計算"""
        if not sentiment_data:
            return {}
        
        avg_sentiment = sentiment_data.get("average_sentiment", 0.0)
        
        # 与野党への異なる影響
        return {
            "自由民主党": avg_sentiment * 0.8,  # 与党は感情影響を受けやすい
            "立憲民主党": -avg_sentiment * 0.5,  # 野党は逆に受益
            "日本維新の会": avg_sentiment * 0.3,
            "公明党": avg_sentiment * 0.2,
            "その他": 0.0
        }
    
    def _calculate_policy_impact_on_election(self, policy_data: Dict) -> Dict[str, float]:
        """政策の選挙への影響計算"""
        if not policy_data:
            return {}
        
        policy_approval = policy_data.get("average_approval", 0.5)
        
        # 政策評価による政党支持への影響
        return {
            "自由民主党": (policy_approval - 0.5) * 0.1,
            "立憲民主党": -(policy_approval - 0.5) * 0.05,
            "日本維新の会": 0.0,
            "公明党": (policy_approval - 0.5) * 0.03,
            "その他": 0.0
        }
    
    def _calculate_election_media_impact(self, media_data: Dict) -> Dict[str, float]:
        """メディアの選挙への影響計算"""
        if not media_data:
            return {}
        
        media_bias = media_data.get("average_bias", 0.0)
        coverage_intensity = media_data.get("coverage_intensity", 0.5)
        
        # メディアバイアスによる影響
        return {
            "自由民主党": media_bias * coverage_intensity * 0.05,
            "立憲民主党": -media_bias * coverage_intensity * 0.05,
            "日本維新の会": 0.0,
            "公明党": 0.0,
            "その他": 0.0
        }
    
    def _predict_seat_distribution(self, party_support: Dict) -> Dict[str, int]:
        """議席配分予測（簡略化）"""
        total_seats = 465  # 衆議院総議席数
        
        seat_distribution = {}
        for party, support_rate in party_support.items():
            # 支持率から議席数への変換（比例的だが小政党不利を反映）
            if support_rate > 0.1:
                seats = int(total_seats * support_rate * 1.1)  # 大政党有利
            else:
                seats = int(total_seats * support_rate * 0.8)  # 小政党不利
            
            seat_distribution[party] = min(seats, total_seats)
        
        # 総議席数調整
        total_predicted = sum(seat_distribution.values())
        if total_predicted != total_seats:
            # 最大政党で調整
            max_party = max(seat_distribution, key=seat_distribution.get)
            seat_distribution[max_party] += total_seats - total_predicted
        
        return seat_distribution
    
    def _analyze_coalition_possibilities(self, party_support: Dict, seat_distribution: Dict) -> Dict[str, Any]:
        """連立可能性分析"""
        total_seats = sum(seat_distribution.values())
        majority_threshold = total_seats // 2 + 1
        
        # 現在の与党連立（自民・公明）
        current_coalition = seat_distribution.get("自由民主党", 0) + seat_distribution.get("公明党", 0)
        
        coalition_scenarios = [
            {
                "coalition": ["自由民主党", "公明党"],
                "seats": current_coalition,
                "probability": 0.8 if current_coalition >= majority_threshold else 0.3,
                "stability": "high" if current_coalition >= majority_threshold else "low"
            }
        ]
        
        # 野党連立の可能性
        opposition_seats = (
            seat_distribution.get("立憲民主党", 0) +
            seat_distribution.get("日本維新の会", 0) +
            seat_distribution.get("その他", 0)
        )
        
        if opposition_seats >= majority_threshold:
            coalition_scenarios.append({
                "coalition": ["立憲民主党", "日本維新の会", "その他"],
                "seats": opposition_seats,
                "probability": 0.4,
                "stability": "medium"
            })
        
        return {
            "majority_threshold": majority_threshold,
            "coalition_scenarios": coalition_scenarios,
            "most_likely_government": coalition_scenarios[0]["coalition"]
        }
    
    def _assess_data_quality(self, data: Dict) -> float:
        """データ品質評価"""
        quality_score = 0.5
        
        # データの豊富さ
        data_richness = len([v for v in data.values() if v]) / max(len(data), 1)
        quality_score += data_richness * 0.3
        
        # データの新しさ（タイムスタンプがある場合）
        if "timestamp" in data:
            try:
                data_time = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
                age_hours = (datetime.now() - data_time).total_seconds() / 3600
                freshness = max(0, 1 - age_hours / 168)  # 1週間で完全に古くなる
                quality_score += freshness * 0.2
            except:
                pass
        
        return min(max(quality_score, 0.1), 1.0)
    
    def _get_fallback_prediction(self, prediction_type: str) -> Dict[str, Any]:
        """フォールバック予測結果"""
        return {
            "prediction_type": prediction_type,
            "confidence_score": 0.3,
            "confidence_level": "low",
            "error": "予測処理中にエラーが発生しました",
            "prediction_timestamp": datetime.now().isoformat()
        }
    
    def test_prediction_engine(self) -> bool:
        """予測エンジン機能テスト"""
        try:
            test_data = {
                "current_support_rate": 0.45,
                "sentiment_data": {"average_sentiment": 0.1},
                "media_data": {"coverage_volume": 0.6},
                "government_data": {"policy_success_rate": 0.7},
                "social_data": {"engagement_level": 0.5}
            }
            
            result = self.predict_support_rating(test_data, 30)
            return "predicted_support_rate" in result
        except Exception as e:
            logger.error(f"予測エンジンテスト失敗: {str(e)}")
            return False