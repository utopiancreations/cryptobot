#!/usr/bin/env python3
"""
Test script for comprehensive multi-wallet portfolio analysis
"""

import json
import sys
from utils.multi_wallet_manager import get_comprehensive_portfolio, check_all_wallet_connections, print_portfolio_summary, get_all_wallet_addresses

def main():
    print("🚀 Multi-Wallet Portfolio Analyzer")
    print("=" * 60)

    # Show configured wallets
    wallets = get_all_wallet_addresses()
    print(f"\n📋 Configured Wallets ({len(wallets)}):")
    for address, name in wallets:
        print(f"   {name}: {address}")

    if len(sys.argv) > 1 and sys.argv[1] == "--connections-only":
        print("\n🔗 Testing Connections Only...")
        connection_results = check_all_wallet_connections()

        print(f"\n📊 Connection Summary:")
        print(f"   Overall Health: {connection_results['overall_health'].upper()}")
        print(f"   Total Successful: {connection_results['total_successful_chains']}/{connection_results['total_possible_chains']}")

        for wallet_name, wallet_data in connection_results['wallets'].items():
            if 'error' in wallet_data:
                print(f"   {wallet_name}: ❌ {wallet_data['error']}")
            else:
                success_rate = wallet_data['successful_chains'] / wallet_data['total_chains']
                print(f"   {wallet_name}: ✅ {wallet_data['successful_chains']}/{wallet_data['total_chains']} ({success_rate:.1%})")
        return

    print("\n💰 Analyzing Complete Portfolio...")

    try:
        portfolio = get_comprehensive_portfolio()

        # Print comprehensive summary
        print_portfolio_summary(portfolio)

        # Save detailed results
        results_file = "multi_wallet_portfolio.json"
        with open(results_file, 'w') as f:
            # Convert sets to lists for JSON serialization
            json_portfolio = json.loads(json.dumps(portfolio, default=str))
            json.dump(json_portfolio, f, indent=2)

        print(f"\n💾 Detailed results saved to: {results_file}")

        # Quick insights
        print(f"\n🎯 Key Insights:")
        total_value = portfolio['total_usd_estimate']
        if total_value > 1000:
            print(f"   💎 High-value portfolio: ${total_value:.2f}")
        elif total_value > 100:
            print(f"   📈 Growing portfolio: ${total_value:.2f}")
        else:
            print(f"   🌱 Starter portfolio: ${total_value:.2f}")

        # Chain diversity
        active_chains = len([chain for chain, data in portfolio['chain_summary'].items() if data['total_usd'] > 0])
        if active_chains >= 5:
            print(f"   🌐 Well diversified across {active_chains} chains")
        elif active_chains >= 3:
            print(f"   🔗 Good diversification across {active_chains} chains")
        else:
            print(f"   ⚠️  Limited diversification: only {active_chains} chains")

        # Token diversity
        valuable_tokens = len([token for token, data in portfolio['token_summary'].items() if data['total_usd_estimate'] > 10])
        if valuable_tokens >= 10:
            print(f"   🪙 Highly diverse: {valuable_tokens} valuable tokens")
        elif valuable_tokens >= 5:
            print(f"   💰 Good token diversity: {valuable_tokens} valuable tokens")
        else:
            print(f"   📊 Conservative: {valuable_tokens} valuable tokens")

    except Exception as e:
        print(f"❌ Error analyzing portfolio: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()