#!/usr/bin/env python3
"""
Quick Test for Real DEX Execution
Tests the core trading components with minimal overhead
"""

import os
import sys
from datetime import datetime

# Add the project directory to Python path
sys.path.insert(0, '/Users/joshuamiller/Developer/llm_crypto_bot')

def test_configuration():
    """Test that all critical configuration is present"""
    print("🔧 Testing Configuration...")

    # Test config import
    try:
        import config
        print("✅ Config module imported successfully")

        # Check critical settings
        wallet_address = config.WALLET_ADDRESS
        private_key = config.PRIVATE_KEY

        if not wallet_address:
            print("❌ WALLET_ADDRESS not configured in environment")
            return False

        if not private_key:
            print("❌ PRIVATE_KEY not configured in environment")
            return False

        print(f"✅ Wallet configured: {wallet_address[:10]}...{wallet_address[-4:]}")

        # Test chain RPC URLs
        chain_count = len([url for url in config.CHAIN_RPC_URLS.values() if url])
        print(f"✅ {chain_count} blockchain RPCs configured")

        return True

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_web3_connections():
    """Test Web3 blockchain connections"""
    print("\n🌐 Testing Blockchain Connections...")

    try:
        from real_dex_executor import get_real_dex_executor

        dex_executor = get_real_dex_executor()
        connected_chains = list(dex_executor.web3_connections.keys())

        if connected_chains:
            print(f"✅ Connected to {len(connected_chains)} chains: {', '.join(connected_chains)}")

            # Test balance check on primary chain (BSC or Ethereum)
            if 'bsc' in connected_chains:
                test_chain = 'bsc'
            elif 'ethereum' in connected_chains:
                test_chain = 'ethereum'
            else:
                test_chain = connected_chains[0]

            import config
            w3 = dex_executor.web3_connections[test_chain]
            balance = w3.eth.get_balance(config.WALLET_ADDRESS)
            balance_eth = w3.from_wei(balance, 'ether')

            print(f"✅ {test_chain.upper()} balance: {balance_eth:.6f} native tokens")

            if balance_eth < 0.001:
                print("⚠️  WARNING: Very low native token balance for gas fees")

            return True
        else:
            print("❌ No blockchain connections established")
            return False

    except Exception as e:
        print(f"❌ Web3 connection test failed: {e}")
        return False

def test_token_discovery():
    """Test token contract discovery"""
    print("\n🔍 Testing Token Discovery...")

    try:
        from token_intelligence import get_token_contract_address

        # Test with a token that exists on BSC (where we have more gas)
        test_token = "CAKE"  # PancakeSwap token - native to BSC
        contract_address = get_token_contract_address(test_token)

        if contract_address:
            print(f"✅ Found {test_token}: {contract_address[:10]}...{contract_address[-4:]}")

            # Get more detailed analysis
            from token_intelligence import get_token_intelligence
            ti = get_token_intelligence()
            analysis = ti.get_comprehensive_token_analysis(test_token)

            # Extract chain info from analysis
            chain_info = analysis.get('contract_info', {}).get('blockchain', 'unknown')
            print(f"   Chain: {chain_info}")

            return True
        else:
            print(f"❌ Could not find contract for {test_token}")
            return False

    except Exception as e:
        print(f"❌ Token discovery test failed: {e}")
        return False

def test_mock_trade():
    """Test a mock trade execution to verify the pipeline"""
    print("\n💰 Testing Mock Trade Execution...")

    try:
        from real_executor import execute_real_trade

        # Create a minimal test decision using BSC token (we have more BNB for gas)
        test_decision = {
            'action': 'BUY',
            'token': 'CAKE',  # BSC token where we have sufficient gas
            'amount_usd': 1.0,  # $1 test trade
            'confidence': 0.75,
            'reasoning': 'Test trade to verify execution pipeline on BSC'
        }

        print(f"🎯 Testing trade: {test_decision['action']} {test_decision['token']} for ${test_decision['amount_usd']}")
        print("⚠️  This is a REAL MONEY test - will attempt actual blockchain transaction")

        # Execute the trade
        result = execute_real_trade(test_decision)

        print(f"\n📋 Trade Result:")
        print(f"   Status: {result.get('status', 'Unknown')}")
        print(f"   Trade Executed: {result.get('trade_executed', False)}")

        if result.get('error'):
            print(f"   Error: {result['error']}")
            return False

        if result.get('tx_hash'):
            print(f"   Transaction Hash: {result['tx_hash']}")

        return result.get('status') == 'SUCCESS'

    except Exception as e:
        print(f"❌ Mock trade test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Real Trading System Tests")
    print("=" * 50)

    tests = [
        ("Configuration", test_configuration),
        ("Web3 Connections", test_web3_connections),
        ("Token Discovery", test_token_discovery),
        ("Mock Trade Execution", test_mock_trade)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except KeyboardInterrupt:
            print(f"\n⚠️  Test interrupted by user")
            break
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print(f"\n{'='*20} TEST SUMMARY {'='*20}")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")

    print(f"\n📊 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Real trading system is ready.")
    else:
        print("⚠️  Some tests failed. Review errors above before enabling real trades.")

    return passed == total

if __name__ == "__main__":
    main()