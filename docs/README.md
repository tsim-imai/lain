# lain-politics Documentation

日本政治予測システム「lain-politics」の包括的ドキュメント

## ドキュメント構成

### 📋 [要件定義書](political_requirements.md)
- システム概要と機能要件
- 技術要件とデータ設計
- 開発計画と課題

### 🏗️ [システムアーキテクチャ](lain-politics-architecture.md)
- 完全なシステム構成図
- 各コンポーネントの詳細仕様
- データフロー・処理フロー
- パフォーマンス・セキュリティ仕様

### 📖 [ユーザーガイド](lain-politics-user-guide.md)
- インストール・セットアップ手順
- 基本的な使用方法
- 全機能の詳細な使用例
- トラブルシューティング

### 🔧 [API リファレンス](lain-politics-api-reference.md)
- 全コンポーネントのAPI仕様
- パラメータ・戻り値の詳細
- エラーハンドリング
- ベストプラクティス

## クイックスタート

### 1. システムテスト
```bash
python -m src.political_cli test
```

### 2. 基本的な分析
```bash
# 感情分析
python -m src.political_cli sentiment "政治ニュースのテキスト"

# 信頼性評価
python -m src.political_cli reliability "https://example.com"

# 支持率予測
python -m src.political_cli support-rating --prediction-days 30
```

### 3. 包括的分析
```bash
# 政治トピック分析
python -m src.political_cli analyze "岸田内閣"

# 予測レポート生成
python -m src.political_cli forecast --forecast-days 90 --save-report report.json
```

## 主要機能

### ✨ 政治感情分析
- 政治コンテンツの感情・論調・バイアス分析
- -1.0(ネガティブ) ～ +1.0(ポジティブ)スコア
- 政治的立場(左派/右派/中立)検出

### 🔍 信頼性評価
- 情報源とコンテンツの多層信頼性評価
- 偽情報・デマ・センセーショナリズム検出
- A+～Fグレード評価

### 📊 政治予測
- **内閣支持率予測**: 7日～1年先の支持率変動
- **選挙結果予測**: 議席配分・連立可能性分析
- **政策影響予測**: 政策発表の支持率への影響
- **スキャンダル影響予測**: 政治スキャンダルの影響度・回復時期

### 🔎 包括的データ収集
- **政府公式**: 官邸・各省庁の政策発表
- **政党公式**: 8つの主要政党データ
- **メディア監視**: 8つの主要メディア
- **SNS監視**: 政治家アカウント・政治ハッシュタグ

## システム特徴

### 🎯 完全政治特化
- 日本政治に最適化されたアルゴリズム
- 政治用語・人名の専門認識
- 政治的文脈を考慮した分析

### ⚡ 高性能処理
- 並行処理による高速データ収集
- インテリジェントキャッシュシステム
- レート制限対応

### 🔒 信頼性重視
- 複数ソースクロス検証
- 透明性のある信頼性スコア
- バイアス検出・補正機能

### 🎨 ユーザーフレンドリー
- 直感的なCLIインターフェース
- カラー対応の見やすい出力
- インタラクティブモード

## 技術スタック

- **言語**: Python 3.8+
- **LLM**: LM Studio (ローカル実行)
- **データベース**: SQLite
- **Webスクレイピング**: requests + BeautifulSoup
- **CLI**: Click
- **並行処理**: ThreadPoolExecutor

## 対応データソース

### 政府・公的機関
- 首相官邸 (kantei.go.jp)
- 各省庁公式サイト
- 国会図書館
- 選挙管理委員会

### 政党公式
- 自民党、立憲民主党、日本維新の会
- 公明党、共産党、国民民主党
- れいわ新選組、社民党

### メディア
- **公共放送**: NHK
- **通信社**: 共同通信、時事通信
- **新聞**: 朝日、読売、毎日、産経、日経

### SNS・専門メディア
- Twitter/X政治アカウント
- 政治山、選挙ドットコム

## 使用例

### 日次政治監視
```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
python -m src.political_cli analyze "日本政治" > "daily_analysis_${DATE}.txt"
python -m src.political_cli support-rating > "support_${DATE}.txt"
```

### 週次レポート生成
```python
from src.political_cli import PoliticalInterface

interface = PoliticalInterface(config)
interface.generate_analysis_report(
    topics=["内閣支持率", "経済政策", "外交", "選挙"],
    output_file="weekly_report.json",
    include_forecast=True
)
```

### バッチ分析
```bash
python -m src.political_cli batch-sentiment political_texts.txt --output-file results.json
```

## 導入・運用

### 開発環境
```bash
git clone <repository>
cd lain-politics
pip install -r requirements.txt
```

### 本番運用
- LM Studioの安定運用
- 定期的なデータベース最適化
- ログ監視・アラート設定
- 予測精度の継続的評価

## ライセンス・免責事項

### 著作権・引用
- フェアユース範囲での情報収集
- 適切な引用・出典表示
- robots.txt準拠

### 政治的中立性
- バイアス検出・表示機能
- 複数視点の情報提供
- 透明性のある分析過程

### 予測の限界
- 統計的予測であり確実性は保証されない
- 急激な政治変動は予測困難
- 予測信頼度の参考推奨

## サポート

- **ドキュメント**: 本ドキュメント群を参照
- **バグレポート**: GitHubイシューで報告
- **機能要望**: ディスカッションで提案
- **質問**: イシューで質問（ドキュメント確認後）

---

**lain-politics** は日本政治の理解と予測をサポートする高度なAIシステムです。政治研究者、ジャーナリスト、政策立案者、そして政治に関心のある全ての方にご活用いただけます。