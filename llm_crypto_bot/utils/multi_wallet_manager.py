"""
Multi-Wallet Portfolio Manager
Handles multiple wallets across multiple chains for comprehensive portfolio management
"""

from typing import Dict, List, Optional, Tuple
import config
from .multi_chain_wallet import get_all_chain_balances, check_all_chain_connections

def get_all_wallet_addresses() -> List[Tuple[str, str]]:
    """Get all configured wallet addresses with their names"""
    wallets = []

    # Primary wallet
    if config.WALLET_ADDRESS:
        primary_name = "Primary" if not config.WALLET_NAMES else config.WALLET_NAMES[0]
        wallets.append((config.WALLET_ADDRESS, primary_name))

    # Additional wallets
    for i, wallet_address in enumerate(config.ADDITIONAL_WALLETS):
        if wallet_address.strip():
            wallet_name = f"Wallet{i+2}"
            if len(config.WALLET_NAMES) > i + 1:
                wallet_name = config.WALLET_NAMES[i + 1]
            wallets.append((wallet_address.strip(), wallet_name))

    return wallets

def get_comprehensive_portfolio() -> Dict:
    """Get comprehensive portfolio across all wallets and all chains"""

    all_wallets = get_all_wallet_addresses()

    portfolio = {
        'total_usd_estimate': 0.0,
        'wallet_count': len(all_wallets),
        'wallets': {},
        'chain_summary': {},
        'token_summary': {},
        'top_holdings_global': [],
        'summary': {
            'total_chains_checked': 0,
            'total_successful_connections': 0,
            'total_native_balance_usd': 0.0,
            'total_token_balance_usd': 0.0,
            'most_valuable_wallet': '',
            'most_diverse_wallet': ''
        }
    }

    print(f"📊 Analyzing {len(all_wallets)} wallets across all chains...")

    all_holdings = []

    for wallet_address, wallet_name in all_wallets:
        print(f"\n🔍 Analyzing {wallet_name}: {wallet_address}")

        try:
            wallet_portfolio = get_all_chain_balances(wallet_address)

            if wallet_portfolio:
                portfolio['wallets'][wallet_name] = {
                    'address': wallet_address,
                    'portfolio': wallet_portfolio,
                    'total_usd': wallet_portfolio.get('total_usd_estimate', 0),
                    'active_chains': wallet_portfolio['summary']['successful_connections']
                }

                portfolio['total_usd_estimate'] += wallet_portfolio.get('total_usd_estimate', 0)
                portfolio['summary']['total_chains_checked'] += wallet_portfolio['summary']['total_chains_checked']
                portfolio['summary']['total_successful_connections'] += wallet_portfolio['summary']['successful_connections']

                # Aggregate chain data
                for chain_name, chain_data in wallet_portfolio.get('chains', {}).items():
                    if 'error' not in chain_data:
                        if chain_name not in portfolio['chain_summary']:
                            portfolio['chain_summary'][chain_name] = {
                                'total_usd': 0,
                                'wallets_with_balance': 0,
                                'total_native_balance': 0,
                                'native_symbol': chain_data.get('native_token', {}).get('symbol', 'Unknown')
                            }

                        chain_usd = chain_data.get('total_usd_estimate', 0)
                        if chain_usd > 0:
                            portfolio['chain_summary'][chain_name]['total_usd'] += chain_usd
                            portfolio['chain_summary'][chain_name]['wallets_with_balance'] += 1

                        native_balance = chain_data.get('native_token', {}).get('balance', 0)
                        if native_balance > 0:
                            portfolio['chain_summary'][chain_name]['total_native_balance'] += native_balance

                # Collect all holdings for global top list
                for holding in wallet_portfolio.get('top_holdings', []):
                    holding['wallet'] = wallet_name
                    all_holdings.append(holding)

                print(f"✅ {wallet_name}: ${wallet_portfolio.get('total_usd_estimate', 0):.2f} across {wallet_portfolio['summary']['successful_connections']} chains")
            else:
                print(f"❌ {wallet_name}: Failed to get portfolio data")
                portfolio['wallets'][wallet_name] = {
                    'address': wallet_address,
                    'error': 'Failed to retrieve portfolio data',
                    'total_usd': 0,
                    'active_chains': 0
                }

        except Exception as e:
            print(f"❌ {wallet_name}: Error - {e}")
            portfolio['wallets'][wallet_name] = {
                'address': wallet_address,
                'error': str(e),
                'total_usd': 0,
                'active_chains': 0
            }

    # Generate token summary
    portfolio['token_summary'] = _generate_token_summary(portfolio['wallets'])

    # Sort and get top holdings globally
    all_holdings.sort(key=lambda x: x['usd_estimate'], reverse=True)
    portfolio['top_holdings_global'] = all_holdings[:20]  # Top 20 globally

    # Calculate summary stats
    portfolio['total_usd_estimate'] = round(portfolio['total_usd_estimate'], 2)

    if portfolio['wallets']:
        # Find most valuable wallet
        most_valuable = max(portfolio['wallets'].items(), key=lambda x: x[1].get('total_usd', 0))
        portfolio['summary']['most_valuable_wallet'] = f"{most_valuable[0]} (${most_valuable[1].get('total_usd', 0):.2f})"

        # Find most diverse wallet (most chains)
        most_diverse = max(portfolio['wallets'].items(), key=lambda x: x[1].get('active_chains', 0))
        portfolio['summary']['most_diverse_wallet'] = f"{most_diverse[0]} ({most_diverse[1].get('active_chains', 0)} chains)"

    return portfolio

def check_all_wallet_connections() -> Dict:
    """Test connections for all configured wallets"""
    all_wallets = get_all_wallet_addresses()

    results = {
        'wallet_count': len(all_wallets),
        'wallets': {},
        'overall_health': 'unknown',
        'total_successful_chains': 0,
        'total_possible_chains': 0
    }

    for wallet_address, wallet_name in all_wallets:
        print(f"\n🔗 Testing {wallet_name}: {wallet_address}")

        try:
            connection_result = check_all_chain_connections(wallet_address)
            results['wallets'][wallet_name] = {
                'address': wallet_address,
                'connection_result': connection_result,
                'successful_chains': connection_result.get('successful_connections', 0),
                'total_chains': connection_result.get('total_chains', 0)
            }

            results['total_successful_chains'] += connection_result.get('successful_connections', 0)
            results['total_possible_chains'] += connection_result.get('total_chains', 0)

        except Exception as e:
            print(f"❌ {wallet_name}: Connection test failed - {e}")
            results['wallets'][wallet_name] = {
                'address': wallet_address,
                'error': str(e),
                'successful_chains': 0,
                'total_chains': 0
            }

    # Calculate overall health
    if results['total_possible_chains'] > 0:
        success_rate = results['total_successful_chains'] / results['total_possible_chains']
        if success_rate >= 0.8:
            results['overall_health'] = 'excellent'
        elif success_rate >= 0.6:
            results['overall_health'] = 'good'
        elif success_rate >= 0.4:
            results['overall_health'] = 'fair'
        else:
            results['overall_health'] = 'poor'

    return results

def get_wallet_by_name(wallet_name: str) -> Optional[str]:
    """Get wallet address by name"""
    all_wallets = get_all_wallet_addresses()
    for address, name in all_wallets:
        if name.lower() == wallet_name.lower():
            return address
    return None

def get_trading_wallet() -> Tuple[str, str]:
    """Get the primary trading wallet (with private key)"""
    if config.WALLET_ADDRESS and config.PRIVATE_KEY:
        wallet_name = "Primary" if not config.WALLET_NAMES else config.WALLET_NAMES[0]
        return config.WALLET_ADDRESS, wallet_name
    else:
        raise ValueError("No trading wallet configured (missing WALLET_ADDRESS or PRIVATE_KEY)")

def _generate_token_summary(wallets_data: Dict) -> Dict:
    """Generate aggregated token summary across all wallets"""
    token_summary = {}

    for wallet_name, wallet_info in wallets_data.items():
        if 'portfolio' not in wallet_info:
            continue

        portfolio = wallet_info['portfolio']

        for chain_name, chain_data in portfolio.get('chains', {}).items():
            if 'error' in chain_data:
                continue

            # Native tokens
            native_token = chain_data.get('native_token', {})
            if native_token.get('balance', 0) > 0:
                symbol = native_token['symbol']
                if symbol not in token_summary:
                    token_summary[symbol] = {
                        'total_balance': 0,
                        'total_usd_estimate': 0,
                        'chains': set(),
                        'wallets': set()
                    }

                token_summary[symbol]['total_balance'] += native_token['balance']
                token_summary[symbol]['total_usd_estimate'] += native_token['balance'] * _get_mock_price(symbol)
                token_summary[symbol]['chains'].add(chain_name)
                token_summary[symbol]['wallets'].add(wallet_name)

            # Regular tokens
            for token_symbol, token_data in chain_data.get('tokens', {}).items():
                if token_symbol not in token_summary:
                    token_summary[token_symbol] = {
                        'total_balance': 0,
                        'total_usd_estimate': 0,
                        'chains': set(),
                        'wallets': set()
                    }

                token_summary[token_symbol]['total_balance'] += token_data['balance']
                token_summary[token_symbol]['total_usd_estimate'] += token_data['balance'] * _get_mock_price(token_symbol)
                token_summary[token_symbol]['chains'].add(chain_name)
                token_summary[token_symbol]['wallets'].add(wallet_name)

    # Convert sets to lists for JSON serialization
    for token_data in token_summary.values():
        token_data['chains'] = list(token_data['chains'])
        token_data['wallets'] = list(token_data['wallets'])
        token_data['total_usd_estimate'] = round(token_data['total_usd_estimate'], 2)

    return token_summary

def _get_mock_price(symbol: str) -> float:
    """Mock prices for USD estimation"""
    prices = {
        'ETH': 2500.0, 'BTC': 45000.0, 'MATIC': 0.8, 'BNB': 300.0,
        'AVAX': 25.0, 'FTM': 0.3, 'SOL': 140.0,
        'USDT': 1.0, 'USDC': 1.0, 'BUSD': 1.0, 'DAI': 1.0,
        'WETH': 2500.0, 'WBTC': 45000.0, 'BTCB': 45000.0, 'mSOL': 140.0
    }
    return prices.get(symbol.upper(), 0.0)

def print_portfolio_summary(portfolio: Dict):
    """Print a formatted portfolio summary"""
    print(f"\n" + "=" * 80)
    print(f"📊 COMPREHENSIVE MULTI-WALLET PORTFOLIO SUMMARY")
    print(f"=" * 80)

    print(f"\n💰 Overall Portfolio:")
    print(f"   Total Value: ${portfolio['total_usd_estimate']:.2f}")
    print(f"   Wallets: {portfolio['wallet_count']}")
    print(f"   Most Valuable: {portfolio['summary']['most_valuable_wallet']}")
    print(f"   Most Diverse: {portfolio['summary']['most_diverse_wallet']}")

    print(f"\n🌐 Chain Distribution:")
    for chain_name, chain_data in sorted(portfolio['chain_summary'].items(), key=lambda x: x[1]['total_usd'], reverse=True):
        if chain_data['total_usd'] > 0:
            print(f"   {chain_name.upper()}: ${chain_data['total_usd']:.2f} ({chain_data['wallets_with_balance']} wallets)")

    print(f"\n🪙 Top Token Holdings:")
    for symbol, token_data in sorted(portfolio['token_summary'].items(), key=lambda x: x[1]['total_usd_estimate'], reverse=True)[:10]:
        print(f"   {symbol}: {token_data['total_balance']:.4f} (${token_data['total_usd_estimate']:.2f}) across {len(token_data['chains'])} chains")

    print(f"\n🏆 Top 10 Individual Holdings:")
    for i, holding in enumerate(portfolio['top_holdings_global'][:10], 1):
        print(f"   {i:2d}. {holding['balance']:.4f} {holding['symbol']} on {holding['chain']} ({holding['wallet']}) - ${holding['usd_estimate']:.2f}")