"""
政治エンティティ認識システム
政治家・政党・政策・地域などの政治関連エンティティを認識
"""
import logging
import re
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PoliticalEntity:
    """政治エンティティデータクラス"""
    text: str
    entity_type: str
    confidence: float
    start_pos: int
    end_pos: int


class PoliticalEntityRecognizer:
    """政治エンティティ認識クラス"""
    
    def __init__(self):
        """初期化"""
        self._load_political_dictionaries()
        logger.info("政治エンティティ認識システムを初期化")
    
    def _load_political_dictionaries(self):
        """政治関連辞書を読み込み"""
        
        # 政治家名辞書（現職・元職の主要政治家）
        self.politicians = {
            # 現職総理・元総理
            "岸田文雄", "菅義偉", "安倍晋三", "野田佳彦", "鳩山由紀夫", "麻生太郎",
            "福田康夫", "小泉純一郎", "森喜朗", "小渕恵三", "橋本龍太郎",
            
            # 現職閣僚
            "林芳正", "茂木敏充", "松野博一", "鈴木俊一", "萩生田光一", "西村康稔",
            "河野太郎", "加藤勝信", "野田聖子", "古川禎久", "金子恭之",
            
            # 野党主要政治家
            "泉健太", "志位和夫", "玉木雄一郎", "馬場伸幸", "福島みずほ", "山本太郎",
            "枝野幸男", "蓮舫", "辻元清美", "小沢一郎", "亀井静香",
            
            # 地方政治家
            "小池百合子", "吉村洋文", "河村たかし", "松井一郎"
        }
        
        # 政党名辞書
        self.parties = {
            # 主要政党
            "自由民主党", "自民党", "立憲民主党", "立憲", "公明党", "日本共産党", "共産党",
            "日本維新の会", "維新", "国民民主党", "国民", "れいわ新選組", "れいわ",
            "社会民主党", "社民党", "NHK党", "参政党",
            
            # 過去の政党
            "民主党", "民進党", "希望の党", "国民の生活が第一", "みんなの党",
            "日本のこころ", "次世代の党", "太陽の党"
        }
        
        # 政治役職辞書
        self.positions = {
            "内閣総理大臣", "総理大臣", "総理", "首相", "副総理", "官房長官",
            "外務大臣", "財務大臣", "法務大臣", "文部科学大臣", "厚生労働大臣",
            "農林水産大臣", "経済産業大臣", "国土交通大臣", "環境大臣", "防衛大臣",
            "内閣府特命担当大臣", "復興大臣", "国家公安委員長", "総務大臣",
            
            "衆議院議長", "参議院議長", "衆議院副議長", "参議院副議長",
            "自民党総裁", "幹事長", "政調会長", "国対委員長", "選対委員長"
        }
        
        # 政策・制度辞書
        self.policies = {
            "アベノミクス", "新しい資本主義", "成長と分配", "骨太の方針",
            "デジタル田園都市国家構想", "全世代型社会保障", "働き方改革",
            "地方創生", "1億総活躍", "女性活躍", "少子化対策", "子育て支援",
            "教育無償化", "消費税", "所得税", "法人税", "相続税", "固定資産税",
            "年金制度", "医療制度", "介護保険", "雇用保険", "労働法",
            "憲法改正", "集団的自衛権", "防衛力強化", "日米同盟", "自由貿易",
            "脱炭素", "カーボンニュートラル", "再生可能エネルギー", "原発政策"
        }
        
        # 選挙・政治制度辞書
        self.political_terms = {
            "衆議院選挙", "参議院選挙", "統一地方選挙", "都知事選", "市長選",
            "衆議院", "参議院", "国会", "内閣", "最高裁判所",
            "小選挙区", "比例代表", "参議院選挙区", "定数", "一票の格差",
            "解散", "総選挙", "補欠選挙", "政権交代", "連立政権", "野党",
            "与党", "第一党", "過半数", "三分の二", "絶対安定多数"
        }
        
        # 地域辞書
        self.regions = {
            "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
            "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
            "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
            "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
            "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
            "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
            "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県"
        }
    
    def extract_political_entities(self, text: str) -> List[str]:
        """
        テキストから政治エンティティを抽出
        
        Args:
            text: 分析対象テキスト
            
        Returns:
            抽出された政治エンティティのリスト
        """
        entities = []
        
        # 各カテゴリのエンティティを検索
        entities.extend(self._find_entities(text, self.politicians, "POLITICIAN"))
        entities.extend(self._find_entities(text, self.parties, "PARTY"))
        entities.extend(self._find_entities(text, self.positions, "POSITION"))
        entities.extend(self._find_entities(text, self.policies, "POLICY"))
        entities.extend(self._find_entities(text, self.political_terms, "POLITICAL_TERM"))
        entities.extend(self._find_entities(text, self.regions, "REGION"))
        
        # 重複を除去してソート
        unique_entities = list(set(entities))
        unique_entities.sort(key=len, reverse=True)  # 長い順でソート
        
        return unique_entities
    
    def extract_detailed_entities(self, text: str) -> List[PoliticalEntity]:
        """
        詳細な政治エンティティ情報を抽出
        
        Args:
            text: 分析対象テキスト
            
        Returns:
            詳細な政治エンティティ情報のリスト
        """
        detailed_entities = []
        
        # 各カテゴリの詳細エンティティを検索
        detailed_entities.extend(self._find_detailed_entities(text, self.politicians, "POLITICIAN"))
        detailed_entities.extend(self._find_detailed_entities(text, self.parties, "PARTY"))
        detailed_entities.extend(self._find_detailed_entities(text, self.positions, "POSITION"))
        detailed_entities.extend(self._find_detailed_entities(text, self.policies, "POLICY"))
        detailed_entities.extend(self._find_detailed_entities(text, self.political_terms, "POLITICAL_TERM"))
        detailed_entities.extend(self._find_detailed_entities(text, self.regions, "REGION"))
        
        # 重複を除去（位置が重複する場合は長い方を優先）
        return self._remove_overlapping_entities(detailed_entities)
    
    def _find_entities(self, text: str, entity_dict: Set[str], entity_type: str) -> List[str]:
        """指定されたカテゴリのエンティティを検索"""
        found_entities = []
        
        for entity in entity_dict:
            if entity in text:
                found_entities.append(entity)
        
        return found_entities
    
    def _find_detailed_entities(self, text: str, entity_dict: Set[str], entity_type: str) -> List[PoliticalEntity]:
        """詳細なエンティティ情報を検索"""
        detailed_entities = []
        
        for entity in entity_dict:
            start_pos = 0
            while True:
                pos = text.find(entity, start_pos)
                if pos == -1:
                    break
                
                detailed_entity = PoliticalEntity(
                    text=entity,
                    entity_type=entity_type,
                    confidence=1.0,  # 辞書マッチングなので確信度は1.0
                    start_pos=pos,
                    end_pos=pos + len(entity)
                )
                detailed_entities.append(detailed_entity)
                start_pos = pos + 1
        
        return detailed_entities
    
    def _remove_overlapping_entities(self, entities: List[PoliticalEntity]) -> List[PoliticalEntity]:
        """重複するエンティティを除去（長い方を優先）"""
        if not entities:
            return []
        
        # 開始位置でソート
        sorted_entities = sorted(entities, key=lambda x: (x.start_pos, -len(x.text)))
        result = []
        
        for entity in sorted_entities:
            # 既存のエンティティと重複しているかチェック
            overlaps = False
            for existing in result:
                if (entity.start_pos < existing.end_pos and 
                    entity.end_pos > existing.start_pos):
                    overlaps = True
                    break
            
            if not overlaps:
                result.append(entity)
        
        return result
    
    def get_entity_context(self, text: str, entity: str, context_length: int = 50) -> str:
        """
        エンティティの文脈を取得
        
        Args:
            text: 全体テキスト
            entity: エンティティ
            context_length: 前後の文脈長
            
        Returns:
            エンティティを含む文脈
        """
        pos = text.find(entity)
        if pos == -1:
            return ""
        
        start = max(0, pos - context_length)
        end = min(len(text), pos + len(entity) + context_length)
        
        return text[start:end]