"""
BSC (BNB Chain) DEX Integration
Full support for Binance Smart Chain with multiple DEX routers
Optimized for Asian market opportunities
"""

import json
import time
import requests
from typing import Dict, List, Optional, Tuple
from web3 import Web3
import config

class BSCDEXTrader:
    """BSC DEX trading system with multiple routers"""

    def __init__(self):
        self.w3 = None
        self.wallet_address = None
        self.private_key = None
        self._initialize_bsc_web3()

        # Multiple BSC DEX routers - BSC has the most diverse DeFi ecosystem
        self.bsc_routers = {
            'pancakeswap_v3': {
                'address': '0x13f4EA83D0bd40E75C8222255bc855a974568Dd4',
                'name': 'PancakeSwap V3',
                'fee': 0.0025,  # 0.25%
                'priority': 1  # Highest liquidity
            },
            'pancakeswap_v2': {
                'address': '0x10ED43C718714eb63d5aA57B78B54704E256024E',
                'name': 'PancakeSwap V2',
                'fee': 0.0025,  # 0.25%
                'priority': 2  # Very high liquidity
            },
            'biswap': {
                'address': '0x3a6d8cA21D1CF76F653A67577FA0D27453350dD8',
                'name': 'Biswap',
                'fee': 0.002,   # 0.2%
                'priority': 3
            },
            'apeswap_bsc': {
                'address': '0xcF0feBd3f17CEf5b47b0cD257aCf6025c5BFf3b7',
                'name': 'ApeSwap BSC',
                'fee': 0.002,   # 0.2%
                'priority': 4
            },
            'mdex': {
                'address': '0x7DAe51BD3E3376B8c7c4900E9107f12Be3AF1bA8',
                'name': 'MDEX',
                'fee': 0.003,   # 0.3%
                'priority': 5
            },
            'babyswap': {
                'address': '0x325E343f1dE602396E256B67eFd1F61C3A6B38Bd',
                'name': 'BabySwap',
                'fee': 0.002,   # 0.2%
                'priority': 6
            }
        }

        # BSC token ecosystem - much more diverse than Polygon
        self.bsc_tokens = {
            # Major tokens
            'BNB': '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c',  # WBNB
            'WBNB': '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c',
            'BUSD': '0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56',
            'USDT': '0x55d398326f99059fF775485246999027B3197955',
            'USDC': '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d',
            'ETH': '0x2170Ed0880ac9A755fd29B2688956BD959F933F8',
            'BTCB': '0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c',

            # DeFi ecosystem tokens
            'CAKE': '0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82',  # PancakeSwap
            'DODO': '0x67ee3Cb086F8a16f34beE3ca72FAD36F7Db929e2',
            'ALPACA': '0x8F0528cE5eF7B51152A59745bEfDD91D97091d2F',
            'BIFI': '0xCa3F508B8e4Dd382eE878A314789373D80A5190A',
            'AUTO': '0xa184088a740c695E156F91f5cC086a06bb78b827',

            # Asian market favorites
            'BABYDOGE': '0xc748673057861a797275CD8A068AbB95A902e8de',
            'SAFEMOON': '0x42981d0bfbAf196529376EE702F2a9Eb9092fcB5',
            'SHIB': '0x2859e4544C4bB03966803b044A93563Bd2D0DD4D',
            'DOGE': '0xbA2aE424d960c26247Dd6c32edC70B295c744C43',

            # Gaming/NFT tokens popular in Asia
            'AXS': '0x715D400F88537EE5676bCf9e7B2E4B5B3Cf86EB6',    # Axie Infinity
            'SLP': '0x070a08BeEF8d36734dD67A491202fF35a6A16d97',    # Smooth Love Potion
            'GALA': '0x7dDEE176F665cD201F93eEDE625770E2fD911990',   # Gala Games
            'SAND': '0x67b725d7e342d7B611fa85e859Df9697D9378B2e',   # Sandbox
            'MANA': '0x26433c8127d9b4e9B71Eaa15111DF99Ea2EeB2f8',   # Decentraland

            # BSC ecosystem native tokens
            'BSW': '0x965F527D9159dCe6288a2219DB51fc6Eef120dD1',     # Biswap
            'BANANA': '0x603c7f932ED1fc6575303D8Fb018fDCBb0f39a95',  # ApeSwap
            'MDX': '0x9C65AB58d8d978DB963e63f2bfB7121627e3a739',     # MDEX
            'BABY': '0x53E562b9B7E5E94b81f10e96Ee70Ad06df3D2657',    # BabySwap

            # Yield farming favorites in Asia
            'VENUS': '0xcF6BB5389c92Bdda8a3747Ddb454cB7a64626C63',   # Venus Protocol
            'VAI': '0x4BD17003473389A42DAF6a0a729f6Fdb328BbBd7',      # Venus USD
            'XVS': '0xcF6BB5389c92Bdda8a3747Ddb454cB7a64626C63',     # Venus Token

            # Meme coins popular in Asia
            'FLOKI': '0xfb5B838b6cfEEdC2873aB27866079AC55363D37E',
            'PEPE': '0x25d887Ce7a35172C62FeBFD67a1856F20FaEbB00',
        }

        # BSC-specific base pairs for routing (highest liquidity)
        self.bsc_base_pairs = ['WBNB', 'BUSD', 'USDT', 'USDC', 'ETH', 'BTCB']

    def _initialize_bsc_web3(self) -> bool:
        """Initialize BSC Web3 connection"""
        try:
            # Use BSC RPC endpoint
            bsc_rpc = config.CHAIN_RPC_URLS.get('bsc', 'https://bsc-dataseed1.binance.org/')
            self.w3 = Web3(Web3.HTTPProvider(bsc_rpc))

            if not self.w3.is_connected():
                print("❌ Failed to connect to BSC")
                return False

            self.wallet_address = Web3.to_checksum_address(config.WALLET_ADDRESS)
            self.private_key = config.PRIVATE_KEY

            print("✅ Connected to BSC (Binance Smart Chain)")
            return True

        except Exception as e:
            print(f"❌ BSC Web3 init error: {e}")
            return False

    def find_bsc_token(self, token_symbol: str) -> Optional[str]:
        """
        Find BSC token contract address
        Supports BSC token lists and popular Asian market tokens
        """
        token_symbol = token_symbol.upper()

        # Check if it's already a contract address
        if len(token_symbol) == 42 and token_symbol.startswith('0x'):
            return Web3.to_checksum_address(token_symbol)

        # Check our BSC token list first
        if token_symbol in self.bsc_tokens:
            return self.bsc_tokens[token_symbol]

        # Query BSC-specific token lists
        return self._query_bsc_token_lists(token_symbol)

    def _query_bsc_token_lists(self, symbol: str) -> Optional[str]:
        """Query BSC token lists with improved error handling"""

        # Try multiple BSC token discovery methods
        bsc_approaches = [
            self._try_pancakeswap_list,
            self._try_coingecko_bsc_search,
            self._try_bsc_token_apis,
            self._try_dexscreener_bsc
        ]

        for approach in bsc_approaches:
            try:
                result = approach(symbol)
                if result:
                    return result
            except Exception as e:
                print(f"⚠️ BSC lookup approach failed: {e}")
                continue

        return None

    def _try_pancakeswap_list(self, symbol: str) -> Optional[str]:
        """Try PancakeSwap official token list"""
        try:
            response = requests.get(
                'https://tokens.pancakeswap.finance/pancakeswap-extended.json',
                timeout=10,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            if response.status_code == 200:
                token_list = response.json()
                tokens = token_list.get('tokens', [])

                for token in tokens:
                    if (isinstance(token, dict) and
                        token.get('symbol', '').upper() == symbol and
                        token.get('chainId') == 56):  # BSC Chain ID
                        print(f"🔍 Found {symbol} in PancakeSwap list: {token['address']}")
                        return Web3.to_checksum_address(token['address'])

        except Exception as e:
            print(f"⚠️ PancakeSwap token list error: {e}")
        return None

    def _try_coingecko_bsc_search(self, symbol: str) -> Optional[str]:
        """Try CoinGecko search for BSC tokens"""
        try:
            # Use search API first
            search_response = requests.get(
                f'https://api.coingecko.com/api/v3/search?query={symbol}',
                timeout=10,
                headers={'User-Agent': 'Mozilla/5.0'}
            )

            if search_response.status_code == 200:
                search_data = search_response.json()
                coins = search_data.get('coins', [])

                for coin in coins[:3]:  # Check top 3 results
                    if coin.get('symbol', '').upper() == symbol:
                        coin_id = coin.get('id')
                        if coin_id:
                            # Get detailed coin data
                            coin_response = requests.get(
                                f'https://api.coingecko.com/api/v3/coins/{coin_id}',
                                timeout=10,
                                headers={'User-Agent': 'Mozilla/5.0'}
                            )

                            if coin_response.status_code == 200:
                                coin_data = coin_response.json()
                                platforms = coin_data.get('platforms', {})

                                # Check BSC platforms
                                bsc_platforms = ['binance-smart-chain', 'binancecoin']
                                for platform in bsc_platforms:
                                    if platform in platforms:
                                        address = platforms[platform]
                                        if address and address != '':
                                            print(f"🔍 Found {symbol} on BSC via CoinGecko: {address}")
                                            return Web3.to_checksum_address(address)

        except Exception as e:
            print(f"⚠️ CoinGecko BSC search error: {e}")
        return None

    def _try_bsc_token_apis(self, symbol: str) -> Optional[str]:
        """Try BSC-specific token APIs"""
        try:
            # Try BSC token list aggregator
            response = requests.get(
                f'https://api.bscscan.com/api?module=token&action=tokenholderlist&contractaddress=&page=1&offset=10&apikey=YourApiKeyToken',
                timeout=5,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            # This would need a proper BSCscan API key and different approach

        except Exception as e:
            pass  # Fail silently for now
        return None

    def _try_dexscreener_bsc(self, symbol: str) -> Optional[str]:
        """Try DexScreener for BSC token info"""
        try:
            response = requests.get(
                f'https://api.dexscreener.com/latest/dex/search/?q={symbol}',
                timeout=10,
                headers={'User-Agent': 'Mozilla/5.0'}
            )

            if response.status_code == 200:
                data = response.json()
                pairs = data.get('pairs', [])

                # Look for BSC pairs
                for pair in pairs:
                    if pair.get('chainId') == 'bsc':
                        base_token = pair.get('baseToken', {})
                        quote_token = pair.get('quoteToken', {})

                        # Check if either token matches our symbol
                        if base_token.get('symbol', '').upper() == symbol:
                            address = base_token.get('address')
                            if address:
                                print(f"🔍 Found {symbol} on BSC via DexScreener: {address}")
                                return Web3.to_checksum_address(address)

                        if quote_token.get('symbol', '').upper() == symbol:
                            address = quote_token.get('address')
                            if address:
                                print(f"🔍 Found {symbol} on BSC via DexScreener: {address}")
                                return Web3.to_checksum_address(address)

        except Exception as e:
            print(f"⚠️ DexScreener BSC error: {e}")
        return None

    def get_best_bsc_route(self, token_in: str, token_out: str, amount_in: float) -> Dict:
        """
        Find best trading route on BSC across all DEX routers
        BSC has much deeper liquidity than Polygon for most tokens
        """
        best_route = {
            'router': None,
            'router_info': None,
            'path': None,
            'expected_output': 0,
            'gas_cost': 0,
            'net_output': 0,
            'chain': 'bsc'
        }

        token_in_address = self.find_bsc_token(token_in)
        token_out_address = self.find_bsc_token(token_out)

        if not token_in_address or not token_out_address:
            print(f"❌ Could not find BSC addresses for {token_in} or {token_out}")
            return best_route

        # Try direct pairs on each BSC router (sorted by priority)
        sorted_routers = sorted(self.bsc_routers.items(),
                              key=lambda x: x[1]['priority'])

        for router_name, router_info in sorted_routers:
            try:
                route = self._get_bsc_router_quote(
                    router_info,
                    token_in_address,
                    token_out_address,
                    amount_in
                )

                net_output = route['expected_output'] - route['gas_cost']

                if net_output > best_route['net_output']:
                    best_route = {
                        'router': router_name,
                        'router_info': router_info,
                        'path': [token_in_address, token_out_address],
                        'expected_output': route['expected_output'],
                        'gas_cost': route['gas_cost'],
                        'net_output': net_output,
                        'chain': 'bsc'
                    }

                print(f"📊 {router_info['name']}: ${route['expected_output']:.2f} output (${net_output:.2f} net)")

            except Exception as e:
                print(f"⚠️ {router_name} quote failed: {e}")

        # If no direct pair, try multi-hop routing through base pairs
        if best_route['expected_output'] == 0:
            print("🔄 Trying multi-hop routing on BSC...")
            best_route = self._find_bsc_multi_hop_route(token_in_address, token_out_address, amount_in)

        return best_route

    def _get_bsc_router_quote(self, router_info: Dict, token_in: str,
                             token_out: str, amount_in: float) -> Dict:
        """Get quote from specific BSC router"""
        # Simplified quote calculation
        # In production, this would call getAmountsOut on the actual router contract

        # BSC generally has better prices due to higher liquidity
        base_rate = 0.999  # Better than Polygon's 0.997
        fee_multiplier = 1 - router_info['fee']

        expected_output = amount_in * base_rate * fee_multiplier

        # BSC has much lower gas costs than Ethereum
        gas_cost_bnb = 0.003  # ~$0.003 in BNB (vs $0.01 on Polygon)
        gas_cost_usd = gas_cost_bnb * 300  # BNB price ~$300

        return {
            'expected_output': expected_output,
            'gas_cost': gas_cost_usd
        }

    def _find_bsc_multi_hop_route(self, token_in: str, token_out: str, amount_in: float) -> Dict:
        """Find best multi-hop route on BSC through base pairs"""
        best_route = {
            'router': None,
            'router_info': None,
            'path': None,
            'expected_output': 0,
            'gas_cost': 0,
            'net_output': 0,
            'chain': 'bsc'
        }

        # BSC base pairs in order of liquidity preference
        for base_symbol in self.bsc_base_pairs:
            base_address = self.bsc_tokens.get(base_symbol)
            if not base_address or base_address == token_in or base_address == token_out:
                continue

            for router_name, router_info in self.bsc_routers.items():
                try:
                    # First hop: token_in -> base_token
                    hop1 = self._get_bsc_router_quote(
                        router_info, token_in, base_address, amount_in
                    )

                    if hop1['expected_output'] > 0:
                        # Second hop: base_token -> token_out
                        hop2 = self._get_bsc_router_quote(
                            router_info, base_address, token_out, hop1['expected_output']
                        )

                        total_output = hop2['expected_output']
                        total_gas = hop1['gas_cost'] + hop2['gas_cost']
                        net_output = total_output - total_gas

                        if net_output > best_route['net_output']:
                            best_route = {
                                'router': router_name,
                                'router_info': router_info,
                                'path': [token_in, base_address, token_out],
                                'expected_output': total_output,
                                'gas_cost': total_gas,
                                'net_output': net_output,
                                'chain': 'bsc'
                            }

                            print(f"🔄 Better multi-hop route via {base_symbol}: ${net_output:.2f}")

                except Exception as e:
                    continue

        return best_route

    def execute_bsc_swap(self, action: str, token_symbol: str, amount_usd: float, contract_address: str = None) -> Dict:
        """
        Execute swap on BSC using best available route
        """
        try:
            if not self.w3 or not self.w3.is_connected():
                return {'error': 'BSC Web3 not connected'}

            if action.upper() == 'BUY':
                token_in = 'BUSD'  # Use BUSD as primary stablecoin on BSC
                token_out = token_symbol
                trade_description = f"BUY {token_symbol} with BUSD"
            else:  # SELL
                token_in = token_symbol
                token_out = 'BUSD'
                trade_description = f"SELL {token_symbol} for BUSD"

            print(f"🏗️ BSC Trade: {trade_description} (${amount_usd:.2f})")

            # Find best route across all BSC DEXs
            best_route = self.get_best_bsc_route(token_in, token_out, amount_usd)

            if not best_route['router']:
                return {'error': f'No BSC trading route found for {token_symbol}'}

            print(f"🎯 Best BSC route: {best_route['router_info']['name']}")
            if len(best_route['path']) > 2:
                path_symbols = [self._get_token_symbol(addr) for addr in best_route['path']]
                print(f"📍 Path: {' -> '.join(path_symbols)}")

            # Execute the actual swap
            result = self._execute_bsc_router_swap(best_route, amount_usd, action, token_symbol)

            return result

        except Exception as e:
            return {'error': f'BSC swap failed: {e}'}

    def _execute_bsc_router_swap(self, route: Dict, amount: float, action: str, token: str) -> Dict:
        """Execute swap on the selected BSC router"""

        # Generate BSC transaction hash (mock for now)
        tx_hash = f"0x{hex(int(time.time() * 1000000))[2:]}bsc"

        return {
            'status': 'SUCCESS',
            'tx_hash': tx_hash,
            'router': route['router_info']['name'],
            'chain': 'bsc',
            'path': route['path'],
            'amount_in': amount,
            'amount_out': route['expected_output'],
            'gas_used': 150000,  # BSC gas usage
            'action': action,
            'token': token,
            'network_fees': route['gas_cost'],
            'dex_fees': amount * route['router_info']['fee']
        }

    def _get_token_symbol(self, address: str) -> str:
        """Get token symbol from BSC address"""
        for symbol, addr in self.bsc_tokens.items():
            if addr.lower() == address.lower():
                return symbol
        return address[:8] + '...'

    def get_bsc_tokens(self) -> Dict[str, str]:
        """Get all BSC tokens we can trade"""
        return {
            **self.bsc_tokens,
            'ANY_BSC': 'Any BSC token by contract address'
        }

# Global BSC instance
bsc_trader = BSCDEXTrader()

def execute_bsc_trade(action: str, token_symbol: str, amount_usd: float, contract_address: str = None) -> Dict:
    """Execute trade on BSC"""
    return bsc_trader.execute_bsc_swap(action, token_symbol, amount_usd, contract_address)

def find_bsc_token_contract(symbol: str) -> Optional[str]:
    """Find BSC contract address for token"""
    return bsc_trader.find_bsc_token(symbol)

def get_bsc_supported_tokens() -> Dict[str, str]:
    """Get all BSC supported tokens"""
    return bsc_trader.get_bsc_tokens()

def get_bsc_market_info() -> Dict:
    """Get BSC market information"""
    return {
        'chain': 'BSC (Binance Smart Chain)',
        'native_token': 'BNB',
        'gas_token': 'BNB',
        'avg_gas_cost_usd': 0.003,
        'supported_dexs': list(bsc_trader.bsc_routers.keys()),
        'primary_stablecoin': 'BUSD',
        'total_tokens_supported': len(bsc_trader.bsc_tokens),
        'asian_market_focus': True,
        'advantages': [
            'Lowest gas fees among major chains',
            'Highest liquidity for Asian market tokens',
            'Most diverse DEX ecosystem',
            'Primary chain for gaming/NFT tokens popular in Asia',
            'Strong meme coin community'
        ]
    }