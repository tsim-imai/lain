# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

ローカルLLMを使用した自律的Web検索・要約システム「lain」
- LM Studioと連携してローカルLLMで検索判断・クエリ生成・要約を実行
- Bingスクレイピングによる情報収集
- SQLiteベースのキャッシュ・履歴システム
- CLIインターフェース

## アーキテクチャ

```
CLI → LLM判断モジュール → クエリ生成 → Bingスクレイパー → 結果整理 → LLM要約 → 出力
       ↓                                ↓
    キャッシュ確認                   結果保存
```

## ディレクトリ構成

```
src/
├── llm/          # LM Studio API連携、プロンプト管理
├── scraper/      # Bingスクレイピング、レート制限
├── cache/        # SQLite キャッシュ・履歴管理
├── cli/          # CLI実装、コマンド処理
└── utils/        # 共通ユーティリティ
config/           # 設定ファイル（LM Studio接続情報等）
data/            # SQLiteデータベース
tests/           # ユニットテスト
```

## 開発コマンド

```bash
# 開発環境セットアップ
pip install -r requirements.txt

# テスト実行
pytest tests/

# リンター実行
ruff check src/
ruff format src/

# CLI実行（開発中）
python -m src.cli.main "検索クエリ"
```

## 重要な設計原則

1. **LM Studio依存**: すべてのLLM処理はLM Studio API経由で実行
2. **レート制限**: Bingスクレイピングは1秒間隔で実行
3. **キャッシュ優先**: 同一クエリは24時間キャッシュを使用
4. **エラーハンドリング**: ネットワークエラー、LLMエラーの適切な処理
5. **ログ出力**: デバッグ用の詳細ログ記録

## LM Studio設定

- 接続先: `http://localhost:1234/v1`
- 推奨モデル: 32B以下の日本語対応モデル
- 設定ファイル: `config/llm_config.json`

## データベーススキーマ

- `search_cache`: クエリキャッシュ（query, results, timestamp, ttl）
- `chat_history`: チャット履歴（将来実装）