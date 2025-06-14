# Tests Directory

このディレクトリにはlainプロジェクトのユニットテストが含まれています。

## テストファイル構成

### 🔧 設定ファイル
- **`conftest.py`** - pytest共通設定とフィクスチャ定義
  - テスト用の一時設定ディレクトリ作成
  - モック化されたサービスインスタンス提供
  - サンプルデータ定義
- **`pytest.ini`** - pytest実行設定（プロジェクトルート）

### 🧪 テストファイル（計17テスト）

#### `test_cache_services_simple.py` (6テスト)
キャッシュサービスの基本機能をテスト：
- **初期化テスト**: CacheServiceの正常な初期化
- **キャッシュ確認**: `is_query_cached()` メソッドの動作
- **キャッシュクリア**: `clear_all_cache()` メソッドの動作
- **期限切れクリーンアップ**: `cleanup_expired_cache()` メソッドの動作
- **統計情報取得**: `get_cache_statistics()` メソッドの動作
- **ヘルスチェック**: `health_check()` メソッドの動作

#### `test_llm_services_simple.py` (4テスト)
LLMサービスの基本機能をテスト：
- **初期化テスト**: LLMServiceの正常な初期化
- **検索判断**: `should_search()` メソッドのモックテスト
- **クエリ生成**: `generate_search_query()` メソッドのモックテスト
- **直接回答**: `direct_answer()` メソッドのモックテスト

#### `test_scraper_services_simple.py` (7テスト)
スクレイパーサービスの基本機能をテスト：
- **初期化テスト**: ScraperServiceの正常な初期化
- **DuckDuckGo検索**: DuckDuckGoエンジンでの検索機能
- **Brave検索**: Braveエンジンでの検索機能
- **未知エンジン処理**: 不明な検索エンジンのエラーハンドリング
- **結果クリーンアップ**: 検索結果の基本的なフィルタリング
- **重複除去**: URL重複の検索結果除去機能
- **統計情報**: スクレイパーの設定・統計情報取得

## テスト実行方法

### 基本コマンド
```bash
# 全テスト実行（17テスト）
pytest tests/

# 詳細出力付き実行
pytest tests/ -v

# 静かな実行（合格/失敗のみ表示）
pytest tests/ -q
```

### 特定テスト実行
```bash
# LLMサービスのみ
pytest tests/test_llm_services_simple.py

# キャッシュサービスのみ
pytest tests/test_cache_services_simple.py

# スクレイパーサービスのみ
pytest tests/test_scraper_services_simple.py
```

### 開発時の推奨
```bash
# 開発中の素早い確認
pytest tests/ -q

# デバッグ時の詳細確認
pytest tests/ -v -s
```

## テストの特徴

### ✅ 実用的な設計
- **モック化**: 外部依存（LM Studio、Web検索）を分離
- **フィクスチャ**: 再利用可能なテストデータとインスタンス
- **軽量**: 必要最小限のテストで基本機能をカバー

### 🛡️ 対象機能
- **初期化**: 各サービスの正常な立ち上がり
- **基本操作**: 主要メソッドの動作確認
- **エラーハンドリング**: 異常ケースの適切な処理
- **設定管理**: 設定ファイルの読み込みと検証

### 🚫 意図的に除外した要素
- **ネットワークテスト**: 実際のWeb検索（不安定・時間がかかる）
- **LM Studio依存**: 実際のLLM呼び出し（外部依存）
- **複雑な統合テスト**: エンドツーエンドの複雑なシナリオ

## テスト追加時の注意点

### 新しいテストを追加する場合：
1. **命名規則**: `test_[module]_simple.py` 形式を維持
2. **モック使用**: 外部依存は必ずモック化
3. **シンプル性**: 複雑すぎるテストは避ける
4. **速度重視**: 実行時間は短く保つ

### フィクスチャの活用：
- `config_manager`: テスト用設定管理インスタンス
- `cache_service`: テスト用キャッシュサービス
- `scraper_service`: テスト用スクレイパーサービス
- `sample_search_results`: サンプル検索結果データ

## 期待される結果

正常に動作している場合、以下のような出力が表示されます：

```
================ test session starts ================
platform darwin -- Python 3.11.9, pytest-8.3.5
collected 17 items

tests/test_cache_services_simple.py ......        [ 35%]
tests/test_llm_services_simple.py ....            [ 58%]
tests/test_scraper_services_simple.py .......     [100%]

================= 17 passed in 0.05s ================
```

このテストスイートにより、lainプロジェクトの主要機能が正常に動作することを素早く確認できます。