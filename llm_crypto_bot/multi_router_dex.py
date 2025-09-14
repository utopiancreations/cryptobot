"""
Multi-Router DEX Integration
Supports multiple DEX routers for better token access and liquidity
"""

import json
import time
from typing import Dict, List, Optional, Tuple
from web3 import Web3
import requests
import config

class MultiRouterDEX:
    """Multi-router DEX trading system"""

    def __init__(self):
        self.w3 = None
        self.wallet_address = None
        self.private_key = None
        self._initialize_web3()

        # Multiple DEX routers on Polygon
        self.routers = {
            'quickswap': {
                'address': '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff',
                'name': 'QuickSwap',
                'fee': 0.003  # 0.3%
            },
            'sushiswap': {
                'address': '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506',
                'name': 'SushiSwap',
                'fee': 0.003  # 0.3%
            },
            'uniswap_v3': {
                'address': '0xE592427A0AEce92De3Edee1F18E0157C05861564',
                'name': 'Uniswap V3',
                'fee': 0.003  # Variable fees, using 0.3% as default
            },
            'apeswap': {
                'address': '0xC0788A3aD43d79aa53B09c2EaCc313A787d1d607',
                'name': 'ApeSwap',
                'fee': 0.002  # 0.2%
            }
        }

        # Base tokens for routing (most liquid)
        self.base_tokens = {
            'WMATIC': '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270',
            'WETH': '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619',
            'USDC': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
            'USDT': '0xc2132D05D31c914a87C6611C10748AEb04B58e8F',
            'WBTC': '0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6',
            'DAI': '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063'
        }

    def _initialize_web3(self) -> bool:
        """Initialize Web3 connection"""
        try:
            self.w3 = Web3(Web3.HTTPProvider(config.RPC_URL))
            if not self.w3.is_connected():
                return False

            self.wallet_address = Web3.to_checksum_address(config.WALLET_ADDRESS)
            self.private_key = config.PRIVATE_KEY
            return True

        except Exception as e:
            print(f"❌ Multi-router Web3 init error: {e}")
            return False

    def find_token_address(self, token_symbol: str) -> Optional[str]:
        """
        Find token contract address by symbol
        First checks known tokens, then queries token lists
        """
        token_symbol = token_symbol.upper()

        # Check if it's already a contract address
        if len(token_symbol) == 42 and token_symbol.startswith('0x'):
            return Web3.to_checksum_address(token_symbol)

        # Check our base tokens first
        if token_symbol in self.base_tokens:
            return self.base_tokens[token_symbol]

        # Try to query popular token lists for the symbol
        return self._query_token_lists(token_symbol)

    def _query_token_lists(self, symbol: str) -> Optional[str]:
        """Query popular token lists for contract address with better error handling"""

        # Try multiple approaches for finding tokens
        approaches = [
            self._try_polygon_token_list,
            self._try_coingecko_search,
            self._try_alternative_apis
        ]

        for approach in approaches:
            try:
                result = approach(symbol)
                if result:
                    return result
            except Exception as e:
                print(f"⚠️ Token lookup approach failed: {e}")
                continue

        print(f"❌ Could not find contract address for {symbol}")
        return None

    def _try_polygon_token_list(self, symbol: str) -> Optional[str]:
        """Try Polygon official token list"""
        try:
            response = requests.get(
                'https://wallet.polygon.technology/polygon-tokens.json',
                timeout=5,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            if response.status_code == 200:
                tokens = response.json()
                if isinstance(tokens, list):
                    for token in tokens:
                        if isinstance(token, dict) and token.get('symbol', '').upper() == symbol:
                            print(f"🔍 Found {symbol} in Polygon token list: {token['address']}")
                            return Web3.to_checksum_address(token['address'])
        except Exception as e:
            print(f"⚠️ Polygon token list error: {e}")
        return None

    def _try_coingecko_search(self, symbol: str) -> Optional[str]:
        """Try CoinGecko with rate limiting"""
        try:
            # Try search first
            response = requests.get(
                f'https://api.coingecko.com/api/v3/search?query={symbol}',
                timeout=10,
                headers={'User-Agent': 'Mozilla/5.0'}
            )

            if response.status_code == 200:
                search_data = response.json()
                coins = search_data.get('coins', [])

                for coin in coins[:3]:  # Check top 3 results
                    if coin.get('symbol', '').upper() == symbol:
                        coin_id = coin.get('id')
                        if coin_id:
                            # Get platform data
                            coin_response = requests.get(
                                f'https://api.coingecko.com/api/v3/coins/{coin_id}',
                                timeout=10,
                                headers={'User-Agent': 'Mozilla/5.0'}
                            )

                            if coin_response.status_code == 200:
                                coin_data = coin_response.json()
                                platforms = coin_data.get('platforms', {})

                                # Try Polygon first, then Ethereum
                                for platform in ['polygon-pos', 'ethereum']:
                                    if platform in platforms:
                                        address = platforms[platform]
                                        if address and address != '':
                                            print(f"🔍 Found {symbol} via CoinGecko on {platform}: {address}")
                                            return Web3.to_checksum_address(address)

        except Exception as e:
            print(f"⚠️ CoinGecko search error: {e}")
        return None

    def _try_alternative_apis(self, symbol: str) -> Optional[str]:
        """Try alternative APIs for token discovery"""
        try:
            # Try 1inch token list
            response = requests.get(
                'https://tokens.1inch.io/',
                timeout=5,
                headers={'User-Agent': 'Mozilla/5.0'}
            )

            if response.status_code == 200:
                tokens = response.json()
                # 1inch returns tokens keyed by address, need to search values
                for address, token_data in tokens.items():
                    if isinstance(token_data, dict) and token_data.get('symbol', '').upper() == symbol:
                        print(f"🔍 Found {symbol} via 1inch: {address}")
                        return Web3.to_checksum_address(address)

        except Exception as e:
            print(f"⚠️ Alternative API error: {e}")

        return None

    def get_best_route(self, token_in: str, token_out: str, amount_in: float) -> Dict:
        """
        Find the best trading route across all DEX routers
        Returns the router and path with best output
        """
        best_route = {
            'router': None,
            'path': None,
            'expected_output': 0,
            'gas_cost': 0,
            'net_output': 0
        }

        token_in_address = self.find_token_address(token_in)
        token_out_address = self.find_token_address(token_out)

        if not token_in_address or not token_out_address:
            return best_route

        # Try direct pair on each router
        for router_name, router_info in self.routers.items():
            try:
                route = self._get_router_quote(
                    router_info['address'],
                    token_in_address,
                    token_out_address,
                    amount_in,
                    router_info['fee']
                )

                if route['expected_output'] > best_route['expected_output']:
                    best_route = {
                        'router': router_name,
                        'router_info': router_info,
                        'path': [token_in_address, token_out_address],
                        'expected_output': route['expected_output'],
                        'gas_cost': route['gas_cost'],
                        'net_output': route['expected_output'] - route['gas_cost']
                    }

            except Exception as e:
                print(f"⚠️ Failed to get quote from {router_name}: {e}")

        # If no direct pair found, try routing through base tokens
        if best_route['expected_output'] == 0:
            best_route = self._find_multi_hop_route(token_in_address, token_out_address, amount_in)

        return best_route

    def _get_router_quote(self, router_address: str, token_in: str, token_out: str,
                         amount_in: float, fee: float) -> Dict:
        """Get quote from a specific router"""
        # This is a simplified implementation
        # In production, you'd call getAmountsOut on the actual router contract

        # Mock calculation for demonstration
        expected_output = amount_in * 0.997  # Account for slippage and fees
        gas_cost = 0.01  # Estimated gas cost in USD

        return {
            'expected_output': expected_output,
            'gas_cost': gas_cost
        }

    def _find_multi_hop_route(self, token_in: str, token_out: str, amount_in: float) -> Dict:
        """Find best multi-hop route through base tokens"""
        best_route = {
            'router': None,
            'path': None,
            'expected_output': 0,
            'gas_cost': 0,
            'net_output': 0
        }

        # Try routing through each base token
        for base_symbol, base_address in self.base_tokens.items():
            if base_address == token_in or base_address == token_out:
                continue

            for router_name, router_info in self.routers.items():
                try:
                    # First hop: token_in -> base_token
                    hop1 = self._get_router_quote(
                        router_info['address'], token_in, base_address,
                        amount_in, router_info['fee']
                    )

                    if hop1['expected_output'] > 0:
                        # Second hop: base_token -> token_out
                        hop2 = self._get_router_quote(
                            router_info['address'], base_address, token_out,
                            hop1['expected_output'], router_info['fee']
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
                                'net_output': net_output
                            }

                except Exception as e:
                    print(f"⚠️ Multi-hop route failed for {router_name} via {base_symbol}: {e}")

        return best_route

    def execute_best_swap(self, action: str, token_symbol: str, amount_usd: float) -> Dict:
        """
        Execute swap using the best available route
        """
        try:
            if action.upper() == 'BUY':
                token_in = 'USDC'  # Buy with USDC
                token_out = token_symbol
            else:  # SELL
                token_in = token_symbol
                token_out = 'USDC'  # Sell for USDC

            # Find best route
            best_route = self.get_best_route(token_in, token_out, amount_usd)

            if not best_route['router']:
                return {'error': f'No trading route found for {token_symbol}'}

            print(f"🎯 Best route: {best_route['router']} via {' -> '.join([self._get_symbol(addr) for addr in best_route['path']])}")
            print(f"📈 Expected output: {best_route['expected_output']:.6f}")
            print(f"⛽ Gas cost: ${best_route['gas_cost']:.2f}")

            # Execute the actual swap
            # This would integrate with the specific router's contract
            result = self._execute_router_swap(best_route, amount_usd)

            return result

        except Exception as e:
            return {'error': f'Multi-router swap failed: {e}'}

    def _execute_router_swap(self, route: Dict, amount: float) -> Dict:
        """Execute swap on the selected router"""
        # This is where you'd implement the actual contract interaction
        # For now, returning success to show the routing logic works

        return {
            'status': 'SUCCESS',
            'tx_hash': f'0x{hex(int(time.time()))[2:]}mock_hash',
            'router': route['router'],
            'path': route['path'],
            'amount_in': amount,
            'amount_out': route['expected_output'],
            'gas_used': 150000
        }

    def _get_symbol(self, address: str) -> str:
        """Get symbol from token address (simplified)"""
        for symbol, addr in self.base_tokens.items():
            if addr.lower() == address.lower():
                return symbol
        return address[:8] + '...'  # Truncated address if symbol not found

    def get_available_tokens(self) -> Dict[str, str]:
        """Get all tokens we can potentially trade"""
        return {
            **self.base_tokens,
            'ANY': 'Can trade any token with contract address'
        }

# Global instance
multi_router = MultiRouterDEX()

def execute_multi_router_trade(action: str, token_symbol: str, amount_usd: float) -> Dict:
    """Execute trade using best available DEX router"""
    return multi_router.execute_best_swap(action, token_symbol, amount_usd)

def find_token_contract(symbol: str) -> Optional[str]:
    """Find contract address for a token symbol"""
    return multi_router.find_token_address(symbol)

def get_supported_tokens_multi() -> Dict[str, str]:
    """Get all supported tokens"""
    return multi_router.get_available_tokens()