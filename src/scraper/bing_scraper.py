"""
Bing検索スクレイパー
"""
import logging
import time
import random
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, quote_plus
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


class BingScraper:
    """Bing検索スクレイパークラス"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
        """
        self.config_manager = config_manager
        self.scraper_config = config_manager.get_scraper_config()
        self.bing_config = self.scraper_config["bing"]
        
        # セッションを作成
        self.session = requests.Session()
        
        # User-Agent管理
        if HAS_FAKE_USERAGENT:
            self.ua = UserAgent()
        else:
            self.ua = None
        self.user_agents = self.bing_config["user_agents"]
        
        # レート制限管理
        self.last_request_time = 0
        self.rate_limit = self.bing_config["rate_limit"]
        
        logger.info("Bingスクレイパーを初期化")
    
    def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Bing検索を実行
        
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
            
            logger.info(f"Bing検索開始: '{query}' -> {search_url}")
            
            # リクエスト実行
            response = self._make_request(search_url, headers)
            
            # HTMLをパース
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 検索結果を抽出
            results = self._extract_search_results(soup, max_results)
            
            logger.info(f"Bing検索完了: {len(results)}件の結果を取得")
            return results
            
        except Exception as e:
            logger.error(f"Bing検索エラー: {str(e)}")
            raise ScraperError(f"Bing検索に失敗しました: {str(e)}")
    
    def _build_search_url(self, query: str) -> str:
        """
        検索URLを構築
        
        Args:
            query: 検索クエリ
            
        Returns:
            検索URL
        """
        base_url = self.bing_config["base_url"]
        
        # クエリパラメータ
        params = {
            'q': query,
            'count': '20',  # 多めに取得して後でフィルタリング
            'offset': '0',
            'mkt': 'ja-JP',  # 日本語市場
            'setlang': 'ja'  # 日本語設定
        }
        
        search_url = f"{base_url}?{urlencode(params)}"
        logger.debug(f"検索URL生成: {search_url}")
        return search_url
    
    def _get_request_headers(self) -> Dict[str, str]:
        """
        リクエストヘッダーを取得
        
        Returns:
            リクエストヘッダー辞書
        """
        # ランダムにUser-Agentを選択
        user_agent = random.choice(self.user_agents)
        
        headers = self.bing_config["headers"].copy()
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
                response = self.session.get(
                    url,
                    headers=headers,
                    timeout=30,
                    allow_redirects=True
                )
                
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
        selectors = self.bing_config["selectors"]
        
        # 従来のセレクターを試す
        result_elements = soup.select(selectors["result_item"])
        logger.debug(f"従来セレクター {selectors['result_item']}: {len(result_elements)}件")
        
        # 従来のセレクターで結果が得られない場合、フォールバックを使用
        if not result_elements and "fallback_selectors" in selectors:
            logger.info("従来セレクターで結果なし、フォールバック方式を使用")
            return self._extract_fallback_results(soup, max_results)
        
        # 従来の方式で結果を抽出
        for element in result_elements[:max_results]:
            try:
                # タイトルを抽出
                title_element = element.select_one(selectors["title"])
                title = title_element.get_text(strip=True) if title_element else "タイトルなし"
                
                # URLを抽出
                url_element = element.select_one(selectors["url"])
                url = url_element.get('href') if url_element else ""
                
                # スニペットを抽出
                snippet_element = element.select_one(selectors["snippet"])
                snippet = snippet_element.get_text(strip=True) if snippet_element else "内容なし"
                
                # 結果を構造化
                result = {
                    'title': title,
                    'url': url,
                    'snippet': snippet,
                    'source': 'bing'
                }
                
                # 有効な結果のみ追加
                if title and title != "タイトルなし":
                    results.append(result)
                    logger.debug(f"検索結果追加: {title[:50]}...")
                
            except Exception as e:
                logger.warning(f"検索結果パースエラー: {str(e)}")
                continue
        
        return results
    
    def _extract_fallback_results(self, soup: BeautifulSoup, max_results: int) -> List[Dict[str, Any]]:
        """
        フォールバック方式で検索結果を抽出
        
        Args:
            soup: BeautifulSoupオブジェクト
            max_results: 最大取得結果数
            
        Returns:
            検索結果のリスト
        """
        results = []
        selectors = self.bing_config["selectors"]["fallback_selectors"]
        
        # 外部リンクを直接探す
        external_links = soup.select(selectors["external_links"])
        logger.debug(f"外部リンク数: {len(external_links)}")
        
        seen_urls = set()
        
        for link in external_links[:max_results * 2]:  # 多めに取得してフィルタリング
            try:
                href = link.get('href', '')
                title = link.get_text(strip=True)
                
                # 重複URLや短すぎるタイトルをスキップ
                if not href or href in seen_urls or not title or len(title) < 10:
                    continue
                
                seen_urls.add(href)
                
                # 周辺要素からスニペットを取得
                snippet = self._extract_snippet_from_context(link)
                
                result = {
                    'title': title,
                    'url': href,
                    'snippet': snippet or "説明なし",
                    'source': 'bing_fallback'
                }
                
                results.append(result)
                logger.debug(f"フォールバック結果追加: {title[:50]}...")
                
                if len(results) >= max_results:
                    break
                    
            except Exception as e:
                logger.warning(f"フォールバック結果パースエラー: {str(e)}")
                continue
        
        return results
    
    def _extract_snippet_from_context(self, link_element) -> str:
        """
        リンク要素の周辺からスニペットを抽出
        
        Args:
            link_element: リンク要素
            
        Returns:
            スニペット文字列
        """
        try:
            # 親要素を辿ってテキストを探す
            current = link_element.parent
            max_depth = 3
            depth = 0
            
            while current and depth < max_depth:
                # 同じ親要素内のテキストを探す
                text_elements = current.find_all(['p', 'span', 'div'], string=True)
                
                for elem in text_elements:
                    text = elem.get_text(strip=True)
                    # 適度な長さのテキストを見つけたら使用
                    if 20 <= len(text) <= 200:
                        return text
                
                current = current.parent
                depth += 1
            
            return ""
            
        except Exception as e:
            logger.warning(f"スニペット抽出エラー: {str(e)}")
            return ""
    
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
        Bing接続テスト
        
        Returns:
            接続成功時True
        """
        try:
            test_results = self.search("test", max_results=1)
            logger.info("Bing接続テスト成功")
            return len(test_results) >= 0  # 結果が0件でも接続は成功
        except Exception as e:
            logger.error(f"Bing接続テスト失敗: {str(e)}")
            return False