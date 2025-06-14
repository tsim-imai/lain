# lain-politics ユーザーガイド

## はじめに

**lain-politics**は日本政治の分析・予測に特化したAIシステムです。政治ニュースの感情分析、情報源の信頼性評価、内閣支持率・選挙結果の予測など、包括的な政治分析機能を提供します。

## インストール・セットアップ

### 前提条件

1. **Python 3.8+**
2. **LM Studio** (ローカルLLM実行環境)
3. **必要なライブラリ**:
   ```bash
   pip install -r requirements.txt
   ```

### 設定ファイル

#### 1. LM Studio設定 (`config/llm_config.json`)
```json
{
  "lm_studio": {
    "base_url": "http://localhost:1234/v1",
    "model_name": "japanese-llm-model",
    "max_tokens": 2048,
    "temperature": 0.3
  }
}
```

#### 2. スクレイパー設定 (`config/scraper_config.json`)
```json
{
  "bing": {
    "rate_limit": {
      "requests_per_second": 1
    }
  },
  "cache": {
    "ttl_hours": 24
  }
}
```

## 基本的な使用方法

### 1. システムテスト

まず、全コンポーネントが正常に動作するかテストします。

```bash
python -m src.political_cli test
```

**出力例**:
```
=== 政治分析システム接続テスト ===
✅ llm_service: 成功
✅ database: 成功  
✅ scraper_service: 成功
✅ sentiment_analyzer: 成功
✅ reliability_scorer: 成功
✅ prediction_engine: 成功
✅ 全システムテスト成功
```

### 2. 設定確認

現在の設定を確認します。

```bash
python -m src.political_cli config
```

## 主要機能の使用方法

### 1. 政治感情分析

政治関連テキストの感情・論調・バイアスを分析します。

#### 基本的な使用

```bash
python -m src.political_cli sentiment "岸田内閣の支持率が上昇し、経済政策への評価が高まっています"
```

**出力**:
```
感情スコア: +0.42
信頼度: 0.81
政治的バイアス: neutral
```

#### 詳細オプション

```bash
# ソースタイプ指定
python -m src.political_cli sentiment "政府の政策発表" --source-type official

# JSON出力
python -m src.political_cli sentiment "批判的な報道" --output-format json

# 詳細表示
python -m src.political_cli sentiment "政治コンテンツ" --verbose
```

**ソースタイプ**:
- `news`: ニュース記事（デフォルト）
- `social`: SNS投稿
- `official`: 政府・公式発表
- `statement`: 政党声明

### 2. 信頼性評価

情報源やコンテンツの信頼性を評価します。

#### ソース信頼性評価

```bash
python -m src.political_cli reliability "https://www.kantei.go.jp/jp/news/"
```

**出力**:
```
ソース信頼性: 1.00 (very_high)
```

#### コンテンツも含めた評価

```bash
python -m src.political_cli reliability "https://example.com" --content "評価したいニュース記事の内容"
```

**出力**:
```
ソース信頼性: 0.85 (high)
コンテンツ信頼性: 0.72 (グレード: B+)
```

### 3. 支持率予測

内閣支持率の将来予測を行います。

#### 基本予測

```bash
python -m src.political_cli support-rating
```

**出力**:
```
現在の支持率: 45.0%
予測支持率 (30日後): 47.2%
変化: +2.2%
予測信頼度: 0.73
```

#### 予測期間指定

```bash
# 7日後の予測
python -m src.political_cli support-rating --prediction-days 7

# 3ヶ月後の予測  
python -m src.political_cli support-rating --prediction-days 90
```

#### カスタムデータ使用

```bash
# データファイルを使用
python -m src.political_cli support-rating --data-file custom_data.json --prediction-days 30
```

**データファイル例** (`custom_data.json`):
```json
{
  "current_support_rate": 0.45,
  "sentiment_data": {
    "average_sentiment": 0.1,
    "volatility": 0.3
  },
  "media_data": {
    "coverage_volume": 0.6,
    "average_sentiment": 0.05
  }
}
```

### 4. 選挙結果予測

選挙の議席配分・政党支持率を予測します。

```bash
python -m src.political_cli election --prediction-days 90
```

**出力**:
```
政党支持率予測:
  自由民主党: 34.2%
  立憲民主党: 19.1%
  日本維新の会: 13.5%
  公明党: 8.7%
  その他: 24.5%

議席配分予測:
  自由民主党: 159議席
  立憲民主党: 89議席
  日本維新の会: 63議席
  公明党: 40議席
  その他: 114議席

予測信頼度: 0.68
```

### 5. 包括的政治分析

特定テーマについて複数ソースから情報を収集・分析します。

```bash
python -m src.political_cli analyze "岸田内閣" --max-results 20
```

**出力**:
```
分析クエリ: 岸田内閣

ソース別感情分析:
  government_data: +0.15 (3件)
  media_data: -0.08 (8件)
  social_data: +0.22 (5件)

ソース別信頼性:
  government_data: 0.95
  media_data: 0.87
  social_data: 0.42
```

### 6. 包括的予測レポート

全分野の予測を統合したレポートを生成します。

```bash
python -m src.political_cli forecast --forecast-days 90
```

#### レポート保存

```bash
python -m src.political_cli forecast --forecast-days 90 --save-report political_forecast_2024.json
```

**レポート内容**:
- エグゼクティブサマリー
- 支持率予測
- 選挙予測
- 政策影響分析
- リスク評価
- シナリオ分析

### 7. バッチ処理

複数のテキストを一括で感情分析します。

#### 入力ファイル準備

**input.txt**:
```
政府の新政策について議論が活発化
野党が厳しく追及する姿勢を示した
与党内からも慎重な意見が出ている
専門家は効果を疑問視している
```

#### バッチ実行

```bash
python -m src.political_cli batch-sentiment input.txt --output-file results.json
```

**出力ファイル** (`results.json`):
```json
[
  {
    "index": 1,
    "content": "政府の新政策について議論が活発化",
    "sentiment_score": 0.12,
    "confidence": 0.71,
    "bias": "neutral"
  },
  {
    "index": 2,
    "content": "野党が厳しく追及する姿勢を示した",
    "sentiment_score": -0.45,
    "confidence": 0.83,
    "bias": "neutral"
  }
]
```

## インタラクティブモード

プログラムから直接対話的に分析を実行できます。

```python
from src.political_cli import PoliticalInterface
from src.utils.config import ConfigManager

# 初期化
config = ConfigManager()
interface = PoliticalInterface(config)

# インタラクティブ感情分析
interface.interactive_sentiment_analysis()

# インタラクティブ信頼性評価
interface.interactive_reliability_evaluation()

# インタラクティブ予測
interface.interactive_prediction_mode()
```

## 高度な使用例

### 1. 政治トピックの継続監視

```bash
# 毎日の分析を自動化
#!/bin/bash
DATE=$(date +%Y%m%d)
python -m src.political_cli analyze "日本政治" --output-format json > "analysis_${DATE}.json"
python -m src.political_cli support-rating --output-format json > "support_${DATE}.json"
```

### 2. レポート自動生成

```python
from src.political_cli import PoliticalInterface
from datetime import datetime

interface = PoliticalInterface(config)

# 週次分析レポート
topics = ["内閣支持率", "経済政策", "外交問題", "選挙動向"]
report_file = f"weekly_report_{datetime.now().strftime('%Y%m%d')}.json"

interface.generate_analysis_report(
    topics=topics,
    output_file=report_file,
    include_forecast=True
)
```

### 3. ファイル一括処理

```python
# ディレクトリ内の全ファイルを処理
interface.batch_process_files(
    input_dir="./political_texts",
    output_dir="./analysis_results", 
    process_type="sentiment",
    file_pattern="*.txt"
)
```

## トラブルシューティング

### よくある問題

#### 1. LM Studioに接続できない

**エラー**: `LLM接続テスト失敗`

**解決策**:
1. LM Studioが起動しているか確認
2. ポート1234が使用可能か確認
3. `config/llm_config.json`のURLを確認

#### 2. スクレイピングエラー

**エラー**: `スクレイパー接続テスト失敗`

**解決策**:
1. インターネット接続を確認
2. ファイアウォール設定を確認
3. レート制限設定を緩和

#### 3. 予測精度が低い

**対策**:
1. より多くのデータを収集
2. 予測期間を短縮
3. 最新の政治動向を反映

### ログ確認

詳細なエラー情報を確認：

```bash
# デバッグモードで実行
python -m src.political_cli --debug sentiment "テストテキスト"

# ログファイル確認
tail -f logs/lain-politics.log
```

## パフォーマンス最適化

### 1. キャッシュ活用

```bash
# キャッシュ統計確認
python -m src.political_cli cache --stats

# 期限切れキャッシュ削除
python -m src.political_cli maintenance --cleanup
```

### 2. 並行処理調整

設定ファイルで並行処理数を調整：

```json
{
  "scraper": {
    "max_workers": 4,
    "request_delay": 1.0
  }
}
```

## ベストプラクティス

### 1. 定期的な分析

- 毎日の政治動向監視
- 週次トレンド分析
- 月次予測レポート

### 2. 複数視点の確保

- 異なるソースからの情報収集
- バイアス検出機能の活用
- 信頼性スコアの重視

### 3. 結果の解釈

- 予測信頼度の確認
- 統計的有意性の考慮
- 不確実性の認識

## API仕様（将来拡張）

現在はCLI中心ですが、将来的にREST APIとしても利用可能にする予定です。

```python
# 将来のAPI例
import requests

# 感情分析API
response = requests.post('/api/sentiment', {
    'content': '政治コンテンツ',
    'source_type': 'news'
})

# 予測API
response = requests.post('/api/predict/support-rating', {
    'prediction_days': 30,
    'data': {...}
})
```

## サポート・フィードバック

- バグレポート: GitHubイシュー
- 機能要望: ディスカッション
- 質問: ドキュメント確認後にイシュー作成

lain-politicsは継続的に改善されています。定期的にアップデートを確認し、新機能をご活用ください。