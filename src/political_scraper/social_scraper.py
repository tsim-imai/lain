"""
ソーシャルメディア監視スクレイパー
Twitter/X、政治家公式アカウント、政治ハッシュタグの監視
"""
import logging
import requests
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re
import json

from ..utils.config import ConfigManager
from ..utils.exceptions import ScraperError
from ..political_data.political_database import PoliticalDatabaseManager, SocialPost

logger = logging.getLogger(__name__)


class SocialScraper:
    """ソーシャルメディア監視スクレイパークラス"""
    
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
        
        # 主要政治家のSNSアカウント
        self.political_accounts = {
            "岸田文雄": {
                "twitter": "@kishida230",
                "position": "内閣総理大臣",
                "party": "自由民主党",
                "follower_tier": "top",
                "reliability_score": 0.95
            },
            "泉健太": {
                "twitter": "@izumikenta",
                "position": "立憲民主党代表",
                "party": "立憲民主党",
                "follower_tier": "major",
                "reliability_score": 0.9
            },
            "志位和夫": {
                "twitter": "@shiikazuo",
                "position": "日本共産党委員長",
                "party": "日本共産党",
                "follower_tier": "major",
                "reliability_score": 0.9
            },
            "馬場伸幸": {
                "twitter": "@babajpn",
                "position": "日本維新の会代表",
                "party": "日本維新の会",
                "follower_tier": "major",
                "reliability_score": 0.85
            },
            "玉木雄一郎": {
                "twitter": "@tamakiyuichiro",
                "position": "国民民主党代表",
                "party": "国民民主党",
                "follower_tier": "medium",
                "reliability_score": 0.85
            },
            "山本太郎": {
                "twitter": "@yamamototaro0",
                "position": "れいわ新選組代表",
                "party": "れいわ新選組",
                "follower_tier": "medium",
                "reliability_score": 0.8
            },
            "福島みずほ": {
                "twitter": "@mizuhofukushima",
                "position": "社会民主党党首",
                "party": "社会民主党",
                "follower_tier": "medium",
                "reliability_score": 0.8
            }
        }
        
        # 監視対象政治ハッシュタグ
        self.political_hashtags = [
            "#政治", "#国会", "#内閣", "#総理", "#首相",
            "#選挙", "#衆議院選挙", "#参議院選挙",
            "#自民党", "#立憲民主党", "#日本維新の会", "#公明党",
            "#岸田内閣", "#支持率", "#世論調査",
            "#政策", "#法案", "#予算", "#税制",
            "#憲法改正", "#安全保障", "#外交",
            "#経済政策", "#アベノミクス", "#新しい資本主義"
        ]
        
        # 政治的感情分析キーワード
        self.sentiment_keywords = {
            "positive": [
                "支持", "賛成", "評価", "良い", "素晴らしい", "成功", "成果",
                "前進", "改善", "期待", "頑張れ", "応援"
            ],
            "negative": [
                "反対", "批判", "問題", "失敗", "ダメ", "最悪", "辞任",
                "責任", "追及", "疑惑", "スキャンダル", "許せない"
            ],
            "neutral": [
                "発表", "会見", "決定", "検討", "予定", "開始", "終了",
                "実施", "確認", "報告", "説明"
            ]
        }
        
        self.request_delay = 2.0  # SNSアクセス間隔
        
        logger.info("ソーシャルメディア監視スクレイパーを初期化")
    
    def monitor_political_twitter(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        政治関連ツイートを監視
        
        Args:
            limit: 取得件数上限
            
        Returns:
            政治ツイートデータのリスト
        """
        try:
            political_tweets = []
            
            # 注意: 実際のTwitter API v2の実装では認証が必要
            # ここではサンプルデータとデモ用の構造を提供
            
            # 主要政治家アカウントの投稿を模擬
            for politician, account_info in list(self.political_accounts.items())[:5]:
                sample_tweets = self._generate_sample_tweets(politician, account_info)
                political_tweets.extend(sample_tweets)
            
            # 政治ハッシュタグの投稿を模擬
            hashtag_tweets = self._monitor_political_hashtags(limit // 2)
            political_tweets.extend(hashtag_tweets)
            
            # 投稿時間順にソート
            political_tweets.sort(key=lambda x: x.get("posted_at", ""), reverse=True)
            
            logger.info(f"政治ツイート監視完了: {len(political_tweets)}件")
            return political_tweets[:limit]
            
        except Exception as e:
            logger.error(f"政治ツイート監視エラー: {str(e)}")
            return []
    
    def _generate_sample_tweets(self, politician: str, account_info: Dict) -> List[Dict[str, Any]]:
        """サンプル政治家ツイートを生成"""
        sample_tweets = []
        
        # 政治家別のサンプルツイート内容
        sample_contents = {
            "岸田文雄": [
                "本日、経済対策について関係閣僚と協議を行いました。国民の皆様の生活を守るため、全力で取り組んでまいります。",
                "G7サミットでの成果を国内政策に活かしてまいります。国際協調と国益の両立を図ります。"
            ],
            "泉健太": [
                "政府の説明は不十分です。国民が納得できる政策運営を求めます。",
                "野党として、建設的な政策提案を続けてまいります。"
            ],
            "志位和夫": [
                "平和と民主主義を守る政治の実現に向けて取り組みます。",
                "格差是正と社会保障の充実が急務です。"
            ]
        }
        
        contents = sample_contents.get(politician, ["政治活動に関する投稿"])
        
        for i, content in enumerate(contents):
            tweet_data = {
                "platform": "Twitter",
                "account": account_info["twitter"],
                "politician": politician,
                "party": account_info["party"],
                "position": account_info["position"],
                "content": content,
                "posted_at": (datetime.now() - timedelta(hours=i*2)).isoformat(),
                "engagement": {
                    "likes": 150 + i*50,
                    "retweets": 30 + i*10,
                    "replies": 25 + i*5
                },
                "sentiment_score": self._analyze_tweet_sentiment(content),
                "political_topics": self._extract_political_topics(content),
                "reliability_score": account_info["reliability_score"],
                "category": "政治家発言",
                "scraped_at": datetime.now().isoformat()
            }
            sample_tweets.append(tweet_data)
            
            # データベースに保存
            self._save_post_to_db(tweet_data)
        
        return sample_tweets
    
    def _monitor_political_hashtags(self, limit: int) -> List[Dict[str, Any]]:
        """政治ハッシュタグの投稿を監視"""
        hashtag_tweets = []
        
        try:
            # 主要政治ハッシュタグのサンプル投稿
            sample_hashtag_posts = [
                {
                    "hashtag": "#岸田内閣",
                    "content": "支持率が気になるところですが、経済政策の成果に期待しています #岸田内閣 #経済政策",
                    "sentiment": "neutral"
                },
                {
                    "hashtag": "#国会",
                    "content": "今日の国会審議、与野党の議論が活発でした #国会 #政治",
                    "sentiment": "positive"
                },
                {
                    "hashtag": "#選挙",
                    "content": "次の選挙に向けて各党の政策を比較検討中 #選挙 #政策比較",
                    "sentiment": "neutral"
                },
                {
                    "hashtag": "#政策",
                    "content": "子育て支援政策の拡充は必要だと思います #政策 #子育て支援",
                    "sentiment": "positive"
                },
                {
                    "hashtag": "#世論調査",
                    "content": "最新の世論調査結果が発表されました #世論調査 #支持率",
                    "sentiment": "neutral"
                }
            ]
            
            for i, post_data in enumerate(sample_hashtag_posts[:limit]):
                tweet_data = {
                    "platform": "Twitter",
                    "account": f"@user_{i+1}",
                    "politician": None,
                    "party": None,
                    "position": "一般ユーザー",
                    "content": post_data["content"],
                    "hashtag": post_data["hashtag"],
                    "posted_at": (datetime.now() - timedelta(minutes=i*30)).isoformat(),
                    "engagement": {
                        "likes": 15 + i*5,
                        "retweets": 3 + i,
                        "replies": 2 + i
                    },
                    "sentiment_score": self._get_sentiment_score(post_data["sentiment"]),
                    "political_topics": self._extract_political_topics(post_data["content"]),
                    "reliability_score": 0.5,  # 一般ユーザーは中程度の信頼性
                    "category": "一般世論",
                    "scraped_at": datetime.now().isoformat()
                }
                hashtag_tweets.append(tweet_data)
                
                # データベースに保存
                self._save_post_to_db(tweet_data)
            
            return hashtag_tweets
            
        except Exception as e:
            logger.error(f"ハッシュタグ監視エラー: {str(e)}")
            return hashtag_tweets
    
    def analyze_political_sentiment_trend(self, topic: str, hours: int = 24) -> Dict[str, Any]:
        """
        政治トピックの感情トレンド分析
        
        Args:
            topic: 分析対象トピック
            hours: 分析期間（時間）
            
        Returns:
            感情トレンド分析結果
        """
        try:
            # サンプルデータによる感情トレンド
            sample_timeline = []
            
            for hour in range(hours):
                timestamp = datetime.now() - timedelta(hours=hour)
                
                # 感情スコアの変動をシミュレート
                base_sentiment = 0.1  # 基本的にやや肯定的
                variation = (-1) ** hour * 0.2 * (hour % 5) / 5  # 周期的変動
                sentiment_score = base_sentiment + variation
                
                sample_timeline.append({
                    "timestamp": timestamp.isoformat(),
                    "hour": timestamp.hour,
                    "sentiment_score": round(sentiment_score, 2),
                    "post_count": 50 + (hour % 10) * 5,
                    "positive_ratio": max(0.3, 0.5 + sentiment_score),
                    "negative_ratio": max(0.1, 0.3 - sentiment_score),
                    "neutral_ratio": 0.2
                })
            
            # 統計情報の計算
            sentiment_scores = [item["sentiment_score"] for item in sample_timeline]
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            max_sentiment = max(sentiment_scores)
            min_sentiment = min(sentiment_scores)
            
            trend_analysis = {
                "topic": topic,
                "analysis_period_hours": hours,
                "timeline": sample_timeline,
                "summary": {
                    "average_sentiment": round(avg_sentiment, 2),
                    "max_sentiment": max_sentiment,
                    "min_sentiment": min_sentiment,
                    "sentiment_volatility": round(max_sentiment - min_sentiment, 2),
                    "total_posts": sum(item["post_count"] for item in sample_timeline),
                    "trend_direction": "上昇" if sentiment_scores[0] > sentiment_scores[-1] else "下降"
                },
                "analysis_date": datetime.now().isoformat()
            }
            
            logger.info(f"感情トレンド分析完了: {topic}")
            return trend_analysis
            
        except Exception as e:
            logger.error(f"感情トレンド分析エラー: {str(e)}")
            return {}
    
    def monitor_political_influencers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        政治系インフルエンサーの投稿を監視
        
        Args:
            limit: 取得件数上限
            
        Returns:
            インフルエンサー投稿データのリスト
        """
        try:
            influencer_posts = []
            
            # 政治系インフルエンサー（架空のアカウント）
            political_influencers = [
                {
                    "name": "政治解説者A",
                    "account": "@politics_analyst_a",
                    "follower_count": 150000,
                    "specialty": "国政分析",
                    "reliability": 0.8
                },
                {
                    "name": "政治ジャーナリストB",
                    "account": "@politics_journalist_b",
                    "follower_count": 200000,
                    "specialty": "政局報道",
                    "reliability": 0.85
                }
            ]
            
            for influencer in political_influencers:
                sample_posts = [
                    f"{influencer['specialty']}の観点から最新の政治動向を解説します",
                    f"今日の国会での議論について分析しました"
                ]
                
                for i, content in enumerate(sample_posts):
                    post_data = {
                        "platform": "Twitter",
                        "account": influencer["account"],
                        "influencer_name": influencer["name"],
                        "follower_count": influencer["follower_count"],
                        "specialty": influencer["specialty"],
                        "content": content,
                        "posted_at": (datetime.now() - timedelta(hours=i*3)).isoformat(),
                        "engagement": {
                            "likes": 200 + i*50,
                            "retweets": 80 + i*20,
                            "replies": 45 + i*10
                        },
                        "sentiment_score": self._analyze_tweet_sentiment(content),
                        "political_topics": self._extract_political_topics(content),
                        "reliability_score": influencer["reliability"],
                        "category": "政治解説",
                        "scraped_at": datetime.now().isoformat()
                    }
                    influencer_posts.append(post_data)
            
            logger.info(f"政治インフルエンサー監視完了: {len(influencer_posts)}件")
            return influencer_posts[:limit]
            
        except Exception as e:
            logger.error(f"政治インフルエンサー監視エラー: {str(e)}")
            return []
    
    def _analyze_tweet_sentiment(self, content: str) -> float:
        """ツイート内容の感情分析"""
        positive_count = sum(1 for keyword in self.sentiment_keywords["positive"] if keyword in content)
        negative_count = sum(1 for keyword in self.sentiment_keywords["negative"] if keyword in content)
        
        if positive_count + negative_count == 0:
            return 0.0  # 中立
        
        # -1.0（ネガティブ）から1.0（ポジティブ）
        sentiment_score = (positive_count - negative_count) / (positive_count + negative_count)
        return sentiment_score
    
    def _get_sentiment_score(self, sentiment_type: str) -> float:
        """感情タイプからスコアを取得"""
        sentiment_mapping = {
            "positive": 0.7,
            "negative": -0.7,
            "neutral": 0.0
        }
        return sentiment_mapping.get(sentiment_type, 0.0)
    
    def _extract_political_topics(self, content: str) -> List[str]:
        """投稿内容から政治トピックを抽出"""
        political_topics = []
        
        topic_keywords = {
            "内閣支持率": ["支持率", "内閣", "世論調査"],
            "経済政策": ["経済", "景気", "GDP", "インフレ", "税制"],
            "外交・安保": ["外交", "安全保障", "防衛", "日米", "中国", "韓国"],
            "社会保障": ["年金", "医療", "介護", "福祉", "子育て"],
            "憲法・法制": ["憲法", "改正", "法案", "立法"],
            "選挙": ["選挙", "投票", "候補者", "政党"],
            "国会": ["国会", "審議", "質疑", "委員会"],
            "スキャンダル": ["疑惑", "説明責任", "追及", "辞任"]
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in content for keyword in keywords):
                political_topics.append(topic)
        
        return political_topics
    
    def get_trending_political_topics(self, hours: int = 6) -> List[Dict[str, Any]]:
        """
        トレンド政治トピックを取得
        
        Args:
            hours: 分析期間（時間）
            
        Returns:
            トレンド政治トピックのリスト
        """
        try:
            # サンプルトレンドデータ
            trending_topics = [
                {
                    "topic": "内閣支持率",
                    "post_count": 1250,
                    "sentiment_score": -0.2,
                    "growth_rate": 0.15,
                    "related_hashtags": ["#支持率", "#内閣", "#世論調査"],
                    "key_discussions": [
                        "最新の世論調査結果について",
                        "支持率低下の要因分析",
                        "今後の政局への影響"
                    ]
                },
                {
                    "topic": "経済政策",
                    "post_count": 980,
                    "sentiment_score": 0.1,
                    "growth_rate": 0.08,
                    "related_hashtags": ["#経済政策", "#新しい資本主義"],
                    "key_discussions": [
                        "物価高対策について",
                        "賃上げ政策の効果",
                        "中小企業支援策"
                    ]
                },
                {
                    "topic": "選挙予測",
                    "post_count": 750,
                    "sentiment_score": 0.0,
                    "growth_rate": 0.12,
                    "related_hashtags": ["#選挙", "#政局"],
                    "key_discussions": [
                        "次期総選挙の時期予測",
                        "各党の選挙準備状況",
                        "選挙区情勢分析"
                    ]
                }
            ]
            
            # トレンドスコアでソート（投稿数 × 成長率）
            for topic in trending_topics:
                topic["trend_score"] = topic["post_count"] * (1 + topic["growth_rate"])
            
            trending_topics.sort(key=lambda x: x["trend_score"], reverse=True)
            
            logger.info(f"トレンド政治トピック取得: {len(trending_topics)}件")
            return trending_topics
            
        except Exception as e:
            logger.error(f"トレンド政治トピック取得エラー: {str(e)}")
            return []
    
    def test_connection(self) -> bool:
        """SNS監視システム接続テスト"""
        try:
            # 実際のAPI接続は行わず、システムの初期化状態をチェック
            return len(self.political_accounts) > 0 and len(self.political_hashtags) > 0
        except Exception as e:
            logger.error(f"SNS監視システムテスト失敗: {str(e)}")
            return False
    
    def get_social_media_summary(self) -> Dict[str, Any]:
        """
        ソーシャルメディア監視サマリーを取得
        
        Returns:
            監視サマリーデータ
        """
        try:
            # 各種監視データを取得
            political_tweets = self.monitor_political_twitter(10)
            influencer_posts = self.monitor_political_influencers(5)
            trending_topics = self.get_trending_political_topics()
            
            summary = {
                "monitoring_timestamp": datetime.now().isoformat(),
                "political_tweets": {
                    "count": len(political_tweets),
                    "latest_posts": political_tweets[:3]
                },
                "influencer_posts": {
                    "count": len(influencer_posts),
                    "latest_posts": influencer_posts[:3]
                },
                "trending_topics": trending_topics[:5],
                "monitored_accounts": len(self.political_accounts),
                "monitored_hashtags": len(self.political_hashtags),
                "overall_sentiment": self._calculate_overall_sentiment(political_tweets + influencer_posts)
            }
            
            logger.info("ソーシャルメディア監視サマリー作成完了")
            return summary
            
        except Exception as e:
            logger.error(f"ソーシャルメディアサマリー作成エラー: {str(e)}")
            return {}
    
    def _calculate_overall_sentiment(self, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """全体的な感情傾向を計算"""
        if not posts:
            return {"average": 0.0, "distribution": {"positive": 0, "neutral": 0, "negative": 0}}
        
        sentiment_scores = [post.get("sentiment_score", 0) for post in posts]
        average_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        
        positive_count = sum(1 for score in sentiment_scores if score > 0.2)
        negative_count = sum(1 for score in sentiment_scores if score < -0.2)
        neutral_count = len(sentiment_scores) - positive_count - negative_count
        
        return {
            "average": round(average_sentiment, 2),
            "distribution": {
                "positive": positive_count,
                "neutral": neutral_count,
                "negative": negative_count
            }
        }
    
    def _save_post_to_db(self, post_data: Dict[str, Any]) -> Optional[int]:
        """
        SNS投稿をデータベースに保存
        
        Args:
            post_data: SNS投稿データ
            
        Returns:
            保存された投稿のID（重複の場合はNone）
        """
        try:
            # アカウントタイプを判定
            account_type = "general"
            if post_data.get("politician"):
                account_type = "politician"
            elif "解説" in post_data.get("category", "") or "ジャーナリスト" in post_data.get("account", ""):
                account_type = "influencer"
            
            social_post = SocialPost(
                id=None,
                platform=post_data.get("platform", "Twitter"),
                account_name=post_data.get("account", ""),
                account_type=account_type,
                content=post_data.get("content", ""),
                posted_at=post_data.get("posted_at", ""),
                collected_at=datetime.now().isoformat(),
                engagement_data=post_data.get("engagement", {}),
                sentiment_score=post_data.get("sentiment_score", 0.0),
                reliability_score=post_data.get("reliability_score", 0.5),
                hashtags=post_data.get("hashtag", ""),
                mentioned_entities={
                    "politicians": [post_data.get("politician")] if post_data.get("politician") else [],
                    "parties": [post_data.get("party")] if post_data.get("party") else []
                },
                political_topics=post_data.get("political_topics", [])
            )
            
            saved_id = self.database.save_social_post(social_post)
            if saved_id:
                logger.debug(f"SNS投稿をDB保存: {post_data.get('account', 'Unknown')} (ID: {saved_id})")
            
            return saved_id
            
        except Exception as e:
            logger.error(f"SNS投稿DB保存エラー: {str(e)}")
            return None
    
    def get_cached_posts(self, 
                        platform: Optional[str] = None,
                        account_type: Optional[str] = None,
                        hours: int = 24) -> List[Dict[str, Any]]:
        """
        キャッシュされたSNS投稿を取得
        
        Args:
            platform: プラットフォーム
            account_type: アカウントタイプ
            hours: 取得対象時間
            
        Returns:
            キャッシュされたSNS投稿のリスト
        """
        try:
            cached_posts = self.database.get_latest_social_posts(
                platform=platform,
                account_type=account_type,
                days_back=hours // 24 + 1,
                limit=50
            )
            
            # 投稿形式に変換
            posts = []
            for post in cached_posts:
                post_data = {
                    "platform": post.platform,
                    "account": post.account_name,
                    "account_type": post.account_type,
                    "content": post.content,
                    "posted_at": post.posted_at,
                    "engagement": post.engagement_data,
                    "sentiment_score": post.sentiment_score,
                    "reliability_score": post.reliability_score,
                    "hashtags": post.hashtags,
                    "political_topics": post.political_topics,
                    "cached": True,
                    "scraped_at": post.collected_at
                }
                posts.append(post_data)
            
            logger.info(f"キャッシュからSNS投稿を取得: {len(posts)}件")
            return posts
            
        except Exception as e:
            logger.error(f"キャッシュSNS投稿取得エラー: {str(e)}")
            return []