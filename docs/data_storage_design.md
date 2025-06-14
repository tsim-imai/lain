# 学習データ蓄積システム設計書

## 1. 概要

lain-politics の学習データ蓄積システム。スクレイピング頻度を削減し、過去データから高精度な政治予測を実現する。

## 2. 蓄積対象データ

### 2.1 生データ（Raw Data）
```
政治ニュース記事:
├── ID, タイトル, 本文, 要約
├── 発表日時, 収集日時, ソース
├── URL, 信頼性スコア, 政治的バイアス
└── 関連エンティティ（人物、政党、政策）

SNS投稿:
├── ID, 投稿者, 内容, 投稿日時
├── プラットフォーム, エンゲージメント
├── 感情スコア, 信頼性レベル
└── 関連トピック, ハッシュタグ

政府発表:
├── ID, 発表機関, タイトル, 内容
├── 発表日時, カテゴリ, 重要度
├── 関連法案, 政策分野
└── 影響範囲, 実施予定日

世論調査:
├── ID, 調査機関, 調査日時, 対象者数
├── 支持率データ, 政党支持率
├── 調査方法, 信頼性評価
└── 設問内容, 回答分布

選挙データ:
├── ID, 選挙種別, 実施日, 地域
├── 候補者情報, 得票数, 得票率
├── 投票率, 当選者, 政党別議席
└── 選挙前予測, 実績比較
```

### 2.2 メタデータ
```
データ品質:
├── 収集精度, 完全性, 最新性
├── ソース多様性, 検証済みフラグ
└── エラー情報, 修正履歴

関連性:
├── 政治関連度スコア, トピック分類
├── エンティティ抽出結果, 関係性
└── 時系列パターン, 類似データ
```

## 3. データベース設計拡張

### 3.1 新規テーブル
```sql
-- 政治ニュース記事
political_news (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    summary TEXT,
    url TEXT UNIQUE,
    source_name TEXT,
    published_at TIMESTAMP,
    collected_at TIMESTAMP,
    reliability_score REAL,
    political_bias REAL,
    topic_category TEXT,
    sentiment_score REAL,
    entity_mentions TEXT -- JSON
);

-- SNS投稿データ
social_posts (
    id INTEGER PRIMARY KEY,
    platform TEXT,
    account_name TEXT,
    content TEXT,
    posted_at TIMESTAMP,
    collected_at TIMESTAMP,
    engagement_data TEXT, -- JSON
    sentiment_score REAL,
    reliability_score REAL,
    hashtags TEXT,
    mentioned_entities TEXT -- JSON
);

-- 政府発表データ
government_announcements (
    id INTEGER PRIMARY KEY,
    agency TEXT,
    title TEXT,
    content TEXT,
    announced_at TIMESTAMP,
    collected_at TIMESTAMP,
    category TEXT,
    importance_level INTEGER,
    related_policies TEXT, -- JSON
    implementation_date TIMESTAMP
);

-- 世論調査データ
opinion_polls (
    id INTEGER PRIMARY KEY,
    organization TEXT,
    poll_date TIMESTAMP,
    sample_size INTEGER,
    methodology TEXT,
    questions TEXT, -- JSON
    results TEXT, -- JSON
    reliability_score REAL,
    collected_at TIMESTAMP
);

-- 選挙データ
election_data (
    id INTEGER PRIMARY KEY,
    election_type TEXT,
    election_date DATE,
    region TEXT,
    candidates TEXT, -- JSON
    results TEXT, -- JSON
    turnout_rate REAL,
    predictions TEXT, -- JSON
    collected_at TIMESTAMP
);
```

### 3.2 インデックス設計
```sql
-- 時系列検索用
CREATE INDEX idx_political_news_date ON political_news(published_at);
CREATE INDEX idx_social_posts_date ON social_posts(posted_at);
CREATE INDEX idx_polls_date ON opinion_polls(poll_date);

-- トピック検索用  
CREATE INDEX idx_political_news_topic ON political_news(topic_category);
CREATE INDEX idx_government_category ON government_announcements(category);

-- 全文検索用
CREATE VIRTUAL TABLE news_fts USING fts5(title, content, content='political_news');
```

## 4. キャッシュ戦略

### 4.1 階層キャッシュ
```
Level 1 - メモリキャッシュ:
├── 直近24時間のデータ
├── 頻繁にアクセスされるクエリ結果
└── 実行中の分析結果

Level 2 - DBキャッシュ:
├── 過去1週間のデータ
├── 前処理済み集計データ
└── 関連性スコア付きデータ

Level 3 - アーカイブ:
├── 1週間以上前のデータ
├── 圧縮・最適化済み
└── 統計的サマリー
```

### 4.2 重複排除
```
重複検出ロジック:
├── URL完全一致（ニュース記事）
├── 内容類似度 > 0.9（SNS投稿）
├── 発表日時＋機関（政府発表）
└── 調査日＋機関（世論調査）

重複処理:
├── 最新データを保持
├── 古いデータは統合・アーカイブ
└── 重複履歴をメタデータで管理
```

## 5. データ活用パターン

### 5.1 スクレイピング最適化
```python
def should_scrape(query, timeframe):
    # 既存データチェック
    cached_data = check_cache(query, timeframe)
    
    if cached_data and is_fresh(cached_data, hours=24):
        return False  # キャッシュ利用
    elif cached_data and is_fresh(cached_data, hours=168):
        return "incremental"  # 増分取得
    else:
        return True  # 全取得
```

### 5.2 学習データ検索
```python
def find_similar_patterns(current_situation):
    # 過去の類似状況を検索
    historical_data = search_by_similarity(
        entities=current_situation.entities,
        sentiment=current_situation.sentiment,
        timeframe="-6months"
    )
    return historical_data
```

### 5.3 予測精度向上
```python
def enhance_prediction(base_prediction, historical_context):
    # 過去データから補正係数を計算
    correction_factor = calculate_historical_accuracy(
        similar_situations=historical_context,
        prediction_type=base_prediction.type
    )
    
    return base_prediction * correction_factor
```

## 6. 実装優先順位

### Phase 5.2: データベーススキーマ拡張
- 新規テーブル作成
- インデックス設定
- マイグレーション機能

### Phase 5.3: スクレイパーDB保存機能
- 各スクレイパーにDB保存機能追加
- 重複チェック・排除
- エラーハンドリング

### Phase 5.4: キャッシュシステム
- メモリキャッシュ実装
- キャッシュ有効性判定
- 自動クリーンアップ

### Phase 5.5: データ検索・活用
- 類似データ検索
- 統計的サマリー生成
- 予測精度向上ロジック

## 7. 期待効果

### スクレイピング削減
- **初回以降**: 90%以上削減
- **定期更新**: 1日1回 → 週1回
- **レスポンス速度**: 10倍高速化

### 予測精度向上  
- **支持率予測**: ±2% → ±1%以内
- **選挙予測**: 過去パターン学習で精度向上
- **リスク評価**: 類似事例からより正確な評価