#!/usr/bin/env python3
"""
URL個別スクレイパー
"""
import logging
import time
import random
import requests
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from ..utils.exceptions import ScraperError, NetworkError

logger = logging.getLogger(__name__)


class URLScraper:
    """個別URLスクレイパークラス"""
    
    def __init__(self):
        """初期化"""
        # セッションを作成
        self.session = requests.Session()
        
        # User-Agent リスト
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        # レート制限管理
        self.last_request_time = 0
        self.rate_limit_delay = 2.0  # 2秒間隔
        
        logger.info("URLスクレイパーを初期化")
    
    def scrape_url(self, url: str) -> Dict[str, Any]:
        """
        個別URLをスクレイピング
        
        Args:
            url: スクレイピング対象URL
            
        Returns:
            スクレイピング結果辞書
            
        Raises:
            ScraperError: スクレイピングエラー時
            NetworkError: ネットワークエラー時
        """
        try:
            # レート制限適用
            self._enforce_rate_limit()
            
            # リクエストヘッダーを設定
            headers = self._get_request_headers()
            
            logger.info(f"URL スクレイピング開始: {url}")
            
            # リクエスト実行
            response = self._make_request(url, headers)
            
            # HTMLをパース
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # コンテンツを抽出
            content = self._extract_content(soup, url)
            
            logger.info(f"URL スクレイピング完了: {url}")
            return content
            
        except Exception as e:
            logger.error(f"URL スクレイピングエラー: {url} - {str(e)}")
            raise ScraperError(f"URL スクレイピングに失敗しました: {str(e)}")
    
    def scrape_multiple_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        複数URLを順次スクレイピング
        
        Args:
            urls: スクレイピング対象URLリスト
            
        Returns:
            スクレイピング結果リスト
        """
        results = []
        
        for i, url in enumerate(urls, 1):
            try:
                logger.info(f"URL {i}/{len(urls)} をスクレイピング中...")
                content = self.scrape_url(url)
                results.append(content)
                
            except Exception as e:
                logger.warning(f"URL {i} のスクレイピングに失敗: {url} - {str(e)}")
                # エラーでも続行
                continue
        
        return results
    
    def _get_request_headers(self) -> Dict[str, str]:
        """リクエストヘッダーを取得"""
        user_agent = random.choice(self.user_agents)
        
        headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ja-JP,ja;q=0.9,en;q=0.8",
            "Accept-Encoding": "identity",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "no-cache"
        }
        
        return headers
    
    def _make_request(self, url: str, headers: Dict[str, str]) -> requests.Response:
        """HTTP リクエストを実行"""
        for attempt in range(3):  # 最大3回リトライ
            try:
                response = self.session.get(
                    url,
                    headers=headers,
                    timeout=30,
                    allow_redirects=True
                )
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:
                    # レート制限
                    wait_time = 5 * (attempt + 1)
                    logger.warning(f"レート制限検出、{wait_time}秒待機")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.warning(f"HTTP エラー {response.status_code}: {url}")
                    if attempt < 2:
                        time.sleep(2)
                        continue
                    else:
                        raise NetworkError(f"HTTP {response.status_code}: {response.reason}")
                        
            except requests.exceptions.Timeout:
                logger.warning(f"リクエストタイムアウト (試行{attempt + 1}): {url}")
                if attempt < 2:
                    time.sleep(2)
                    continue
                else:
                    raise NetworkError("リクエストがタイムアウトしました")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"リクエストエラー (試行{attempt + 1}): {str(e)}")
                if attempt < 2:
                    time.sleep(2)
                    continue
                else:
                    raise NetworkError(f"ネットワークエラー: {str(e)}")
        
        raise NetworkError("最大リトライ回数に達しました")
    
    def _extract_content(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """HTMLからコンテンツを抽出"""
        try:
            # 基本情報を抽出
            title = self._extract_title(soup)
            text_content = self._extract_text_content(soup)
            
            # メタデータを抽出
            meta_description = self._extract_meta_description(soup)
            
            # URL解析
            parsed_url = urlparse(url)
            domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            return {
                'url': url,
                'domain': domain,
                'title': title,
                'meta_description': meta_description,
                'text_content': text_content,
                'text_length': len(text_content),
                'scraped_at': time.time()
            }
            
        except Exception as e:
            logger.warning(f"コンテンツ抽出エラー: {str(e)}")
            return {
                'url': url,
                'domain': urlparse(url).netloc,
                'title': '',
                'meta_description': '',
                'text_content': '',
                'text_length': 0,
                'scraped_at': time.time(),
                'error': str(e)
            }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """タイトルを抽出"""
        # title タグから抽出
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text(strip=True)
        
        # h1 タグから抽出
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text(strip=True)
        
        return ""
    
    def _extract_meta_description(self, soup: BeautifulSoup) -> str:
        """メタディスクリプションを抽出"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            return meta_desc.get('content', '')
        
        # Open Graph description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc:
            return og_desc.get('content', '')
        
        return ""
    
    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """メインテキストコンテンツを抽出"""
        # 不要な要素を削除
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # メインコンテンツ候補を探す
        main_selectors = [
            'main',
            'article',
            '[role="main"]',
            '#main',
            '#content',
            '.content',
            '.main',
            '.article'
        ]
        
        for selector in main_selectors:
            main_element = soup.select_one(selector)
            if main_element:
                text = main_element.get_text(separator=' ', strip=True)
                if len(text) > 200:  # 十分な長さがあれば使用
                    return text
        
        # フォールバック: body全体から抽出
        body = soup.find('body')
        if body:
            return body.get_text(separator=' ', strip=True)
        
        # 最後の手段: 全体から抽出
        return soup.get_text(separator=' ', strip=True)
    
    def _enforce_rate_limit(self) -> None:
        """レート制限を適用"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            logger.debug(f"レート制限待機: {sleep_time:.2f}秒")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()