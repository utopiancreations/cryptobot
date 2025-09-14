"""
CoinMarketCap DEX API Integration
Provides real-time market data, price feeds, and trading intelligence
"""

import requests
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import config

class CoinMarketCapAPI:
    """CoinMarketCap API client for market data and trading intelligence"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or config.COINMARKETCAP_API_KEY
        self.base_url = "https://pro-api.coinmarketcap.com/v1"
        self.session = requests.Session()

        if self.api_key:
            self.session.headers.update({
                'X-CMC_PRO_API_KEY': self.api_key,
                'Accept': 'application/json',
                'Accept-Encoding': 'deflate, gzip'
            })

    def get_token_quotes(self, symbols: List[str], convert: str = 'USD') -> Dict:
        """Get latest market quotes for tokens"""
        try:
            symbols_str = ','.join(symbols)
            url = f"{self.base_url}/cryptocurrency/quotes/latest"

            params = {
                'symbol': symbols_str,
                'convert': convert
            }

            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            if data.get('status', {}).get('error_code') == 0:
                return self._process_quotes(data.get('data', {}))
            else:
                print(f"CMC API Error: {data.get('status', {}).get('error_message', 'Unknown error')}")
                return {}

        except Exception as e:
            print(f"Error fetching token quotes: {e}")
            return {}

    def get_trending_tokens(self, limit: int = 50) -> List[Dict]:
        """Get trending/gainers tokens for potential trading opportunities"""
        try:
            url = f"{self.base_url}/cryptocurrency/trending/latest"

            params = {
                'limit': min(limit, 100),
                'convert': 'USD'
            }

            response = self.session.get(url, params=params)

            if response.status_code == 403:
                print("⚠️  Trending tokens require CMC premium plan - skipping")
                return []

            response.raise_for_status()

            data = response.json()

            if data.get('status', {}).get('error_code') == 0:
                return self._process_trending(data.get('data', []))
            else:
                print(f"CMC Trending API Error: {data.get('status', {}).get('error_message')}")
                return []

        except Exception as e:
            if "403" in str(e):
                print("⚠️  Trending tokens require CMC premium plan - skipping")
            else:
                print(f"Error fetching trending tokens: {e}")
            return []

    def get_top_gainers(self, limit: int = 20, time_period: str = '24h') -> List[Dict]:
        """Get top gaining tokens for trading opportunities"""
        try:
            url = f"{self.base_url}/cryptocurrency/trending/gainers-losers"

            params = {
                'limit': min(limit, 100),
                'time_period': time_period,
                'convert': 'USD'
            }

            response = self.session.get(url, params=params)

            if response.status_code == 403:
                print("⚠️  Top gainers require CMC premium plan - skipping")
                return []

            response.raise_for_status()

            data = response.json()

            if data.get('status', {}).get('error_code') == 0:
                gainers = data.get('data', {}).get('gainers', [])
                return self._process_gainers_losers(gainers)
            else:
                print(f"CMC Gainers API Error: {data.get('status', {}).get('error_message')}")
                return []

        except Exception as e:
            if "403" in str(e):
                print("⚠️  Top gainers require CMC premium plan - skipping")
            else:
                print(f"Error fetching gainers: {e}")
            return []

    def get_token_info(self, symbol: str) -> Dict:
        """Get detailed token information"""
        try:
            url = f"{self.base_url}/cryptocurrency/info"

            params = {
                'symbol': symbol
            }

            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            if data.get('status', {}).get('error_code') == 0:
                token_data = data.get('data', {}).get(symbol)
                if token_data:
                    return self._process_token_info(token_data)

            return {}

        except Exception as e:
            print(f"Error fetching token info for {symbol}: {e}")
            return {}

    def get_market_cap_rankings(self, start: int = 1, limit: int = 100) -> List[Dict]:
        """Get market cap rankings for market overview"""
        try:
            url = f"{self.base_url}/cryptocurrency/listings/latest"

            params = {
                'start': start,
                'limit': min(limit, 5000),
                'convert': 'USD',
                'sort': 'market_cap',
                'sort_dir': 'desc'
            }

            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            if data.get('status', {}).get('error_code') == 0:
                return self._process_listings(data.get('data', []))
            else:
                print(f"CMC Rankings API Error: {data.get('status', {}).get('error_message')}")
                return []

        except Exception as e:
            print(f"Error fetching market rankings: {e}")
            return []

    def get_fear_greed_index(self) -> Dict:
        """Get market sentiment indicator"""
        try:
            # Note: CMC doesn't have fear/greed directly, so we'll derive from market data
            top_tokens = self.get_market_cap_rankings(limit=50)

            if not top_tokens:
                return {'index': 50, 'classification': 'neutral'}

            # Calculate sentiment based on 24h changes
            changes = [token.get('percent_change_24h', 0) for token in top_tokens if token.get('percent_change_24h')]

            if changes:
                avg_change = sum(changes) / len(changes)
                positive_count = len([c for c in changes if c > 0])
                positive_ratio = positive_count / len(changes)

                # Derive fear/greed index (0-100)
                sentiment_score = 50 + (avg_change * 2) + ((positive_ratio - 0.5) * 50)
                sentiment_score = max(0, min(100, sentiment_score))

                if sentiment_score >= 75:
                    classification = 'extreme_greed'
                elif sentiment_score >= 55:
                    classification = 'greed'
                elif sentiment_score >= 45:
                    classification = 'neutral'
                elif sentiment_score >= 25:
                    classification = 'fear'
                else:
                    classification = 'extreme_fear'

                return {
                    'index': round(sentiment_score),
                    'classification': classification,
                    'avg_change_24h': round(avg_change, 2),
                    'positive_ratio': round(positive_ratio, 2)
                }

            return {'index': 50, 'classification': 'neutral'}

        except Exception as e:
            print(f"Error calculating market sentiment: {e}")
            return {'index': 50, 'classification': 'neutral'}

    def search_tokens(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for tokens by name or symbol"""
        try:
            # CMC doesn't have a dedicated search endpoint in basic API
            # We'll use the listings endpoint with filtering
            all_tokens = self.get_market_cap_rankings(limit=1000)

            query_lower = query.lower()
            matches = []

            for token in all_tokens:
                symbol = token.get('symbol', '').lower()
                name = token.get('name', '').lower()

                if (query_lower in symbol or
                    query_lower in name or
                    symbol.startswith(query_lower)):
                    matches.append(token)

                if len(matches) >= limit:
                    break

            return matches

        except Exception as e:
            print(f"Error searching tokens: {e}")
            return []

    def _process_quotes(self, data: Dict) -> Dict:
        """Process quotes API response"""
        processed = {}

        for symbol, token_data in data.items():
            quote = token_data.get('quote', {}).get('USD', {})

            processed[symbol] = {
                'symbol': token_data.get('symbol'),
                'name': token_data.get('name'),
                'price': quote.get('price'),
                'market_cap': quote.get('market_cap'),
                'volume_24h': quote.get('volume_24h'),
                'percent_change_1h': quote.get('percent_change_1h'),
                'percent_change_24h': quote.get('percent_change_24h'),
                'percent_change_7d': quote.get('percent_change_7d'),
                'last_updated': quote.get('last_updated'),
                'cmc_rank': token_data.get('cmc_rank')
            }

        return processed

    def _process_trending(self, data: List) -> List[Dict]:
        """Process trending API response"""
        processed = []

        for item in data:
            quote = item.get('quote', {}).get('USD', {})

            processed.append({
                'symbol': item.get('symbol'),
                'name': item.get('name'),
                'price': quote.get('price'),
                'percent_change_24h': quote.get('percent_change_24h'),
                'market_cap': quote.get('market_cap'),
                'volume_24h': quote.get('volume_24h'),
                'cmc_rank': item.get('cmc_rank')
            })

        return processed

    def _process_gainers_losers(self, data: List) -> List[Dict]:
        """Process gainers/losers API response"""
        processed = []

        for item in data:
            quote = item.get('quote', {}).get('USD', {})

            processed.append({
                'symbol': item.get('symbol'),
                'name': item.get('name'),
                'price': quote.get('price'),
                'percent_change_24h': quote.get('percent_change_24h'),
                'market_cap': quote.get('market_cap'),
                'volume_24h': quote.get('volume_24h'),
                'cmc_rank': item.get('cmc_rank')
            })

        return processed

    def _process_token_info(self, data: Dict) -> Dict:
        """Process token info API response"""
        return {
            'symbol': data.get('symbol'),
            'name': data.get('name'),
            'description': data.get('description'),
            'category': data.get('category'),
            'tags': data.get('tags', []),
            'platform': data.get('platform'),
            'urls': data.get('urls', {}),
            'logo': data.get('logo'),
            'date_added': data.get('date_added')
        }

    def _process_listings(self, data: List) -> List[Dict]:
        """Process listings API response"""
        processed = []

        for item in data:
            quote = item.get('quote', {}).get('USD', {})

            processed.append({
                'symbol': item.get('symbol'),
                'name': item.get('name'),
                'price': quote.get('price'),
                'market_cap': quote.get('market_cap'),
                'volume_24h': quote.get('volume_24h'),
                'percent_change_1h': quote.get('percent_change_1h'),
                'percent_change_24h': quote.get('percent_change_24h'),
                'percent_change_7d': quote.get('percent_change_7d'),
                'cmc_rank': item.get('cmc_rank'),
                'circulating_supply': item.get('circulating_supply'),
                'total_supply': item.get('total_supply'),
                'max_supply': item.get('max_supply')
            })

        return processed

# Global API instance
_cmc_api = None

def get_cmc_api() -> CoinMarketCapAPI:
    """Get global CoinMarketCap API instance"""
    global _cmc_api
    if _cmc_api is None:
        _cmc_api = CoinMarketCapAPI()
    return _cmc_api

def get_market_data_for_trading(symbols: List[str] = None) -> Dict:
    """Get comprehensive market data for trading decisions"""
    cmc = get_cmc_api()

    market_data = {
        'timestamp': datetime.now().isoformat(),
        'sentiment': {},
        'top_gainers': [],
        'trending': [],
        'token_quotes': {},
        'market_overview': []
    }

    try:
        # Get market sentiment
        print("📊 Fetching market sentiment...")
        market_data['sentiment'] = cmc.get_fear_greed_index()

        # Get top gainers for opportunities
        print("🚀 Fetching top gainers...")
        market_data['top_gainers'] = cmc.get_top_gainers(limit=10)

        # Get trending tokens
        print("📈 Fetching trending tokens...")
        market_data['trending'] = cmc.get_trending_tokens(limit=20)

        # Get specific token quotes if requested
        if symbols:
            print(f"💰 Fetching quotes for: {', '.join(symbols)}")
            market_data['token_quotes'] = cmc.get_token_quotes(symbols)

        # Get market overview
        print("🌍 Fetching market overview...")
        market_data['market_overview'] = cmc.get_market_cap_rankings(limit=50)

        return market_data

    except Exception as e:
        print(f"Error fetching comprehensive market data: {e}")
        return market_data

def test_cmc_api() -> bool:
    """Test CoinMarketCap API connectivity"""
    try:
        cmc = get_cmc_api()

        if not cmc.api_key:
            print("❌ CoinMarketCap API key not configured")
            return False

        # Test with a simple quote request
        test_data = cmc.get_token_quotes(['BTC', 'ETH'])

        if test_data:
            print("✅ CoinMarketCap API connection successful")
            btc_price = test_data.get('BTC', {}).get('price')
            if btc_price:
                print(f"   BTC Price: ${btc_price:,.2f}")
            return True
        else:
            print("❌ CoinMarketCap API test failed")
            return False

    except Exception as e:
        print(f"❌ CoinMarketCap API test error: {e}")
        return False

def format_market_data_for_llm(market_data: Dict) -> str:
    """Format market data for LLM consumption"""

    formatted = "REAL-TIME MARKET DATA:\n"
    formatted += "=" * 50 + "\n\n"

    # Market sentiment
    sentiment = market_data.get('sentiment', {})
    if sentiment:
        formatted += f"📊 MARKET SENTIMENT:\n"
        formatted += f"Fear/Greed Index: {sentiment.get('index', 50)}/100 ({sentiment.get('classification', 'neutral').upper()})\n"
        if 'avg_change_24h' in sentiment:
            formatted += f"Market Average 24h: {sentiment['avg_change_24h']:.2f}%\n"
        formatted += "\n"

    # Top gainers
    gainers = market_data.get('top_gainers', [])[:5]
    if gainers:
        formatted += f"🚀 TOP GAINERS (24h):\n"
        for i, token in enumerate(gainers, 1):
            change = token.get('percent_change_24h', 0)
            price = token.get('price', 0)
            formatted += f"{i}. {token.get('symbol', 'N/A')} ({token.get('name', 'Unknown')}): +{change:.2f}% (${price:.6f})\n"
        formatted += "\n"

    # Trending tokens
    trending = market_data.get('trending', [])[:5]
    if trending:
        formatted += f"📈 TRENDING TOKENS:\n"
        for i, token in enumerate(trending, 1):
            change = token.get('percent_change_24h', 0)
            price = token.get('price', 0)
            formatted += f"{i}. {token.get('symbol', 'N/A')} ({token.get('name', 'Unknown')}): {change:.2f}% (${price:.6f})\n"
        formatted += "\n"

    # Market overview
    overview = market_data.get('market_overview', [])[:10]
    if overview:
        formatted += f"🌍 TOP 10 BY MARKET CAP:\n"
        for token in overview:
            change = token.get('percent_change_24h', 0)
            mcap = token.get('market_cap', 0)
            formatted += f"#{token.get('cmc_rank', 0)} {token.get('symbol', 'N/A')}: {change:.2f}% (${mcap/1e9:.1f}B)\n"
        formatted += "\n"

    formatted += f"Data updated: {market_data.get('timestamp', 'Unknown')}\n"

    return formatted