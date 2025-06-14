# lain-politics API リファレンス

## 概要

このドキュメントは、lain-politicsシステムの各コンポーネントのAPI仕様と使用方法を詳述します。

## Core Components API

### 1. PoliticalLainApp

メインアプリケーションクラス。全機能への統一インターフェースを提供。

```python
from src.political_cli import PoliticalLainApp
from src.utils.config import ConfigManager

config = ConfigManager()
app = PoliticalLainApp(config, enable_color=True)
```

#### 1.1 感情分析

```python
def analyze_political_sentiment(
    content: str, 
    source_type: str = "news",
    verbose: bool = False
) -> Dict[str, Any]
```

**パラメータ**:
- `content`: 分析対象テキスト
- `source_type`: ソースタイプ (`news`, `social`, `official`, `statement`)
- `verbose`: 詳細表示フラグ

**戻り値**:
```python
{
    "final_sentiment_score": 0.25,        # -1.0 ～ 1.0
    "confidence_level": 0.78,             # 0.0 ～ 1.0
    "basic_sentiment": {
        "scores": {
            "positive": 0.6,
            "negative": 0.2, 
            "neutral": 0.2
        },
        "final_score": 0.4,
        "dominant_sentiment": "positive"
    },
    "political_bias": {
        "overall_bias": 0.1,               # -1.0(左派) ～ 1.0(右派)
        "dominant_bias": "neutral",
        "bias_scores": {
            "right_wing": 0.2,
            "left_wing": 0.1,
            "populist": 0.0
        }
    },
    "emotion_intensity": {
        "intensity_score": 0.6,
        "intensity_level": "medium"
    },
    "processing_time": 1.23
}
```

**使用例**:
```python
result = app.analyze_political_sentiment(
    "政府の新政策に対する評価が高まっています",
    source_type="news"
)
print(f"感情スコア: {result['final_sentiment_score']:.2f}")
```

#### 1.2 信頼性評価

```python
def evaluate_source_reliability(
    source_url: str,
    content: Optional[str] = None,
    verbose: bool = False
) -> Dict[str, Any]
```

**パラメータ**:
- `source_url`: 評価対象URL
- `content`: コンテンツテキスト（オプション）
- `verbose`: 詳細表示フラグ

**戻り値**:
```python
{
    "source_evaluation": {
        "final_reliability_score": 0.95,   # 0.0 ～ 1.0
        "reliability_level": "very_high",
        "source_category": "government",
        "domain": "kantei.go.jp",
        "source_characteristics": {
            "primary_category": "government",
            "editorial_stance": "official",
            "fact_checking_policy": "high_standard"
        }
    },
    "content_evaluation": {             # contentが提供された場合
        "overall_reliability_score": 0.87,
        "reliability_grade": "A",
        "factual_quality": {
            "factual_score": 0.9,
            "high_confidence_markers": 3,
            "positive_structure_indicators": 2
        },
        "misinformation_risk": {
            "misinformation_risk_score": 0.1,
            "risk_level": "low"
        },
        "bias_assessment": {
            "bias_score": 0.2,
            "bias_level": "low"
        }
    },
    "processing_time": 2.15
}
```

#### 1.3 支持率予測

```python
def predict_support_rating(
    current_data: Optional[Dict] = None,
    prediction_days: int = 30,
    verbose: bool = False
) -> Dict[str, Any]
```

**パラメータ**:
- `current_data`: 現在のデータ（未指定時は自動収集）
- `prediction_days`: 予測期間（日数）
- `verbose`: 詳細表示フラグ

**戻り値**:
```python
{
    "prediction_type": "support_rating",
    "current_support_rate": 0.45,
    "predicted_support_rate": 0.47,
    "prediction_change": 0.02,
    "prediction_horizon_days": 30,
    "impact_breakdown": {
        "sentiment_impact": 0.015,
        "media_impact": 0.008,
        "government_impact": 0.012,
        "social_impact": 0.003,
        "event_impact": -0.005,
        "total_impact": 0.033
    },
    "confidence_score": 0.73,
    "confidence_level": "high",
    "factors_summary": [
        "世論の好感度上昇",
        "政策実行力の評価"
    ],
    "processing_time": 8.45
}
```

#### 1.4 選挙予測

```python
def predict_election_outcome(
    current_data: Optional[Dict] = None,
    prediction_days: int = 90,
    verbose: bool = False
) -> Dict[str, Any]
```

**戻り値**:
```python
{
    "prediction_type": "election_outcome",
    "current_party_support": {
        "自由民主党": 0.35,
        "立憲民主党": 0.18,
        "日本維新の会": 0.12,
        "公明党": 0.08,
        "その他": 0.27
    },
    "predicted_party_support": {
        "自由民主党": 0.342,
        "立憲民主党": 0.191,
        "日本維新の会": 0.135,
        "公明党": 0.087,
        "その他": 0.245
    },
    "predicted_seat_distribution": {
        "自由民主党": 159,
        "立憲民主党": 89,
        "日本維新の会": 63,
        "公明党": 40,
        "その他": 114
    },
    "coalition_analysis": {
        "majority_threshold": 233,
        "coalition_scenarios": [
            {
                "coalition": ["自由民主党", "公明党"],
                "seats": 199,
                "probability": 0.8,
                "stability": "high"
            }
        ]
    },
    "confidence_score": 0.68,
    "processing_time": 12.8
}
```

#### 1.5 包括的分析

```python
def analyze_comprehensive_political_data(
    query: str,
    max_results: int = 20,
    verbose: bool = False
) -> Dict[str, Any]
```

**戻り値**:
```python
{
    "query": "岸田内閣",
    "raw_data": {
        "search_results": [...],
        "government_data": {...},
        "party_data": {...},
        "media_data": {...},
        "social_data": [...]
    },
    "sentiment_analysis": {
        "government_data": {
            "average_sentiment": 0.15,
            "sentiment_count": 3
        },
        "media_data": {
            "average_sentiment": -0.08,
            "sentiment_count": 8
        }
    },
    "reliability_analysis": {
        "government_data": 0.95,
        "media_data": 0.87,
        "social_data": 0.42
    },
    "processing_time": 25.6
}
```

### 2. Individual Analysis Components

#### 2.1 PoliticalSentimentAnalyzer

```python
from src.political_analysis import PoliticalSentimentAnalyzer

analyzer = PoliticalSentimentAnalyzer(config_manager, llm_service)
```

**主要メソッド**:

```python
# 基本感情分析
def analyze_political_sentiment(
    content: str,
    source_type: str = "news",
    political_context: Optional[Dict] = None
) -> Dict[str, Any]

# 感情トレンド分析
def analyze_sentiment_trend(
    contents: List[Dict[str, Any]],
    time_window_hours: int = 24
) -> Dict[str, Any]

# ソース別感情比較
def compare_source_sentiment(
    content_by_source: Dict[str, List[str]]
) -> Dict[str, Any]
```

#### 2.2 PoliticalReliabilityScorer

```python
from src.political_analysis import PoliticalReliabilityScorer

scorer = PoliticalReliabilityScorer(config_manager, llm_service)
```

**主要メソッド**:

```python
# ソース信頼性評価
def evaluate_source_reliability(
    source_url: str,
    source_name: Optional[str] = None,
    content_type: str = "news"
) -> Dict[str, Any]

# コンテンツ信頼性評価
def evaluate_content_reliability(
    content: str,
    source_info: Optional[Dict] = None,
    metadata: Optional[Dict] = None
) -> Dict[str, Any]

# クロスソース一貫性評価
def evaluate_cross_source_consistency(
    content_by_source: Dict[str, List[str]]
) -> Dict[str, Any]

# 信頼性履歴追跡
def track_source_reliability_history(
    source: str,
    reliability_scores: List[Dict],
    time_window_days: int = 30
) -> Dict[str, Any]
```

#### 2.3 PoliticalPredictionEngine

```python
from src.political_analysis import PoliticalPredictionEngine

engine = PoliticalPredictionEngine(
    config_manager, llm_service, 
    sentiment_analyzer, reliability_scorer
)
```

**主要メソッド**:

```python
# 支持率予測
def predict_support_rating(
    current_data: Dict[str, Any],
    prediction_horizon_days: int = 30
) -> Dict[str, Any]

# 選挙結果予測
def predict_election_outcome(
    current_polling_data: Dict[str, Any],
    prediction_horizon_days: int = 90
) -> Dict[str, Any]

# 政策影響予測
def predict_policy_impact(
    policy_proposal: Dict[str, Any],
    prediction_horizon_days: int = 60
) -> Dict[str, Any]

# スキャンダル影響予測
def predict_scandal_impact(
    scandal_data: Dict[str, Any],
    prediction_horizon_days: int = 14
) -> Dict[str, Any]

# 包括的予測レポート
def generate_comprehensive_political_forecast(
    comprehensive_data: Dict[str, Any],
    forecast_period_days: int = 90
) -> Dict[str, Any]
```

### 3. Data Collection APIs

#### 3.1 PoliticalScraperService

```python
from src.political_scraper import PoliticalScraperService

scraper = PoliticalScraperService(config_manager)
```

**主要メソッド**:

```python
# 政治意図別検索
def search_by_political_intent(
    query: str,
    intent: str,
    max_results: int = 10
) -> List[Dict[str, Any]]

# リアルタイム政治情報取得
def get_realtime_political_updates(
    max_results: int = 20
) -> Dict[str, List[Dict[str, Any]]]

# 包括的政治データ検索
def search_comprehensive_political_data(
    query: str,
    max_results: int = 20
) -> Dict[str, List[Dict[str, Any]]]
```

### 4. CLI Interface APIs

#### 4.1 Interactive Interface

```python
from src.political_cli import PoliticalInterface

interface = PoliticalInterface(config_manager, enable_color=True)
```

**主要メソッド**:

```python
# インタラクティブモード
def interactive_sentiment_analysis()
def interactive_reliability_evaluation()
def interactive_prediction_mode()

# バッチ処理
def batch_process_files(
    input_dir: str,
    output_dir: str,
    process_type: str = "sentiment",
    file_pattern: str = "*.txt"
) -> Dict[str, Any]

# レポート生成
def generate_analysis_report(
    topics: List[str],
    output_file: str,
    include_forecast: bool = True
) -> bool
```

### 5. Testing APIs

#### 5.1 統合テスト

```python
from src.political_cli import run_integration_test

# 統合テスト実行
result = run_integration_test(
    config_dir=None,
    enable_color=True
)
```

**テスト結果**:
```python
{
    "test_timestamp": "2024-06-15T10:30:00",
    "total_execution_time": 45.6,
    "tests_passed": 8,
    "tests_total": 9,
    "success_rate": 0.89,
    "individual_results": {
        "基本接続テスト": {"success": True, ...},
        "感情分析テスト": {"success": True, ...},
        "信頼性評価テスト": {"success": True, ...},
        ...
    }
}
```

## Error Handling

### Exception Types

```python
from src.utils.exceptions import (
    ConfigError,        # 設定エラー
    LLMError,          # LLMサービスエラー
    ScraperError,      # スクレイピングエラー
    AnalysisError      # 分析エラー
)
```

### Error Response Format

```python
{
    "error": "エラーメッセージ",
    "error_type": "AnalysisError",
    "timestamp": "2024-06-15T10:30:00",
    "context": {
        "function": "analyze_political_sentiment",
        "parameters": {...}
    }
}
```

## Configuration APIs

### ConfigManager

```python
from src.utils.config import ConfigManager

config = ConfigManager(config_dir="/path/to/config")

# 設定取得
llm_config = config.get_llm_config()
scraper_config = config.get_scraper_config()

# 設定検証
is_valid = config.validate_config()
```

## Data Models

### 政治エンティティ

```python
# 政治家情報
politician = {
    "name": "岸田文雄",
    "party": "自由民主党",
    "position": "内閣総理大臣",
    "ideology_score": 0.6,
    "reliability_score": 0.95
}

# 政党情報
party = {
    "name": "自由民主党",
    "ideology_score": 0.6,
    "seat_count": 261,
    "coalition_status": "与党"
}

# 世論調査
poll = {
    "date": "2024-06-15",
    "pollster": "NHK",
    "support_rate": 0.45,
    "sample_size": 1200,
    "reliability_score": 0.9
}
```

### 分析結果

```python
# 感情分析結果
sentiment_result = {
    "final_sentiment_score": float,    # -1.0 ～ 1.0
    "confidence_level": float,         # 0.0 ～ 1.0
    "political_bias": {
        "overall_bias": float,         # -1.0 ～ 1.0
        "dominant_bias": str          # "left_wing" | "right_wing" | "neutral"
    }
}

# 信頼性評価結果
reliability_result = {
    "final_reliability_score": float, # 0.0 ～ 1.0
    "reliability_level": str,         # "very_low" | "low" | "medium" | "high" | "very_high"
    "reliability_grade": str          # "A+" | "A" | "B+" | "B" | "C" | "D" | "F"
}

# 予測結果
prediction_result = {
    "predicted_value": float,
    "confidence_score": float,        # 0.0 ～ 1.0
    "confidence_level": str,         # "very_low" | "low" | "medium" | "high" | "very_high"
    "prediction_horizon_days": int
}
```

## Rate Limits and Quotas

### デフォルト制限

```python
rate_limits = {
    "government_scraping": 1.0,    # 1秒間隔
    "media_scraping": 1.5,         # 1.5秒間隔
    "social_scraping": 2.0,        # 2秒間隔
    "llm_requests": 0.5,           # 0.5秒間隔
}

cache_limits = {
    "ttl_hours": 24,               # キャッシュ有効期間
    "max_entries": 10000,          # 最大エントリ数
    "max_file_size_mb": 100        # 最大ファイルサイズ
}
```

## Best Practices

### 1. エラーハンドリング

```python
try:
    result = app.analyze_political_sentiment(content)
except AnalysisError as e:
    logger.error(f"分析エラー: {e}")
    # フォールバック処理
except Exception as e:
    logger.error(f"予期しないエラー: {e}")
    # エラー処理
```

### 2. パフォーマンス最適化

```python
# バッチ処理時は並行実行
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [
        executor.submit(app.analyze_political_sentiment, content)
        for content in contents
    ]
    results = [future.result() for future in futures]
```

### 3. キャッシュ活用

```python
# 同一クエリの重複実行を避ける
cache_key = f"sentiment_{hash(content)}"
if cache_key not in cache:
    result = app.analyze_political_sentiment(content)
    cache[cache_key] = result
else:
    result = cache[cache_key]
```

このAPIリファレンスにより、lain-politicsシステムの全機能を効率的に活用できます。