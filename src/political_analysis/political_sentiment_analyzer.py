"""
政治感情分析エンジン
政治コンテンツの感情・論調・バイアスを分析し、政治予測に活用
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import re
import json
from collections import defaultdict, Counter
import math

from ..political_llm.political_service import PoliticalLLMService
from ..utils.config import ConfigManager
from ..utils.exceptions import AnalysisError

logger = logging.getLogger(__name__)


class PoliticalSentimentAnalyzer:
    """政治感情分析エンジンクラス"""
    
    def __init__(self, config_manager: ConfigManager, llm_service: PoliticalLLMService):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
            llm_service: 政治LLMサービスインスタンス
        """
        self.config_manager = config_manager
        self.llm_service = llm_service
        
        # 政治感情分析用辞書
        self.political_sentiment_dict = {
            "positive": {
                # 支持・賛成
                "support": ["支持", "賛成", "評価", "称賛", "好感", "信頼", "期待"],
                "achievement": ["成功", "成果", "実績", "効果", "前進", "改善", "向上"],
                "stability": ["安定", "堅実", "確実", "順調", "着実", "安心"],
                "leadership": ["指導力", "決断力", "責任感", "統率力", "リーダーシップ"]
            },
            "negative": {
                # 批判・反対
                "criticism": ["批判", "反対", "非難", "攻撃", "糾弾", "追及"],
                "failure": ["失敗", "失策", "ミス", "問題", "課題", "欠陥", "不備"],
                "scandal": ["疑惑", "スキャンダル", "不正", "汚職", "不祥事", "醜聞"],
                "instability": ["混乱", "動揺", "不安定", "危機", "破綻", "破たん"]
            },
            "neutral": {
                # 中立・事実報道
                "factual": ["発表", "報告", "会見", "説明", "決定", "検討", "協議"],
                "procedural": ["審議", "採決", "提出", "可決", "否決", "継続"],
                "analytical": ["分析", "調査", "検証", "確認", "比較", "評価"]
            }
        }
        
        # 政治バイアス検出キーワード
        self.bias_keywords = {
            "right_wing": {
                "strong": ["保守", "右派", "国家主義", "愛国", "伝統", "秩序"],
                "moderate": ["安定", "実績", "責任", "信頼", "経験"]
            },
            "left_wing": {
                "strong": ["革新", "左派", "平和", "人権", "平等", "改革"],
                "moderate": ["変化", "新しい", "市民", "grassroots", "多様性"]
            },
            "populist": {
                "keywords": ["庶民", "一般市民", "既得権益", "エリート", "官僚", "特権"]
            }
        }
        
        # 政治分野別感情重み
        self.topic_sentiment_weights = {
            "内閣支持率": {"reliability": 0.9, "volatility": 0.7},
            "経済政策": {"reliability": 0.8, "volatility": 0.5},
            "外交・安保": {"reliability": 0.85, "volatility": 0.6},
            "社会保障": {"reliability": 0.75, "volatility": 0.4},
            "選挙": {"reliability": 0.9, "volatility": 0.8},
            "政治スキャンダル": {"reliability": 0.7, "volatility": 0.9}
        }
        
        logger.info("政治感情分析エンジンを初期化")
    
    def analyze_political_sentiment(self, 
                                  content: str, 
                                  source_type: str = "news",
                                  political_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        政治コンテンツの包括的感情分析
        
        Args:
            content: 分析対象コンテンツ
            source_type: ソースタイプ（news, social, official, statement）
            political_context: 政治的文脈情報
            
        Returns:
            感情分析結果辞書
        """
        try:
            # 基本感情分析
            basic_sentiment = self._analyze_basic_sentiment(content)
            
            # 政治的バイアス分析
            political_bias = self._analyze_political_bias(content)
            
            # 感情の強度分析
            emotion_intensity = self._analyze_emotion_intensity(content)
            
            # 政治トピック別感情
            topic_sentiment = self._analyze_topic_sentiment(content, political_context)
            
            # LLMによる高度な感情分析
            llm_sentiment = self._llm_sentiment_analysis(content, source_type)
            
            # 信頼性スコア計算
            credibility_score = self._calculate_credibility_score(
                content, source_type, basic_sentiment
            )
            
            # 総合感情スコア計算
            final_sentiment_score = self._calculate_final_sentiment_score(
                basic_sentiment, llm_sentiment, emotion_intensity, source_type
            )
            
            analysis_result = {
                "content_preview": content[:100] + "..." if len(content) > 100 else content,
                "source_type": source_type,
                "basic_sentiment": basic_sentiment,
                "political_bias": political_bias,
                "emotion_intensity": emotion_intensity,
                "topic_sentiment": topic_sentiment,
                "llm_sentiment": llm_sentiment,
                "credibility_score": credibility_score,
                "final_sentiment_score": final_sentiment_score,
                "analysis_timestamp": datetime.now().isoformat(),
                "confidence_level": self._calculate_confidence_level(basic_sentiment, llm_sentiment)
            }
            
            logger.info(f"政治感情分析完了: スコア={final_sentiment_score:.2f}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"政治感情分析エラー: {str(e)}")
            return self._get_fallback_sentiment()
    
    def analyze_sentiment_trend(self, 
                              contents: List[Dict[str, Any]], 
                              time_window_hours: int = 24) -> Dict[str, Any]:
        """
        感情トレンド分析
        
        Args:
            contents: 分析対象コンテンツリスト
            time_window_hours: 分析時間窓（時間）
            
        Returns:
            感情トレンド分析結果
        """
        try:
            trend_data = []
            sentiment_timeline = []
            
            # 時系列での感情変化を分析
            for content_data in contents:
                content = content_data.get("content", content_data.get("title", ""))
                timestamp = content_data.get("timestamp", datetime.now().isoformat())
                source = content_data.get("source", "unknown")
                
                sentiment_result = self.analyze_political_sentiment(
                    content, 
                    source_type=self._classify_source_type(source)
                )
                
                sentiment_timeline.append({
                    "timestamp": timestamp,
                    "sentiment_score": sentiment_result["final_sentiment_score"],
                    "bias_score": sentiment_result["political_bias"]["overall_bias"],
                    "credibility": sentiment_result["credibility_score"],
                    "source": source
                })
            
            # トレンド統計計算
            if sentiment_timeline:
                sentiment_scores = [item["sentiment_score"] for item in sentiment_timeline]
                bias_scores = [item["bias_score"] for item in sentiment_timeline]
                
                trend_stats = {
                    "average_sentiment": sum(sentiment_scores) / len(sentiment_scores),
                    "sentiment_volatility": self._calculate_volatility(sentiment_scores),
                    "average_bias": sum(bias_scores) / len(bias_scores),
                    "trend_direction": self._calculate_trend_direction(sentiment_scores),
                    "sample_size": len(sentiment_timeline),
                    "time_span_hours": time_window_hours,
                    "confidence_score": min(len(sentiment_timeline) / 20, 1.0)
                }
                
                # 感情変化ポイント検出
                change_points = self._detect_sentiment_change_points(sentiment_timeline)
                
                trend_analysis = {
                    "timeline": sentiment_timeline,
                    "statistics": trend_stats,
                    "change_points": change_points,
                    "analysis_timestamp": datetime.now().isoformat()
                }
                
                logger.info(f"感情トレンド分析完了: 平均感情={trend_stats['average_sentiment']:.2f}")
                return trend_analysis
            
            return {"error": "分析データが不足しています"}
            
        except Exception as e:
            logger.error(f"感情トレンド分析エラー: {str(e)}")
            return {"error": str(e)}
    
    def compare_source_sentiment(self, 
                               content_by_source: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        ソース別感情比較分析
        
        Args:
            content_by_source: ソース別コンテンツ辞書
            
        Returns:
            ソース別感情比較結果
        """
        try:
            source_analysis = {}
            
            for source, contents in content_by_source.items():
                source_sentiments = []
                source_biases = []
                source_credibility = []
                
                for content in contents:
                    sentiment_result = self.analyze_political_sentiment(
                        content, 
                        source_type=self._classify_source_type(source)
                    )
                    
                    source_sentiments.append(sentiment_result["final_sentiment_score"])
                    source_biases.append(sentiment_result["political_bias"]["overall_bias"])
                    source_credibility.append(sentiment_result["credibility_score"])
                
                if source_sentiments:
                    source_analysis[source] = {
                        "average_sentiment": sum(source_sentiments) / len(source_sentiments),
                        "sentiment_range": max(source_sentiments) - min(source_sentiments),
                        "average_bias": sum(source_biases) / len(source_biases),
                        "average_credibility": sum(source_credibility) / len(source_credibility),
                        "sample_count": len(source_sentiments),
                        "sentiment_consistency": 1.0 - self._calculate_volatility(source_sentiments)
                    }
            
            # ソース間の相関分析
            correlation_analysis = self._calculate_source_correlations(source_analysis)
            
            comparison_result = {
                "source_profiles": source_analysis,
                "correlations": correlation_analysis,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"ソース別感情比較完了: {len(source_analysis)}ソース")
            return comparison_result
            
        except Exception as e:
            logger.error(f"ソース別感情比較エラー: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_basic_sentiment(self, content: str) -> Dict[str, Any]:
        """基本感情分析"""
        sentiment_scores = {"positive": 0, "negative": 0, "neutral": 0}
        detected_keywords = {"positive": [], "negative": [], "neutral": []}
        
        content_lower = content.lower()
        
        for sentiment_type, categories in self.political_sentiment_dict.items():
            for category, keywords in categories.items():
                for keyword in keywords:
                    if keyword in content:
                        sentiment_scores[sentiment_type] += 1
                        detected_keywords[sentiment_type].append(keyword)
        
        # 正規化
        total_score = sum(sentiment_scores.values())
        if total_score > 0:
            for sentiment in sentiment_scores:
                sentiment_scores[sentiment] /= total_score
        else:
            sentiment_scores["neutral"] = 1.0
        
        # 最終スコア（-1.0 to 1.0）
        final_score = sentiment_scores["positive"] - sentiment_scores["negative"]
        
        return {
            "scores": sentiment_scores,
            "detected_keywords": detected_keywords,
            "final_score": final_score,
            "dominant_sentiment": max(sentiment_scores, key=sentiment_scores.get)
        }
    
    def _analyze_political_bias(self, content: str) -> Dict[str, Any]:
        """政治的バイアス分析"""
        bias_scores = {"right_wing": 0, "left_wing": 0, "populist": 0}
        detected_indicators = {"right_wing": [], "left_wing": [], "populist": []}
        
        content_lower = content.lower()
        
        # 右派バイアス検出
        for strength, keywords in self.bias_keywords["right_wing"].items():
            weight = 2.0 if strength == "strong" else 1.0
            for keyword in keywords:
                if keyword in content:
                    bias_scores["right_wing"] += weight
                    detected_indicators["right_wing"].append(keyword)
        
        # 左派バイアス検出
        for strength, keywords in self.bias_keywords["left_wing"].items():
            weight = 2.0 if strength == "strong" else 1.0
            for keyword in keywords:
                if keyword in content:
                    bias_scores["left_wing"] += weight
                    detected_indicators["left_wing"].append(keyword)
        
        # ポピュリストバイアス検出
        for keyword in self.bias_keywords["populist"]["keywords"]:
            if keyword in content:
                bias_scores["populist"] += 1
                detected_indicators["populist"].append(keyword)
        
        # 全体的なバイアススコア計算（-1.0 to 1.0）
        overall_bias = 0.0
        if bias_scores["right_wing"] > 0 or bias_scores["left_wing"] > 0:
            total_partisan = bias_scores["right_wing"] + bias_scores["left_wing"]
            overall_bias = (bias_scores["right_wing"] - bias_scores["left_wing"]) / max(total_partisan, 1)
        
        return {
            "bias_scores": bias_scores,
            "detected_indicators": detected_indicators,
            "overall_bias": overall_bias,
            "bias_strength": max(bias_scores.values()),
            "dominant_bias": max(bias_scores, key=bias_scores.get) if max(bias_scores.values()) > 0 else "neutral"
        }
    
    def _analyze_emotion_intensity(self, content: str) -> Dict[str, Any]:
        """感情強度分析"""
        # 感情強化要素
        intensifiers = ["非常に", "とても", "極めて", "大変", "かなり", "相当", "著しく"]
        emphasis_patterns = [r"！+", r"\!\!+", r"？+", r"\?\?+", r"。。+"]
        
        # 基本強度スコア
        intensity_score = 0.5  # ベースライン
        
        # 強化語検出
        for intensifier in intensifiers:
            intensity_score += content.count(intensifier) * 0.1
        
        # 強調記号検出
        for pattern in emphasis_patterns:
            matches = re.findall(pattern, content)
            intensity_score += len(matches) * 0.15
        
        # 大文字の使用（英語部分）
        caps_ratio = sum(1 for c in content if c.isupper()) / max(len(content), 1)
        intensity_score += caps_ratio * 0.2
        
        # 文章の長さによる調整
        length_factor = min(len(content) / 500, 1.0)  # 長い文章ほど強度が増す
        intensity_score *= (0.7 + 0.3 * length_factor)
        
        # 正規化（0.0 to 1.0）
        intensity_score = min(max(intensity_score, 0.0), 1.0)
        
        return {
            "intensity_score": intensity_score,
            "intensity_level": self._categorize_intensity(intensity_score)
        }
    
    def _analyze_topic_sentiment(self, content: str, political_context: Optional[Dict]) -> Dict[str, Any]:
        """政治トピック別感情分析"""
        topic_sentiments = {}
        
        if not political_context:
            political_context = {}
        
        # 主要政治トピックを検出
        detected_topics = []
        for topic in self.topic_sentiment_weights.keys():
            if any(keyword in content for keyword in topic.split()):
                detected_topics.append(topic)
        
        # 各トピックに対する感情を分析
        for topic in detected_topics:
            topic_weight = self.topic_sentiment_weights[topic]
            
            # トピック関連キーワード周辺の感情を重点的に分析
            topic_sentiment = self._extract_topic_specific_sentiment(content, topic)
            
            topic_sentiments[topic] = {
                "sentiment_score": topic_sentiment,
                "reliability": topic_weight["reliability"],
                "volatility": topic_weight["volatility"]
            }
        
        return {
            "detected_topics": detected_topics,
            "topic_sentiments": topic_sentiments,
            "primary_topic": detected_topics[0] if detected_topics else None
        }
    
    def _llm_sentiment_analysis(self, content: str, source_type: str) -> Dict[str, Any]:
        """LLMによる高度な感情分析"""
        try:
            # LLMプロンプト構築
            sentiment_prompt = f"""
以下の政治関連コンテンツの感情・論調を分析してください：

【コンテンツ】
{content[:500]}...

【分析項目】
1. 感情スコア（-1.0 to 1.0）
2. 論調の特徴
3. 政治的立場の推定
4. 信頼性の評価

JSON形式で回答してください。
"""
            
            # LLMに分析依頼
            llm_response = self.llm_service.get_llm_response(sentiment_prompt)
            
            # レスポンスをパース
            try:
                llm_result = json.loads(llm_response)
            except:
                # JSONパースに失敗した場合のフォールバック
                llm_result = {
                    "sentiment_score": 0.0,
                    "tone": "neutral",
                    "political_stance": "unknown",
                    "credibility": 0.5
                }
            
            return {
                "llm_sentiment_score": llm_result.get("sentiment_score", 0.0),
                "llm_tone": llm_result.get("tone", "neutral"),
                "llm_political_stance": llm_result.get("political_stance", "unknown"),
                "llm_credibility": llm_result.get("credibility", 0.5),
                "llm_confidence": 0.8  # LLM分析の信頼度
            }
            
        except Exception as e:
            logger.warning(f"LLM感情分析エラー: {str(e)}")
            return {
                "llm_sentiment_score": 0.0,
                "llm_tone": "neutral",
                "llm_political_stance": "unknown",
                "llm_credibility": 0.5,
                "llm_confidence": 0.0
            }
    
    def _calculate_credibility_score(self, content: str, source_type: str, basic_sentiment: Dict) -> float:
        """信頼性スコア計算"""
        credibility = 0.5  # ベースライン
        
        # ソースタイプによる基本信頼性
        source_credibility = {
            "official": 0.9,
            "news": 0.8,
            "statement": 0.7,
            "social": 0.4,
            "unknown": 0.5
        }
        credibility = source_credibility.get(source_type, 0.5)
        
        # 感情の極端さによる減点
        sentiment_extremity = abs(basic_sentiment["final_score"])
        if sentiment_extremity > 0.8:
            credibility *= 0.8
        
        # 内容の長さによる調整
        length_factor = min(len(content) / 200, 1.0)
        credibility *= (0.7 + 0.3 * length_factor)
        
        return min(max(credibility, 0.0), 1.0)
    
    def _calculate_final_sentiment_score(self, basic_sentiment: Dict, llm_sentiment: Dict, 
                                       emotion_intensity: Dict, source_type: str) -> float:
        """最終感情スコア計算"""
        # 重み付け
        basic_weight = 0.4
        llm_weight = 0.5 if llm_sentiment["llm_confidence"] > 0.5 else 0.2
        intensity_weight = 0.1
        
        # 正規化
        total_weight = basic_weight + llm_weight + intensity_weight
        basic_weight /= total_weight
        llm_weight /= total_weight
        intensity_weight /= total_weight
        
        # 最終スコア計算
        final_score = (
            basic_sentiment["final_score"] * basic_weight +
            llm_sentiment["llm_sentiment_score"] * llm_weight +
            (emotion_intensity["intensity_score"] - 0.5) * 2 * intensity_weight
        )
        
        # ソースタイプによる調整
        if source_type == "social":
            final_score *= 0.8  # SNSは感情が極端になりがちなので減衰
        
        return min(max(final_score, -1.0), 1.0)
    
    def _calculate_confidence_level(self, basic_sentiment: Dict, llm_sentiment: Dict) -> float:
        """分析信頼度計算"""
        basic_confidence = 0.8 if basic_sentiment["final_score"] != 0 else 0.5
        llm_confidence = llm_sentiment["llm_confidence"]
        
        # 両者の一致度
        score_diff = abs(basic_sentiment["final_score"] - llm_sentiment["llm_sentiment_score"])
        agreement_factor = 1.0 - min(score_diff, 1.0)
        
        return (basic_confidence + llm_confidence) * 0.5 * agreement_factor
    
    def _calculate_volatility(self, scores: List[float]) -> float:
        """変動性計算"""
        if len(scores) < 2:
            return 0.0
        
        mean_score = sum(scores) / len(scores)
        variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
        return math.sqrt(variance)
    
    def _calculate_trend_direction(self, scores: List[float]) -> str:
        """トレンド方向計算"""
        if len(scores) < 2:
            return "insufficient_data"
        
        # 線形回帰の傾き計算
        n = len(scores)
        x_mean = (n - 1) / 2
        y_mean = sum(scores) / n
        
        numerator = sum((i - x_mean) * (scores[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return "stable"
        
        slope = numerator / denominator
        
        if slope > 0.05:
            return "improving"
        elif slope < -0.05:
            return "declining"
        else:
            return "stable"
    
    def _detect_sentiment_change_points(self, timeline: List[Dict]) -> List[Dict]:
        """感情変化ポイント検出"""
        change_points = []
        
        if len(timeline) < 3:
            return change_points
        
        for i in range(1, len(timeline) - 1):
            prev_sentiment = timeline[i-1]["sentiment_score"]
            curr_sentiment = timeline[i]["sentiment_score"]
            next_sentiment = timeline[i+1]["sentiment_score"]
            
            # 急激な変化を検出
            change_magnitude = abs(curr_sentiment - prev_sentiment)
            if change_magnitude > 0.3:
                change_points.append({
                    "timestamp": timeline[i]["timestamp"],
                    "change_magnitude": change_magnitude,
                    "direction": "positive" if curr_sentiment > prev_sentiment else "negative",
                    "context": f"感情スコア: {prev_sentiment:.2f} → {curr_sentiment:.2f}"
                })
        
        return change_points
    
    def _calculate_source_correlations(self, source_analysis: Dict) -> Dict[str, Any]:
        """ソース間相関計算"""
        sources = list(source_analysis.keys())
        correlations = {}
        
        if len(sources) < 2:
            return correlations
        
        for i, source1 in enumerate(sources):
            for source2 in sources[i+1:]:
                sentiment1 = source_analysis[source1]["average_sentiment"]
                sentiment2 = source_analysis[source2]["average_sentiment"]
                bias1 = source_analysis[source1]["average_bias"]
                bias2 = source_analysis[source2]["average_bias"]
                
                # 簡易相関計算
                sentiment_similarity = 1.0 - abs(sentiment1 - sentiment2) / 2.0
                bias_similarity = 1.0 - abs(bias1 - bias2) / 2.0
                
                correlations[f"{source1}-{source2}"] = {
                    "sentiment_similarity": sentiment_similarity,
                    "bias_similarity": bias_similarity,
                    "overall_similarity": (sentiment_similarity + bias_similarity) / 2
                }
        
        return correlations
    
    def _classify_source_type(self, source: str) -> str:
        """ソースタイプ分類"""
        source_lower = source.lower()
        
        if any(term in source_lower for term in ["go.jp", "kantei", "gov"]):
            return "official"
        elif any(term in source_lower for term in ["nhk", "asahi", "yomiuri", "mainichi"]):
            return "news"
        elif any(term in source_lower for term in ["twitter", "facebook", "social"]):
            return "social"
        elif any(term in source_lower for term in ["statement", "seimei", "danwa"]):
            return "statement"
        else:
            return "unknown"
    
    def _categorize_intensity(self, intensity_score: float) -> str:
        """感情強度カテゴリ化"""
        if intensity_score < 0.3:
            return "low"
        elif intensity_score < 0.7:
            return "medium"
        else:
            return "high"
    
    def _extract_topic_specific_sentiment(self, content: str, topic: str) -> float:
        """トピック特異的感情抽出"""
        # トピックキーワード周辺の感情を重点的に分析
        topic_keywords = topic.split()
        
        sentiment_score = 0.0
        keyword_count = 0
        
        for keyword in topic_keywords:
            keyword_index = content.find(keyword)
            if keyword_index != -1:
                # キーワード前後50文字の感情を分析
                context_start = max(0, keyword_index - 50)
                context_end = min(len(content), keyword_index + len(keyword) + 50)
                context = content[context_start:context_end]
                
                context_sentiment = self._analyze_basic_sentiment(context)
                sentiment_score += context_sentiment["final_score"]
                keyword_count += 1
        
        return sentiment_score / max(keyword_count, 1)
    
    def _get_fallback_sentiment(self) -> Dict[str, Any]:
        """フォールバック感情分析結果"""
        return {
            "basic_sentiment": {
                "scores": {"positive": 0.33, "negative": 0.33, "neutral": 0.34},
                "final_score": 0.0,
                "dominant_sentiment": "neutral"
            },
            "political_bias": {
                "overall_bias": 0.0,
                "dominant_bias": "neutral"
            },
            "emotion_intensity": {
                "intensity_score": 0.5,
                "intensity_level": "medium"
            },
            "final_sentiment_score": 0.0,
            "confidence_level": 0.3,
            "error": "分析処理中にエラーが発生しました"
        }
    
    def test_sentiment_analysis(self) -> bool:
        """感情分析機能テスト"""
        try:
            test_content = "岸田内閣の支持率が上昇し、経済政策に対する評価が高まっています。"
            result = self.analyze_political_sentiment(test_content)
            return "final_sentiment_score" in result
        except Exception as e:
            logger.error(f"感情分析テスト失敗: {str(e)}")
            return False