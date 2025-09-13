import feedparser
import tweepy
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import config

class RealtimeFeedsConnector:
    """Real-time data connector for RSS feeds and X (Twitter) posts"""
    
    def __init__(self):
        self.rss_cache = {}
        self.x_cache = {}
        self.last_fetch_time = {}
        
        # Predefined crypto RSS feeds
        self.crypto_rss_feeds = [
            'https://cointelegraph.com/rss',
            'https://coindesk.com/arc/outboundfeeds/rss/',
            'https://decrypt.co/feed',
            'https://blockworks.co/feed/',
            'https://theblock.co/rss.xml',
            'https://cryptopotato.com/feed/',
            'https://cryptoslate.com/feed/'
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
    
    def fetch_from_rss_feeds(self, feed_urls: Optional[List[str]] = None, max_articles_per_feed: int = 10) -> List[Dict]:
        """
        Fetch latest articles from RSS feeds
        
        Args:
            feed_urls: List of RSS feed URLs (uses defaults if None)
            max_articles_per_feed: Maximum articles to fetch per feed
            
        Returns:
            List of articles with title, link, published date, and source
        """
        if feed_urls is None:
            feed_urls = self.crypto_rss_feeds
        
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
                
                # Fetch feed with timeout
                print(f"  📰 Fetching: {self._get_domain_name(feed_url)}")
                
                feed = feedparser.parse(feed_url)
                
                if feed.bozo and feed.bozo_exception:
                    print(f"  ⚠️  Feed parsing issue for {feed_url}: {feed.bozo_exception}")
                    continue
                
                feed_articles = []
                entries = feed.entries[:max_articles_per_feed]
                
                for entry in entries:
                    article = {
                        'title': entry.get('title', 'No title'),
                        'link': entry.get('link', ''),
                        'published': self._parse_published_date(entry),
                        'source': feed.feed.get('title', self._get_domain_name(feed_url)),
                        'summary': entry.get('summary', '')[:200] + '...' if entry.get('summary') else '',
                        'feed_type': 'RSS',
                        'feed_url': feed_url
                    }
                    
                    # Filter for recent articles (last 24 hours)
                    if self._is_recent_article(article['published']):
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
        
        age = datetime.now() - published_date
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

def get_combined_realtime_feed(max_total_items: int = 50) -> List[Dict]:
    """
    Get combined feed from both RSS and X sources
    
    Args:
        max_total_items: Maximum total items to return
        
    Returns:
        Combined and sorted list of articles and tweets
    """
    print("🔄 Fetching real-time feeds...")
    
    # Fetch from both sources
    rss_articles = fetch_from_rss_feeds(max_articles_per_feed=8)
    x_posts = fetch_from_x_accounts(max_tweets_per_account=4)
    
    # Combine and sort by timestamp
    combined_feed = []
    
    # Add RSS articles
    for article in rss_articles:
        combined_feed.append({
            'content': article['title'],
            'source': article['source'],
            'timestamp': article['published'],
            'type': 'article',
            'url': article['link'],
            'summary': article.get('summary', ''),
            'feed_type': 'RSS'
        })
    
    # Add X posts
    for tweet in x_posts:
        combined_feed.append({
            'content': tweet['text'],
            'source': f"@{tweet['user']}",
            'timestamp': tweet['created_at'],
            'type': 'tweet',
            'url': tweet['url'],
            'engagement': tweet['like_count'] + tweet['retweet_count'],
            'feed_type': 'X'
        })
    
    # Sort by timestamp (newest first)
    combined_feed.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Limit total items
    combined_feed = combined_feed[:max_total_items]
    
    print(f"📊 Combined feed: {len(combined_feed)} items ({len(rss_articles)} articles + {len(x_posts)} tweets)")
    
    return combined_feed

def format_realtime_feed_for_llm(feed_items: List[Dict]) -> str:
    """
    Format real-time feed items for LLM consumption
    
    Args:
        feed_items: List of combined feed items
        
    Returns:
        Formatted string for LLM
    """
    if not feed_items:
        return "No recent real-time feed data available."
    
    formatted_feed = "REAL-TIME CRYPTO FEED:\n\n"
    
    for i, item in enumerate(feed_items[:20], 1):  # Limit to top 20
        time_ago = _get_time_ago(item['timestamp'])
        
        type_emoji = "📰" if item['type'] == 'article' else "🐦"
        
        formatted_feed += f"{i}. {type_emoji} [{item['source']}] ({time_ago})\n"
        formatted_feed += f"   {item['content']}\n"
        
        if item['type'] == 'tweet' and 'engagement' in item:
            formatted_feed += f"   💬 Engagement: {item['engagement']} interactions\n"
        
        formatted_feed += "\n"
    
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