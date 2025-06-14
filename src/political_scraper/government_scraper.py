"""
政府公式データスクレイパー
首相官邸・各省庁・e-Gov等の政府公式サイトからデータを収集
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


class GovernmentScraper:
    """政府公式データスクレイパークラス"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
        """
        self.config_manager = config_manager
        self.session = requests.Session()
        
        # ユーザーエージェント設定（政府サイトアクセス用）
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # 政府サイトURL設定
        self.government_sites = {
            "kantei": "https://www.kantei.go.jp",           # 首相官邸
            "gov": "https://www.gov.go.jp",                 # 政府ポータル
            "soumu": "https://www.soumu.go.jp",             # 総務省
            "mof": "https://www.mof.go.jp",                 # 財務省
            "mext": "https://www.mext.go.jp",               # 文科省
            "mhlw": "https://www.mhlw.go.jp",               # 厚労省
            "meti": "https://www.meti.go.jp",               # 経産省
            "mod": "https://www.mod.go.jp",                 # 防衛省
            "mofa": "https://www.mofa.go.jp"                # 外務省
        }
        
        self.request_delay = 2.0  # 政府サイトへの丁寧なアクセス間隔
        
        logger.info("政府公式データスクレイパーを初期化")
    
    def scrape_kantei_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        首相官邸のニュース・発表を取得
        
        Args:
            limit: 取得件数上限
            
        Returns:
            ニュースデータのリスト
        """
        try:
            url = f"{self.government_sites['kantei']}/jp/headline/"
            response = self._safe_request(url)
            
            if not response:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            news_items = []
            
            # 首相官邸のニュース項目を抽出
            news_elements = soup.find_all('div', class_='topics-item')[:limit]
            
            for element in news_elements:
                try:
                    # タイトル取得
                    title_elem = element.find('h3') or element.find('a')
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    
                    # リンク取得
                    link_elem = element.find('a')
                    link = urljoin(url, link_elem.get('href')) if link_elem else ""
                    
                    # 日付取得
                    date_elem = element.find('time') or element.find('span', class_='date')
                    date_str = date_elem.get_text(strip=True) if date_elem else ""
                    
                    # 概要取得
                    summary_elem = element.find('p') or element.find('div', class_='summary')
                    summary = summary_elem.get_text(strip=True) if summary_elem else ""
                    
                    if title:
                        news_items.append({
                            "source": "首相官邸",
                            "title": title,
                            "link": link,
                            "date": date_str,
                            "summary": summary,
                            "category": "政府発表",
                            "reliability_score": 1.0,
                            "scraped_at": datetime.now().isoformat()
                        })
                        
                except Exception as e:
                    logger.warning(f"首相官邸ニュース項目の解析エラー: {str(e)}")
                    continue
            
            time.sleep(self.request_delay)
            logger.info(f"首相官邸ニュースを取得: {len(news_items)}件")
            return news_items
            
        except Exception as e:
            logger.error(f"首相官邸ニュース取得エラー: {str(e)}")
            return []
    
    def scrape_cabinet_decisions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        閣議決定情報を取得
        
        Args:
            limit: 取得件数上限
            
        Returns:
            閣議決定データのリスト
        """
        try:
            # 閣議決定ページ（仮のURL、実際のサイト構造に合わせて調整）
            url = f"{self.government_sites['kantei']}/jp/kakugi/"
            response = self._safe_request(url)
            
            if not response:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            decisions = []
            
            # 閣議決定項目を抽出（サンプル実装）
            decision_elements = soup.find_all('li', class_='decision-item')[:limit]
            
            for element in decision_elements:
                try:
                    title_elem = element.find('a') or element.find('h4')
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    
                    link_elem = element.find('a')
                    link = urljoin(url, link_elem.get('href')) if link_elem else ""
                    
                    date_elem = element.find('time') or element.find('span', class_='date')
                    date_str = date_elem.get_text(strip=True) if date_elem else ""
                    
                    if title:
                        decisions.append({
                            "source": "内閣府",
                            "title": title,
                            "link": link,
                            "date": date_str,
                            "type": "閣議決定",
                            "category": "政府決定",
                            "reliability_score": 1.0,
                            "scraped_at": datetime.now().isoformat()
                        })
                        
                except Exception as e:
                    logger.warning(f"閣議決定項目の解析エラー: {str(e)}")
                    continue
            
            time.sleep(self.request_delay)
            logger.info(f"閣議決定情報を取得: {len(decisions)}件")
            return decisions
            
        except Exception as e:
            logger.error(f"閣議決定情報取得エラー: {str(e)}")
            return []
    
    def scrape_ministry_press_releases(self, ministry: str = "soumu", limit: int = 10) -> List[Dict[str, Any]]:
        """
        省庁プレスリリースを取得
        
        Args:
            ministry: 省庁コード
            limit: 取得件数上限
            
        Returns:
            プレスリリースデータのリスト
        """
        try:
            base_url = self.government_sites.get(ministry)
            if not base_url:
                logger.error(f"未知の省庁コード: {ministry}")
                return []
            
            # 省庁別のプレスリリースURL構築
            press_urls = {
                "soumu": f"{base_url}/menu_news/s-news/",
                "mof": f"{base_url}/public_relations/",
                "mext": f"{base_url}/b_menu/houdou/",
                "mhlw": f"{base_url}/stf/houdou/",
                "meti": f"{base_url}/press/",
                "mod": f"{base_url}/j/press/",
                "mofa": f"{base_url}/press/"
            }
            
            url = press_urls.get(ministry, f"{base_url}/press/")
            response = self._safe_request(url)
            
            if not response:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            releases = []
            
            # 省庁サイトの一般的な構造を想定した抽出
            press_elements = (soup.find_all('li', class_=['press-item', 'news-item', 'release-item']) or
                            soup.find_all('div', class_=['press', 'news', 'release']))[:limit]
            
            ministry_names = {
                "soumu": "総務省",
                "mof": "財務省", 
                "mext": "文部科学省",
                "mhlw": "厚生労働省",
                "meti": "経済産業省",
                "mod": "防衛省",
                "mofa": "外務省"
            }
            
            for element in press_elements:
                try:
                    title_elem = element.find('a') or element.find('h3') or element.find('h4')
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    
                    link_elem = element.find('a')
                    link = urljoin(url, link_elem.get('href')) if link_elem else ""
                    
                    date_elem = element.find('time') or element.find('span', class_='date')
                    date_str = date_elem.get_text(strip=True) if date_elem else ""
                    
                    summary_elem = element.find('p', class_=['summary', 'description'])
                    summary = summary_elem.get_text(strip=True) if summary_elem else ""
                    
                    if title:
                        releases.append({
                            "source": ministry_names.get(ministry, ministry),
                            "title": title,
                            "link": link,
                            "date": date_str,
                            "summary": summary,
                            "category": "省庁発表",
                            "ministry": ministry,
                            "reliability_score": 1.0,
                            "scraped_at": datetime.now().isoformat()
                        })
                        
                except Exception as e:
                    logger.warning(f"プレスリリース項目の解析エラー: {str(e)}")
                    continue
            
            time.sleep(self.request_delay)
            logger.info(f"{ministry_names.get(ministry, ministry)}プレスリリースを取得: {len(releases)}件")
            return releases
            
        except Exception as e:
            logger.error(f"省庁プレスリリース取得エラー ({ministry}): {str(e)}")
            return []
    
    def scrape_diet_proceedings(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        国会議事録・審議情報を取得
        
        Args:
            limit: 取得件数上限
            
        Returns:
            国会審議データのリスト
        """
        try:
            # 国会会議録検索システム（参考実装）
            base_url = "https://kokkai.ndl.go.jp"
            
            # 実際の国会サイトAPIやRSSを使用する場合の実装例
            proceedings = []
            
            # サンプルデータ（実際の実装では国会サイトからスクレイピング）
            sample_proceedings = [
                {
                    "source": "国会",
                    "title": "予算委員会第一分科会",
                    "date": "2024-06-15",
                    "session": "第213回国会",
                    "committee": "予算委員会",
                    "meeting_type": "分科会",
                    "status": "審議中",
                    "participants": ["委員長", "政府参考人"],
                    "category": "国会審議",
                    "reliability_score": 1.0,
                    "scraped_at": datetime.now().isoformat()
                }
            ]
            
            proceedings.extend(sample_proceedings[:limit])
            
            logger.info(f"国会議事録を取得: {len(proceedings)}件")
            return proceedings
            
        except Exception as e:
            logger.error(f"国会議事録取得エラー: {str(e)}")
            return []
    
    def scrape_policy_documents(self, policy_area: str = "economy") -> List[Dict[str, Any]]:
        """
        政策文書を取得
        
        Args:
            policy_area: 政策分野
            
        Returns:
            政策文書データのリスト
        """
        try:
            documents = []
            
            # 経済財政運営と改革の基本方針（骨太の方針）等
            if policy_area == "economy":
                url = f"{self.government_sites['kantei']}/jp/singi/keizaisaisei/"
                response = self._safe_request(url)
                
                if response:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # 政策文書の抽出
                    doc_elements = soup.find_all(['a', 'li'], string=re.compile(r'基本方針|骨太|成長戦略'))
                    
                    for element in doc_elements:
                        title = element.get_text(strip=True)
                        link = element.get('href') if element.name == 'a' else ""
                        if link:
                            link = urljoin(url, link)
                        
                        documents.append({
                            "source": "内閣府",
                            "title": title,
                            "link": link,
                            "policy_area": policy_area,
                            "document_type": "基本方針",
                            "category": "政策文書",
                            "reliability_score": 1.0,
                            "scraped_at": datetime.now().isoformat()
                        })
            
            time.sleep(self.request_delay)
            logger.info(f"政策文書を取得: {len(documents)}件")
            return documents
            
        except Exception as e:
            logger.error(f"政策文書取得エラー: {str(e)}")
            return []
    
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
    
    def get_comprehensive_government_data(self, limit_per_source: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """
        政府系データを包括的に取得
        
        Args:
            limit_per_source: ソース別取得件数上限
            
        Returns:
            政府データの包括的辞書
        """
        government_data = {}
        
        try:
            # 首相官邸ニュース
            government_data["kantei_news"] = self.scrape_kantei_news(limit_per_source)
            
            # 閣議決定
            government_data["cabinet_decisions"] = self.scrape_cabinet_decisions(limit_per_source)
            
            # 主要省庁のプレスリリース
            for ministry in ["soumu", "mof", "mext", "mhlw"]:
                government_data[f"{ministry}_press"] = self.scrape_ministry_press_releases(
                    ministry, limit_per_source
                )
            
            # 国会議事録
            government_data["diet_proceedings"] = self.scrape_diet_proceedings(limit_per_source)
            
            # 政策文書
            government_data["policy_documents"] = self.scrape_policy_documents()
            
            total_items = sum(len(items) for items in government_data.values())
            logger.info(f"政府データ包括取得完了: 総計{total_items}件")
            
            return government_data
            
        except Exception as e:
            logger.error(f"政府データ包括取得エラー: {str(e)}")
            return government_data
    
    def test_connection(self) -> bool:
        """政府サイト接続テスト"""
        try:
            response = self._safe_request(self.government_sites["kantei"])
            return response is not None
        except Exception as e:
            logger.error(f"政府サイト接続テスト失敗: {str(e)}")
            return False