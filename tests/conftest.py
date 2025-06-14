"""
pytest共通設定・フィクスチャ
"""
import pytest
import tempfile
import shutil
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock
import sqlite3

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.config import ConfigManager
from src.llm.services import LLMService
from src.scraper.services import ScraperService
from src.cache.services import CacheService


@pytest.fixture
def temp_config_dir():
    """テスト用の一時設定ディレクトリを作成"""
    temp_dir = tempfile.mkdtemp()
    config_dir = Path(temp_dir) / "config"
    config_dir.mkdir()
    
    # テスト用設定ファイルを作成
    llm_config = {
        "lm_studio": {
            "base_url": "http://localhost:1234/v1",
            "api_key": "dummy",
            "model": "test-model",
            "temperature": 0.7,
            "max_tokens": 1000,
            "timeout": 30
        },
        "prompts": {
            "search_decision": "以下の質問について、Web検索が必要かどうかを判断してください。\\n検索が必要な場合は「YES」、不要な場合は「NO」で答えてください。\\n\\n質問: {query}",
            "query_generation": "以下の質問に対して、最適な検索クエリを生成してください。\\n日本語で簡潔に、検索に適したキーワードを返してください。\\n\\n質問: {query}",
            "result_summary": "以下の検索結果を元に、ユーザーの質問に対する回答を作成してください。\\n\\n質問: {query}\\n\\n検索結果:\\n{search_results}\\n\\n回答:"
        }
    }
    
    scraper_config = {
        "search_engines": {
            "primary": "duckduckgo",
            "fallback": "brave"
        },
        "duckduckgo": {
            "base_url": "https://html.duckduckgo.com/html/",
            "user_agents": ["test-agent"],
            "headers": {"Accept": "text/html"},
            "rate_limit": {"requests_per_second": 1, "retry_attempts": 3, "retry_delay": 2},
            "selectors": {
                "result_item": ".result",
                "title": ".result__a", 
                "url": ".result__a",
                "snippet": ".result__snippet"
            }
        },
        "brave": {
            "base_url": "https://search.brave.com/search",
            "user_agents": ["test-agent"],
            "headers": {"Accept": "text/html"},
            "rate_limit": {"requests_per_second": 1, "retry_attempts": 3, "retry_delay": 2},
            "selectors": {
                "result_item": ".snippet",
                "title": "a",
                "url": "a", 
                "snippet": "p"
            }
        },
        "cache": {
            "ttl_hours": 24,
            "max_results": 10,
            "database_path": "data/test_cache.db"
        }
    }
    
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "standard",
                "stream": "ext://sys.stdout"
            }
        },
        "loggers": {
            "src": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            }
        }
    }
    
    # 設定ファイルを書き込み
    import json
    with open(config_dir / "llm_config.json", "w", encoding="utf-8") as f:
        json.dump(llm_config, f, ensure_ascii=False, indent=2)
    
    with open(config_dir / "scraper_config.json", "w", encoding="utf-8") as f:
        json.dump(scraper_config, f, ensure_ascii=False, indent=2)
        
    with open(config_dir / "logging_config.json", "w", encoding="utf-8") as f:
        json.dump(logging_config, f, ensure_ascii=False, indent=2)
    
    yield str(config_dir)
    
    # クリーンアップ
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_db():
    """テスト用の一時データベースを作成"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_file.close()
    
    yield temp_file.name
    
    # クリーンアップ
    Path(temp_file.name).unlink(missing_ok=True)


@pytest.fixture
def config_manager(temp_config_dir):
    """テスト用ConfigManagerインスタンス"""
    return ConfigManager(temp_config_dir)


@pytest.fixture
def mock_llm_client():
    """モックLLMクライアント"""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = "テスト応答"
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


@pytest.fixture
def llm_service(config_manager, mock_llm_client):
    """テスト用LLMServiceインスタンス"""
    service = LLMService(config_manager)
    service.client = mock_llm_client
    return service


@pytest.fixture
def mock_requests():
    """モックrequestsレスポンス"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = """
    <html>
        <div class="result">
            <a class="result__a" href="https://example.com">テストタイトル</a>
            <p class="result__snippet">テストスニペット</p>
        </div>
    </html>
    """
    mock_response.encoding = "utf-8"
    return mock_response


@pytest.fixture
def scraper_service(config_manager):
    """テスト用ScraperServiceインスタンス"""
    return ScraperService(config_manager)


@pytest.fixture
def cache_service(config_manager, temp_db):
    """テスト用CacheServiceインスタンス"""
    # 一時データベースパスで設定を更新
    config_manager._scraper_config = None  # キャッシュをクリア
    scraper_config = config_manager.get_scraper_config()
    scraper_config["cache"]["database_path"] = temp_db
    
    return CacheService(config_manager)


@pytest.fixture
def sample_search_results():
    """サンプル検索結果データ"""
    return [
        {
            "title": "岸田文雄 - Wikipedia",
            "url": "https://ja.wikipedia.org/wiki/岸田文雄",
            "snippet": "岸田 文雄（きしだ ふみお、1957年7月29日 - ）は、日本の政治家。",
            "source": "duckduckgo"
        },
        {
            "title": "首相官邸 - 岸田内閣",
            "url": "https://www.kantei.go.jp/",
            "snippet": "岸田文雄内閣総理大臣のプロフィール",
            "source": "duckduckgo"
        }
    ]