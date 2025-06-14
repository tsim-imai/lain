"""
メディア監視スクレイパー
主要メディア（NHK、朝日、読売、毎日、産経、日経等）から政治ニュースを収集
"""
import logging
import requests
import time
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
import re
# concurrent.futures を削除（シーケンシャル処理に変更）

from ..utils.config import ConfigManager
from ..utils.exceptions import ScraperError
from ..political_data.political_database import PoliticalDatabaseManager, PoliticalNews

logger = logging.getLogger(__name__)


class MediaScraper:
    """メディア監視スクレイパークラス"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初期化
        
        Args:
            config_manager: 設定管理インスタンス
        """
        self.config_manager = config_manager
        self.session = requests.Session()
        self.database = PoliticalDatabaseManager(config_manager)
        
        # ユーザーエージェント設定
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive'
        })
        
        # 主要メディアサイト設定
        self.media_sites = {
            "NHK": {
                "base_url": "https://www3.nhk.or.jp",
                "politics_path": "/news/html/20240615/k10014473711000.html",  # 政治セクション
                "rss_url": "https://www3.nhk.or.jp/rss/news/cat6.xml",
                "reliability_score": 0.95,
                "political_bias": 0.0,  # 中立
                "selectors": {
                    "title": "h1.content-title, h1.module-title",
                    "date": "time, .content-date, .module-date",
                    "content": ".content-body, .module-body, p",
                    "link": "a"
                }
            },
            "朝日新聞": {
                "base_url": "https://www.asahi.com",
                "politics_path": "/politics/",
                "reliability_score": 0.85,
                "political_bias": -0.3,  # やや左派
                "selectors": {
                    "title": "h1, h2.Title, .ArticleTitle",
                    "date": "time, .Date, .PublishDate",
                    "content": ".ArticleText, .Body, p",
                    "link": "a"
                }
            },
            "読売新聞": {
                "base_url": "https://www.yomiuri.co.jp",
                "politics_path": "/politics/",
                "reliability_score": 0.85,
                "political_bias": 0.2,  # やや右派
                "selectors": {
                    "title": "h1, h2.title, .article-header h1",
                    "date": "time, .date, .publish-time",
                    "content": ".article-body, .body, p",
                    "link": "a"
                }
            },
            "毎日新聞": {
                "base_url": "https://mainichi.jp",
                "politics_path": "/seiji/",
                "reliability_score": 0.8,
                "political_bias": -0.2,  # やや左派
                "selectors": {
                    "title": "h1, .articledetail-title, .news-title",
                    "date": "time, .date, .articledetail-date",
                    "content": ".articledetail-body, .article-body, p",
                    "link": "a"
                }
            },
            "産経新聞": {
                "base_url": "https://www.sankei.com",
                "politics_path": "/politics/",
                "reliability_score": 0.8,
                "political_bias": 0.4,  # 右派
                "selectors": {
                    "title": "h1, .article-title, .entry-title",
                    "date": "time, .date, .entry-date",
                    "content": ".article-body, .entry-content, p",
                    "link": "a"
                }
            },
            "日本経済新聞": {
                "base_url": "https://www.nikkei.com",
                "politics_path": "/politics/",
                "reliability_score": 0.85,
                "political_bias": 0.1,  # やや右派（経済寄り）
                "selectors": {
                    "title": "h1, .cmn-article_title, .k-article-title",
                    "date": "time, .cmn-article_date, .k-article-date",
                    "content": ".cmn-article_text, .k-article-text, p",
                    "link": "a"
                }
            },
            "共同通信": {
                "base_url": "https://www.kyodo.co.jp",
                "politics_path": "/politics/",
                "reliability_score": 0.9,
                "political_bias": 0.0,  # 中立
                "selectors": {
                    "title": "h1, .article-title",
                    "date": "time, .date",
                    "content": ".article-body, p",
                    "link": "a"
                }
            },
            "時事通信": {
                "base_url": "https://www.jiji.com",
                "politics_path": "/jc/c?g=pol",
                "reliability_score": 0.9,
                "political_bias": 0.0,  # 中立
                "selectors": {
                    "title": "h1, .ArticleTitle",
                    "date": "time, .ArticleDate",
                    "content": ".ArticleBody, p",
                    "link": "a"
                }
            }
        }
        
        # 政治専門メディア
        self.political_media = {
            "政治山": {
                "base_url": "https://seijiyama.jp",
                "reliability_score": 0.75,
                "political_bias": 0.0
            },
            "選挙ドットコム": {
                "base_url": "https://go2senkyo.com",
                "reliability_score": 0.8,
                "political_bias": 0.0
            }
        }
        
        self.request_delay = 1.5  # メディアサイトへのアクセス間隔
        
        logger.info("メディア監視スクレイパーを初期化")
    
    def scrape_media_politics(self, media_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        指定メディアの政治ニュースを取得
        
        Args:
            media_name: メディア名
            limit: 取得件数上限
            
        Returns:
            政治ニュースデータのリスト
        """
        try:
            media_info = self.media_sites.get(media_name)
            if not media_info:
                logger.warning(f"未対応のメディア: {media_name}")
                return []
            
            base_url = media_info["base_url"]
            politics_url = urljoin(base_url, media_info["politics_path"])
            
            response = self._safe_request(politics_url)
            if not response:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            # メディア固有の記事抽出
            article_elements = self._extract_articles(soup, media_name)
            
            for element in article_elements[:limit]:
                try:
                    article = self._parse_article(element, politics_url, media_name, media_info)
                    if article:
                        articles.append(article)
                        
                        # データベースに保存
                        self._save_article_to_db(article, media_info)
                        
                except Exception as e:
                    logger.warning(f"記事解析エラー ({media_name}): {str(e)}")
                    continue
            
            time.sleep(self.request_delay)
            logger.info(f"{media_name}政治ニュースを取得: {len(articles)}件")
            return articles
            
        except Exception as e:
            logger.error(f"メディア政治ニュース取得エラー ({media_name}): {str(e)}")
            return []
    
    def scrape_political_headlines(self, limit_per_media: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """
        全主要メディアの政治ヘッドラインを取得
        
        Args:
            limit_per_media: メディア別取得件数上限
            
        Returns:
            メディア別政治ヘッドライン辞書
        """
        headlines = {}
        
        # シーケンシャル処理で複数メディアから取得（bot認定回避）
        media_list = list(self.media_sites.keys())[:6]  # 主要6メディア
        logger.info(f"メディアヘッドライン順次取得開始: {len(media_list)}メディア")
        
        for i, media_name in enumerate(media_list):
            try:
                logger.info(f"[{i+1}/{len(media_list)}] {media_name}ヘッドライン取得中...")
                media_articles = self.scrape_media_politics(media_name, limit_per_media)
                headlines[media_name] = media_articles
                
                # メディア間の待機時間
                if i < len(media_list) - 1:  # 最後でなければ待機
                    time.sleep(2.0)
                    
            except Exception as e:
                logger.error(f"メディアヘッドライン取得エラー ({media_name}): {str(e)}")
                headlines[media_name] = []
        
        total_articles = sum(len(articles) for articles in headlines.values())
        logger.info(f"全メディア政治ヘッドライン取得完了: 総計{total_articles}件")
        
        return headlines
    
    def scrape_breaking_news(self) -> List[Dict[str, Any]]:
        """
        速報・重要ニュースを取得
        
        Returns:
            速報ニュースのリスト
        """
        breaking_news = []
        
        try:
            # NHKの速報を優先
            nhk_breaking = self._scrape_nhk_breaking()
            breaking_news.extend(nhk_breaking)
            
            # 共同通信の速報
            kyodo_breaking = self._scrape_kyodo_breaking()
            breaking_news.extend(kyodo_breaking)
            
            # 時事通信の速報
            jiji_breaking = self._scrape_jiji_breaking()
            breaking_news.extend(jiji_breaking)
            
            logger.info(f"速報ニュースを取得: {len(breaking_news)}件")
            return breaking_news
            
        except Exception as e:
            logger.error(f"速報ニュース取得エラー: {str(e)}")
            return breaking_news
    
    def analyze_media_sentiment(self, query: str, days: int = 7) -> Dict[str, Dict[str, Any]]:
        """
        メディア別の政治的感情・論調を分析
        
        Args:
            query: 分析対象キーワード
            days: 分析期間（日数）
            
        Returns:
            メディア別感情分析結果
        """
        sentiment_analysis = {}
        
        try:
            for media_name, media_info in self.media_sites.items():
                # 過去数日の記事を取得
                articles = self.scrape_media_politics(media_name, 20)
                
                # クエリに関連する記事をフィルタリング
                relevant_articles = [
                    article for article in articles 
                    if query.lower() in article.get("title", "").lower() or 
                       query.lower() in article.get("summary", "").lower()
                ]
                
                if relevant_articles:
                    # 感情分析（簡易版）
                    sentiment_score = self._analyze_articles_sentiment(relevant_articles)
                    
                    sentiment_analysis[media_name] = {
                        "article_count": len(relevant_articles),
                        "sentiment_score": sentiment_score,
                        "political_bias": media_info["political_bias"],
                        "reliability_score": media_info["reliability_score"],
                        "sample_headlines": [
                            article["title"] for article in relevant_articles[:3]
                        ]
                    }
            
            logger.info(f"メディア感情分析完了: {len(sentiment_analysis)}メディア")
            return sentiment_analysis
            
        except Exception as e:
            logger.error(f"メディア感情分析エラー: {str(e)}")
            return sentiment_analysis
    
    def _extract_articles(self, soup: BeautifulSoup, media_name: str) -> List:
        """メディア固有の記事要素を抽出"""
        # 一般的な記事要素のセレクタ
        article_selectors = [
            'article', 'div.article', 'li.article',
            'div.news-item', 'li.news-item',
            'div.story', 'li.story',
            'div[class*="article"]', 'li[class*="article"]',
            'div[class*="news"]', 'li[class*="news"]'
        ]
        
        # メディア固有のセレクタがある場合は優先
        if media_name == "NHK":
            article_selectors.insert(0, 'div.content-item')
            article_selectors.insert(0, 'li.module-item')
        elif media_name == "朝日新聞":
            article_selectors.insert(0, 'div.List_item')
            article_selectors.insert(0, 'article.Article')
        
        for selector in article_selectors:
            elements = soup.select(selector)
            if elements and len(elements) >= 3:  # 最低3件の記事があれば採用
                return elements
        
        # フォールバック: h2, h3を含む要素
        return soup.find_all(['div', 'li'], limit=20)
    
    def _parse_article(self, element, base_url: str, media_name: str, media_info: Dict) -> Optional[Dict[str, Any]]:
        """記事要素を解析"""
        try:
            selectors = media_info.get("selectors", {})
            
            # タイトル取得
            title_elem = (
                element.select_one(selectors.get("title", "h1, h2, h3")) or
                element.find(['h1', 'h2', 'h3', 'h4', 'a'])
            )
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # リンク取得
            link_elem = element.find('a')
            link = urljoin(base_url, link_elem.get('href')) if link_elem else ""
            
            # 日付取得
            date_elem = (
                element.select_one(selectors.get("date", "time")) or
                element.find(['time', 'span'], class_=re.compile(r'date|time'))
            )
            date_str = date_elem.get_text(strip=True) if date_elem else ""
            
            # 概要取得
            content_elem = (
                element.select_one(selectors.get("content", "p")) or
                element.find('p')
            )
            summary = content_elem.get_text(strip=True) if content_elem else ""
            
            # 政治関連キーワードチェック
            political_keywords = [
                "政治", "政府", "内閣", "総理", "大臣", "議員", "国会", "選挙",
                "政党", "自民", "立憲", "維新", "公明", "共産", "政策", "法案"
            ]
            
            is_political = any(keyword in title + summary for keyword in political_keywords)
            
            if title and is_political:
                return {
                    "source": media_name,
                    "title": title,
                    "link": link,
                    "date": date_str,
                    "summary": summary[:200],  # 概要は200文字まで
                    "category": "政治ニュース",
                    "reliability_score": media_info["reliability_score"],
                    "political_bias": media_info["political_bias"],
                    "scraped_at": datetime.now().isoformat()
                }
            
            return None
            
        except Exception as e:
            logger.warning(f"記事解析エラー: {str(e)}")
            return None
    
    def _scrape_nhk_breaking(self) -> List[Dict[str, Any]]:
        """NHK速報を取得"""
        try:
            # NHKの速報ページ（仮URL）
            url = f"{self.media_sites['NHK']['base_url']}/news/breaking/"
            response = self._safe_request(url)
            
            if not response:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            breaking_items = []
            
            # 速報要素を抽出
            breaking_elements = soup.find_all(['div', 'li'], class_=re.compile(r'breaking|urgent|flash'))
            
            for element in breaking_elements[:5]:
                title_elem = element.find(['h1', 'h2', 'h3', 'a'])
                title = title_elem.get_text(strip=True) if title_elem else ""
                
                if title:
                    breaking_items.append({
                        "source": "NHK",
                        "title": title,
                        "type": "速報",
                        "category": "速報ニュース",
                        "reliability_score": 0.95,
                        "political_bias": 0.0,
                        "scraped_at": datetime.now().isoformat()
                    })
            
            return breaking_items
            
        except Exception as e:
            logger.warning(f"NHK速報取得エラー: {str(e)}")
            return []
    
    def _scrape_kyodo_breaking(self) -> List[Dict[str, Any]]:
        """共同通信速報を取得"""
        try:
            url = f"{self.media_sites['共同通信']['base_url']}/news/flash/"
            response = self._safe_request(url)
            
            if not response:
                return []
            
            # 実装は簡略化
            return []
            
        except Exception as e:
            logger.warning(f"共同通信速報取得エラー: {str(e)}")
            return []
    
    def _scrape_jiji_breaking(self) -> List[Dict[str, Any]]:
        """時事通信速報を取得"""
        try:
            url = f"{self.media_sites['時事通信']['base_url']}/news/flash/"
            response = self._safe_request(url)
            
            if not response:
                return []
            
            # 実装は簡略化
            return []
            
        except Exception as e:
            logger.warning(f"時事通信速報取得エラー: {str(e)}")
            return []
    
    def _analyze_articles_sentiment(self, articles: List[Dict[str, Any]]) -> float:
        """記事群の感情分析（簡易版）"""
        positive_keywords = ["成功", "成果", "評価", "支持", "賛成", "前進"]
        negative_keywords = ["失敗", "批判", "反対", "問題", "懸念", "混乱"]
        
        positive_count = 0
        negative_count = 0
        
        for article in articles:
            text = article.get("title", "") + " " + article.get("summary", "")
            
            positive_count += sum(1 for keyword in positive_keywords if keyword in text)
            negative_count += sum(1 for keyword in negative_keywords if keyword in text)
        
        if positive_count + negative_count == 0:
            return 0.0  # 中立
        
        # -1.0（ネガティブ）から1.0（ポジティブ）
        sentiment_score = (positive_count - negative_count) / (positive_count + negative_count)
        return sentiment_score
    
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
    
    def get_media_coverage_analysis(self, topic: str) -> Dict[str, Any]:
        """
        特定トピックのメディア報道分析
        
        Args:
            topic: 分析トピック
            
        Returns:
            メディア報道分析結果
        """
        try:
            # 各メディアからトピック関連記事を取得
            coverage_data = {}
            total_articles = 0
            
            for media_name in self.media_sites.keys():
                articles = self.scrape_media_politics(media_name, 10)
                relevant_articles = [
                    article for article in articles
                    if topic.lower() in article.get("title", "").lower()
                ]
                
                coverage_data[media_name] = {
                    "article_count": len(relevant_articles),
                    "coverage_ratio": len(relevant_articles) / max(len(articles), 1),
                    "headlines": [article["title"] for article in relevant_articles[:3]]
                }
                total_articles += len(relevant_articles)
            
            return {
                "topic": topic,
                "total_articles": total_articles,
                "media_coverage": coverage_data,
                "analysis_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"メディア報道分析エラー: {str(e)}")
            return {}
    
    def _save_article_to_db(self, article: Dict[str, Any], media_info: Dict[str, Any]) -> Optional[int]:
        """
        記事をデータベースに保存
        
        Args:
            article: 記事データ
            media_info: メディア情報
            
        Returns:
            保存された記事のID（重複の場合はNone）
        """
        try:
            # 政治関連キーワード抽出
            keywords = self._extract_keywords(article.get("title", "") + " " + article.get("summary", ""))
            
            # エンティティ抽出（簡易版）
            entities = self._extract_entities(article.get("title", "") + " " + article.get("summary", ""))
            
            # トピック分類（簡易版）
            topic_category = self._classify_topic(article.get("title", "") + " " + article.get("summary", ""))
            
            news = PoliticalNews(
                id=None,
                title=article["title"],
                content=article.get("summary", ""),
                summary=article.get("summary", ""),
                url=article.get("link", ""),
                source_name=article["source"],
                published_at=article.get("date", ""),
                collected_at=datetime.now().isoformat(),
                reliability_score=article["reliability_score"],
                political_bias=article["political_bias"],
                topic_category=topic_category,
                sentiment_score=0.0,  # 後で感情分析で更新
                entity_mentions=entities,
                keywords=keywords
            )
            
            saved_id = self.database.save_political_news(news)
            if saved_id:
                logger.debug(f"記事をDB保存: {article['title'][:30]}... (ID: {saved_id})")
            
            return saved_id
            
        except Exception as e:
            logger.error(f"記事DB保存エラー: {str(e)}")
            return None
    
    def _extract_keywords(self, text: str) -> List[str]:
        """政治関連キーワードを抽出"""
        political_keywords = [
            "政治", "政府", "内閣", "総理", "首相", "大臣", "議員", "国会", "選挙", "政党",
            "自民党", "立憲民主党", "日本維新の会", "公明党", "日本共産党",
            "岸田", "泉", "志位", "馬場", "玉木", "山本", "福島",
            "政策", "法案", "予算", "税制", "憲法", "安全保障", "外交", "経済政策",
            "支持率", "世論調査", "選挙結果", "投票", "有権者"
        ]
        
        found_keywords = []
        text_lower = text.lower()
        
        for keyword in political_keywords:
            if keyword in text:
                found_keywords.append(keyword)
        
        return list(set(found_keywords))  # 重複除去
    
    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """政治エンティティを抽出"""
        entities = {
            "politicians": [],
            "parties": [],
            "policies": [],
            "organizations": []
        }
        
        # 政治家名
        politicians = ["岸田文雄", "泉健太", "志位和夫", "馬場伸幸", "玉木雄一郎", "山本太郎", "福島みずほ"]
        for politician in politicians:
            if politician in text:
                entities["politicians"].append(politician)
        
        # 政党名
        parties = ["自由民主党", "立憲民主党", "日本維新の会", "公明党", "日本共産党", "国民民主党", "れいわ新選組", "社会民主党"]
        for party in parties:
            if party in text or party.replace("党", "") in text:
                entities["parties"].append(party)
        
        # 政府機関
        organizations = ["内閣", "総理官邸", "国会", "衆議院", "参議院", "財務省", "外務省", "防衛省"]
        for org in organizations:
            if org in text:
                entities["organizations"].append(org)
        
        return entities
    
    def _classify_topic(self, text: str) -> str:
        """記事のトピック分類"""
        topic_keywords = {
            "内閣支持率": ["支持率", "世論調査", "内閣支持"],
            "経済政策": ["経済", "景気", "GDP", "インフレ", "税制", "予算"],
            "外交・安保": ["外交", "安全保障", "防衛", "日米", "中国", "韓国", "安保"],
            "社会保障": ["年金", "医療", "介護", "福祉", "子育て", "少子化"],
            "憲法・法制": ["憲法", "改正", "法案", "立法", "法律"],
            "選挙": ["選挙", "投票", "候補者", "政党", "当選", "落選"],
            "国会": ["国会", "審議", "質疑", "委員会", "本会議"],
            "政治スキャンダル": ["疑惑", "説明責任", "追及", "辞任", "スキャンダル"]
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text for keyword in keywords):
                return topic
        
        return "その他"
    
    def get_cached_articles(self, query: str, hours: int = 24) -> List[Dict[str, Any]]:
        """
        キャッシュされた記事を取得
        
        Args:
            query: 検索クエリ
            hours: 取得対象時間（時間）
            
        Returns:
            キャッシュされた記事のリスト
        """
        try:
            # データベースから検索
            cached_news = self.database.search_political_news(
                keyword=query,
                days_back=hours // 24 + 1,  # 時間を日数に換算
                limit=50
            )
            
            # 記事形式に変換
            articles = []
            for news in cached_news:
                article = {
                    "source": news.source_name,
                    "title": news.title,
                    "link": news.url or "",
                    "date": news.published_at or "",
                    "summary": news.summary or "",
                    "category": news.topic_category or "政治ニュース",
                    "reliability_score": news.reliability_score,
                    "political_bias": news.political_bias,
                    "scraped_at": news.collected_at,
                    "keywords": news.keywords,
                    "cached": True
                }
                articles.append(article)
            
            logger.info(f"キャッシュから記事を取得: {len(articles)}件")
            return articles
            
        except Exception as e:
            logger.error(f"キャッシュ記事取得エラー: {str(e)}")
            return []
    
    def should_scrape_fresh(self, query: str, hours: int = 24) -> bool:
        """
        新しいスクレイピングが必要かチェック
        
        Args:
            query: 検索クエリ
            hours: キャッシュ有効期間
            
        Returns:
            新しいスクレイピングが必要な場合True
        """
        try:
            cache_status = self.database.get_cache_status(query, hours)
            
            # キャッシュが新しい場合はスクレイピング不要
            if cache_status.get("has_fresh_data", False):
                logger.info(f"キャッシュ利用: {query} ({cache_status['news_count']}件)")
                return False
            
            logger.info(f"新規スクレイピング実行: {query}")
            return True
            
        except Exception as e:
            logger.warning(f"キャッシュ状況確認エラー: {str(e)}")
            return True  # エラー時は安全のためスクレイピング実行
    
    def test_connection(self) -> bool:
        """メディアサイト接続テスト"""
        try:
            # NHKサイトでテスト
            test_url = self.media_sites["NHK"]["base_url"]
            response = self._safe_request(test_url)
            return response is not None
        except Exception as e:
            logger.error(f"メディアサイト接続テスト失敗: {str(e)}")
            return False