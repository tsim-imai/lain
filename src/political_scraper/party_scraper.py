"""
政党公式データスクレイパー
主要政党の公式サイト・SNSから政策・発言・ニュースを収集
"""
import logging
import requests
import time
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urljoin, urlparse
import re

from ..utils.config import ConfigManager
from ..utils.exceptions import ScraperError

logger = logging.getLogger(__name__)


class PartyScraper:
    """政党公式データスクレイパークラス"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
        """
        self.config_manager = config_manager
        self.session = requests.Session()
        
        # ユーザーエージェント設定
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive'
        })
        
        # 主要政党の公式サイトURL
        self.party_sites = {
            "自由民主党": {
                "base_url": "https://www.jimin.jp",
                "news_path": "/news/",
                "policy_path": "/policy/",
                "ideology_score": 0.6
            },
            "立憲民主党": {
                "base_url": "https://cdp-japan.jp",
                "news_path": "/news/",
                "policy_path": "/policies/",
                "ideology_score": -0.4
            },
            "日本維新の会": {
                "base_url": "https://o-ishin.jp",
                "news_path": "/news/",
                "policy_path": "/policy/",
                "ideology_score": 0.3
            },
            "公明党": {
                "base_url": "https://www.komei.or.jp",
                "news_path": "/news/",
                "policy_path": "/policy/",
                "ideology_score": 0.2
            },
            "日本共産党": {
                "base_url": "https://www.jcp.or.jp",
                "news_path": "/web_info/",
                "policy_path": "/web_policy/",
                "ideology_score": -0.8
            },
            "国民民主党": {
                "base_url": "https://new-kokumin.jp",
                "news_path": "/news/",
                "policy_path": "/policy/",
                "ideology_score": -0.1
            },
            "れいわ新選組": {
                "base_url": "https://reiwa-shinsengumi.com",
                "news_path": "/news/",
                "policy_path": "/policy/",
                "ideology_score": -0.7
            },
            "社会民主党": {
                "base_url": "https://sdp.or.jp",
                "news_path": "/news/",
                "policy_path": "/policy/",
                "ideology_score": -0.6
            }
        }
        
        self.request_delay = 2.0  # 政党サイトへの丁寧なアクセス間隔
        
        logger.info("政党公式データスクレイパーを初期化")
    
    def scrape_party_news(self, party_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        政党ニュースを取得
        
        Args:
            party_name: 政党名
            limit: 取得件数上限
            
        Returns:
            政党ニュースデータのリスト
        """
        try:
            party_info = self.party_sites.get(party_name)
            if not party_info:
                logger.warning(f"未対応の政党: {party_name}")
                return []
            
            base_url = party_info["base_url"]
            news_url = urljoin(base_url, party_info["news_path"])
            
            response = self._safe_request(news_url)
            if not response:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            news_items = []
            
            # 政党サイトの一般的な構造を想定した抽出
            news_elements = self._extract_news_elements(soup, party_name)
            
            for element in news_elements[:limit]:
                try:
                    news_item = self._parse_news_element(element, news_url, party_name, party_info)
                    if news_item:
                        news_items.append(news_item)
                        
                except Exception as e:
                    logger.warning(f"政党ニュース項目の解析エラー ({party_name}): {str(e)}")
                    continue
            
            time.sleep(self.request_delay)
            logger.info(f"{party_name}ニュースを取得: {len(news_items)}件")
            return news_items
            
        except Exception as e:
            logger.error(f"政党ニュース取得エラー ({party_name}): {str(e)}")
            return []
    
    def scrape_party_policies(self, party_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        政党政策を取得
        
        Args:
            party_name: 政党名
            limit: 取得件数上限
            
        Returns:
            政党政策データのリスト
        """
        try:
            party_info = self.party_sites.get(party_name)
            if not party_info:
                logger.warning(f"未対応の政党: {party_name}")
                return []
            
            base_url = party_info["base_url"]
            policy_url = urljoin(base_url, party_info["policy_path"])
            
            response = self._safe_request(policy_url)
            if not response:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            policies = []
            
            # 政策項目の抽出
            policy_elements = self._extract_policy_elements(soup, party_name)
            
            for element in policy_elements[:limit]:
                try:
                    policy_item = self._parse_policy_element(element, policy_url, party_name, party_info)
                    if policy_item:
                        policies.append(policy_item)
                        
                except Exception as e:
                    logger.warning(f"政党政策項目の解析エラー ({party_name}): {str(e)}")
                    continue
            
            time.sleep(self.request_delay)
            logger.info(f"{party_name}政策を取得: {len(policies)}件")
            return policies
            
        except Exception as e:
            logger.error(f"政党政策取得エラー ({party_name}): {str(e)}")
            return []
    
    def scrape_party_statements(self, party_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        政党声明・談話を取得
        
        Args:
            party_name: 政党名
            limit: 取得件数上限
            
        Returns:
            政党声明データのリスト
        """
        try:
            party_info = self.party_sites.get(party_name)
            if not party_info:
                logger.warning(f"未対応の政党: {party_name}")
                return []
            
            base_url = party_info["base_url"]
            
            # 声明・談話ページを探索
            statement_paths = ["/statement/", "/comment/", "/danwa/", "/seimei/"]
            statements = []
            
            for path in statement_paths:
                statement_url = urljoin(base_url, path)
                response = self._safe_request(statement_url)
                
                if response and response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # 声明項目を抽出
                    statement_elements = soup.find_all(['div', 'li', 'article'], 
                                                     class_=re.compile(r'statement|comment|danwa|seimei'))
                    
                    for element in statement_elements:
                        try:
                            title_elem = element.find(['h2', 'h3', 'h4', 'a'])
                            title = title_elem.get_text(strip=True) if title_elem else ""
                            
                            link_elem = element.find('a')
                            link = urljoin(statement_url, link_elem.get('href')) if link_elem else ""
                            
                            date_elem = element.find(['time', 'span'], class_=re.compile(r'date'))
                            date_str = date_elem.get_text(strip=True) if date_elem else ""
                            
                            if title and len(statements) < limit:
                                statements.append({
                                    "source": party_name,
                                    "title": title,
                                    "link": link,
                                    "date": date_str,
                                    "type": "党声明",
                                    "category": "政党声明",
                                    "ideology_score": party_info["ideology_score"],
                                    "reliability_score": 0.9,
                                    "scraped_at": datetime.now().isoformat()
                                })
                                
                        except Exception as e:
                            logger.warning(f"声明項目解析エラー: {str(e)}")
                            continue
                
                time.sleep(self.request_delay)
                
                if len(statements) >= limit:
                    break
            
            logger.info(f"{party_name}声明を取得: {len(statements)}件")
            return statements[:limit]
            
        except Exception as e:
            logger.error(f"政党声明取得エラー ({party_name}): {str(e)}")
            return []
    
    def _extract_news_elements(self, soup: BeautifulSoup, party_name: str) -> List:
        """ニュース要素を抽出"""
        # 一般的なニュース要素のクラス名で検索
        news_selectors = [
            'div.news-item', 'li.news-item', 'article.news',
            'div.post', 'li.post', 'article.post',
            'div.entry', 'li.entry', 'article.entry',
            'div[class*="news"]', 'li[class*="news"]',
            'div[class*="information"]', 'li[class*="information"]'
        ]
        
        for selector in news_selectors:
            elements = soup.select(selector)
            if elements:
                return elements
        
        # フォールバック: 記事やリンクを含む要素
        return soup.find_all(['article', 'div', 'li'], 
                           limit=20)  # 過度な取得を防ぐ
    
    def _extract_policy_elements(self, soup: BeautifulSoup, party_name: str) -> List:
        """政策要素を抽出"""
        policy_selectors = [
            'div.policy-item', 'li.policy-item', 'article.policy',
            'div[class*="policy"]', 'li[class*="policy"]',
            'div[class*="manifesto"]', 'li[class*="manifesto"]',
            'div.manifesto-item', 'li.manifesto-item'
        ]
        
        for selector in policy_selectors:
            elements = soup.select(selector)
            if elements:
                return elements
        
        # フォールバック
        return soup.find_all(['div', 'li', 'section'], 
                           limit=15)
    
    def _parse_news_element(self, element, base_url: str, party_name: str, party_info: Dict) -> Optional[Dict[str, Any]]:
        """ニュース要素を解析"""
        try:
            # タイトル取得
            title_elem = (element.find(['h1', 'h2', 'h3', 'h4', 'h5']) or 
                         element.find('a') or 
                         element.find(class_=re.compile(r'title|headline')))
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # リンク取得
            link_elem = element.find('a')
            link = urljoin(base_url, link_elem.get('href')) if link_elem else ""
            
            # 日付取得
            date_elem = (element.find('time') or 
                        element.find(class_=re.compile(r'date|time')) or
                        element.find('span', string=re.compile(r'\\d{4}[/-]\\d{1,2}[/-]\\d{1,2}')))
            date_str = date_elem.get_text(strip=True) if date_elem else ""
            
            # 概要取得
            summary_elem = (element.find('p') or 
                          element.find(class_=re.compile(r'summary|excerpt|description')))
            summary = summary_elem.get_text(strip=True) if summary_elem else ""
            
            if title:
                return {
                    "source": party_name,
                    "title": title,
                    "link": link,
                    "date": date_str,
                    "summary": summary,
                    "category": "政党ニュース",
                    "ideology_score": party_info["ideology_score"],
                    "reliability_score": 0.85,
                    "scraped_at": datetime.now().isoformat()
                }
            
            return None
            
        except Exception as e:
            logger.warning(f"ニュース要素解析エラー: {str(e)}")
            return None
    
    def _parse_policy_element(self, element, base_url: str, party_name: str, party_info: Dict) -> Optional[Dict[str, Any]]:
        """政策要素を解析"""
        try:
            # タイトル取得
            title_elem = (element.find(['h1', 'h2', 'h3', 'h4', 'h5']) or 
                         element.find('a') or
                         element.find(class_=re.compile(r'title|headline|policy-name')))
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # リンク取得
            link_elem = element.find('a')
            link = urljoin(base_url, link_elem.get('href')) if link_elem else ""
            
            # 政策分野を推定
            policy_category = self._categorize_policy(title)
            
            # 説明取得
            description_elem = (element.find('p') or 
                              element.find(class_=re.compile(r'description|summary|content')))
            description = description_elem.get_text(strip=True) if description_elem else ""
            
            if title:
                return {
                    "source": party_name,
                    "title": title,
                    "link": link,
                    "description": description,
                    "policy_category": policy_category,
                    "category": "政党政策",
                    "ideology_score": party_info["ideology_score"],
                    "reliability_score": 0.9,
                    "scraped_at": datetime.now().isoformat()
                }
            
            return None
            
        except Exception as e:
            logger.warning(f"政策要素解析エラー: {str(e)}")
            return None
    
    def _categorize_policy(self, title: str) -> str:
        """政策タイトルからカテゴリを推定"""
        categories = {
            "経済": ["経済", "税制", "財政", "予算", "成長", "雇用", "労働"],
            "社会保障": ["年金", "医療", "介護", "福祉", "子育て", "少子化"],
            "教育": ["教育", "学校", "大学", "奨学金", "学習"],
            "外交・安保": ["外交", "安全保障", "防衛", "平和", "憲法", "自衛隊"],
            "環境": ["環境", "脱炭素", "エネルギー", "原発", "再生可能"],
            "地方": ["地方", "地域", "都市", "農業", "農村", "過疎"],
            "デジタル": ["デジタル", "DX", "IT", "テクノロジー", "AI"],
            "その他": []
        }
        
        title_lower = title.lower()
        for category, keywords in categories.items():
            if any(keyword in title for keyword in keywords):
                return category
        
        return "その他"
    
    def get_all_party_news(self, limit_per_party: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """
        全政党のニュースを取得
        
        Args:
            limit_per_party: 政党別取得件数上限
            
        Returns:
            政党別ニュースデータ辞書
        """
        all_news = {}
        
        for party_name in self.party_sites.keys():
            try:
                party_news = self.scrape_party_news(party_name, limit_per_party)
                all_news[party_name] = party_news
                
                # 政党間でのアクセス間隔
                time.sleep(self.request_delay)
                
            except Exception as e:
                logger.error(f"全政党ニュース取得エラー ({party_name}): {str(e)}")
                all_news[party_name] = []
        
        total_items = sum(len(items) for items in all_news.values())
        logger.info(f"全政党ニュース取得完了: 総計{total_items}件")
        
        return all_news
    
    def get_comprehensive_party_data(self, party_name: str, limit: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """
        指定政党の包括的データを取得
        
        Args:
            party_name: 政党名
            limit: カテゴリ別取得件数上限
            
        Returns:
            政党データの包括的辞書
        """
        party_data = {}
        
        try:
            # ニュース
            party_data["news"] = self.scrape_party_news(party_name, limit)
            
            # 政策
            party_data["policies"] = self.scrape_party_policies(party_name, limit)
            
            # 声明
            party_data["statements"] = self.scrape_party_statements(party_name, limit)
            
            total_items = sum(len(items) for items in party_data.values())
            logger.info(f"{party_name}包括データ取得完了: 総計{total_items}件")
            
            return party_data
            
        except Exception as e:
            logger.error(f"政党包括データ取得エラー ({party_name}): {str(e)}")
            return party_data
    
    def _safe_request(self, url: str, timeout: int = 10) -> Optional[requests.Response]:
        """
        安全なHTTPリクエスト実行
        
        Args:
            url: リクエストURL
            timeout: タイムアウト秒数
            
        Returns:
            レスポンスオブジェクト
        """
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            
            # 文字エンコーディングを適切に設定
            if response.encoding is None or response.encoding == 'ISO-8859-1':
                response.encoding = 'utf-8'
            
            return response
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"リクエストエラー ({url}): {str(e)}")
            return None
        except Exception as e:
            logger.error(f"予期しないエラー ({url}): {str(e)}")
            return None
    
    def test_connection(self) -> bool:
        """政党サイト接続テスト"""
        try:
            # 自民党サイトでテスト
            test_url = self.party_sites["自由民主党"]["base_url"]
            response = self._safe_request(test_url)
            return response is not None
        except Exception as e:
            logger.error(f"政党サイト接続テスト失敗: {str(e)}")
            return False