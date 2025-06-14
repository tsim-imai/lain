"""
DuckDuckGo検索スクレイパー
"""
import logging
import time
import random
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode
import requests
from bs4 import BeautifulSoup
try:
    from fake_useragent import UserAgent
    HAS_FAKE_USERAGENT = True
except ImportError:
    HAS_FAKE_USERAGENT = False
from ..utils.config import ConfigManager
from ..utils.exceptions import ScraperError, NetworkError

logger = logging.getLogger(__name__)


class DuckDuckGoScraper:
    """DuckDuckGo検索スクレイパークラス"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
        """
        self.config_manager = config_manager
        self.scraper_config = config_manager.get_scraper_config()
        self.ddg_config = self.scraper_config["duckduckgo"]
        
        # セッションを作成
        self.session = requests.Session()
        
        # User-Agent管理
        if HAS_FAKE_USERAGENT:
            self.ua = UserAgent()
        else:
            self.ua = None
        self.user_agents = self.ddg_config["user_agents"]
        
        # レート制限管理
        self.last_request_time = 0
        self.rate_limit = self.ddg_config["rate_limit"]
        
        logger.info("DuckDuckGoスクレイパーを初期化")
    
    def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        DuckDuckGo検索を実行
        
        Args:
            query: 検索クエリ
            max_results: 最大取得結果数
            
        Returns:
            検索結果のリスト
            
        Raises:
            ScraperError: スクレイピングエラー時
            NetworkError: ネットワークエラー時
        """
        try:
            # レート制限チェック
            self._enforce_rate_limit()
            
            # 検索URLを生成
            search_url = self._build_search_url(query)
            
            # リクエストヘッダーを設定
            headers = self._get_request_headers()
            
            logger.info(f"DuckDuckGo検索開始: '{query}' -> {search_url}")
            
            # リクエスト実行
            response = self._make_request(search_url, headers)
            
            # HTMLをパース
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 検索結果を抽出
            results = self._extract_search_results(soup, max_results)
            
            logger.info(f"DuckDuckGo検索完了: {len(results)}件の結果を取得")
            return results
            
        except Exception as e:
            logger.error(f"DuckDuckGo検索エラー: {str(e)}")
            raise ScraperError(f"DuckDuckGo検索に失敗しました: {str(e)}")
    
    def _build_search_url(self, query: str) -> str:
        """
        検索URLを構築
        
        Args:
            query: 検索クエリ
            
        Returns:
            検索URL
        """
        base_url = self.ddg_config["base_url"]
        
        # クエリパラメータ
        params = {
            'q': query
        }
        
        search_url = f"{base_url}?{urlencode(params)}"
        logger.debug(f"DuckDuckGo検索URL生成: {search_url}")
        return search_url
    
    def _get_request_headers(self) -> Dict[str, str]:
        """
        リクエストヘッダーを取得
        
        Returns:
            リクエストヘッダー辞書
        """
        # ランダムにUser-Agentを選択
        user_agent = random.choice(self.user_agents)
        
        headers = self.ddg_config["headers"].copy()
        headers["User-Agent"] = user_agent
        
        logger.debug(f"User-Agent設定: {user_agent}")
        return headers
    
    def _make_request(self, url: str, headers: Dict[str, str]) -> requests.Response:
        """
        HTTP リクエストを実行
        
        Args:
            url: リクエストURL
            headers: リクエストヘッダー
            
        Returns:
            レスポンスオブジェクト
            
        Raises:
            NetworkError: ネットワークエラー時
        """
        for attempt in range(self.rate_limit["retry_attempts"]):
            try:
                # Accept-Encodingを除去してデコーディング問題を回避
                headers_for_request = headers.copy()
                if 'Accept-Encoding' in headers_for_request:
                    del headers_for_request['Accept-Encoding']
                
                response = self.session.get(
                    url,
                    headers=headers_for_request,
                    timeout=30,
                    allow_redirects=True
                )
                
                # レスポンスのエンコーディングを明示的に設定
                response.encoding = response.apparent_encoding or 'utf-8'
                
                # ステータスコードチェック
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:
                    # Too Many Requests - レート制限に引っかかった
                    wait_time = self.rate_limit["retry_delay"] * (attempt + 1)
                    logger.warning(f"レート制限検出、{wait_time}秒待機 (試行{attempt + 1})")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.warning(f"HTTP エラー {response.status_code}: {url}")
                    if attempt < self.rate_limit["retry_attempts"] - 1:
                        time.sleep(self.rate_limit["retry_delay"])
                        continue
                    else:
                        raise NetworkError(f"HTTP {response.status_code}: {response.reason}")
                        
            except requests.exceptions.Timeout:
                logger.warning(f"リクエストタイムアウト (試行{attempt + 1}): {url}")
                if attempt < self.rate_limit["retry_attempts"] - 1:
                    time.sleep(self.rate_limit["retry_delay"])
                    continue
                else:
                    raise NetworkError("リクエストがタイムアウトしました")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"リクエストエラー (試行{attempt + 1}): {str(e)}")
                if attempt < self.rate_limit["retry_attempts"] - 1:
                    time.sleep(self.rate_limit["retry_delay"])
                    continue
                else:
                    raise NetworkError(f"ネットワークエラー: {str(e)}")
        
        raise NetworkError("最大リトライ回数に達しました")
    
    def _extract_search_results(self, soup: BeautifulSoup, max_results: int) -> List[Dict[str, Any]]:
        """
        検索結果をHTMLから抽出
        
        Args:
            soup: BeautifulSoupオブジェクト
            max_results: 最大取得結果数
            
        Returns:
            検索結果のリスト
        """
        results = []
        selectors = self.ddg_config["selectors"]
        
        # 検索結果要素を取得
        result_elements = soup.select(selectors["result_item"])
        
        logger.debug(f"DuckDuckGo検索結果要素数: {len(result_elements)}")
        
        for i, element in enumerate(result_elements[:max_results]):
            try:
                logger.debug(f"要素 {i+1} を処理中...")
                
                # タイトルを抽出
                title_element = element.select_one(selectors["title"])
                title = title_element.get_text(strip=True) if title_element else "タイトルなし"
                logger.debug(f"タイトル: {title}")
                
                # URLを抽出（DuckDuckGoのプロキシURLを処理）
                url_element = element.select_one(selectors["url"])
                if url_element:
                    href = url_element.get('href', '')
                    logger.debug(f"元のhref: {href}")
                    
                    # DuckDuckGoプロキシURLから実際のURLを抽出
                    if href.startswith('//duckduckgo.com/l/?uddg='):
                        import urllib.parse
                        # uddgパラメータから実際のURLを取得
                        try:
                            # スキームを追加してパース
                            full_url = f"https:{href}"
                            parsed_url = urllib.parse.urlparse(full_url)
                            query_params = urllib.parse.parse_qs(parsed_url.query)
                            if 'uddg' in query_params:
                                url = urllib.parse.unquote(query_params['uddg'][0])
                                logger.debug(f"抽出されたURL: {url}")
                            else:
                                url = href
                        except Exception as parse_error:
                            logger.warning(f"URL抽出エラー: {parse_error}")
                            url = href
                    else:
                        url = href
                else:
                    url = ""
                    logger.debug("URL要素が見つかりませんでした")
                
                # スニペットを抽出
                snippet_element = element.select_one(selectors["snippet"])
                snippet = snippet_element.get_text(strip=True) if snippet_element else "内容なし"
                logger.debug(f"スニペット: {snippet[:50]}...")
                
                # 結果を構造化
                result = {
                    'title': title,
                    'url': url,
                    'snippet': snippet,
                    'source': 'duckduckgo'
                }
                
                # 有効な結果のみ追加
                if title and title != "タイトルなし" and len(title) > 10:
                    results.append(result)
                    logger.info(f"DuckDuckGo検索結果追加: {title[:50]}...")
                else:
                    logger.debug(f"無効な結果をスキップ: タイトル='{title}'")
                
            except Exception as e:
                logger.warning(f"DuckDuckGo検索結果パースエラー: {str(e)}")
                continue
        
        return results
    
    def _enforce_rate_limit(self) -> None:
        """
        レート制限を適用
        """
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        min_interval = 1.0 / self.rate_limit["requests_per_second"]
        
        if time_since_last_request < min_interval:
            sleep_time = min_interval - time_since_last_request
            logger.debug(f"レート制限待機: {sleep_time:.2f}秒")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def test_connection(self) -> bool:
        """
        DuckDuckGo接続テスト
        
        Returns:
            接続成功時True
        """
        try:
            test_results = self.search("test", max_results=1)
            logger.info("DuckDuckGo接続テスト成功")
            return len(test_results) >= 0  # 結果が0件でも接続は成功
        except Exception as e:
            logger.error(f"DuckDuckGo接続テスト失敗: {str(e)}")
            return False