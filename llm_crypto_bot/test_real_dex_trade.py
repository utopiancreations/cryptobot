#!/usr/bin/env python3
"""
Test script for real DEX trading with QuickSwap integration
"""

from real_executor import execute_real_trade
from dex_integration import get_supported_tokens

def test_small_trade():
    """Test a very small real trade to verify DEX integration"""
    
    print("🧪 Testing REAL DEX Trade Integration")
    print("=" * 50)
    
    # Show supported tokens
    print(f"Supported tokens: {', '.join(get_supported_tokens())}")
    print()
    
    # Create a small test trade decision
    test_decision = {
        'action': 'BUY',
        'token': 'USDC',  # Safe stable coin
        'amount_usd': 2.0,  # Very small amount
        'confidence': 0.8,  # High confidence to trigger execution
        'reasoning': 'Test trade for DEX integration verification'
    }
    
    print(f"📋 Test Trade:")
    print(f"   Action: {test_decision['action']} {test_decision['token']}")
    print(f"   Amount: ${test_decision['amount_usd']:.2f}")
    print(f"   Confidence: {test_decision['confidence']:.1%}")
    print()
    
    # Confirm test execution
    print("⚠️  This will execute a REAL trade on QuickSwap!")
    print("⚠️  Only proceed if you want to test with real money")
    print()
    
    # Execute the trade
    print("🚀 Executing test trade...")
    result = execute_real_trade(test_decision)
    
    print("\n" + "=" * 50)
    print("📊 TRADE EXECUTION RESULT")
    print("=" * 50)
    
    if result.get('status') == 'EXECUTED_REAL':
        print("✅ REAL TRADE EXECUTED SUCCESSFULLY!")
        print(f"🆔 Trade ID: {result.get('trade_id')}")
        print(f"🔗 TX Hash: {result.get('transaction_hash')}")
        print(f"⛽ Gas Used: {result.get('gas_used', 0)}")
        print(f"🏢 Platform: {result.get('dex_platform', 'Unknown')}")
        print(f"🌐 Network: {result.get('network', 'Unknown')}")
        
        # Show Polygonscan link if we have a real tx hash
        tx_hash = result.get('transaction_hash', '')
        if tx_hash and not tx_hash.startswith('VALIDATED'):
            print(f"🔍 View on Polygonscan: https://polygonscan.com/tx/{tx_hash}")
        
    elif result.get('status') == 'ERROR':
        print(f"❌ Trade failed: {result.get('error', 'Unknown error')}")
        
    else:
        print(f"⚠️ Unexpected result: {result}")
    
    print("\n" + "=" * 50)
    print("🎉 DEX Integration Test Complete!")
    
    return result

if __name__ == "__main__":
    test_small_trade()