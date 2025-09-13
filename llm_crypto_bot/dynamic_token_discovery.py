"""
Dynamic Token Discovery System

This module enables trading of ANY cryptocurrency token by:
1. Dynamically discovering token contracts across all chains
2. Finding available trading pairs on supported DEXs  
3. Validating token safety and legitimacy
4. Supporting unlimited meme coins and new launches

No more predefined token lists - trade anything that exists!
"""

import requests
import json
import time
from typing import Dict, List, Optional, Tuple
from web3 import Web3
import re
from datetime import datetime, timedelta

# Token discovery APIs
COINGECKO_API_BASE = "https://api.coingecko.com/api/v3"
DEXSCREENER_API_BASE = "https://api.dexscreener.com/latest"
MORALIS_API_BASE = "https://deep-index.moralis.io/api/v2"

# Chain ID mappings for different services
CHAIN_MAPPINGS = {
    'polygon': {
        'coingecko_id': 'polygon-pos',
        'dexscreener_id': 'polygon',
        'moralis_chain': '0x89',
        'chain_id': 137
    },
    'bsc': {
        'coingecko_id': 'binance-smart-chain', 
        'dexscreener_id': 'bsc',
        'moralis_chain': '0x38',
        'chain_id': 56
    },
    'ethereum': {
        'coingecko_id': 'ethereum',
        'dexscreener_id': 'ethereum', 
        'moralis_chain': '0x1',
        'chain_id': 1
    },
    'avalanche': {
        'coingecko_id': 'avalanche',
        'dexscreener_id': 'avalanche',
        'moralis_chain': '0xa86a', 
        'chain_id': 43114
    },
    'fantom': {
        'coingecko_id': 'fantom',
        'dexscreener_id': 'fantom',
        'moralis_chain': '0xfa',
        'chain_id': 250
    }
}

class DynamicTokenDiscovery:
    """Dynamic token discovery and validation system"""
    
    def __init__(self):
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        
    def find_token_by_symbol(self, symbol: str) -> List[Dict]:
        """
        Find token contracts across all chains by symbol
        Returns list of token info with contract addresses
        """
        symbol = symbol.upper().strip()
        cache_key = f"symbol_{symbol}"
        
        # Check cache first
        if self._is_cache_fresh(cache_key):
            return self.cache.get(cache_key, [])
        
        print(f"🔍 Discovering token: {symbol}")
        
        tokens_found = []
        
        # Method 1: CoinGecko search
        coingecko_tokens = self._search_coingecko_by_symbol(symbol)
        tokens_found.extend(coingecko_tokens)
        
        # Method 2: DexScreener search  
        dexscreener_tokens = self._search_dexscreener_by_symbol(symbol)
        tokens_found.extend(dexscreener_tokens)
        
        # Remove duplicates by contract address
        unique_tokens = self._deduplicate_tokens(tokens_found)
        
        # Cache results
        self.cache[cache_key] = unique_tokens
        self.cache[f"{cache_key}_timestamp"] = time.time()
        
        print(f"✅ Found {len(unique_tokens)} token matches for {symbol}")
        return unique_tokens
    
    def find_token_by_address(self, address: str, chain: str = None) -> Optional[Dict]:
        """
        Find token information by contract address
        """
        address = Web3.to_checksum_address(address)
        cache_key = f"address_{address}_{chain}"
        
        # Check cache
        if self._is_cache_fresh(cache_key):
            return self.cache.get(cache_key)
        
        print(f"🔍 Looking up token contract: {address[:10]}...")
        
        # Try multiple methods to get token info
        token_info = None
        
        # Method 1: CoinGecko by contract
        if chain:
            token_info = self._get_coingecko_by_contract(address, chain)
        
        # Method 2: DexScreener lookup  
        if not token_info:
            token_info = self._get_dexscreener_by_contract(address)
            
        # Method 3: Direct contract query (basic info)
        if not token_info:
            token_info = self._query_contract_basic_info(address, chain)
        
        # Cache result
        if token_info:
            self.cache[cache_key] = token_info
            self.cache[f"{cache_key}_timestamp"] = time.time()
        
        return token_info
    
    def search_trending_meme_coins(self, limit: int = 20) -> List[Dict]:
        """
        Find currently trending meme coins and new launches
        """
        cache_key = "trending_memes"
        
        if self._is_cache_fresh(cache_key):
            return self.cache.get(cache_key, [])[:limit]
        
        print(f"🚀 Searching for trending meme coins...")
        
        trending_tokens = []
        
        # Get trending tokens from multiple sources
        trending_tokens.extend(self._get_coingecko_trending())
        trending_tokens.extend(self._get_dexscreener_trending()) 
        trending_tokens.extend(self._get_new_token_launches())
        
        # Sort by volume and recent activity
        trending_tokens.sort(key=lambda x: x.get('volume_24h', 0), reverse=True)
        
        # Cache results
        self.cache[cache_key] = trending_tokens
        self.cache[f"{cache_key}_timestamp"] = time.time()
        
        return trending_tokens[:limit]
    
    def validate_token_safety(self, token_info: Dict) -> Dict:
        """
        Validate token safety and provide risk assessment
        """
        safety_score = 100  # Start with perfect score
        warnings = []
        flags = []
        
        # Check age
        if token_info.get('launch_date'):
            try:
                launch_date = datetime.fromisoformat(token_info['launch_date'])
                age_days = (datetime.now() - launch_date).days
                if age_days < 1:
                    safety_score -= 30
                    flags.append('VERY_NEW')
                    warnings.append(f'Token launched {age_days} days ago')
                elif age_days < 7:
                    safety_score -= 15
                    flags.append('NEW')
            except:
                pass
        
        # Check liquidity
        volume_24h = token_info.get('volume_24h', 0)
        if volume_24h < 1000:
            safety_score -= 25
            flags.append('LOW_LIQUIDITY')
            warnings.append(f'Very low 24h volume: ${volume_24h:,.0f}')
        elif volume_24h < 10000:
            safety_score -= 10
            flags.append('MEDIUM_LIQUIDITY')
        
        # Check market cap
        market_cap = token_info.get('market_cap', 0)
        if market_cap < 100000:  # Under $100k
            safety_score -= 20
            flags.append('MICRO_CAP')
            warnings.append(f'Micro cap: ${market_cap:,.0f}')
        
        # Check price volatility
        price_change_24h = abs(token_info.get('price_change_24h', 0))
        if price_change_24h > 100:
            safety_score -= 15
            flags.append('EXTREME_VOLATILITY')
            warnings.append(f'Extreme volatility: {price_change_24h:.1f}%')
        elif price_change_24h > 50:
            safety_score -= 10
            flags.append('HIGH_VOLATILITY')
        
        # Check social presence
        if not token_info.get('website') and not token_info.get('twitter'):
            safety_score -= 20
            flags.append('NO_SOCIAL')
            warnings.append('No website or social media found')
        
        # Determine risk level
        if safety_score >= 80:
            risk_level = 'LOW'
        elif safety_score >= 60:
            risk_level = 'MEDIUM' 
        elif safety_score >= 40:
            risk_level = 'HIGH'
        else:
            risk_level = 'EXTREME'
        
        return {
            'safety_score': safety_score,
            'risk_level': risk_level,
            'flags': flags,
            'warnings': warnings,
            'tradeable': safety_score >= 20  # Minimum threshold
        }
    
    def get_trading_pairs(self, token_address: str, chain: str) -> List[Dict]:
        """
        Find available trading pairs for a token on DEXs
        """
        cache_key = f"pairs_{token_address}_{chain}"
        
        if self._is_cache_fresh(cache_key):
            return self.cache.get(cache_key, [])
        
        pairs = []
        
        # DexScreener pairs
        try:
            url = f"{DEXSCREENER_API_BASE}/dex/tokens/{token_address}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for pair in data.get('pairs', []):
                    if pair.get('chainId') == CHAIN_MAPPINGS.get(chain, {}).get('dexscreener_id'):
                        pairs.append({
                            'dex': pair.get('dexId', 'unknown'),
                            'pair_address': pair.get('pairAddress'),
                            'base_token': pair.get('baseToken', {}),
                            'quote_token': pair.get('quoteToken', {}),
                            'liquidity_usd': pair.get('liquidity', {}).get('usd', 0),
                            'volume_24h': pair.get('volume', {}).get('h24', 0),
                            'price_usd': pair.get('priceUsd', 0)
                        })
        except Exception as e:
            print(f"⚠️  Error fetching pairs: {e}")
        
        # Cache results
        self.cache[cache_key] = pairs
        self.cache[f"{cache_key}_timestamp"] = time.time()
        
        return pairs
    
    def _search_coingecko_by_symbol(self, symbol: str) -> List[Dict]:
        """Search CoinGecko for tokens by symbol"""
        tokens = []
        
        try:
            # Search endpoint
            url = f"{COINGECKO_API_BASE}/search"
            params = {'query': symbol}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for coin in data.get('coins', []):
                    if coin.get('symbol', '').upper() == symbol:
                        # Get detailed info
                        coin_detail = self._get_coingecko_coin_detail(coin['id'])
                        if coin_detail:
                            tokens.append(coin_detail)
                            
        except Exception as e:
            print(f"⚠️  CoinGecko search error: {e}")
        
        return tokens
    
    def _search_dexscreener_by_symbol(self, symbol: str) -> List[Dict]:
        """Search DexScreener for tokens by symbol"""
        tokens = []
        
        try:
            url = f"{DEXSCREENER_API_BASE}/dex/search"
            params = {'q': symbol}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for pair in data.get('pairs', [])[:10]:  # Limit results
                    base_token = pair.get('baseToken', {})
                    if base_token.get('symbol', '').upper() == symbol:
                        tokens.append({
                            'symbol': base_token.get('symbol'),
                            'name': base_token.get('name'),
                            'contract_address': base_token.get('address'),
                            'chain': self._map_dexscreener_chain(pair.get('chainId')),
                            'price_usd': float(pair.get('priceUsd', 0)),
                            'volume_24h': pair.get('volume', {}).get('h24', 0),
                            'price_change_24h': pair.get('priceChange', {}).get('h24', 0),
                            'liquidity_usd': pair.get('liquidity', {}).get('usd', 0),
                            'dex': pair.get('dexId'),
                            'source': 'dexscreener'
                        })
                        
        except Exception as e:
            print(f"⚠️  DexScreener search error: {e}")
        
        return tokens
    
    def _get_coingecko_trending(self) -> List[Dict]:
        """Get trending tokens from CoinGecko"""
        tokens = []
        
        try:
            url = f"{COINGECKO_API_BASE}/search/trending"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for coin_data in data.get('coins', []):
                    coin = coin_data.get('item', {})
                    # Get detailed info for each trending coin
                    detail = self._get_coingecko_coin_detail(coin.get('id'))
                    if detail:
                        detail['trending_score'] = coin.get('score', 0)
                        tokens.append(detail)
                        
        except Exception as e:
            print(f"⚠️  Error fetching trending: {e}")
        
        return tokens
    
    def _get_dexscreener_trending(self) -> List[Dict]:
        """Get trending pairs from DexScreener"""
        tokens = []
        
        try:
            # Get trending pairs (this is a simplified approach)
            url = f"{DEXSCREENER_API_BASE}/dex/tokens/trending"  # Hypothetical endpoint
            # DexScreener doesn't have a direct trending endpoint, so we'll skip this for now
            pass
                        
        except Exception as e:
            print(f"⚠️  Error fetching DexScreener trending: {e}")
        
        return tokens
    
    def _get_new_token_launches(self) -> List[Dict]:
        """Find newly launched tokens"""
        tokens = []
        
        try:
            # This would require specialized APIs or contract monitoring
            # For now, we'll use CoinGecko's newest listings
            url = f"{COINGECKO_API_BASE}/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': 50,
                'page': 10,  # Get newer coins (page 10+)
                'sparkline': False
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for coin in data:
                    # Focus on newer, smaller cap coins
                    market_cap_rank = coin.get('market_cap_rank', 999999)
                    if market_cap_rank > 500:  # Smaller cap = potentially newer
                        volume_24h = coin.get('total_volume', 0)
                        price_change = abs(coin.get('price_change_percentage_24h', 0))
                        
                        # Look for high volatility + decent volume = potential new gem
                        if volume_24h > 50000 and price_change > 15:
                            tokens.append({
                                'symbol': coin.get('symbol', '').upper(),
                                'name': coin.get('name'),
                                'price_usd': coin.get('current_price', 0),
                                'volume_24h': volume_24h,
                                'price_change_24h': coin.get('price_change_percentage_24h', 0),
                                'market_cap': coin.get('market_cap', 0),
                                'market_cap_rank': market_cap_rank,
                                'source': 'coingecko_new',
                                'image': coin.get('image', '')
                            })
                        
        except Exception as e:
            print(f"⚠️  Error fetching new launches: {e}")
        
        return tokens[:10]  # Limit to top 10
    
    def _get_coingecko_coin_detail(self, coin_id: str) -> Optional[Dict]:
        """Get detailed coin information from CoinGecko"""
        try:
            url = f"{COINGECKO_API_BASE}/coins/{coin_id}"
            params = {
                'localization': False,
                'tickers': False,
                'market_data': True,
                'community_data': False,
                'developer_data': False,
                'sparkline': False
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                platforms = data.get('platforms', {})
                
                # Convert to our standard format
                token_info = {
                    'symbol': data.get('symbol', '').upper(),
                    'name': data.get('name'),
                    'coingecko_id': data.get('id'),
                    'image': data.get('image', {}).get('large', ''),
                    'website': data.get('links', {}).get('homepage', [''])[0],
                    'twitter': data.get('links', {}).get('twitter_screen_name'),
                    'source': 'coingecko'
                }
                
                # Market data
                market_data = data.get('market_data', {})
                if market_data:
                    token_info.update({
                        'price_usd': market_data.get('current_price', {}).get('usd', 0),
                        'market_cap': market_data.get('market_cap', {}).get('usd', 0),
                        'volume_24h': market_data.get('total_volume', {}).get('usd', 0),
                        'price_change_24h': market_data.get('price_change_percentage_24h', 0),
                        'market_cap_rank': market_data.get('market_cap_rank', 999999)
                    })
                
                # Contract addresses for different chains
                contracts = []
                for platform_key, address in platforms.items():
                    if address and address != '':
                        chain = self._map_coingecko_platform(platform_key)
                        if chain:
                            contracts.append({
                                'chain': chain,
                                'address': address
                            })
                
                token_info['contracts'] = contracts
                return token_info
                
        except Exception as e:
            print(f"⚠️  Error getting coin detail: {e}")
            
        return None
    
    def _deduplicate_tokens(self, tokens: List[Dict]) -> List[Dict]:
        """Remove duplicate tokens based on contract address"""
        seen = set()
        unique = []
        
        for token in tokens:
            # Create unique key based on symbol + chain + address
            contracts = token.get('contracts', [])
            if contracts:
                for contract in contracts:
                    key = f"{token['symbol']}_{contract['chain']}_{contract['address']}"
                    if key not in seen:
                        seen.add(key)
                        # Add current contract info to token
                        token_copy = token.copy()
                        token_copy['contract_address'] = contract['address']
                        token_copy['chain'] = contract['chain']
                        unique.append(token_copy)
            else:
                # Token without contract info
                key = f"{token['symbol']}_{token.get('chain', '')}_{token.get('contract_address', '')}"
                if key not in seen:
                    seen.add(key)
                    unique.append(token)
        
        return unique
    
    def _map_coingecko_platform(self, platform: str) -> Optional[str]:
        """Map CoinGecko platform names to our chain names"""
        mapping = {
            'ethereum': 'ethereum',
            'polygon-pos': 'polygon', 
            'binance-smart-chain': 'bsc',
            'avalanche': 'avalanche',
            'fantom': 'fantom'
        }
        return mapping.get(platform)
    
    def _map_dexscreener_chain(self, chain_id: str) -> Optional[str]:
        """Map DexScreener chain IDs to our chain names"""
        mapping = {
            'ethereum': 'ethereum',
            'polygon': 'polygon',
            'bsc': 'bsc', 
            'avalanche': 'avalanche',
            'fantom': 'fantom'
        }
        return mapping.get(chain_id)
    
    def _get_coingecko_by_contract(self, address: str, chain: str) -> Optional[Dict]:
        """Get token info from CoinGecko by contract address"""
        try:
            # CoinGecko doesn't have a direct contract lookup, so we'll skip this
            return None
        except Exception as e:
            print(f"⚠️  CoinGecko contract lookup error: {e}")
            return None
    
    def _get_dexscreener_by_contract(self, address: str) -> Optional[Dict]:
        """Get token info from DexScreener by contract address"""
        try:
            url = f"{DEXSCREENER_API_BASE}/dex/tokens/{address}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                pairs = data.get('pairs', [])
                
                if pairs:
                    # Use the first pair to get token info
                    pair = pairs[0]
                    base_token = pair.get('baseToken', {})
                    
                    return {
                        'symbol': base_token.get('symbol'),
                        'name': base_token.get('name'),
                        'contract_address': base_token.get('address'),
                        'chain': self._map_dexscreener_chain(pair.get('chainId')),
                        'price_usd': float(pair.get('priceUsd', 0)),
                        'volume_24h': pair.get('volume', {}).get('h24', 0),
                        'price_change_24h': pair.get('priceChange', {}).get('h24', 0),
                        'liquidity_usd': pair.get('liquidity', {}).get('usd', 0),
                        'source': 'dexscreener_contract'
                    }
        except Exception as e:
            print(f"⚠️  DexScreener contract lookup error: {e}")
            return None
    
    def _query_contract_basic_info(self, address: str, chain: str) -> Optional[Dict]:
        """Query basic token info directly from contract"""
        try:
            # This would require Web3 connection to query token contract
            # For now, return None
            return None
        except Exception as e:
            print(f"⚠️  Contract query error: {e}")
            return None
    
    def _is_cache_fresh(self, key: str) -> bool:
        """Check if cached data is still fresh"""
        if key not in self.cache:
            return False
            
        timestamp_key = f"{key}_timestamp"
        if timestamp_key not in self.cache:
            return False
            
        age = time.time() - self.cache[timestamp_key]
        return age < self.cache_duration

# Global instance
token_discovery = DynamicTokenDiscovery()

# Main functions for external use
def find_any_token(symbol_or_address: str) -> List[Dict]:
    """
    Find any token by symbol or contract address
    Returns list of token matches with full details
    """
    # Check if it's an address (starts with 0x and is 42 chars)
    if re.match(r'^0x[a-fA-F0-9]{40}$', symbol_or_address):
        # It's a contract address
        token_info = token_discovery.find_token_by_address(symbol_or_address)
        return [token_info] if token_info else []
    else:
        # It's a symbol
        return token_discovery.find_token_by_symbol(symbol_or_address)

def get_trending_gems(limit: int = 20) -> List[Dict]:
    """Get currently trending meme coins and gems"""
    return token_discovery.search_trending_meme_coins(limit)

def validate_token(token_info: Dict) -> Dict:
    """Validate token safety and get risk assessment"""
    return token_discovery.validate_token_safety(token_info)

def get_token_pairs(token_address: str, chain: str) -> List[Dict]:
    """Get available trading pairs for a token"""
    return token_discovery.get_trading_pairs(token_address, chain)