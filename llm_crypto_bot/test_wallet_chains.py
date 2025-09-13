#!/usr/bin/env python3
"""
Test script to check wallet balances across all supported chains
Useful for discovering assets in old wallets
"""

import sys
import json
from utils.multi_chain_wallet import get_all_chain_balances, check_all_chain_connections

def test_wallet(wallet_address: str):
    """Test wallet across all chains"""

    print(f"🔍 Analyzing wallet: {wallet_address}")
    print("=" * 60)

    # First, test connections
    print("\n🔗 Testing chain connections...")
    connection_results = check_all_chain_connections(wallet_address)

    print(f"\n📊 Connection Status: {connection_results['overall_health'].upper()}")
    print(f"✅ Successful: {connection_results['successful_connections']}/{connection_results['total_chains']}")

    if connection_results['failed_connections'] > 0:
        print(f"❌ Failed connections:")
        for chain, status in connection_results['chain_status'].items():
            if status['status'] != 'connected':
                print(f"   {chain}: {status['status']}")

    print("\n" + "=" * 60)

    # Get balances across all chains
    print("\n💰 Scanning wallet balances across all chains...")
    portfolio = get_all_chain_balances(wallet_address)

    print(f"\n📊 Portfolio Summary:")
    print(f"Total Estimated Value: ${portfolio['total_usd_estimate']:.2f}")
    print(f"Active Chains: {portfolio['summary']['successful_connections']}")
    print(f"Native Token Value: ${portfolio['summary']['total_native_balance_usd']:.2f}")
    print(f"Token Value: ${portfolio['summary']['total_token_balance_usd']:.2f}")

    # Show chain-by-chain breakdown
    print(f"\n🌐 Chain-by-Chain Breakdown:")
    print("-" * 50)

    for chain_name, chain_data in portfolio['chains'].items():
        if 'error' in chain_data:
            print(f"{chain_name.upper()}: ❌ {chain_data['error']}")
            continue

        chain_value = chain_data.get('total_usd_estimate', 0)
        print(f"\n{chain_name.upper()}: ${chain_value:.2f}")

        # Native token
        native = chain_data['native_token']
        if native['balance'] > 0:
            native_usd = native['balance'] * get_mock_price(native['symbol'])
            print(f"  🏦 {native['balance']:.4f} {native['symbol']} (${native_usd:.2f})")

        # Tokens
        if chain_data['tokens']:
            print(f"  🪙 Tokens:")
            for symbol, token_data in chain_data['tokens'].items():
                token_usd = token_data['balance'] * get_mock_price(symbol)
                print(f"     {token_data['balance']:.4f} {symbol} (${token_usd:.2f})")

        if not chain_data['tokens'] and native['balance'] == 0:
            print(f"  💸 No balance")

    # Show top holdings
    if portfolio['top_holdings']:
        print(f"\n🏆 Top Holdings:")
        print("-" * 50)
        for i, holding in enumerate(portfolio['top_holdings'], 1):
            print(f"{i:2d}. {holding['balance']:.4f} {holding['symbol']} on {holding['chain']} (${holding['usd_estimate']:.2f})")

    return portfolio

def get_mock_price(symbol: str) -> float:
    """Mock prices for estimation"""
    prices = {
        'ETH': 2500.0, 'BTC': 45000.0, 'MATIC': 0.8, 'BNB': 300.0,
        'AVAX': 25.0, 'FTM': 0.3, 'SOL': 140.0,
        'USDT': 1.0, 'USDC': 1.0, 'BUSD': 1.0, 'DAI': 1.0,
        'WETH': 2500.0, 'WBTC': 45000.0, 'BTCB': 45000.0
    }
    return prices.get(symbol.upper(), 0.0)

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 test_wallet_chains.py <wallet_address>")
        print("Example: python3 test_wallet_chains.py 0x742d35cc6465c4c8ce44bd38b6b82e0200c12345")
        sys.exit(1)

    wallet_address = sys.argv[1]

    # Validate address format (basic check)
    if not wallet_address.startswith('0x') or len(wallet_address) != 42:
        print("❌ Invalid Ethereum address format. Address should start with 0x and be 42 characters long.")
        sys.exit(1)

    try:
        portfolio = test_wallet(wallet_address)

        # Save results
        results_file = f"wallet_analysis_{wallet_address[-8:]}.json"
        with open(results_file, 'w') as f:
            json.dump(portfolio, f, indent=2, default=str)
        print(f"\n💾 Results saved to: {results_file}")

    except Exception as e:
        print(f"❌ Error analyzing wallet: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()