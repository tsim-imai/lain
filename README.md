# lain

ローカルLLMを使用したWeb検索・要約システム

## 概要

lainは、LM Studioと連携してローカルLLMで検索判断・クエリ生成・要約を実行し、Bingスクレイピングによる情報収集を行うCLIツールです。

## 主な機能

- **自律的検索判断**: LLMが検索の必要性を自動判断
- **最適なクエリ生成**: 自然言語入力から効果的な検索クエリを生成
- **Webスクレイピング**: Bing検索結果の自動取得（レート制限付き）
- **インテリジェント要約**: LLMによる検索結果の要約・回答生成
- **キャッシュシステム**: 24時間TTLでの検索結果キャッシュ
- **CLIインターフェース**: 直感的なコマンドライン操作

## 必要要件

- Python 3.8+
- LM Studio（ローカルLLM実行環境）
- インターネット接続（Web検索用）

## インストール

1. リポジトリをクローン
```bash
git clone https://github.com/tsim-imai/lain.git
cd lain
```

2. 依存関係をインストール
```bash
pip install -r requirements.txt
```

3. LM Studioを起動し、32B以下のモデルをロード
   - 接続先: `http://localhost:1234/v1`

4. テスト実行（オプション）
```bash
# 全テスト実行
pytest tests/

# 特定モジュールのテスト
pytest tests/test_llm_services_simple.py

# 静かな出力
pytest tests/ -q
```

## 使用方法

### 基本的な検索
```bash
python -m src.cli.main search "岸田文雄の誕生日はいつ？"
```

### システムテスト
```bash
python -m src.cli.main test
```

### 設定確認
```bash
python -m src.cli.main config
```

### キャッシュ管理
```bash
# キャッシュ統計表示
python -m src.cli.main cache --stats

# 期限切れキャッシュクリーンアップ
python -m src.cli.main maintenance --cleanup

# 全キャッシュ削除
python -m src.cli.main maintenance --clear-cache
```

### オプション

- `--no-cache`: キャッシュを使用せずに検索
- `--max-results N`: 最大検索結果数を指定
- `--output-format json`: JSON形式で出力
- `--verbose`: 詳細ログを有効化
- `--debug`: デバッグモードを有効化

## アーキテクチャ

```
CLI → LLM判断モジュール → クエリ生成 → Bingスクレイパー → 結果整理 → LLM要約 → 出力
       ↓                                ↓
    キャッシュ確認                   結果保存
```

## ディレクトリ構成

```
lain/
├── src/
│   ├── llm/          # LM Studio API連携、プロンプト管理
│   ├── scraper/      # Bingスクレイピング、レート制限
│   ├── cache/        # SQLite キャッシュ・履歴管理
│   ├── cli/          # CLI実装、コマンド処理
│   └── utils/        # 共通ユーティリティ
├── config/           # 設定ファイル
├── data/             # SQLiteデータベース
└── tests/            # テスト（今後実装）
```

## 設定

設定ファイルは `config/` ディレクトリにあります：

- `llm_config.json`: LM Studio接続設定とプロンプト
- `scraper_config.json`: Bingスクレイピング設定
- `logging_config.json`: ログ設定

## トラブルシューティング

### LM Studio接続エラー
1. LM Studioが起動しているか確認
2. モデルがロードされているか確認
3. ポート1234が使用可能か確認

### スクレイピングエラー
- レート制限により一時的に制限される場合があります
- 数分待ってから再試行してください

### キャッシュエラー
- `data/` ディレクトリの書き込み権限を確認
- `maintenance --cleanup` でキャッシュをクリーンアップ

## 開発

### テスト実行
```bash
pytest tests/  # 今後実装予定
```

### コード品質チェック
```bash
ruff check src/
ruff format src/
```

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 貢献

バグ報告や機能提案はIssueでお願いします。