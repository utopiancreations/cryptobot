import requests
import json
from typing import List, Dict, Optional
from datetime import datetime
import config

def fetch_crypto_news(limit: int = 20) -> List[Dict]:
    """
    Fetch latest crypto news from CryptoPanic API
    
    Args:
        limit: Maximum number of news articles to fetch
        
    Returns:
        List of news articles with title, url, published_at, and source
    """
    if not config.CRYPTO_PANIC_API_KEY:
        print("Warning: CRYPTO_PANIC_API_KEY not configured. Using mock data.")
        return _get_mock_news()
    
    url = "https://cryptopanic.com/api/v1/posts/"
    params = {
        'auth_token': config.CRYPTO_PANIC_API_KEY,
        'public': 'true',
        'kind': 'news',
        'filter': 'rising',
        'currencies': 'BTC,ETH,BNB',
        'limit': limit
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        articles = []
        
        for post in data.get('results', []):
            article = {
                'title': post.get('title', ''),
                'url': post.get('url', ''),
                'published_at': post.get('published_at', ''),
                'source': post.get('source', {}).get('title', 'Unknown'),
                'sentiment': _extract_sentiment(post),
                'currencies': [currency['code'] for currency in post.get('currencies', [])]
            }
            articles.append(article)
        
        print(f"Successfully fetched {len(articles)} news articles")
        return articles
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching news: {e}")
        return _get_mock_news()
    except json.JSONDecodeError as e:
        print(f"Error parsing news response: {e}")
        return _get_mock_news()

def _extract_sentiment(post: Dict) -> str:
    """Extract sentiment from post metadata"""
    votes = post.get('votes', {})
    positive = votes.get('positive', 0)
    negative = votes.get('negative', 0)
    
    if positive > negative:
        return 'positive'
    elif negative > positive:
        return 'negative'
    else:
        return 'neutral'

def _get_mock_news() -> List[Dict]:
    """Return mock news data for testing when API is unavailable"""
    return [
        {
            'title': 'Bitcoin reaches new monthly high amid institutional adoption',
            'url': 'https://example.com/btc-high',
            'published_at': datetime.now().isoformat(),
            'source': 'CoinDesk',
            'sentiment': 'positive',
            'currencies': ['BTC']
        },
        {
            'title': 'Ethereum network upgrade shows promising scalability improvements',
            'url': 'https://example.com/eth-upgrade',
            'published_at': datetime.now().isoformat(),
            'source': 'CoinTelegraph',
            'sentiment': 'positive',
            'currencies': ['ETH']
        },
        {
            'title': 'Binance announces new trading pairs and reduced fees',
            'url': 'https://example.com/bnb-pairs',
            'published_at': datetime.now().isoformat(),
            'source': 'Binance Blog',
            'sentiment': 'positive',
            'currencies': ['BNB']
        }
    ]

def format_news_for_llm(articles: List[Dict]) -> str:
    """
    Format news articles into a readable string for LLM consumption
    
    Args:
        articles: List of news articles
        
    Returns:
        Formatted string containing news summary
    """
    if not articles:
        return "No recent crypto news available."
    
    formatted_news = "RECENT CRYPTO NEWS:\n\n"
    
    for i, article in enumerate(articles[:10], 1):  # Limit to top 10
        sentiment_emoji = {
            'positive': '📈',
            'negative': '📉',
            'neutral': '➡️'
        }.get(article['sentiment'], '➡️')
        
        currencies = ', '.join(article['currencies']) if article['currencies'] else 'General'
        
        formatted_news += f"{i}. {sentiment_emoji} [{currencies}] {article['title']}\n"
        formatted_news += f"   Source: {article['source']}\n\n"
    
    return formatted_news

def get_market_sentiment() -> Dict:
    """
    Analyze overall market sentiment from news
    
    Returns:
        Dictionary with sentiment analysis
    """
    articles = fetch_crypto_news(50)  # Get more articles for better sentiment analysis
    
    if not articles:
        return {'overall': 'neutral', 'confidence': 0.0, 'article_count': 0}
    
    sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
    
    for article in articles:
        sentiment = article.get('sentiment', 'neutral')
        sentiment_counts[sentiment] += 1
    
    total_articles = len(articles)
    positive_ratio = sentiment_counts['positive'] / total_articles
    negative_ratio = sentiment_counts['negative'] / total_articles
    
    if positive_ratio > 0.6:
        overall_sentiment = 'bullish'
        confidence = positive_ratio
    elif negative_ratio > 0.6:
        overall_sentiment = 'bearish'
        confidence = negative_ratio
    else:
        overall_sentiment = 'neutral'
        confidence = max(positive_ratio, negative_ratio)
    
    return {
        'overall': overall_sentiment,
        'confidence': confidence,
        'article_count': total_articles,
        'breakdown': sentiment_counts
    }