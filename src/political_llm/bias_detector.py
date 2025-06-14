"""
政治バイアス検知システム
政治的偏向・バイアスを検知して中立性を評価
"""
import logging
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class BiasType(Enum):
    """バイアスタイプ"""
    LEFT_WING = "left_wing"          # 左派偏向
    RIGHT_WING = "right_wing"        # 右派偏向
    PRO_GOVERNMENT = "pro_government" # 政府寄り
    ANTI_GOVERNMENT = "anti_government" # 反政府
    PARTISAN = "partisan"            # 党派的
    NEUTRAL = "neutral"              # 中立


@dataclass
class BiasAnalysis:
    """バイアス分析結果"""
    overall_score: float  # 全体バイアススコア (0.0-1.0, 0が中立)
    bias_type: BiasType
    confidence: float
    detected_phrases: List[str]
    explanation: str


class PoliticalBiasDetector:
    """政治バイアス検知クラス"""
    
    def __init__(self):
        """初期化"""
        self._load_bias_dictionaries()
        logger.info("政治バイアス検知システムを初期化")
    
    def _load_bias_dictionaries(self):
        """バイアス検知用辞書を読み込み"""
        
        # 左派的表現
        self.left_wing_phrases = {
            # 政府批判的表現
            "政府の失政", "政治の腐敗", "権力の暴走", "民意を無視",
            "弱者切り捨て", "格差拡大", "新自由主義の弊害", "庶民いじめ",
            "大企業優遇", "富裕層優遇", "労働者軽視", "社会保障削減",
            
            # 左派政党支持的表現
            "市民の声", "草の根民主主義", "反戦平和", "護憲",
            "人権重視", "多様性尊重", "環境保護", "脱原発",
            
            # 右派批判的表現
            "軍国主義", "戦争への道", "改憲阻止", "歴史修正主義"
        }
        
        # 右派的表現
        self.right_wing_phrases = {
            # 愛国的表現
            "日本の誇り", "国益重視", "愛国心", "伝統文化",
            "国家の威信", "領土主権", "拉致問題解決", "毅然とした外交",
            
            # 保守的価値観
            "家族の絆", "道徳教育", "規律重視", "秩序維持",
            "自助努力", "競争原理", "経済成長", "企業活動支援",
            
            # 左派批判的表現
            "左翼思想", "反日勢力", "偏向報道", "既得権益",
            "バラマキ政策", "ポピュリズム", "空想的平和主義"
        }
        
        # 政府寄り表現
        self.pro_government_phrases = {
            "政府の適切な判断", "政策の成果", "着実な成長", "安定した政権運営",
            "責任ある政治", "現実的な政策", "バランスの取れた", "慎重な検討",
            "総合的な判断", "国民の理解", "政府方針に沿った", "適切な対応"
        }
        
        # 反政府表現
        self.anti_government_phrases = {
            "政府の隠蔽", "説明責任を果たさない", "強行採決", "民意に反する",
            "密室政治", "利権政治", "官僚支配", "政治とカネ",
            "政府の失態", "政策の破綻", "責任逃れ", "問題の先送り"
        }
        
        # 党派的表現
        self.partisan_phrases = {
            # 特定政党への過度の賛美
            "素晴らしい政党", "唯一の選択肢", "完璧な政策", "間違いない判断",
            
            # 特定政党への過度の批判
            "最悪の政党", "売国政党", "無能な政治家", "税金泥棒",
            "国民の敵", "日本を破壊", "嘘つき政党"
        }
        
        # 中立的表現
        self.neutral_phrases = {
            "複数の意見", "様々な見方", "賛否両論", "課題も指摘",
            "一方で", "他方で", "検討が必要", "議論が分かれる",
            "慎重な判断", "総合的な検討", "客観的事実", "データに基づく"
        }
        
        # 感情的表現（バイアスの指標）
        self.emotional_phrases = {
            # 強い否定的感情
            "許せない", "けしからん", "とんでもない", "ふざけるな",
            "最悪", "最低", "呆れる", "激怒", "憤慨",
            
            # 強い肯定的感情
            "素晴らしい", "完璧", "最高", "感動", "大絶賛",
            "神対応", "英断", "名判断"
        }
    
    def detect_bias(self, text: str) -> float:
        """
        テキストの政治的バイアスを検知
        
        Args:
            text: 分析対象テキスト
            
        Returns:
            バイアススコア (0.0-1.0, 0が中立)
        """
        analysis = self.analyze_bias(text)
        return analysis.overall_score
    
    def analyze_bias(self, text: str) -> BiasAnalysis:
        """
        詳細なバイアス分析を実行
        
        Args:
            text: 分析対象テキスト
            
        Returns:
            詳細なバイアス分析結果
        """
        # 各種バイアス指標を計算
        left_score = self._calculate_phrase_score(text, self.left_wing_phrases)
        right_score = self._calculate_phrase_score(text, self.right_wing_phrases)
        pro_gov_score = self._calculate_phrase_score(text, self.pro_government_phrases)
        anti_gov_score = self._calculate_phrase_score(text, self.anti_government_phrases)
        partisan_score = self._calculate_phrase_score(text, self.partisan_phrases)
        neutral_score = self._calculate_phrase_score(text, self.neutral_phrases)
        emotional_score = self._calculate_phrase_score(text, self.emotional_phrases)
        
        # 検出されたフレーズを収集
        detected_phrases = []
        detected_phrases.extend(self._find_phrases(text, self.left_wing_phrases))
        detected_phrases.extend(self._find_phrases(text, self.right_wing_phrases))
        detected_phrases.extend(self._find_phrases(text, self.pro_government_phrases))
        detected_phrases.extend(self._find_phrases(text, self.anti_government_phrases))
        detected_phrases.extend(self._find_phrases(text, self.partisan_phrases))
        
        # 主要なバイアスタイプを判定
        bias_type, confidence = self._determine_bias_type(
            left_score, right_score, pro_gov_score, 
            anti_gov_score, partisan_score, neutral_score
        )
        
        # 全体的なバイアススコアを計算
        overall_score = self._calculate_overall_bias_score(
            left_score, right_score, pro_gov_score, 
            anti_gov_score, partisan_score, neutral_score, emotional_score
        )
        
        # 説明文を生成
        explanation = self._generate_explanation(
            bias_type, overall_score, detected_phrases
        )
        
        return BiasAnalysis(
            overall_score=overall_score,
            bias_type=bias_type,
            confidence=confidence,
            detected_phrases=detected_phrases,
            explanation=explanation
        )
    
    def _calculate_phrase_score(self, text: str, phrases: set) -> float:
        """指定されたフレーズセットのスコアを計算"""
        matches = 0
        total_length = 0
        
        for phrase in phrases:
            if phrase in text:
                matches += 1
                total_length += len(phrase)
        
        # テキスト長で正規化
        if len(text) == 0:
            return 0.0
        
        return min((matches * 10 + total_length) / len(text), 1.0)
    
    def _find_phrases(self, text: str, phrases: set) -> List[str]:
        """テキスト内で見つかったフレーズを返す"""
        found = []
        for phrase in phrases:
            if phrase in text:
                found.append(phrase)
        return found
    
    def _determine_bias_type(self, left_score: float, right_score: float, 
                           pro_gov_score: float, anti_gov_score: float,
                           partisan_score: float, neutral_score: float) -> Tuple[BiasType, float]:
        """主要なバイアスタイプと確信度を判定"""
        
        # スコアを辞書にまとめる
        scores = {
            BiasType.LEFT_WING: left_score,
            BiasType.RIGHT_WING: right_score,
            BiasType.PRO_GOVERNMENT: pro_gov_score,
            BiasType.ANTI_GOVERNMENT: anti_gov_score,
            BiasType.PARTISAN: partisan_score,
            BiasType.NEUTRAL: neutral_score
        }
        
        # 最高スコアのバイアスタイプを選択
        max_bias_type = max(scores, key=scores.get)
        max_score = scores[max_bias_type]
        
        # 確信度を計算（最高スコアと他のスコアの差）
        other_scores = [score for bias_type, score in scores.items() 
                       if bias_type != max_bias_type]
        
        if other_scores:
            second_max = max(other_scores)
            confidence = min(max_score - second_max + 0.5, 1.0)
        else:
            confidence = max_score
        
        # 中立判定の閾値
        if max_score < 0.1:
            return BiasType.NEUTRAL, confidence
        
        return max_bias_type, confidence
    
    def _calculate_overall_bias_score(self, left_score: float, right_score: float,
                                    pro_gov_score: float, anti_gov_score: float,
                                    partisan_score: float, neutral_score: float,
                                    emotional_score: float) -> float:
        """全体的なバイアススコアを計算"""
        
        # 各種バイアススコアの合計
        bias_sum = (left_score + right_score + pro_gov_score + 
                   anti_gov_score + partisan_score + emotional_score * 0.5)
        
        # 中立スコアで割り引き
        bias_penalty = max(0, bias_sum - neutral_score * 2)
        
        return min(bias_penalty, 1.0)
    
    def _generate_explanation(self, bias_type: BiasType, 
                            overall_score: float, 
                            detected_phrases: List[str]) -> str:
        """バイアス分析の説明文を生成"""
        
        if overall_score < 0.2:
            return "中立的で客観的な表現が多く、特定の政治的偏向は検出されませんでした。"
        
        bias_explanations = {
            BiasType.LEFT_WING: "左派的な政治観点や政府批判的な表現が検出されました。",
            BiasType.RIGHT_WING: "右派的・保守的な政治観点や愛国的表現が検出されました。",
            BiasType.PRO_GOVERNMENT: "政府寄りの表現や政策支持的な内容が検出されました。",
            BiasType.ANTI_GOVERNMENT: "反政府的な表現や政策批判的な内容が検出されました。",
            BiasType.PARTISAN: "特定政党への強い支持・批判など党派的な表現が検出されました。",
            BiasType.NEUTRAL: "比較的中立的な表現が多用されています。"
        }
        
        explanation = bias_explanations.get(bias_type, "政治的傾向を分析中です。")
        
        if detected_phrases:
            top_phrases = detected_phrases[:3]
            explanation += f" 検出された表現例: {', '.join(top_phrases)}"
        
        return explanation
    
    def check_source_bias(self, url: str) -> float:
        """
        情報源URLのバイアス傾向をチェック
        
        Args:
            url: チェック対象URL
            
        Returns:
            ソースバイアススコア (0.0-1.0)
        """
        # 信頼性の高い公式・主要メディア
        trusted_domains = {
            'kantei.go.jp': 0.0,      # 首相官邸
            'gov.go.jp': 0.0,         # 政府
            'soumu.go.jp': 0.0,       # 総務省
            'nhk.or.jp': 0.1,         # NHK
            'kyodo.co.jp': 0.1,       # 共同通信
            'jiji.com': 0.1,          # 時事通信
        }
        
        # やや偏向傾向のあるメディア
        biased_domains = {
            'sankei.com': 0.3,        # 産経（やや右派）
            'asahi.com': 0.3,         # 朝日（やや左派）
            'mainichi.jp': 0.2,       # 毎日
            'yomiuri.co.jp': 0.2,     # 読売
        }
        
        # 高い偏向性のあるメディア
        highly_biased_domains = {
            'blogos.com': 0.5,        # ブロゴス
            'yahoo.co.jp': 0.4,       # Yahoo!ニュース
        }
        
        for domain, bias_score in trusted_domains.items():
            if domain in url:
                return bias_score
                
        for domain, bias_score in biased_domains.items():
            if domain in url:
                return bias_score
                
        for domain, bias_score in highly_biased_domains.items():
            if domain in url:
                return bias_score
        
        # 不明なソースは中程度のバイアスとして扱う
        return 0.5