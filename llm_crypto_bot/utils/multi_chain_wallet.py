"""
Multi-Chain Wallet utilities for comprehensive portfolio management across all supported chains
"""

from web3 import Web3
from typing import Dict, Optional, List, Tuple
import config
from .wallet import get_token_balance

try:
    from .solana_wallet import get_solana_wallet_balance
    SOLANA_SUPPORT = True
except ImportError:
    SOLANA_SUPPORT = False

def get_all_chain_balances(wallet_address: str = None, private_key: str = None) -> Dict:
    """
    Get wallet balances across all supported EVM chains + Solana

    Returns comprehensive portfolio data across all chains
    """
    if not wallet_address:
        wallet_address = config.WALLET_ADDRESS

    portfolio = {
        'total_usd_estimate': 0.0,
        'chains': {},
        'summary': {
            'total_chains_checked': 0,
            'successful_connections': 0,
            'total_native_balance_usd': 0.0,
            'total_token_balance_usd': 0.0
        },
        'top_holdings': []
    }

    # Check EVM chains
    for chain_name, rpc_url in config.CHAIN_RPC_URLS.items():
        try:
            chain_data = get_chain_balance(chain_name, rpc_url, wallet_address)
            if chain_data:
                portfolio['chains'][chain_name] = chain_data
                portfolio['total_usd_estimate'] += chain_data.get('total_usd_estimate', 0)
                portfolio['summary']['successful_connections'] += 1

            portfolio['summary']['total_chains_checked'] += 1

        except Exception as e:
            print(f"⚠️  Error checking {chain_name}: {e}")
            portfolio['chains'][chain_name] = {
                'error': str(e),
                'native_token': {'balance': 0, 'symbol': _get_native_symbol(chain_name)},
                'tokens': {},
                'total_usd_estimate': 0.0
            }

    # Check Solana
    if SOLANA_SUPPORT and config.SOLANA_WALLET_ADDRESS:
        try:
            solana_data = get_solana_wallet_balance()
            if solana_data:
                portfolio['chains']['solana'] = solana_data
                portfolio['total_usd_estimate'] += solana_data.get('total_usd_estimate', 0)
                portfolio['summary']['successful_connections'] += 1
            portfolio['summary']['total_chains_checked'] += 1
        except Exception as e:
            print(f"⚠️  Error checking Solana: {e}")

    # Calculate summary statistics
    for chain_name, chain_data in portfolio['chains'].items():
        if 'native_token' in chain_data:
            native_usd = chain_data['native_token']['balance'] * _get_mock_price(chain_data['native_token']['symbol'])
            portfolio['summary']['total_native_balance_usd'] += native_usd

        if 'tokens' in chain_data:
            for symbol, token_data in chain_data['tokens'].items():
                token_usd = token_data['balance'] * _get_mock_price(symbol)
                portfolio['summary']['total_token_balance_usd'] += token_usd

    # Generate top holdings
    portfolio['top_holdings'] = _generate_top_holdings(portfolio['chains'])

    portfolio['total_usd_estimate'] = round(portfolio['total_usd_estimate'], 2)
    portfolio['summary']['total_native_balance_usd'] = round(portfolio['summary']['total_native_balance_usd'], 2)
    portfolio['summary']['total_token_balance_usd'] = round(portfolio['summary']['total_token_balance_usd'], 2)

    return portfolio

def get_chain_balance(chain_name: str, rpc_url: str, wallet_address: str) -> Optional[Dict]:
    """Get balance for a specific EVM chain"""
    try:
        # Connect to chain
        w3 = Web3(Web3.HTTPProvider(rpc_url))

        if not w3.is_connected():
            return None

        wallet_address = Web3.to_checksum_address(wallet_address)

        # Get native token balance
        native_balance_wei = w3.eth.get_balance(wallet_address)
        native_balance = w3.from_wei(native_balance_wei, 'ether')
        native_symbol = _get_native_symbol(chain_name)

        chain_data = {
            'chain': chain_name,
            'rpc_url': rpc_url,
            'wallet_address': wallet_address,
            'native_token': {
                'symbol': native_symbol,
                'balance': float(native_balance),
                'balance_wei': native_balance_wei
            },
            'tokens': {},
            'total_usd_estimate': 0.0
        }

        # Get token balances for this chain
        token_contracts = config.CHAIN_TOKEN_CONTRACTS.get(chain_name, {})

        for symbol, contract_address in token_contracts.items():
            try:
                token_balance = get_token_balance(wallet_address, contract_address, w3)
                if token_balance > 0.001:  # Only include meaningful balances
                    chain_data['tokens'][symbol] = {
                        'balance': token_balance,
                        'contract_address': contract_address
                    }
            except Exception as e:
                print(f"Error getting {symbol} balance on {chain_name}: {e}")

        # Estimate USD value
        chain_data['total_usd_estimate'] = _estimate_chain_usd_value(chain_data)

        return chain_data

    except Exception as e:
        print(f"Error connecting to {chain_name}: {e}")
        return None

def check_all_chain_connections(wallet_address: str = None) -> Dict:
    """Test connections to all supported chains"""
    if not wallet_address:
        wallet_address = config.WALLET_ADDRESS

    results = {
        'total_chains': 0,
        'successful_connections': 0,
        'failed_connections': 0,
        'chain_status': {},
        'overall_health': 'unknown'
    }

    # Test EVM chains
    for chain_name, rpc_url in config.CHAIN_RPC_URLS.items():
        results['total_chains'] += 1
        try:
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            if w3.is_connected():
                # Quick balance test
                checksum_address = Web3.to_checksum_address(wallet_address)
                balance = w3.eth.get_balance(checksum_address)

                results['chain_status'][chain_name] = {
                    'status': 'connected',
                    'balance': w3.from_wei(balance, 'ether'),
                    'symbol': _get_native_symbol(chain_name)
                }
                results['successful_connections'] += 1
            else:
                results['chain_status'][chain_name] = {'status': 'rpc_failed'}
                results['failed_connections'] += 1
        except Exception as e:
            results['chain_status'][chain_name] = {'status': 'error', 'error': str(e)}
            results['failed_connections'] += 1

    # Test Solana
    if SOLANA_SUPPORT:
        results['total_chains'] += 1
        try:
            from .solana_wallet import check_solana_wallet_connection
            if check_solana_wallet_connection():
                results['chain_status']['solana'] = {'status': 'connected'}
                results['successful_connections'] += 1
            else:
                results['chain_status']['solana'] = {'status': 'connection_failed'}
                results['failed_connections'] += 1
        except Exception as e:
            results['chain_status']['solana'] = {'status': 'error', 'error': str(e)}
            results['failed_connections'] += 1

    # Determine overall health
    success_rate = results['successful_connections'] / results['total_chains']
    if success_rate >= 0.8:
        results['overall_health'] = 'excellent'
    elif success_rate >= 0.6:
        results['overall_health'] = 'good'
    elif success_rate >= 0.4:
        results['overall_health'] = 'fair'
    else:
        results['overall_health'] = 'poor'

    return results

def find_best_chain_for_trading(token_symbol: str = None) -> Tuple[str, str]:
    """
    Find the best chain for trading based on:
    1. Liquidity availability
    2. Transaction fees
    3. Network congestion
    """

    # Priority ranking based on fees and activity
    chain_priorities = {
        'arbitrum': {'score': 95, 'reason': 'Low fees, high liquidity'},
        'base': {'score': 90, 'reason': 'Very low fees, growing ecosystem'},
        'polygon': {'score': 85, 'reason': 'Low fees, established DeFi'},
        'optimism': {'score': 80, 'reason': 'Low fees, good ecosystem'},
        'bsc': {'score': 75, 'reason': 'Low fees, high volume'},
        'avalanche': {'score': 70, 'reason': 'Fast, good for new tokens'},
        'fantom': {'score': 60, 'reason': 'Low fees but lower liquidity'},
        'ethereum': {'score': 50, 'reason': 'High liquidity but expensive'}
    }

    # If looking for a specific token, adjust priorities
    if token_symbol:
        # Meme coins and new tokens often launch on specific chains first
        meme_friendly_chains = ['base', 'arbitrum', 'bsc', 'polygon']
        if any(keyword in token_symbol.lower() for keyword in ['pepe', 'doge', 'shib', 'meme']):
            for chain in meme_friendly_chains:
                if chain in chain_priorities:
                    chain_priorities[chain]['score'] += 10

    # Find best available chain
    best_chain = max(chain_priorities.keys(), key=lambda x: chain_priorities[x]['score'])
    best_rpc = config.CHAIN_RPC_URLS.get(best_chain)

    return best_chain, best_rpc

def _get_native_symbol(chain_name: str) -> str:
    """Get native token symbol for chain"""
    symbols = {
        'ethereum': 'ETH',
        'polygon': 'MATIC',
        'bsc': 'BNB',
        'arbitrum': 'ETH',
        'optimism': 'ETH',
        'base': 'ETH',
        'avalanche': 'AVAX',
        'fantom': 'FTM'
    }
    return symbols.get(chain_name, 'ETH')

def _get_mock_price(symbol: str) -> float:
    """Mock prices for USD estimation"""
    prices = {
        'ETH': 2500.0, 'BTC': 45000.0, 'MATIC': 0.8, 'BNB': 300.0,
        'AVAX': 25.0, 'FTM': 0.3, 'SOL': 140.0,
        'USDT': 1.0, 'USDC': 1.0, 'BUSD': 1.0, 'DAI': 1.0,
        'WETH': 2500.0, 'WBTC': 45000.0, 'BTCB': 45000.0
    }
    return prices.get(symbol.upper(), 0.0)

def _estimate_chain_usd_value(chain_data: Dict) -> float:
    """Estimate USD value for a chain's holdings"""
    total_usd = 0.0

    # Native token
    native_balance = chain_data['native_token']['balance']
    native_symbol = chain_data['native_token']['symbol']
    total_usd += native_balance * _get_mock_price(native_symbol)

    # Tokens
    for symbol, token_info in chain_data['tokens'].items():
        token_balance = token_info['balance']
        total_usd += token_balance * _get_mock_price(symbol)

    return round(total_usd, 2)

def _generate_top_holdings(chains_data: Dict) -> List[Dict]:
    """Generate top holdings across all chains"""
    holdings = []

    for chain_name, chain_data in chains_data.items():
        if 'error' in chain_data:
            continue

        # Native token
        if 'native_token' in chain_data:
            native = chain_data['native_token']
            if native['balance'] > 0:
                holdings.append({
                    'symbol': native['symbol'],
                    'balance': native['balance'],
                    'chain': chain_name,
                    'usd_estimate': native['balance'] * _get_mock_price(native['symbol']),
                    'type': 'native'
                })

        # Tokens
        if 'tokens' in chain_data:
            for symbol, token_data in chain_data['tokens'].items():
                if token_data['balance'] > 0:
                    holdings.append({
                        'symbol': symbol,
                        'balance': token_data['balance'],
                        'chain': chain_name,
                        'usd_estimate': token_data['balance'] * _get_mock_price(symbol),
                        'type': 'token'
                    })

    # Sort by USD value and return top 10
    holdings.sort(key=lambda x: x['usd_estimate'], reverse=True)
    return holdings[:10]