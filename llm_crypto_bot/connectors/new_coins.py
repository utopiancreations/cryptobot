"""
New Coin Discovery and Monitoring

This module tracks newly launched tokens and trending coins for potential opportunities.
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

class NewCoinMonitor:
    """Monitor for new and trending cryptocurrency tokens"""
    
    def __init__(self):
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
    
    def get_new_coins(self) -> List[Dict]:
        """
        Get recently launched coins and trending tokens
        
        Returns:
            List of new coin data
        """
        # Check cache
        if self._is_cache_fresh('new_coins'):
            return self.cache.get('new_coins', [])
        
        new_coins = []
        
        # Get trending coins from CoinGecko
        trending = self._get_trending_coins()
        if trending:
            new_coins.extend(trending)
        
        # Get new listings from various sources
        new_listings = self._get_new_listings()
        if new_listings:
            new_coins.extend(new_listings)
        
        # Cache results
        self.cache['new_coins'] = new_coins
        self.cache['new_coins_timestamp'] = time.time()
        
        return new_coins
    
    def _get_trending_coins(self) -> List[Dict]:
        """Get trending coins from CoinGecko"""
        try:
            print("🔥 Fetching trending coins...")
            
            url = "https://api.coingecko.com/api/v3/search/trending"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            trending_coins = []
            
            for coin_data in data.get('coins', [])[:5]:  # Top 5 trending
                coin = coin_data.get('item', {})
                
                trending_coins.append({
                    'name': coin.get('name', 'Unknown'),
                    'symbol': coin.get('symbol', 'UNKNOWN'),
                    'market_cap_rank': coin.get('market_cap_rank'),
                    'price_btc': coin.get('price_btc', 0),
                    'score': coin.get('score', 0),
                    'large_image': coin.get('large', ''),
                    'type': 'trending',
                    'source': 'CoinGecko Trending',
                    'timestamp': datetime.now().isoformat()
                })
            
            print(f"✅ Found {len(trending_coins)} trending coins")
            return trending_coins
            
        except Exception as e:
            print(f"❌ Error fetching trending coins: {e}")
            return []
    
    def _get_new_listings(self) -> List[Dict]:
        """Get new coin listings"""
        try:
            print("🆕 Fetching new coin listings...")
            
            # CoinGecko new coins - search deeper in the rankings for gems
            new_listings = []
            
            # Search multiple pages to find smaller cap gems - spread out search
            for page in [4, 6, 8]:  # Pages 4,6,8 (ranks ~150-400) - spread to avoid rate limits
                url = "https://api.coingecko.com/api/v3/coins/markets"
                params = {
                    'vs_currency': 'usd',
                    'order': 'market_cap_desc',
                    'per_page': 50,
                    'page': page,
                    'sparkline': False,
                    'price_change_percentage': '24h,7d'
                }
                
                print(f"  🔍 Searching page {page} for gems...")
                
                try:
                    response = requests.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    
                    page_data = response.json()
                    if not page_data:
                        continue
                        
                    self._process_coin_data_for_gems(page_data, new_listings)
                    
                except Exception as e:
                    print(f"  ⚠️  Error fetching page {page}: {e}")
                    continue
            
            print(f"✅ Found {len(new_listings)} potential opportunities from {len([5, 6, 7])} pages")
            return new_listings[:10]  # Return top 10
            
        except Exception as e:
            print(f"❌ Error fetching new listings: {e}")
            return []
    
    def _process_coin_data_for_gems(self, data, new_listings):
        """Process coin data to find gems"""
        for coin in data:
            market_cap_rank = coin.get('market_cap_rank', 999999)
            volume_24h = coin.get('total_volume', 0)
            price_change_24h = coin.get('price_change_percentage_24h', 0)
            
            # Look for coins with strong momentum regardless of volume size
            # High volume established opportunities
            high_volume_opportunity = (volume_24h > 100000 and abs(price_change_24h) > 10)
            
            # Low volume gems with explosive potential (50x-100x candidates)
            low_volume_gem = (volume_24h >= 10000 and volume_24h <= 50000 and  # Sweet spot: $10k-50k volume
                            abs(price_change_24h) > 15 and  # Strong price movement >15%
                            market_cap_rank > 200)  # Very small cap
            
            # Medium volume with extreme movement
            medium_volume_momentum = (volume_24h > 50000 and volume_24h <= 100000 and
                                    abs(price_change_24h) > 12)  # >12% movement
            
            if ((high_volume_opportunity or low_volume_gem or medium_volume_momentum) and
                market_cap_rank > 100):  # Not in top 100 (newer/smaller)
                
                # Classify the opportunity type for better LLM analysis
                if low_volume_gem:
                    opportunity_type = 'low_volume_gem'
                    risk_level = 'VERY_HIGH'
                    potential_return = 'EXPLOSIVE (50x-100x possible)'
                elif medium_volume_momentum:
                    opportunity_type = 'medium_volume_momentum'
                    risk_level = 'HIGH'
                    potential_return = 'HIGH (10x-50x possible)'
                else:
                    opportunity_type = 'high_volume_opportunity'
                    risk_level = 'MEDIUM'
                    potential_return = 'MODERATE (2x-10x possible)'
                
                new_listings.append({
                    'name': coin.get('name', 'Unknown'),
                    'symbol': coin.get('symbol', 'UNKNOWN').upper(),
                    'current_price': coin.get('current_price', 0),
                    'market_cap_rank': market_cap_rank,
                    'total_volume': volume_24h,
                    'price_change_24h': price_change_24h,
                    'price_change_7d': coin.get('price_change_percentage_7d_in_currency', 0),
                    'market_cap': coin.get('market_cap', 0),
                    'type': 'new_listing',
                    'opportunity_type': opportunity_type,
                    'risk_level': risk_level,
                    'potential_return': potential_return,
                    'source': 'CoinGecko Markets',
                    'timestamp': datetime.now().isoformat(),
                    'image': coin.get('image', '')
                })
    
    def _is_cache_fresh(self, key: str) -> bool:
        """Check if cached data is still fresh"""
        if key not in self.cache:
            return False
        
        timestamp_key = f"{key}_timestamp"
        if timestamp_key not in self.cache:
            return False
        
        age = time.time() - self.cache[timestamp_key]
        return age < self.cache_duration
    
    def format_new_coins_for_llm(self, new_coins: List[Dict]) -> str:
        """Format new coin data for LLM consumption"""
        if not new_coins:
            return "No new coins or trending opportunities detected."
        
        formatted = "🆕 NEW COIN OPPORTUNITIES:\n\n"
        
        for i, coin in enumerate(new_coins, 1):
            if coin['type'] == 'trending':
                formatted += f"{i}. 🔥 [TRENDING] {coin['name']} ({coin['symbol']})\n"
                formatted += f"   CoinGecko Score: {coin['score']}\n"
                if coin['market_cap_rank']:
                    formatted += f"   Market Cap Rank: #{coin['market_cap_rank']}\n"
                formatted += f"   Source: {coin['source']}\n\n"
                
            elif coin['type'] == 'new_listing':
                # Use different emoji based on opportunity type
                if coin.get('opportunity_type') == 'low_volume_gem':
                    emoji = '💎'  # Diamond for gems
                    category = '[LOW VOLUME GEM]'
                elif coin.get('opportunity_type') == 'medium_volume_momentum':
                    emoji = '🚀'  # Rocket for momentum
                    category = '[MOMENTUM PLAY]'
                else:
                    emoji = '🆕'  # Default new opportunity
                    category = '[NEW OPPORTUNITY]'
                
                formatted += f"{i}. {emoji} {category} {coin['name']} ({coin['symbol']})\n"
                formatted += f"   Price: ${coin['current_price']:.6f}\n"
                formatted += f"   24h Change: {coin['price_change_24h']:+.1f}%\n"
                formatted += f"   Volume: ${coin['total_volume']:,.0f}\n"
                formatted += f"   Market Cap Rank: #{coin['market_cap_rank']}\n"
                if coin.get('potential_return'):
                    formatted += f"   Potential: {coin['potential_return']}\n"
                if coin.get('risk_level'):
                    formatted += f"   Risk Level: {coin['risk_level']}\n"
                formatted += f"   Source: {coin['source']}\n\n"
        
        formatted += "⚠️ NEW COINS ARE HIGH RISK - Research thoroughly before trading\n"
        formatted += f"Last updated: {datetime.now().strftime('%H:%M:%S')}\n"
        
        return formatted

# Global monitor instance
new_coin_monitor = NewCoinMonitor()

def get_new_coin_opportunities() -> List[Dict]:
    """Get new coin and trending opportunities"""
    return new_coin_monitor.get_new_coins()

def format_new_coins_for_llm(new_coins: List[Dict]) -> str:
    """Format new coins for LLM analysis"""
    return new_coin_monitor.format_new_coins_for_llm(new_coins)