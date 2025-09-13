import feedparser
import tweepy
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import config
# Import market data sources with fallbacks
from connectors.simple_market_data import get_simple_market_data, format_market_data_for_llm
from connectors.new_coins import get_new_coin_opportunities, format_new_coins_for_llm

# Import Cryptofeed with fallback for robust operation
try:
    from connectors.cryptofeed_connector import get_cryptofeed_data, format_cryptofeed_for_llm
    CRYPTOFEED_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Cryptofeed not available: {e}")
    CRYPTOFEED_AVAILABLE = False
    
    # Fallback functions
    def get_cryptofeed_data(*args, **kwargs):
        return {'error': 'Cryptofeed not available'}
    
    def format_cryptofeed_for_llm(*args, **kwargs):
        return "Cryptofeed Error: Module not available"

class RealtimeFeedsConnector:
    """Real-time data connector for RSS feeds and X (Twitter) posts"""
    
    def __init__(self):
        self.rss_cache = {}
        self.x_cache = {}
        self.last_fetch_time = {}
        
        # Predefined crypto RSS feeds
        self.crypto_rss_feeds = [
            'https://www.coindesk.com/arc/outboundfeeds/rss',
            'https://cointelegraph.com/rss',
            'https://rss.app/feeds/ivBTittPQVQXd8Lv.xml'
        ]
        
        # Reddit crypto subreddit feeds for trend analysis
        self.reddit_feeds = [
            'https://www.reddit.com/r/SatoshiStreetBets.rss',
            'https://www.reddit.com/r/CryptoCurrency.rss',
            'https://www.reddit.com/r/CryptoMoonShots.rss'
        ]
        
        # Predefined crypto X accounts (without @ symbol)
        self.crypto_x_accounts = [
            'cz_binance',
            'elonmusk',
            'VitalikButerin',
            'justinsuntron',
            'coinbase',
            'binance',
            'ethereum',
            'bitcoin',
            'coingecko',
            'coinmarketcap'
        ]
    
    def fetch_from_rss_feeds(self, feed_urls: Optional[List[str]] = None, max_articles_per_feed: int = 10, include_reddit: bool = True) -> List[Dict]:
        """
        Fetch latest articles from RSS feeds including Reddit trend analysis
        
        Args:
            feed_urls: List of RSS feed URLs (uses defaults if None)
            max_articles_per_feed: Maximum articles to fetch per feed
            include_reddit: Whether to include Reddit feeds for trend analysis
            
        Returns:
            List of articles with title, link, published date, and source
        """
        if feed_urls is None:
            feed_urls = self.crypto_rss_feeds.copy()
            if include_reddit:
                feed_urls.extend(self.reddit_feeds)
        
        all_articles = []
        successful_feeds = 0
        
        print(f"📡 Fetching from {len(feed_urls)} RSS feeds...")
        
        for feed_url in feed_urls:
            try:
                # Check cache age
                cache_key = f"rss_{feed_url}"
                if self._is_cache_fresh(cache_key, minutes=5):
                    cached_articles = self.rss_cache.get(cache_key, [])
                    all_articles.extend(cached_articles)
                    continue
                
                # Fetch feed with timeout and SSL handling
                print(f"  📰 Fetching: {self._get_domain_name(feed_url)}")
                
                try:
                    # Try using requests with SSL verification disabled
                    import ssl
                    import requests
                    from requests.adapters import HTTPAdapter
                    from urllib3.util.retry import Retry
                    
                    # Create session with custom SSL settings
                    session = requests.Session()
                    session.verify = False  # Disable SSL verification
                    
                    # Suppress SSL warnings
                    import urllib3
                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                    
                    # Set up retry strategy
                    retry_strategy = Retry(
                        total=3,
                        status_forcelist=[429, 500, 502, 503, 504],
                        allowed_methods=["HEAD", "GET", "OPTIONS"]
                    )
                    adapter = HTTPAdapter(max_retries=retry_strategy)
                    session.mount("http://", adapter)
                    session.mount("https://", adapter)
                    
                    # Fetch the RSS content
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    response = session.get(feed_url, headers=headers, timeout=10)
                    response.raise_for_status()
                    
                    # Parse the fetched content
                    feed = feedparser.parse(response.content)
                    
                except Exception as e:
                    print(f"  ❌ Requests method failed: {e}")
                    # Fallback to direct feedparser
                    feed = feedparser.parse(feed_url)
                
                if feed.bozo and feed.bozo_exception:
                    print(f"  ⚠️  Feed parsing issue for {feed_url}: {feed.bozo_exception}")
                    continue
                
                feed_articles = []
                entries = feed.entries[:max_articles_per_feed]
                
                # Check if this is a Reddit feed
                is_reddit_feed = 'reddit.com' in feed_url
                
                for entry in entries:
                    article = {
                        'title': entry.get('title', 'No title'),
                        'link': entry.get('link', ''),
                        'published': self._parse_published_date(entry),
                        'source': feed.feed.get('title', self._get_domain_name(feed_url)),
                        'summary': entry.get('summary', '')[:200] + '...' if entry.get('summary') else '',
                        'feed_type': 'Reddit' if is_reddit_feed else 'RSS',
                        'feed_url': feed_url,
                        'is_reddit': is_reddit_feed
                    }
                    
                    # Filter for recent articles (last 24 hours for news, 12 hours for Reddit)
                    hours_limit = 12 if is_reddit_feed else 24
                    if self._is_recent_article(article['published'], hours_limit):
                        feed_articles.append(article)
                
                # Cache the results
                self.rss_cache[cache_key] = feed_articles
                self.last_fetch_time[cache_key] = datetime.now()
                
                all_articles.extend(feed_articles)
                successful_feeds += 1
                
                print(f"  ✅ {len(feed_articles)} recent articles from {self._get_domain_name(feed_url)}")
                
            except Exception as e:
                print(f"  ❌ Error fetching RSS feed {feed_url}: {e}")
                continue
        
        print(f"📊 RSS Summary: {len(all_articles)} articles from {successful_feeds}/{len(feed_urls)} feeds")
        
        # Sort by publication date (newest first)
        all_articles.sort(key=lambda x: x['published'], reverse=True)
        
        return all_articles
    
    def fetch_from_x_accounts(self, usernames: Optional[List[str]] = None, max_tweets_per_account: int = 5) -> List[Dict]:
        """
        Fetch latest posts from X (Twitter) accounts
        
        Args:
            usernames: List of X usernames (uses defaults if None)
            max_tweets_per_account: Maximum tweets to fetch per account
            
        Returns:
            List of tweets with text, user, created_at, and metrics
        """
        if usernames is None:
            usernames = self.crypto_x_accounts
        
        # Check if X API credentials are configured
        x_bearer_token = getattr(config, 'X_BEARER_TOKEN', None)
        
        if not x_bearer_token:
            print("⚠️  X (Twitter) API credentials not configured. Using mock data.")
            return self._get_mock_x_posts()
        
        all_tweets = []
        successful_accounts = 0
        
        print(f"🐦 Fetching from {len(usernames)} X accounts...")
        
        try:
            # Initialize Twitter API v2
            client = tweepy.Client(bearer_token=x_bearer_token)
            
            for username in usernames:
                try:
                    # Check cache age
                    cache_key = f"x_{username}"
                    if self._is_cache_fresh(cache_key, minutes=3):
                        cached_tweets = self.x_cache.get(cache_key, [])
                        all_tweets.extend(cached_tweets)
                        continue
                    
                    print(f"  🐦 Fetching: @{username}")
                    
                    # Get user ID first
                    user = client.get_user(username=username)
                    if not user.data:
                        print(f"  ❌ User @{username} not found")
                        continue
                    
                    user_id = user.data.id
                    
                    # Fetch recent tweets
                    tweets = client.get_users_tweets(
                        id=user_id,
                        max_results=max_tweets_per_account,
                        tweet_fields=['created_at', 'public_metrics', 'context_annotations'],
                        exclude=['retweets', 'replies']
                    )
                    
                    if not tweets.data:
                        print(f"  ⚠️  No recent tweets from @{username}")
                        continue
                    
                    user_tweets = []
                    for tweet in tweets.data:
                        # Filter for crypto-related content
                        if self._is_crypto_related(tweet.text):
                            tweet_data = {
                                'text': tweet.text,
                                'user': username,
                                'created_at': tweet.created_at,
                                'tweet_id': tweet.id,
                                'retweet_count': tweet.public_metrics.get('retweet_count', 0),
                                'like_count': tweet.public_metrics.get('like_count', 0),
                                'reply_count': tweet.public_metrics.get('reply_count', 0),
                                'quote_count': tweet.public_metrics.get('quote_count', 0),
                                'feed_type': 'X',
                                'url': f"https://twitter.com/{username}/status/{tweet.id}"
                            }
                            
                            # Filter for recent tweets (last 6 hours)
                            if self._is_recent_tweet(tweet.created_at):
                                user_tweets.append(tweet_data)
                    
                    # Cache the results
                    self.x_cache[cache_key] = user_tweets
                    self.last_fetch_time[cache_key] = datetime.now()
                    
                    all_tweets.extend(user_tweets)
                    successful_accounts += 1
                    
                    print(f"  ✅ {len(user_tweets)} crypto tweets from @{username}")
                    
                except tweepy.TooManyRequests:
                    print(f"  ⏳ Rate limit reached for @{username}")
                    break
                except Exception as e:
                    print(f"  ❌ Error fetching tweets from @{username}: {e}")
                    continue
        
        except Exception as e:
            print(f"❌ X API connection error: {e}")
            return self._get_mock_x_posts()
        
        print(f"📊 X Summary: {len(all_tweets)} tweets from {successful_accounts}/{len(usernames)} accounts")
        
        # Sort by creation date (newest first)
        all_tweets.sort(key=lambda x: x['created_at'], reverse=True)
        
        return all_tweets
    
    def analyze_reddit_trends(self, reddit_articles: List[Dict]) -> Dict:
        """
        Analyze Reddit posts to identify trending topics and sentiment
        Filters noise by focusing on patterns and frequency
        
        Args:
            reddit_articles: List of Reddit posts from RSS feeds
            
        Returns:
            Dictionary with trend analysis and top topics
        """
        if not reddit_articles:
            return {'trending_topics': [], 'sentiment': 'neutral', 'volume': 0}
        
        # Extract keywords and topics
        topic_frequency = {}
        sentiment_indicators = {'bullish': 0, 'bearish': 0, 'neutral': 0}
        total_posts = len(reddit_articles)
        
        # Common crypto terms to track
        crypto_terms = [
            'bitcoin', 'btc', 'ethereum', 'eth', 'polygon', 'matic', 'altcoin',
            'defi', 'nft', 'web3', 'pump', 'dump', 'moon', 'hodl', 'buy', 'sell',
            'bullish', 'bearish', 'rally', 'crash', 'dip', 'ath', 'support', 'resistance'
        ]
        
        # Analyze each post
        for article in reddit_articles:
            title_lower = article['title'].lower()
            source = article.get('source', '')
            
            # Count crypto term mentions
            for term in crypto_terms:
                if term in title_lower:
                    topic_frequency[term] = topic_frequency.get(term, 0) + 1
            
            # Sentiment analysis based on keywords
            if any(word in title_lower for word in ['pump', 'moon', 'bullish', 'rally', 'buy', 'ath']):
                sentiment_indicators['bullish'] += 1
            elif any(word in title_lower for word in ['dump', 'crash', 'bearish', 'sell', 'dip', 'bear']):
                sentiment_indicators['bearish'] += 1
            else:
                sentiment_indicators['neutral'] += 1
        
        # Identify trending topics (mentioned in >20% of posts)
        trending_threshold = max(1, total_posts * 0.2)
        trending_topics = [
            {'topic': topic, 'mentions': count, 'frequency': count/total_posts}
            for topic, count in topic_frequency.items()
            if count >= trending_threshold
        ]
        
        # Sort by frequency
        trending_topics.sort(key=lambda x: x['mentions'], reverse=True)
        
        # Determine overall sentiment
        max_sentiment = max(sentiment_indicators.values())
        if max_sentiment == sentiment_indicators['bullish']:
            overall_sentiment = 'bullish'
        elif max_sentiment == sentiment_indicators['bearish']:
            overall_sentiment = 'bearish'
        else:
            overall_sentiment = 'neutral'
        
        return {
            'trending_topics': trending_topics[:10],  # Top 10 trends
            'sentiment': overall_sentiment,
            'sentiment_breakdown': sentiment_indicators,
            'volume': total_posts,
            'analysis_time': datetime.now().isoformat(),
            'subreddit_activity': self._analyze_subreddit_activity(reddit_articles)
        }
    
    def _analyze_subreddit_activity(self, reddit_articles: List[Dict]) -> Dict:
        """Analyze activity levels by subreddit"""
        subreddit_counts = {}
        
        for article in reddit_articles:
            # Extract subreddit from source or URL
            source = article.get('source', '')
            if 'SatoshiStreetBets' in source or 'SatoshiStreetBets' in article.get('feed_url', ''):
                subreddit = 'SatoshiStreetBets'
            elif 'CryptoCurrency' in source or 'CryptoCurrency' in article.get('feed_url', ''):
                subreddit = 'CryptoCurrency'
            elif 'CryptoMoonShots' in source or 'CryptoMoonShots' in article.get('feed_url', ''):
                subreddit = 'CryptoMoonShots'
            else:
                subreddit = 'Unknown'
            
            subreddit_counts[subreddit] = subreddit_counts.get(subreddit, 0) + 1
        
        return subreddit_counts
    
    def fetch_from_benzinga(self, max_articles: int = 10) -> List[Dict]:
        """
        Fetch latest crypto news from Benzinga API
        
        Args:
            max_articles: Maximum articles to fetch
            
        Returns:
            List of Benzinga news articles
        """
        benzinga_api_key = getattr(config, 'BENZINGA_API_KEY', None)
        
        if not benzinga_api_key:
            print("⚠️  Benzinga API key not configured. Skipping Benzinga feed.")
            return []
        
        # Check cache age
        cache_key = "benzinga_news"
        if self._is_cache_fresh(cache_key, minutes=10):
            cached_articles = self.rss_cache.get(cache_key, [])
            print(f"📰 Using cached Benzinga articles: {len(cached_articles)} articles")
            return cached_articles
        
        try:
            print("📰 Fetching from Benzinga API...")
            
            # Benzinga News API endpoint
            url = "https://api.benzinga.com/api/v2/news"
            
            # Parameters for crypto-related news
            params = {
                'token': benzinga_api_key,
                'channels': 'Cryptocurrency',  # Focus on crypto channel
                'pagesize': max_articles,
                'displayOutput': 'full'
            }
            
            # Make request with SSL verification disabled
            session = requests.Session()
            session.verify = False
            
            # Suppress SSL warnings
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            headers = {
                'User-Agent': 'LLM-Crypto-Bot/1.0',
                'Accept': 'application/json'
            }
            
            response = session.get(url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if not data or not isinstance(data, list):
                print("⚠️  No valid data received from Benzinga API")
                return []
            
            articles = []
            for item in data:
                try:
                    # Parse the article data
                    article = {
                        'title': item.get('title', 'No title'),
                        'link': item.get('url', ''),
                        'published': self._parse_benzinga_date(item.get('created')),
                        'source': 'Benzinga',
                        'summary': item.get('teaser', '')[:300] + '...' if item.get('teaser') else '',
                        'feed_type': 'Benzinga_API',
                        'author': item.get('author', ''),
                        'stocks': item.get('stocks', []),  # Related stocks/tickers
                        'channels': item.get('channels', [])
                    }
                    
                    # Filter for recent articles (last 24 hours)
                    if self._is_recent_article(article['published'], hours=24):
                        articles.append(article)
                        
                except Exception as e:
                    print(f"  ⚠️  Error parsing Benzinga article: {e}")
                    continue
            
            # Cache the results
            self.rss_cache[cache_key] = articles
            self.last_fetch_time[cache_key] = datetime.now()
            
            print(f"✅ Fetched {len(articles)} recent articles from Benzinga")
            return articles
            
        except Exception as e:
            print(f"❌ Error fetching from Benzinga API: {e}")
            return []
    
    def _parse_benzinga_date(self, date_str: str) -> datetime:
        """Parse Benzinga date format"""
        try:
            if not date_str:
                return datetime.now() - timedelta(hours=1)
            
            # Benzinga typically uses ISO format: 2023-01-01T12:00:00Z
            from dateutil import parser
            return parser.parse(date_str)
        except:
            return datetime.now() - timedelta(hours=1)
    
    def _is_cache_fresh(self, cache_key: str, minutes: int) -> bool:
        """Check if cached data is still fresh"""
        if cache_key not in self.last_fetch_time:
            return False
        
        cache_age = datetime.now() - self.last_fetch_time[cache_key]
        return cache_age < timedelta(minutes=minutes)
    
    def _get_domain_name(self, url: str) -> str:
        """Extract domain name from URL"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc.replace('www.', '')
        except:
            return url
    
    def _parse_published_date(self, entry) -> datetime:
        """Parse published date from RSS entry"""
        try:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                import time
                return datetime.fromtimestamp(time.mktime(entry.published_parsed))
            elif hasattr(entry, 'published'):
                from dateutil import parser
                return parser.parse(entry.published)
            else:
                return datetime.now() - timedelta(hours=1)  # Default to 1 hour ago
        except:
            return datetime.now() - timedelta(hours=1)
    
    def _is_recent_article(self, published_date: datetime, hours: int = 24) -> bool:
        """Check if article is recent (within specified hours)"""
        if not published_date:
            return False
        
        # Handle timezone-aware vs naive datetime comparison
        if published_date.tzinfo:
            from datetime import timezone
            now = datetime.now(timezone.utc)
        else:
            now = datetime.now()
        
        age = now - published_date
        return age < timedelta(hours=hours)
    
    def _is_recent_tweet(self, created_at: datetime, hours: int = 6) -> bool:
        """Check if tweet is recent (within specified hours)"""
        if not created_at:
            return False
        
        # Handle timezone-aware datetime
        if created_at.tzinfo:
            from datetime import timezone
            now = datetime.now(timezone.utc)
        else:
            now = datetime.now()
        
        age = now - created_at
        return age < timedelta(hours=hours)
    
    def _is_crypto_related(self, text: str) -> bool:
        """Check if text content is crypto-related"""
        crypto_keywords = [
            'bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'blockchain',
            'defi', 'nft', 'web3', 'trading', 'hodl', 'altcoin', 'binance',
            'coinbase', 'doge', 'solana', 'cardano', 'polkadot', 'chainlink',
            'uniswap', 'aave', 'compound', 'yearn', 'sushi', 'pancake',
            'bnb', 'usdt', 'usdc', 'dai', 'maker', 'curve', 'synthetix'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in crypto_keywords)
    
    def _get_mock_x_posts(self) -> List[Dict]:
        """Return mock X posts for testing"""
        mock_posts = [
            {
                'text': 'Bitcoin continues to show strong fundamentals despite market volatility. Long-term outlook remains bullish.',
                'user': 'crypto_analyst',
                'created_at': datetime.now() - timedelta(minutes=30),
                'tweet_id': '1234567890',
                'retweet_count': 145,
                'like_count': 523,
                'reply_count': 67,
                'quote_count': 23,
                'feed_type': 'X',
                'url': 'https://twitter.com/crypto_analyst/status/1234567890'
            },
            {
                'text': 'Ethereum network activity reaching new highs. Developer adoption continues to grow exponentially.',
                'user': 'eth_researcher',
                'created_at': datetime.now() - timedelta(hours=1),
                'tweet_id': '1234567891',
                'retweet_count': 89,
                'like_count': 312,
                'reply_count': 45,
                'quote_count': 12,
                'feed_type': 'X',
                'url': 'https://twitter.com/eth_researcher/status/1234567891'
            },
            {
                'text': 'DeFi protocols showing resilience. Total value locked continues to stabilize around key support levels.',
                'user': 'defi_tracker',
                'created_at': datetime.now() - timedelta(hours=2),
                'tweet_id': '1234567892',
                'retweet_count': 67,
                'like_count': 198,
                'reply_count': 34,
                'quote_count': 8,
                'feed_type': 'X',
                'url': 'https://twitter.com/defi_tracker/status/1234567892'
            }
        ]
        
        return mock_posts

# Global connector instance
realtime_feeds = RealtimeFeedsConnector()

def fetch_from_rss_feeds(feed_urls: Optional[List[str]] = None, max_articles_per_feed: int = 10) -> List[Dict]:
    """
    Fetch latest articles from RSS feeds
    
    Args:
        feed_urls: List of RSS feed URLs (uses defaults if None)
        max_articles_per_feed: Maximum articles to fetch per feed
        
    Returns:
        List of articles
    """
    return realtime_feeds.fetch_from_rss_feeds(feed_urls, max_articles_per_feed)

def fetch_from_x_accounts(usernames: Optional[List[str]] = None, max_tweets_per_account: int = 5) -> List[Dict]:
    """
    Fetch latest posts from X (Twitter) accounts
    
    Args:
        usernames: List of X usernames (uses defaults if None)
        max_tweets_per_account: Maximum tweets to fetch per account
        
    Returns:
        List of tweets
    """
    return realtime_feeds.fetch_from_x_accounts(usernames, max_tweets_per_account)

def get_combined_realtime_feed(max_total_items: int = 50, include_cryptofeed: bool = True) -> List[Dict]:
    """
    Get combined feed from RSS sources, Benzinga API, Cryptofeed real-time data, and Reddit trend analysis
    
    Args:
        max_total_items: Maximum total items to return
        include_cryptofeed: Whether to include real-time market data from Cryptofeed
        
    Returns:
        Combined feed with news articles, Benzinga articles, real-time market data, and Reddit trend analysis
    """
    print("🔄 Fetching real-time feeds...")
    
    # Fetch from RSS sources (includes Reddit)
    all_articles = realtime_feeds.fetch_from_rss_feeds(max_articles_per_feed=15, include_reddit=True)
    
    # Fetch from Benzinga API
    benzinga_articles = realtime_feeds.fetch_from_benzinga(max_articles=15)
    
    # Fetch market data (Simple Market Data as primary, Cryptofeed as backup)
    market_data = None
    if include_cryptofeed:
        try:
            print("📊 Fetching current market data...")
            market_data = get_simple_market_data(['bitcoin', 'ethereum', 'solana', 'polygon'])
            
            if 'error' not in market_data:
                print("✅ Market data collected successfully")
            else:
                print(f"⚠️  Simple market data error: {market_data['error']}")
                # Try Cryptofeed as backup if simple method fails
                if CRYPTOFEED_AVAILABLE:
                    print("📊 Trying Cryptofeed as backup...")
                    market_data = get_cryptofeed_data(
                        symbols=['BTC-USD', 'ETH-USD', 'SOL-USD', 'MATIC-USD'],
                        duration=15  # Shorter duration to reduce threading issues
                    )
                else:
                    market_data = None
        except Exception as e:
            print(f"⚠️  Market data error: {e}")
            market_data = None
    
    # Fetch new coin opportunities
    new_coins = []
    try:
        print("🆕 Fetching new coin opportunities...")
        new_coins = get_new_coin_opportunities()
        print(f"✅ Found {len(new_coins)} new coin opportunities")
    except Exception as e:
        print(f"⚠️  New coin monitoring error: {e}")
        new_coins = []
    
    # Separate Reddit posts from news articles
    reddit_posts = [article for article in all_articles if article.get('is_reddit', False)]
    news_articles = [article for article in all_articles if not article.get('is_reddit', False)]
    
    print(f"📰 Fetched {len(news_articles)} RSS news articles")
    print(f"📈 Fetched {len(benzinga_articles)} Benzinga articles")
    if market_data and 'error' not in market_data:
        # Handle both simple market data and cryptofeed data formats
        if 'symbols_tracked' in market_data:
            print(f"📊 Collected market data: {len(market_data.get('symbols_tracked', []))} coins tracked")
        elif 'market_activity' in market_data:
            print(f"📊 Collected real-time data: {market_data.get('market_activity', {}).get('total_trades', 0)} trades")
    print(f"🔍 Analyzing {len(reddit_posts)} Reddit posts for trends...")
    
    # Analyze Reddit trends
    reddit_trends = realtime_feeds.analyze_reddit_trends(reddit_posts)
    
    # Disable X posts for now since API isn't working
    # x_posts = fetch_from_x_accounts(max_tweets_per_account=4)
    
    # Build combined feed with news and trend analysis
    combined_feed = []
    
    # Add RSS news articles
    for article in news_articles:
        combined_feed.append({
            'content': article['title'],
            'source': article['source'],
            'timestamp': article['published'],
            'type': 'article',
            'url': article['link'],
            'summary': article.get('summary', ''),
            'feed_type': 'RSS'
        })
    
    # Add Benzinga articles
    for article in benzinga_articles:
        combined_feed.append({
            'content': article['title'],
            'source': 'Benzinga',
            'timestamp': article['published'],
            'type': 'article',
            'url': article['link'],
            'summary': article.get('summary', ''),
            'feed_type': 'Benzinga_API',
            'author': article.get('author', ''),
            'stocks': article.get('stocks', []),
            'channels': article.get('channels', [])
        })
    
    # Add Reddit trend analysis as a special item
    if reddit_trends['volume'] > 0:
        combined_feed.append({
            'content': f"Reddit Trend Analysis: {reddit_trends['sentiment'].title()} sentiment detected",
            'source': 'Reddit Analysis',
            'timestamp': datetime.now(),
            'type': 'trend_analysis',
            'trends': reddit_trends,
            'feed_type': 'Reddit_Trends'
        })
    
    # Add market data as a special item
    if market_data and 'error' not in market_data:
        # Handle both simple market data and cryptofeed data formats
        if 'symbols_tracked' in market_data:
            # Simple market data format
            sentiment = market_data.get('overall_sentiment', 'neutral')
            coin_count = len(market_data.get('symbols_tracked', []))
            combined_feed.append({
                'content': f"Current Market Data: {sentiment.title()} sentiment, {coin_count} coins tracked",
                'source': 'Market Data API',
                'timestamp': datetime.now(),
                'type': 'market_data',
                'market_data': market_data,
                'feed_type': 'SimpleMarketData'
            })
        elif 'market_activity' in market_data:
            # Cryptofeed format
            activity = market_data.get('market_activity', {})
            combined_feed.append({
                'content': f"Real-Time Market Data: {activity.get('level', 'unknown').title()} activity with {activity.get('total_trades', 0)} trades",
                'source': 'Cryptofeed Real-Time',
                'timestamp': datetime.now(),
                'type': 'market_data',
                'market_data': market_data,
                'feed_type': 'Cryptofeed_RealTime'
            })
    
    # Add new coin opportunities as special items
    for coin in new_coins:
        coin_type = coin.get('type', 'unknown')
        if coin_type == 'trending':
            content = f"🔥 TRENDING: {coin['name']} ({coin['symbol']}) - CoinGecko Score: {coin.get('score', 0)}"
        elif coin_type == 'new_listing':
            # Use enhanced formatting based on opportunity type
            opportunity_type = coin.get('opportunity_type', 'high_volume_opportunity')
            if opportunity_type == 'low_volume_gem':
                content = f"💎 LOW VOLUME GEM: {coin['name']} ({coin['symbol']}) - ${coin.get('current_price', 0):.6f} ({coin.get('price_change_24h', 0):+.1f}% 24h) - EXPLOSIVE POTENTIAL"
            elif opportunity_type == 'medium_volume_momentum':
                content = f"🚀 MOMENTUM PLAY: {coin['name']} ({coin['symbol']}) - ${coin.get('current_price', 0):.6f} ({coin.get('price_change_24h', 0):+.1f}% 24h) - HIGH POTENTIAL"
            else:
                content = f"🆕 NEW OPPORTUNITY: {coin['name']} ({coin['symbol']}) - ${coin.get('current_price', 0):.6f} ({coin.get('price_change_24h', 0):+.1f}% 24h)"
        else:
            content = f"🪙 {coin['name']} ({coin['symbol']}) - New opportunity detected"
        
        combined_feed.append({
            'content': content,
            'source': coin.get('source', 'New Coin Monitor'),
            'timestamp': datetime.fromisoformat(coin['timestamp'].replace('Z', '+00:00')) if 'timestamp' in coin else datetime.now(),
            'type': 'new_coin',
            'coin_data': coin,
            'feed_type': 'NewCoins'
        })
    
    # Sort items with priority for special items, then by timestamp
    def get_sort_priority(item):
        # Special items get higher priority (lower number = higher priority)
        special_types = {'new_coin': 1, 'market_data': 2, 'trend_analysis': 3}
        priority = special_types.get(item['type'], 4)  # Regular articles get priority 4
        
        # Secondary sort by timestamp (newest first)
        timestamp = item['timestamp']
        if timestamp.tzinfo:
            timestamp_tuple = timestamp.utctimetuple()
        else:
            timestamp_tuple = timestamp.timetuple()
        
        return (priority, [-x for x in timestamp_tuple])  # Negative for reverse sort
    
    combined_feed.sort(key=get_sort_priority)
    
    # Limit total items but ensure we preserve at least some of each important type
    if len(combined_feed) > max_total_items:
        # Preserve special items and get a mix
        special_items = [item for item in combined_feed if item['type'] in ['new_coin', 'market_data', 'trend_analysis']]
        regular_items = [item for item in combined_feed if item['type'] not in ['new_coin', 'market_data', 'trend_analysis']]
        
        # Take all special items (they're usually few) + remaining regular items
        remaining_slots = max_total_items - len(special_items)
        if remaining_slots > 0:
            combined_feed = special_items + regular_items[:remaining_slots]
        else:
            combined_feed = special_items[:max_total_items]
    else:
        combined_feed = combined_feed[:max_total_items]
    
    total_articles = len(news_articles) + len(benzinga_articles)
    market_status = "Market data" if market_data and 'error' not in market_data else "No market data"
    new_coins_status = f"{len(new_coins)} new coins" if new_coins else "No new coins"
    print(f"📊 Combined feed: {len(combined_feed)} items ({len(news_articles)} RSS + {len(benzinga_articles)} Benzinga + Reddit trends + {market_status} + {new_coins_status})")
    
    return combined_feed

def format_realtime_feed_for_llm(feed_items: List[Dict]) -> str:
    """
    Format real-time feed items for LLM consumption with Reddit trend analysis
    
    Args:
        feed_items: List of combined feed items including trend analysis
        
    Returns:
        Formatted string for LLM
    """
    if not feed_items:
        return "No recent real-time feed data available."
    
    formatted_feed = "REAL-TIME CRYPTO FEED:\n\n"
    
    # Process items and format appropriately
    article_count = 0
    trend_analysis_included = False
    
    for i, item in enumerate(feed_items[:25], 1):  # Increased limit for better analysis
        time_ago = _get_time_ago(item['timestamp'])
        
        if item['type'] == 'trend_analysis':
            # Special formatting for Reddit trend analysis
            trends = item.get('trends', {})
            formatted_feed += f"🔍 [REDDIT TREND ANALYSIS] ({time_ago})\n"
            formatted_feed += f"   Overall Sentiment: {trends.get('sentiment', 'neutral').upper()}\n"
            formatted_feed += f"   Posts Analyzed: {trends.get('volume', 0)} across crypto subreddits\n"
            
            # Include top trending topics
            trending_topics = trends.get('trending_topics', [])
            if trending_topics:
                formatted_feed += f"   Top Trends: "
                top_3_trends = trending_topics[:3]
                trend_strs = [f"{t['topic']} ({t['mentions']})" for t in top_3_trends]
                formatted_feed += ", ".join(trend_strs) + "\n"
            
            # Include subreddit activity
            subreddit_activity = trends.get('subreddit_activity', {})
            if subreddit_activity:
                formatted_feed += f"   Activity: "
                activity_strs = [f"{sub}: {count}" for sub, count in subreddit_activity.items()]
                formatted_feed += ", ".join(activity_strs) + "\n"
            
            trend_analysis_included = True
        
        elif item['type'] == 'market_data':
            # Special formatting for market data (simple or cryptofeed)
            market_data = item.get('market_data', {})
            
            if 'symbols_tracked' in market_data:
                # Simple market data format
                formatted_feed += f"📊 [CURRENT MARKET DATA] ({time_ago})\n"
                sentiment = market_data.get('overall_sentiment', 'neutral')
                formatted_feed += f"   Market Sentiment: {sentiment.upper()}\n"
                
                # Include price information
                prices = market_data.get('prices', {})
                if prices:
                    formatted_feed += f"   Current Prices: "
                    price_strs = []
                    for coin_id, data in list(prices.items())[:3]:
                        price = data.get('price_usd', 0)
                        change = data.get('change_24h_percent', 0)
                        trend = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                        price_strs.append(f"{coin_id.upper()}: ${price:.4f} ({change:+.1f}%) {trend}")
                    formatted_feed += ", ".join(price_strs) + "\n"
                
                # Include trending coins
                trending = market_data.get('trending_coins', [])
                if trending:
                    trending_names = [coin['symbol'] for coin in trending[:3]]
                    formatted_feed += f"   Trending: {', '.join(trending_names)}\n"
                    
            elif 'market_activity' in market_data:
                # Cryptofeed format
                activity = market_data.get('market_activity', {})
                formatted_feed += f"📊 [REAL-TIME MARKET DATA] ({time_ago})\n"
                formatted_feed += f"   Activity Level: {activity.get('level', 'unknown').upper()}\n"
                formatted_feed += f"   Total Trades: {activity.get('total_trades', 0)} in {activity.get('collection_duration', 'unknown')}\n"
                
                # Include ticker information
                tickers = market_data.get('tickers', {})
                if tickers:
                    formatted_feed += f"   Current Prices: "
                    price_strs = [f"{symbol}: ${ticker['bid']:.2f}-${ticker['ask']:.2f}" for symbol, ticker in list(tickers.items())[:3]]
                    formatted_feed += ", ".join(price_strs) + "\n"
        
        elif item['type'] == 'new_coin':
            # Special formatting for new coin opportunities
            coin_data = item.get('coin_data', {})
            coin_type = coin_data.get('type', 'unknown')
            
            if coin_type == 'trending':
                formatted_feed += f"🔥 [TRENDING COIN] ({time_ago})\n"
                formatted_feed += f"   {coin_data['name']} ({coin_data['symbol']})\n"
                formatted_feed += f"   CoinGecko Trending Score: {coin_data.get('score', 0)}\n"
                if coin_data.get('market_cap_rank'):
                    formatted_feed += f"   Market Cap Rank: #{coin_data['market_cap_rank']}\n"
                formatted_feed += f"   Source: {coin_data.get('source', 'Unknown')}\n"
                
            elif coin_type == 'new_listing':
                opportunity_type = coin_data.get('opportunity_type', 'high_volume_opportunity')
                
                if opportunity_type == 'low_volume_gem':
                    formatted_feed += f"💎 [LOW VOLUME GEM] ({time_ago})\n"
                    formatted_feed += f"   {coin_data['name']} ({coin_data['symbol']}) - EXPLOSIVE POTENTIAL\n"
                elif opportunity_type == 'medium_volume_momentum':
                    formatted_feed += f"🚀 [MOMENTUM PLAY] ({time_ago})\n"
                    formatted_feed += f"   {coin_data['name']} ({coin_data['symbol']}) - HIGH POTENTIAL\n"
                else:
                    formatted_feed += f"🆕 [NEW OPPORTUNITY] ({time_ago})\n"
                    formatted_feed += f"   {coin_data['name']} ({coin_data['symbol']})\n"
                    
                formatted_feed += f"   Current Price: ${coin_data.get('current_price', 0):.6f}\n"
                formatted_feed += f"   24h Change: {coin_data.get('price_change_24h', 0):+.1f}%\n"
                formatted_feed += f"   24h Volume: ${coin_data.get('total_volume', 0):,.0f}\n"
                formatted_feed += f"   Market Cap Rank: #{coin_data.get('market_cap_rank', 'N/A')}\n"
                
                # Add enhanced opportunity info
                if coin_data.get('potential_return'):
                    formatted_feed += f"   Potential Return: {coin_data['potential_return']}\n"
                if coin_data.get('risk_level'):
                    formatted_feed += f"   Risk Level: {coin_data['risk_level']}\n"
                    
                formatted_feed += f"   Source: {coin_data.get('source', 'Unknown')}\n"
                
            else:
                formatted_feed += f"🪙 [NEW COIN DETECTED] ({time_ago})\n"
                formatted_feed += f"   {coin_data.get('name', 'Unknown')} ({coin_data.get('symbol', 'UNKNOWN')})\n"
                formatted_feed += f"   Source: {coin_data.get('source', 'Unknown')}\n"
        
        else:
            # Regular article formatting
            if item.get('feed_type') == 'Benzinga_API':
                type_emoji = "📈"  # Special emoji for Benzinga
            else:
                type_emoji = "📰" if item['type'] == 'article' else "🐦"
            
            formatted_feed += f"{i}. {type_emoji} [{item['source']}] ({time_ago})\n"
            formatted_feed += f"   {item['content']}\n"
            
            # Add summary if available
            if item.get('summary'):
                formatted_feed += f"   Summary: {item['summary']}\n"
            
            # Add Benzinga-specific data
            if item.get('feed_type') == 'Benzinga_API':
                if item.get('author'):
                    formatted_feed += f"   Author: {item['author']}\n"
                if item.get('stocks'):
                    # Handle stocks - they might be strings or dicts
                    stock_names = []
                    for stock in item['stocks'][:5]:  # Limit to 5 stocks
                        if isinstance(stock, dict):
                            # Extract name from stock dict (Benzinga format)
                            stock_names.append(stock.get('name', str(stock)))
                        else:
                            # It's already a string
                            stock_names.append(str(stock))
                    stocks_str = ', '.join(stock_names)
                    formatted_feed += f"   Related Stocks: {stocks_str}\n"
            
            if item['type'] == 'tweet' and 'engagement' in item:
                formatted_feed += f"   💬 Engagement: {item['engagement']} interactions\n"
            
            article_count += 1
        
        formatted_feed += "\n"
    
    # Add summary footer
    formatted_feed += f"FEED SUMMARY:\n"
    formatted_feed += f"- {article_count} news articles analyzed (RSS + Benzinga professional feeds)\n"
    if trend_analysis_included:
        formatted_feed += f"- Reddit trend analysis included (filters noise by focusing on patterns)\n"
    formatted_feed += f"- Premium Benzinga financial news included for professional insights\n"
    formatted_feed += f"- Current market data with prices, trends, and sentiment analysis\n"
    formatted_feed += f"- Data freshness: Live market data + last 12-24 hours for news\n"
    
    return formatted_feed

def _get_time_ago(timestamp: datetime) -> str:
    """Get human-readable time ago string"""
    try:
        if timestamp.tzinfo:
            from datetime import timezone
            now = datetime.now(timezone.utc)
        else:
            now = datetime.now()
        
        diff = now - timestamp
        
        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours}h ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes}m ago"
        else:
            return "just now"
    except:
        return "unknown"