"""
Simple Market Data Collector

A reliable alternative to Cryptofeed that uses public APIs
without authentication requirements or threading issues.
"""

import requests
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

class SimpleMarketDataCollector:
    """Simple market data collector using public APIs"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'LLM-Crypto-Bot/1.0'
        })
        
    def get_market_data(self, symbols: List[str] = None) -> Dict[str, Any]:
        """
        Get current market data for specified symbols
        
        Args:
            symbols: List of symbols like ['BTC', 'ETH', 'SOL', 'MATIC']
            
        Returns:
            Market data dictionary
        """
        if symbols is None:
            symbols = ['bitcoin', 'ethereum', 'solana', 'polygon']
        
        # Convert to CoinGecko IDs
        symbol_map = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum', 
            'SOL': 'solana',
            'MATIC': 'polygon',
            'bitcoin': 'bitcoin',
            'ethereum': 'ethereum',
            'solana': 'solana',
            'polygon': 'polygon'
        }
        
        coingecko_ids = []
        for symbol in symbols:
            symbol_clean = symbol.replace('-USD', '').replace('USD', '').upper()
            gecko_id = symbol_map.get(symbol_clean, symbol_map.get(symbol, symbol.lower()))
            coingecko_ids.append(gecko_id)
        
        try:
            print(f"📊 Fetching market data for {len(coingecko_ids)} coins...")
            
            # Get current prices from CoinGecko (free, no auth required)
            price_url = "https://api.coingecko.com/api/v3/simple/price"
            price_params = {
                'ids': ','.join(coingecko_ids),
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true',
                'include_market_cap': 'true'
            }
            
            response = self.session.get(price_url, params=price_params, timeout=10)
            response.raise_for_status()
            price_data = response.json()
            
            # Get trending coins
            trending_url = "https://api.coingecko.com/api/v3/search/trending"
            trending_response = self.session.get(trending_url, timeout=10)
            trending_response.raise_for_status()
            trending_data = trending_response.json()
            
            # Process the data
            market_summary = {
                'timestamp': datetime.now().isoformat(),
                'data_source': 'CoinGecko Public API',
                'symbols_tracked': list(price_data.keys()),
                'prices': {},
                'market_analysis': {},
                'trending_coins': [],
                'overall_sentiment': 'neutral'
            }
            
            # Process price data
            total_change = 0
            positive_changes = 0
            total_coins = 0
            
            for coin_id, data in price_data.items():
                price = data.get('usd', 0)
                change_24h = data.get('usd_24h_change', 0)
                volume_24h = data.get('usd_24h_vol', 0)
                market_cap = data.get('usd_market_cap', 0)
                
                market_summary['prices'][coin_id] = {
                    'price_usd': price,
                    'change_24h_percent': change_24h,
                    'volume_24h_usd': volume_24h,
                    'market_cap_usd': market_cap,
                    'trend': 'up' if change_24h > 0 else 'down' if change_24h < 0 else 'flat'
                }
                
                total_change += change_24h
                if change_24h > 0:
                    positive_changes += 1
                total_coins += 1
            
            # Calculate overall market sentiment
            if total_coins > 0:
                avg_change = total_change / total_coins
                positive_ratio = positive_changes / total_coins
                
                if avg_change > 2 and positive_ratio > 0.6:
                    sentiment = 'bullish'
                elif avg_change < -2 and positive_ratio < 0.4:
                    sentiment = 'bearish'
                else:
                    sentiment = 'neutral'
                    
                market_summary['overall_sentiment'] = sentiment
                market_summary['market_analysis'] = {
                    'average_change_24h': avg_change,
                    'positive_coins_ratio': positive_ratio,
                    'total_coins_tracked': total_coins,
                    'market_direction': sentiment
                }
            
            # Process trending coins
            trending_coins = trending_data.get('coins', [])[:5]  # Top 5 trending
            for coin in trending_coins:
                market_summary['trending_coins'].append({
                    'name': coin.get('item', {}).get('name', 'Unknown'),
                    'symbol': coin.get('item', {}).get('symbol', 'Unknown'),
                    'market_cap_rank': coin.get('item', {}).get('market_cap_rank', 'N/A')
                })
            
            print(f"✅ Market data collected for {total_coins} coins")
            return market_summary
            
        except Exception as e:
            print(f"❌ Error fetching market data: {e}")
            return {'error': f'Failed to fetch market data: {e}'}

def get_simple_market_data(symbols: List[str] = None) -> Dict[str, Any]:
    """
    Convenience function to get market data
    
    Args:
        symbols: List of symbols to track
        
    Returns:
        Market data dictionary
    """
    collector = SimpleMarketDataCollector()
    return collector.get_market_data(symbols)

def format_market_data_for_llm(market_data: Dict[str, Any]) -> str:
    """
    Format market data for LLM consumption
    
    Args:
        market_data: Market data from get_simple_market_data
        
    Returns:
        Formatted string for LLM analysis
    """
    if 'error' in market_data:
        return f"Market Data Error: {market_data['error']}"
        
    formatted = "CURRENT MARKET DATA:\n\n"
    
    # Overall market sentiment
    sentiment = market_data.get('overall_sentiment', 'neutral')
    analysis = market_data.get('market_analysis', {})
    
    formatted += f"📊 MARKET SENTIMENT: {sentiment.upper()}\n"
    if analysis:
        formatted += f"📈 Average 24h Change: {analysis.get('average_change_24h', 0):.2f}%\n"
        formatted += f"📊 Positive Coins: {analysis.get('positive_coins_ratio', 0):.1%}\n\n"
    
    # Current prices
    prices = market_data.get('prices', {})
    if prices:
        formatted += "💰 CURRENT PRICES:\n"
        for coin_id, data in prices.items():
            price = data['price_usd']
            change = data['change_24h_percent']
            trend_emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
            formatted += f"   {coin_id.upper()}: ${price:.4f} ({change:+.2f}%) {trend_emoji}\n"
        formatted += "\n"
    
    # Trending coins
    trending = market_data.get('trending_coins', [])
    if trending:
        formatted += "🔥 TRENDING COINS:\n"
        for i, coin in enumerate(trending[:3], 1):
            formatted += f"   {i}. {coin['name']} ({coin['symbol']}) - Rank #{coin['market_cap_rank']}\n"
        formatted += "\n"
    
    formatted += f"Data source: {market_data.get('data_source', 'Unknown')}\n"
    formatted += f"Updated: {market_data.get('timestamp', 'Unknown')}\n"
    
    return formatted