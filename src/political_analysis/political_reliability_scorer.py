"""
政治信頼性評価エンジン
政治情報ソース・コンテンツの信頼性を多角的に評価し、予測精度向上に貢献
"""
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
import re
import json
from collections import defaultdict, Counter
import math
from urllib.parse import urlparse

from ..political_llm.political_service import PoliticalLLMService
from ..utils.config import ConfigManager
from ..utils.exceptions import AnalysisError

logger = logging.getLogger(__name__)


class PoliticalReliabilityScorer:
    """政治信頼性評価エンジンクラス"""
    
    def __init__(self, config_manager: ConfigManager, llm_service: PoliticalLLMService):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
            llm_service: 政治LLMサービスインスタンス
        """
        self.config_manager = config_manager
        self.llm_service = llm_service
        
        # ソース信頼性基準スコア
        self.source_reliability_scores = {
            # 政府公式 - 最高信頼性
            "government": {
                "kantei.go.jp": 1.0,
                "gov.go.jp": 1.0,
                "soumu.go.jp": 0.98,
                "mof.go.jp": 0.98,
                "mofa.go.jp": 0.98,
                "mhlw.go.jp": 0.95,
                "mext.go.jp": 0.95,
                "meti.go.jp": 0.95,
                "mlit.go.jp": 0.95
            },
            
            # 主要報道機関 - 高信頼性
            "major_media": {
                "nhk.or.jp": 0.95,
                "kyodo.co.jp": 0.93,
                "jiji.com": 0.93,
                "asahi.com": 0.88,
                "yomiuri.co.jp": 0.88,
                "mainichi.jp": 0.85,
                "sankei.com": 0.85,
                "nikkei.com": 0.90
            },
            
            # 政党公式 - 高信頼性（バイアスあり）
            "political_parties": {
                "jimin.jp": 0.90,
                "cdp-japan.jp": 0.90,
                "o-ishin.jp": 0.88,
                "komei.or.jp": 0.88,
                "jcp.or.jp": 0.88,
                "new-kokumin.jp": 0.85,
                "reiwa-shinsengumi.com": 0.82,
                "sdp.or.jp": 0.82
            },
            
            # 国会・公的機関 - 高信頼性
            "official_institutions": {
                "kokkai.ndl.go.jp": 0.95,
                "senkyo.go.jp": 0.93,
                "stat.go.jp": 0.95,
                "cao.go.jp": 0.92
            },
            
            # 専門メディア - 中高信頼性
            "specialized_media": {
                "seijiyama.jp": 0.78,
                "go2senkyo.com": 0.80,
                "blogos.com": 0.70,
                "newspicks.com": 0.75
            },
            
            # 一般メディア - 中信頼性
            "general_media": {
                "yahoo.co.jp": 0.65,
                "livedoor.com": 0.60,
                "goo.ne.jp": 0.62
            },
            
            # SNS・個人発信 - 低信頼性
            "social_media": {
                "twitter.com": 0.40,
                "facebook.com": 0.40,
                "instagram.com": 0.35,
                "note.com": 0.50,
                "ameblo.jp": 0.35,
                "hatena.ne.jp": 0.45
            }
        }
        
        # 信頼性減点要因
        self.reliability_penalties = {
            "misinformation_indicators": {
                "strong": ["デマ", "フェイクニュース", "捏造", "偽情報"],
                "medium": ["未確認", "疑問視", "根拠不明", "憶測"],
                "weak": ["らしい", "という話", "噂では", "とのこと"]
            },
            "sensationalism": {
                "excessive_emphasis": [r"！{3,}", r"\!{3,}", r"？{3,}", r"\?{3,}"],
                "clickbait_phrases": ["衝撃", "緊急", "速報", "大炸裂", "激震", "驚愕"],
                "emotional_language": ["大変だ", "とんでもない", "信じられない", "ありえない"]
            },
            "bias_indicators": {
                "extreme_language": ["絶対", "完全に", "間違いなく", "必ず", "100%"],
                "partisan_attacks": ["売国奴", "反日", "左翼", "右翼", "工作員"],
                "conspiracy_terms": ["陰謀", "裏で操る", "隠蔽", "闇の勢力", "真実を隠す"]
            }
        }
        
        # コンテンツ品質評価基準
        self.content_quality_metrics = {
            "structure_indicators": {
                "positive": ["出典", "引用", "データ", "統計", "調査結果", "専門家"],
                "negative": ["個人的意見", "主観", "推測", "想像", "決めつけ"]
            },
            "factual_markers": {
                "high_confidence": ["発表", "公式", "正式", "確認", "認定"],
                "medium_confidence": ["報告", "発言", "表明", "見解", "分析"],
                "low_confidence": ["可能性", "予想", "推定", "見込み", "おそらく"]
            },
            "time_sensitivity": {
                "breaking_news": ["速報", "緊急", "臨時", "号外"],
                "regular_news": ["報告", "発表", "会見", "取材"],
                "analysis": ["分析", "解説", "考察", "評価", "検証"]
            }
        }
        
        # ファクトチェック関連キーワード
        self.fact_check_indicators = {
            "verification_sources": ["ファクトチェック", "検証", "確認済み", "裏付け"],
            "correction_indicators": ["訂正", "修正", "誤報", "取り消し", "撤回"],
            "uncertainty_markers": ["未確認", "検証中", "調査中", "詳細不明"]
        }
        
        logger.info("政治信頼性評価エンジンを初期化")
    
    def evaluate_source_reliability(self, 
                                   source_url: str, 
                                   source_name: Optional[str] = None,
                                   content_type: str = "news") -> Dict[str, Any]:
        """
        ソースの信頼性評価
        
        Args:
            source_url: ソースURL
            source_name: ソース名（オプション）
            content_type: コンテンツタイプ
            
        Returns:
            ソース信頼性評価結果
        """
        try:
            # URL解析
            parsed_url = urlparse(source_url)
            domain = parsed_url.netloc.lower()
            
            # ドメインベースの基本信頼性スコア
            base_reliability = self._get_domain_reliability_score(domain)
            
            # ソースカテゴリ判定
            source_category = self._categorize_source(domain)
            
            # URL構造による信頼性調整
            url_reliability_factor = self._analyze_url_structure(source_url)
            
            # コンテンツタイプによる調整
            content_type_factor = self._get_content_type_factor(content_type)
            
            # 最終信頼性スコア計算
            final_reliability = (
                base_reliability * 0.6 +
                url_reliability_factor * 0.2 +
                content_type_factor * 0.2
            )
            
            # ソース特徴分析
            source_characteristics = self._analyze_source_characteristics(domain, source_category)
            
            evaluation_result = {
                "source_url": source_url,
                "domain": domain,
                "source_name": source_name,
                "source_category": source_category,
                "base_reliability": base_reliability,
                "url_reliability_factor": url_reliability_factor,
                "content_type_factor": content_type_factor,
                "final_reliability_score": final_reliability,
                "source_characteristics": source_characteristics,
                "reliability_level": self._categorize_reliability_level(final_reliability),
                "evaluation_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"ソース信頼性評価完了: {domain} = {final_reliability:.2f}")
            return evaluation_result
            
        except Exception as e:
            logger.error(f"ソース信頼性評価エラー: {str(e)}")
            return self._get_fallback_source_evaluation()
    
    def evaluate_content_reliability(self, 
                                   content: str, 
                                   source_info: Optional[Dict] = None,
                                   metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        コンテンツの信頼性評価
        
        Args:
            content: 評価対象コンテンツ
            source_info: ソース情報
            metadata: メタデータ（日付、著者等）
            
        Returns:
            コンテンツ信頼性評価結果
        """
        try:
            # 基本的な信頼性指標
            factual_quality = self._assess_factual_quality(content)
            
            # 偽情報・デマ指標
            misinformation_risk = self._detect_misinformation_indicators(content)
            
            # センセーショナリズム評価
            sensationalism_score = self._evaluate_sensationalism(content)
            
            # バイアス検出
            bias_assessment = self._assess_content_bias(content)
            
            # 構造的品質評価
            structural_quality = self._evaluate_content_structure(content)
            
            # ファクトチェック要因
            fact_check_status = self._analyze_fact_check_indicators(content)
            
            # LLMによる高度な信頼性評価
            llm_reliability = self._llm_reliability_assessment(content)
            
            # ソース情報との整合性
            source_consistency = self._evaluate_source_consistency(content, source_info)
            
            # 総合信頼性スコア計算
            overall_reliability = self._calculate_overall_content_reliability(
                factual_quality, misinformation_risk, sensationalism_score,
                bias_assessment, structural_quality, llm_reliability, source_consistency
            )
            
            reliability_result = {
                "content_preview": content[:150] + "..." if len(content) > 150 else content,
                "factual_quality": factual_quality,
                "misinformation_risk": misinformation_risk,
                "sensationalism_score": sensationalism_score,
                "bias_assessment": bias_assessment,
                "structural_quality": structural_quality,
                "fact_check_status": fact_check_status,
                "llm_reliability": llm_reliability,
                "source_consistency": source_consistency,
                "overall_reliability_score": overall_reliability,
                "reliability_grade": self._assign_reliability_grade(overall_reliability),
                "evaluation_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"コンテンツ信頼性評価完了: スコア={overall_reliability:.2f}")
            return reliability_result
            
        except Exception as e:
            logger.error(f"コンテンツ信頼性評価エラー: {str(e)}")
            return self._get_fallback_content_evaluation()
    
    def evaluate_cross_source_consistency(self, 
                                        content_by_source: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        複数ソース間の情報一貫性評価
        
        Args:
            content_by_source: ソース別コンテンツ辞書
            
        Returns:
            一貫性評価結果
        """
        try:
            source_evaluations = {}
            content_similarities = {}
            consistency_matrix = {}
            
            # 各ソースの信頼性評価
            for source, contents in content_by_source.items():
                source_reliability = self.evaluate_source_reliability(source)
                
                content_reliabilities = []
                for content in contents:
                    content_eval = self.evaluate_content_reliability(content, source_reliability)
                    content_reliabilities.append(content_eval["overall_reliability_score"])
                
                source_evaluations[source] = {
                    "source_reliability": source_reliability["final_reliability_score"],
                    "content_count": len(contents),
                    "average_content_reliability": sum(content_reliabilities) / len(content_reliabilities),
                    "reliability_variance": self._calculate_variance(content_reliabilities)
                }
            
            # ソース間の内容類似性分析
            sources = list(content_by_source.keys())
            for i, source1 in enumerate(sources):
                for source2 in sources[i+1:]:
                    similarity = self._calculate_content_similarity(
                        content_by_source[source1], 
                        content_by_source[source2]
                    )
                    content_similarities[f"{source1}-{source2}"] = similarity
            
            # 一貫性スコア計算
            consistency_scores = self._calculate_consistency_scores(
                source_evaluations, content_similarities
            )
            
            # 異常値・外れ値検出
            outliers = self._detect_reliability_outliers(source_evaluations)
            
            consistency_result = {
                "source_evaluations": source_evaluations,
                "content_similarities": content_similarities,
                "consistency_scores": consistency_scores,
                "detected_outliers": outliers,
                "overall_consistency": consistency_scores.get("overall_consistency", 0.5),
                "evaluation_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"クロスソース一貫性評価完了: 一貫性={consistency_scores.get('overall_consistency', 0.5):.2f}")
            return consistency_result
            
        except Exception as e:
            logger.error(f"クロスソース一貫性評価エラー: {str(e)}")
            return {"error": str(e)}
    
    def track_source_reliability_history(self, 
                                       source: str, 
                                       reliability_scores: List[Dict],
                                       time_window_days: int = 30) -> Dict[str, Any]:
        """
        ソース信頼性履歴追跡
        
        Args:
            source: ソース名/URL
            reliability_scores: 信頼性スコア履歴
            time_window_days: 分析期間（日数）
            
        Returns:
            信頼性履歴分析結果
        """
        try:
            # 時系列データ整理
            timeline_data = sorted(reliability_scores, 
                                 key=lambda x: x.get("timestamp", datetime.now().isoformat()))
            
            # 統計指標計算
            scores = [item.get("reliability_score", 0.5) for item in timeline_data]
            
            if scores:
                stats = {
                    "average_reliability": sum(scores) / len(scores),
                    "reliability_trend": self._calculate_trend(scores),
                    "reliability_volatility": self._calculate_variance(scores),
                    "min_reliability": min(scores),
                    "max_reliability": max(scores),
                    "sample_count": len(scores)
                }
                
                # 異常期間検出
                anomaly_periods = self._detect_reliability_anomalies(timeline_data)
                
                # 改善・悪化トレンド
                trend_analysis = self._analyze_reliability_trends(timeline_data)
                
                history_result = {
                    "source": source,
                    "time_window_days": time_window_days,
                    "timeline_data": timeline_data,
                    "statistics": stats,
                    "anomaly_periods": anomaly_periods,
                    "trend_analysis": trend_analysis,
                    "reliability_grade_history": [
                        self._assign_reliability_grade(score) for score in scores
                    ],
                    "analysis_timestamp": datetime.now().isoformat()
                }
                
                logger.info(f"信頼性履歴追跡完了: {source} - 平均={stats['average_reliability']:.2f}")
                return history_result
            
            return {"error": "分析データが不足しています"}
            
        except Exception as e:
            logger.error(f"信頼性履歴追跡エラー: {str(e)}")
            return {"error": str(e)}
    
    def _get_domain_reliability_score(self, domain: str) -> float:
        """ドメインベース信頼性スコア取得"""
        domain_lower = domain.lower()
        
        # 各カテゴリを順番に確認
        for category, domains in self.source_reliability_scores.items():
            for known_domain, score in domains.items():
                if known_domain in domain_lower:
                    return score
        
        # 未知のドメインの場合は中程度の信頼性
        return 0.5
    
    def _categorize_source(self, domain: str) -> str:
        """ソースカテゴリ分類"""
        domain_lower = domain.lower()
        
        if any(domain_lower.find(gov_domain) != -1 for gov_domain in 
               ["go.jp", "kantei", "gov", "mhlw", "mext", "meti", "mlit"]):
            return "government"
        elif any(domain_lower.find(media_domain) != -1 for media_domain in 
                ["nhk", "asahi", "yomiuri", "mainichi", "sankei", "nikkei", "kyodo", "jiji"]):
            return "major_media"
        elif any(domain_lower.find(party_domain) != -1 for party_domain in 
                ["jimin", "cdp-japan", "o-ishin", "komei", "jcp"]):
            return "political_parties"
        elif any(domain_lower.find(sns_domain) != -1 for sns_domain in 
                ["twitter", "facebook", "instagram", "note", "ameblo"]):
            return "social_media"
        else:
            return "general_media"
    
    def _analyze_url_structure(self, url: str) -> float:
        """URL構造による信頼性調整"""
        reliability_factor = 1.0
        
        # HTTPS使用
        if url.startswith("https://"):
            reliability_factor += 0.05
        
        # 公式パス構造
        official_paths = ["/news/", "/press/", "/policy/", "/official/"]
        if any(path in url for path in official_paths):
            reliability_factor += 0.03
        
        # 怪しいパス構造
        suspicious_paths = ["/fake/", "/rumor/", "/gossip/", "/opinion/"]
        if any(path in url for path in suspicious_paths):
            reliability_factor -= 0.1
        
        # 非常に長いURL（スパム的）
        if len(url) > 200:
            reliability_factor -= 0.02
        
        return min(max(reliability_factor, 0.5), 1.2)
    
    def _get_content_type_factor(self, content_type: str) -> float:
        """コンテンツタイプによる信頼性調整"""
        type_factors = {
            "official_statement": 1.0,
            "news": 0.9,
            "analysis": 0.8,
            "opinion": 0.6,
            "social_post": 0.4,
            "rumor": 0.2
        }
        return type_factors.get(content_type, 0.7)
    
    def _analyze_source_characteristics(self, domain: str, category: str) -> Dict[str, Any]:
        """ソース特徴分析"""
        characteristics = {
            "primary_category": category,
            "update_frequency": "unknown",
            "editorial_stance": "unknown",
            "fact_checking_policy": "unknown"
        }
        
        # カテゴリ別特徴
        if category == "government":
            characteristics.update({
                "update_frequency": "regular",
                "editorial_stance": "official",
                "fact_checking_policy": "high_standard"
            })
        elif category == "major_media":
            characteristics.update({
                "update_frequency": "frequent",
                "editorial_stance": "varies",
                "fact_checking_policy": "standard"
            })
        elif category == "social_media":
            characteristics.update({
                "update_frequency": "real_time",
                "editorial_stance": "personal",
                "fact_checking_policy": "user_dependent"
            })
        
        return characteristics
    
    def _assess_factual_quality(self, content: str) -> Dict[str, Any]:
        """事実性品質評価"""
        factual_score = 0.5  # ベースライン
        
        # 高信頼性指標
        high_confidence_count = sum(
            1 for marker in self.content_quality_metrics["factual_markers"]["high_confidence"]
            if marker in content
        )
        factual_score += high_confidence_count * 0.1
        
        # 中信頼性指標
        medium_confidence_count = sum(
            1 for marker in self.content_quality_metrics["factual_markers"]["medium_confidence"]
            if marker in content
        )
        factual_score += medium_confidence_count * 0.05
        
        # 低信頼性指標（減点）
        low_confidence_count = sum(
            1 for marker in self.content_quality_metrics["factual_markers"]["low_confidence"]
            if marker in content
        )
        factual_score -= low_confidence_count * 0.05
        
        # 構造的品質指標
        positive_structure = sum(
            1 for indicator in self.content_quality_metrics["structure_indicators"]["positive"]
            if indicator in content
        )
        factual_score += positive_structure * 0.08
        
        # 負の構造指標（減点）
        negative_structure = sum(
            1 for indicator in self.content_quality_metrics["structure_indicators"]["negative"]
            if indicator in content
        )
        factual_score -= negative_structure * 0.06
        
        return {
            "factual_score": min(max(factual_score, 0.0), 1.0),
            "high_confidence_markers": high_confidence_count,
            "medium_confidence_markers": medium_confidence_count,
            "low_confidence_markers": low_confidence_count,
            "positive_structure_indicators": positive_structure,
            "negative_structure_indicators": negative_structure
        }
    
    def _detect_misinformation_indicators(self, content: str) -> Dict[str, Any]:
        """偽情報・デマ指標検出"""
        misinformation_risk = 0.0
        detected_indicators = {"strong": [], "medium": [], "weak": []}
        
        for strength, indicators in self.reliability_penalties["misinformation_indicators"].items():
            count = 0
            for indicator in indicators:
                if indicator in content:
                    count += 1
                    detected_indicators[strength].append(indicator)
            
            # 強度別リスクスコア
            if strength == "strong":
                misinformation_risk += count * 0.3
            elif strength == "medium":
                misinformation_risk += count * 0.2
            else:  # weak
                misinformation_risk += count * 0.1
        
        return {
            "misinformation_risk_score": min(misinformation_risk, 1.0),
            "detected_indicators": detected_indicators,
            "risk_level": "high" if misinformation_risk > 0.6 else 
                         "medium" if misinformation_risk > 0.3 else "low"
        }
    
    def _evaluate_sensationalism(self, content: str) -> Dict[str, Any]:
        """センセーショナリズム評価"""
        sensationalism_score = 0.0
        
        # 過度な強調
        for pattern in self.reliability_penalties["sensationalism"]["excessive_emphasis"]:
            matches = re.findall(pattern, content)
            sensationalism_score += len(matches) * 0.2
        
        # クリックベイト表現
        clickbait_count = sum(
            1 for phrase in self.reliability_penalties["sensationalism"]["clickbait_phrases"]
            if phrase in content
        )
        sensationalism_score += clickbait_count * 0.15
        
        # 感情的言語
        emotional_count = sum(
            1 for phrase in self.reliability_penalties["sensationalism"]["emotional_language"]
            if phrase in content
        )
        sensationalism_score += emotional_count * 0.1
        
        return {
            "sensationalism_score": min(sensationalism_score, 1.0),
            "clickbait_indicators": clickbait_count,
            "emotional_language_count": emotional_count,
            "sensationalism_level": "high" if sensationalism_score > 0.6 else 
                                   "medium" if sensationalism_score > 0.3 else "low"
        }
    
    def _assess_content_bias(self, content: str) -> Dict[str, Any]:
        """コンテンツバイアス評価"""
        bias_score = 0.0
        bias_indicators = []
        
        # 極端な言語
        extreme_count = sum(
            1 for phrase in self.reliability_penalties["bias_indicators"]["extreme_language"]
            if phrase in content
        )
        bias_score += extreme_count * 0.2
        
        # 党派攻撃
        partisan_count = sum(
            1 for phrase in self.reliability_penalties["bias_indicators"]["partisan_attacks"]
            if phrase in content
        )
        bias_score += partisan_count * 0.3
        bias_indicators.extend(["partisan_attack"] * partisan_count)
        
        # 陰謀論用語
        conspiracy_count = sum(
            1 for phrase in self.reliability_penalties["bias_indicators"]["conspiracy_terms"]
            if phrase in content
        )
        bias_score += conspiracy_count * 0.25
        bias_indicators.extend(["conspiracy_theory"] * conspiracy_count)
        
        return {
            "bias_score": min(bias_score, 1.0),
            "bias_indicators": bias_indicators,
            "extreme_language_count": extreme_count,
            "partisan_attack_count": partisan_count,
            "conspiracy_indicator_count": conspiracy_count,
            "bias_level": "high" if bias_score > 0.6 else 
                         "medium" if bias_score > 0.3 else "low"
        }
    
    def _evaluate_content_structure(self, content: str) -> Dict[str, Any]:
        """コンテンツ構造評価"""
        structure_score = 0.5  # ベースライン
        
        # 文章長による基本評価
        length_factor = min(len(content) / 500, 1.0)
        structure_score *= (0.6 + 0.4 * length_factor)
        
        # 段落構造（改行の適切な使用）
        paragraph_count = content.count('\n\n') + 1
        if paragraph_count >= 3:
            structure_score += 0.1
        
        # 数字・データの使用
        numeric_pattern = r'\d+[%\.\d]*'
        numeric_matches = re.findall(numeric_pattern, content)
        structure_score += min(len(numeric_matches) * 0.02, 0.2)
        
        # 引用符の使用（直接引用）
        quote_count = content.count('「') + content.count('『')
        structure_score += min(quote_count * 0.03, 0.15)
        
        return {
            "structure_score": min(max(structure_score, 0.0), 1.0),
            "paragraph_count": paragraph_count,
            "numeric_data_count": len(numeric_matches),
            "quote_count": quote_count,
            "content_length": len(content)
        }
    
    def _analyze_fact_check_indicators(self, content: str) -> Dict[str, Any]:
        """ファクトチェック指標分析"""
        verification_indicators = []
        correction_indicators = []
        uncertainty_indicators = []
        
        # 検証関連
        for indicator in self.fact_check_indicators["verification_sources"]:
            if indicator in content:
                verification_indicators.append(indicator)
        
        # 訂正関連
        for indicator in self.fact_check_indicators["correction_indicators"]:
            if indicator in content:
                correction_indicators.append(indicator)
        
        # 不確実性関連
        for indicator in self.fact_check_indicators["uncertainty_markers"]:
            if indicator in content:
                uncertainty_indicators.append(indicator)
        
        # ファクトチェックスコア
        fact_check_score = (
            len(verification_indicators) * 0.3 -
            len(correction_indicators) * 0.2 -
            len(uncertainty_indicators) * 0.1
        )
        
        return {
            "fact_check_score": max(fact_check_score, -0.5),
            "verification_indicators": verification_indicators,
            "correction_indicators": correction_indicators,
            "uncertainty_indicators": uncertainty_indicators,
            "has_fact_checking": len(verification_indicators) > 0
        }
    
    def _llm_reliability_assessment(self, content: str) -> Dict[str, Any]:
        """LLMによる信頼性評価"""
        try:
            reliability_prompt = f"""
以下のコンテンツの信頼性を評価してください：

【コンテンツ】
{content[:400]}...

【評価項目】
1. 事実性（0.0-1.0）
2. 客観性（0.0-1.0）
3. 情報源の明確性（0.0-1.0）
4. 全体的信頼性（0.0-1.0）

JSON形式で回答してください。
"""
            
            llm_response = self.llm_service.get_llm_response(reliability_prompt)
            
            try:
                llm_result = json.loads(llm_response)
            except:
                llm_result = {
                    "factuality": 0.5,
                    "objectivity": 0.5,
                    "source_clarity": 0.5,
                    "overall_reliability": 0.5
                }
            
            return {
                "llm_factuality": llm_result.get("factuality", 0.5),
                "llm_objectivity": llm_result.get("objectivity", 0.5),
                "llm_source_clarity": llm_result.get("source_clarity", 0.5),
                "llm_overall_reliability": llm_result.get("overall_reliability", 0.5),
                "llm_assessment_confidence": 0.7
            }
            
        except Exception as e:
            logger.warning(f"LLM信頼性評価エラー: {str(e)}")
            return {
                "llm_factuality": 0.5,
                "llm_objectivity": 0.5,
                "llm_source_clarity": 0.5,
                "llm_overall_reliability": 0.5,
                "llm_assessment_confidence": 0.0
            }
    
    def _evaluate_source_consistency(self, content: str, source_info: Optional[Dict]) -> Dict[str, Any]:
        """ソース情報との整合性評価"""
        if not source_info:
            return {"consistency_score": 0.5, "notes": "ソース情報なし"}
        
        consistency_score = 0.5
        
        # ソースの信頼性レベルとコンテンツの整合性
        source_reliability = source_info.get("final_reliability_score", 0.5)
        source_category = source_info.get("source_category", "unknown")
        
        # 政府ソースなのに感情的な内容 → 整合性低下
        if source_category == "government" and "!" in content:
            consistency_score -= 0.1
        
        # SNSソースなのに公式発表的な内容 → 整合性低下
        if source_category == "social_media" and any(word in content for word in ["発表", "公式", "正式"]):
            consistency_score -= 0.1
        
        # 高信頼性ソースは基本的に整合性が高い
        if source_reliability > 0.8:
            consistency_score += 0.2
        
        return {
            "consistency_score": min(max(consistency_score, 0.0), 1.0),
            "source_reliability": source_reliability,
            "source_category": source_category
        }
    
    def _calculate_overall_content_reliability(self, factual_quality: Dict, misinformation_risk: Dict,
                                             sensationalism_score: Dict, bias_assessment: Dict,
                                             structural_quality: Dict, llm_reliability: Dict,
                                             source_consistency: Dict) -> float:
        """総合コンテンツ信頼性計算"""
        # 重み付き平均
        reliability_score = (
            factual_quality["factual_score"] * 0.25 +
            (1.0 - misinformation_risk["misinformation_risk_score"]) * 0.2 +
            (1.0 - sensationalism_score["sensationalism_score"]) * 0.15 +
            (1.0 - bias_assessment["bias_score"]) * 0.15 +
            structural_quality["structure_score"] * 0.1 +
            llm_reliability["llm_overall_reliability"] * 0.1 +
            source_consistency["consistency_score"] * 0.05
        )
        
        return min(max(reliability_score, 0.0), 1.0)
    
    def _categorize_reliability_level(self, score: float) -> str:
        """信頼性レベル分類"""
        if score >= 0.8:
            return "very_high"
        elif score >= 0.65:
            return "high"
        elif score >= 0.5:
            return "medium"
        elif score >= 0.35:
            return "low"
        else:
            return "very_low"
    
    def _assign_reliability_grade(self, score: float) -> str:
        """信頼性グレード付与"""
        if score >= 0.9:
            return "A+"
        elif score >= 0.8:
            return "A"
        elif score >= 0.7:
            return "B+"
        elif score >= 0.6:
            return "B"
        elif score >= 0.5:
            return "C"
        elif score >= 0.4:
            return "D"
        else:
            return "F"
    
    def _calculate_content_similarity(self, contents1: List[str], contents2: List[str]) -> float:
        """コンテンツ類似性計算"""
        if not contents1 or not contents2:
            return 0.0
        
        # 簡易的な類似性計算（キーワード重複度）
        all_words1 = set()
        all_words2 = set()
        
        for content in contents1:
            words = content.split()
            all_words1.update(words)
        
        for content in contents2:
            words = content.split()
            all_words2.update(words)
        
        if not all_words1 or not all_words2:
            return 0.0
        
        intersection = len(all_words1 & all_words2)
        union = len(all_words1 | all_words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_consistency_scores(self, source_evaluations: Dict, content_similarities: Dict) -> Dict[str, Any]:
        """一貫性スコア計算"""
        if not source_evaluations:
            return {"overall_consistency": 0.0}
        
        # 信頼性の分散
        reliabilities = [eval_data["source_reliability"] for eval_data in source_evaluations.values()]
        reliability_variance = self._calculate_variance(reliabilities)
        
        # 類似性の平均
        similarities = list(content_similarities.values()) if content_similarities else [0.0]
        avg_similarity = sum(similarities) / len(similarities)
        
        # 全体一貫性
        overall_consistency = (
            (1.0 - reliability_variance) * 0.6 +
            avg_similarity * 0.4
        )
        
        return {
            "overall_consistency": overall_consistency,
            "reliability_variance": reliability_variance,
            "average_content_similarity": avg_similarity,
            "source_count": len(source_evaluations)
        }
    
    def _detect_reliability_outliers(self, source_evaluations: Dict) -> List[Dict]:
        """信頼性外れ値検出"""
        if len(source_evaluations) < 3:
            return []
        
        reliabilities = [(source, data["source_reliability"]) 
                        for source, data in source_evaluations.items()]
        
        # 平均と標準偏差
        scores = [score for _, score in reliabilities]
        mean_score = sum(scores) / len(scores)
        std_dev = math.sqrt(sum((score - mean_score) ** 2 for score in scores) / len(scores))
        
        outliers = []
        for source, score in reliabilities:
            z_score = abs(score - mean_score) / max(std_dev, 0.1)
            if z_score > 2.0:  # 2σ以上の外れ値
                outliers.append({
                    "source": source,
                    "reliability_score": score,
                    "z_score": z_score,
                    "deviation_type": "unusually_high" if score > mean_score else "unusually_low"
                })
        
        return outliers
    
    def _calculate_variance(self, values: List[float]) -> float:
        """分散計算"""
        if len(values) < 2:
            return 0.0
        
        mean_val = sum(values) / len(values)
        variance = sum((val - mean_val) ** 2 for val in values) / len(values)
        return variance
    
    def _calculate_trend(self, values: List[float]) -> str:
        """トレンド計算"""
        if len(values) < 2:
            return "insufficient_data"
        
        # 線形回帰の傾き
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        
        numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return "stable"
        
        slope = numerator / denominator
        
        if slope > 0.02:
            return "improving"
        elif slope < -0.02:
            return "declining"
        else:
            return "stable"
    
    def _detect_reliability_anomalies(self, timeline_data: List[Dict]) -> List[Dict]:
        """信頼性異常期間検出"""
        anomalies = []
        
        if len(timeline_data) < 5:
            return anomalies
        
        scores = [item.get("reliability_score", 0.5) for item in timeline_data]
        mean_score = sum(scores) / len(scores)
        std_dev = math.sqrt(sum((score - mean_score) ** 2 for score in scores) / len(scores))
        
        for i, item in enumerate(timeline_data):
            score = item.get("reliability_score", 0.5)
            if abs(score - mean_score) > 2 * std_dev:
                anomalies.append({
                    "timestamp": item.get("timestamp"),
                    "reliability_score": score,
                    "deviation": abs(score - mean_score),
                    "anomaly_type": "spike" if score > mean_score else "drop"
                })
        
        return anomalies
    
    def _analyze_reliability_trends(self, timeline_data: List[Dict]) -> Dict[str, Any]:
        """信頼性トレンド分析"""
        if len(timeline_data) < 3:
            return {"trend": "insufficient_data"}
        
        scores = [item.get("reliability_score", 0.5) for item in timeline_data]
        
        # 短期トレンド（最新5件）
        recent_scores = scores[-5:]
        recent_trend = self._calculate_trend(recent_scores)
        
        # 長期トレンド（全期間）
        long_term_trend = self._calculate_trend(scores)
        
        # 変動性
        volatility = self._calculate_variance(scores)
        
        return {
            "recent_trend": recent_trend,
            "long_term_trend": long_term_trend,
            "volatility": volatility,
            "trend_consistency": "consistent" if recent_trend == long_term_trend else "inconsistent"
        }
    
    def _get_fallback_source_evaluation(self) -> Dict[str, Any]:
        """フォールバックソース評価結果"""
        return {
            "source_category": "unknown",
            "final_reliability_score": 0.5,
            "reliability_level": "medium",
            "error": "評価処理中にエラーが発生しました"
        }
    
    def _get_fallback_content_evaluation(self) -> Dict[str, Any]:
        """フォールバックコンテンツ評価結果"""
        return {
            "overall_reliability_score": 0.5,
            "reliability_grade": "C",
            "error": "評価処理中にエラーが発生しました"
        }
    
    def test_reliability_scoring(self) -> bool:
        """信頼性評価機能テスト"""
        try:
            test_url = "https://www.kantei.go.jp/jp/news/"
            test_content = "政府は本日、経済対策について正式に発表しました。"
            
            source_result = self.evaluate_source_reliability(test_url)
            content_result = self.evaluate_content_reliability(test_content)
            
            return (source_result.get("final_reliability_score", 0) > 0 and
                   content_result.get("overall_reliability_score", 0) > 0)
        except Exception as e:
            logger.error(f"信頼性評価テスト失敗: {str(e)}")
            return False