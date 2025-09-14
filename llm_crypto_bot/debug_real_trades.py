#!/usr/bin/env python3
"""
Debug script to test real trade execution
"""

import sys
sys.path.append('.')

from real_executor import execute_real_trade

def test_real_trade_execution():
    print("🔍 DEBUGGING REAL TRADE EXECUTION")
    print("=" * 50)

    # Test with a simple BUY decision similar to what the bot generates
    test_decision = {
        'action': 'BUY',
        'token': 'DORA',  # From your logs
        'amount_usd': 3.00,
        'confidence': 0.85,
        'reasoning': 'Test trade for debugging'
    }

    print(f"Testing trade execution with decision:")
    for key, value in test_decision.items():
        print(f"  {key}: {value}")

    print("\n🔄 Calling execute_real_trade...")

    try:
        result = execute_real_trade(test_decision)
        print(f"\n✅ Trade execution returned:")
        print(f"Result type: {type(result)}")
        for key, value in result.items():
            print(f"  {key}: {value}")

        if 'error' in result:
            print(f"\n❌ ERROR: {result['error']}")
        elif result.get('status') == 'EXECUTED_REAL':
            print(f"\n🎉 SUCCESS: Trade executed with tx hash: {result.get('transaction_hash')}")
        else:
            print(f"\n⚠️  Unexpected result status: {result.get('status')}")

    except Exception as e:
        print(f"\n❌ EXCEPTION during trade execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_real_trade_execution()