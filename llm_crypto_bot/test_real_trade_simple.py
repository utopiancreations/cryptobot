#!/usr/bin/env python3
"""
Test Real DEX Trading

This script tests the actual DEX trading functionality with a small amount.
"""

import sys
from decimal import Decimal
from dex_integration import execute_dex_trade, get_supported_tokens
from utils.wallet import get_wallet_balance

def test_real_dex_trade():
    """Test real DEX trading with a very small amount"""
    
    print("🧪 Testing Real DEX Trading")
    print("=" * 50)
    
    # Check wallet balance first
    print("💰 Checking wallet balance...")
    balance = get_wallet_balance()
    if not balance:
        print("❌ Cannot retrieve wallet balance")
        return False
    
    print(f"📊 Current balance: {balance}")
    available_matic = balance.get('native_token', {}).get('balance', 0)
    
    if available_matic < 0.1:  # Need at least 0.1 MATIC for gas + trade
        print(f"❌ Insufficient MATIC balance: {available_matic} MATIC")
        print("   Need at least 0.1 MATIC for testing")
        return False
    
    # Test with very small amount - $0.50 worth
    test_amount_usd = 0.50
    
    print(f"🔄 Testing BUY trade: ${test_amount_usd} USDC")
    print("⚠️  THIS WILL BE A REAL TRADE ON THE BLOCKCHAIN")
    print("⚠️  Using lowered threshold (60%) for more aggressive trading")
    
    # Show supported tokens
    supported = get_supported_tokens()
    print(f"📋 Supported tokens: {supported}")
    
    # Execute test trade
    result = execute_dex_trade(
        action='BUY',
        token_symbol='USDC',
        amount_usd=test_amount_usd
    )
    
    print("\n📊 Trade Result:")
    print("-" * 30)
    
    if 'error' in result:
        print(f"❌ Trade failed: {result['error']}")
        return False
    else:
        print("✅ Trade executed successfully!")
        print(f"🔗 Transaction hash: {result.get('tx_hash', 'Unknown')}")
        print(f"⛽ Gas used: {result.get('gas_used', 'Unknown')}")
        print(f"💰 MATIC spent: {result.get('matic_spent', 'Unknown')}")
        print(f"🪙 Expected tokens: {result.get('expected_tokens', 'Unknown')}")
        
        if result.get('tx_hash'):
            print(f"🔍 View on PolygonScan: https://polygonscan.com/tx/{result['tx_hash']}")
        
        return True

if __name__ == "__main__":
    try:
        success = test_real_dex_trade()
        if success:
            print("\n🎉 Real DEX trading test completed successfully!")
            print("💎 Your trading bot can now execute real blockchain transactions!")
        else:
            print("\n❌ Real DEX trading test failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test crashed: {e}")
        sys.exit(1)