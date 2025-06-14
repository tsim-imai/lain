# lain-politics システムアーキテクチャ

## 概要

**lain-politics**は、既存の汎用LLM検索システム「lain」を日本政治予測に完全特化させた高度な政治分析システムです。感情分析・信頼性評価・予測エンジンを統合し、リアルタイムの政治データから包括的な分析と予測を提供します。

## システム構成

```
lain-politics アーキテクチャ
├── Political Data Layer (政治データ層)
│   ├── Government Scraper (政府データ収集)
│   ├── Party Scraper (政党データ収集)
│   ├── Media Scraper (メディア監視)
│   ├── Social Scraper (SNS監視)
│   └── Political Search Engine (政治特化検索)
│
├── Analysis Engine Layer (分析エンジン層)
│   ├── Political Sentiment Analyzer (政治感情分析)
│   ├── Political Reliability Scorer (信頼性評価)
│   └── Political Prediction Engine (予測エンジン)
│
├── Intelligence Layer (知能層)
│   ├── Political LLM Service (政治特化LLM)
│   ├── Political Entity Recognition (政治エンティティ認識)
│   └── Political Intent Classification (政治意図分類)
│
├── Data Management Layer (データ管理層)
│   ├── Political Database (政治専用DB)
│   ├── Cache System (キャッシュシステム)
│   └── Configuration Management (設定管理)
│
└── Interface Layer (インターフェース層)
    ├── Political CLI (政治特化CLI)
    ├── Interactive Interface (対話型インターフェース)
    └── Integration Tests (統合テスト)
```

## 主要コンポーネント

### 1. 政治データ収集システム

#### 1.1 Government Scraper (`src/political_scraper/government_scraper.py`)
- **対象**: 官邸、各省庁、政府機関
- **収集データ**: 政策発表、記者会見、閣議決定
- **信頼性**: 最高レベル (1.0)
- **更新頻度**: リアルタイム

#### 1.2 Party Scraper (`src/political_scraper/party_scraper.py`)
- **対象**: 主要8政党の公式サイト
- **収集データ**: 政策、ニュース、声明
- **政党リスト**:
  - 自由民主党、立憲民主党、日本維新の会
  - 公明党、日本共産党、国民民主党
  - れいわ新選組、社会民主党
- **イデオロギースコア**: -1.0(左派) ～ +1.0(右派)

#### 1.3 Media Scraper (`src/political_scraper/media_scraper.py`)
- **対象メディア**: NHK、朝日、読売、毎日、産経、日経、共同、時事
- **バイアス検出**: 各メディアの政治的立場を数値化
- **信頼性評価**: メディア別信頼性スコア (0.8-0.95)

#### 1.4 Social Scraper (`src/political_scraper/social_scraper.py`)
- **監視対象**: 政治家公式アカウント、政治ハッシュタグ
- **感情分析**: リアルタイム世論動向分析
- **トレンド検出**: 政治トピックのバイラル化検知

### 2. 分析エンジンシステム

#### 2.1 Political Sentiment Analyzer (`src/political_analysis/political_sentiment_analyzer.py`)

**主要機能**:
- 政治コンテンツの包括的感情分析
- 政治的バイアス検出（左派/右派/ポピュリスト）
- 感情強度・信頼度評価
- 時系列感情トレンド分析

**分析指標**:
```python
sentiment_categories = {
    "positive": ["支持", "賛成", "評価", "成功", "前進"],
    "negative": ["批判", "反対", "失敗", "問題", "スキャンダル"],
    "neutral": ["発表", "会見", "決定", "検討", "協議"]
}

bias_detection = {
    "right_wing": ["保守", "伝統", "秩序", "国家"],
    "left_wing": ["革新", "平和", "人権", "平等"],
    "populist": ["庶民", "既得権益", "エリート", "官僚"]
}
```

#### 2.2 Political Reliability Scorer (`src/political_analysis/political_reliability_scorer.py`)

**信頼性評価基準**:
```python
source_reliability = {
    "government": 1.0,      # 政府公式
    "major_media": 0.85,    # 大手メディア
    "parties": 0.90,        # 政党公式（バイアスあり）
    "social_media": 0.40    # SNS
}
```

**評価項目**:
- ソース信頼性（ドメイン・組織ベース）
- コンテンツ品質（構造・事実性）
- 偽情報・デマ検出
- センセーショナリズム評価
- クロスソース一貫性検証

#### 2.3 Political Prediction Engine (`src/political_analysis/political_prediction_engine.py`)

**予測機能**:
1. **内閣支持率予測**
   - 感情分析・メディア報道・政府活動を統合
   - 短期(7日)〜長期(365日)予測対応
   - 予測信頼度付き

2. **選挙結果予測**
   - 政党支持率→議席配分変換
   - 連立可能性分析
   - 歴史的データとの比較

3. **政策影響予測**
   - 政策発表の支持率への影響
   - 実現可能性評価
   - 世論への影響度分析

4. **スキャンダル影響予測**
   - メディア増幅効果分析
   - 回復時期予測
   - 類似事例との比較

### 3. 政治特化LLMシステム

#### 3.1 Political LLM Service (`src/political_llm/political_service.py`)

**政治意図分類**:
```python
political_intents = [
    "support_rating",      # 支持率関連
    "election_prediction", # 選挙予測
    "policy_analysis",     # 政策分析
    "political_news",      # 政治ニュース
    "politician_info",     # 政治家情報
    "party_info",          # 政党情報
    "political_scandal",   # 政治スキャンダル
    "coalition_analysis",  # 連立分析
    "general_political"    # 一般政治
]
```

**エンティティ認識**:
- 政治家: 50+名の主要政治家
- 政党: 8つの主要政党
- 政策分野: 40+の政策領域

#### 3.2 Specialized Prompts (`src/political_llm/political_prompts.py`)

政治分析専用のプロンプトテンプレート:
- 選挙予測分析
- 政策評価
- 世論分析
- 信頼性評価
- 感情分析

### 4. データ管理システム

#### 4.1 Political Database (`src/political_data/political_database.py`)

**データスキーマ**:
```sql
-- 政治家マスタ
politicians (id, name, party, position, ideology_score, reliability_score)

-- 政党マスタ
parties (id, name, ideology_score, seat_count, coalition_status)

-- 選挙データ
elections (id, date, type, region, results, turnout)

-- 世論調査データ
polls (id, date, pollster, target, results, reliability_score)
```

## CLIインターフェース

### 基本コマンド

```bash
# 感情分析
python -m src.political_cli sentiment "政治コンテンツ" --source-type news

# 信頼性評価
python -m src.political_cli reliability "https://example.com" --content "評価コンテンツ"

# 支持率予測
python -m src.political_cli support-rating --prediction-days 30

# 選挙予測
python -m src.political_cli election --prediction-days 90

# 包括的分析
python -m src.political_cli analyze "分析クエリ" --max-results 20

# 予測レポート
python -m src.political_cli forecast --forecast-days 90 --save-report report.json

# システムテスト
python -m src.political_cli test

# バッチ処理
python -m src.political_cli batch-sentiment input.txt --output-file results.json
```

### 出力形式

**Text形式** (デフォルト):
```
感情スコア: +0.25
信頼度: 0.78
政治的バイアス: neutral
```

**JSON形式**:
```json
{
  "final_sentiment_score": 0.25,
  "confidence_level": 0.78,
  "political_bias": {
    "dominant_bias": "neutral",
    "overall_bias": 0.02
  },
  "processing_time": 1.23
}
```

## パフォーマンス仕様

### 処理速度目標
- 感情分析: < 2秒
- 信頼性評価: < 3秒
- 支持率予測: < 10秒
- 包括的分析: < 30秒

### スケーラビリティ
- 並行処理対応（ThreadPoolExecutor）
- インメモリキャッシュ
- レート制限機能
- 段階的フォールバック

## 設定管理

### LLM設定 (`config/llm_config.json`)
```json
{
  "lm_studio": {
    "base_url": "http://localhost:1234/v1",
    "model_name": "japanese-political-model",
    "max_tokens": 2048,
    "temperature": 0.3
  }
}
```

### スクレイパー設定 (`config/scraper_config.json`)
```json
{
  "rate_limits": {
    "government": 1.0,
    "media": 1.5,
    "social": 2.0
  },
  "cache": {
    "ttl_hours": 24,
    "max_entries": 10000
  }
}
```

## セキュリティ・倫理配慮

### データプライバシー
- 個人情報の匿名化
- キャッシュデータの定期削除
- アクセスログの最小化

### 政治的中立性
- バイアス検出・補正機能
- 複数視点の情報提供
- 透明性のある信頼性スコア

### 著作権・法的配慮
- フェアユース範囲での引用
- robots.txt尊重
- レート制限による負荷配慮

## 拡張性

### 新機能追加ポイント
- 地方政治対応
- 国際政治比較
- 可視化ダッシュボード
- API化

### データソース拡張
- 追加メディア対応
- 海外メディア統合
- 学術研究データ
- 経済指標連携

## 運用・保守

### ログ管理
- 構造化ログ出力
- エラー追跡機能
- パフォーマンス監視

### 品質保証
- 統合テストスイート
- 継続的ベンチマーク
- データ品質チェック

このアーキテクチャにより、lain-politicsは日本政治分析のための包括的で高精度なシステムとして機能します。