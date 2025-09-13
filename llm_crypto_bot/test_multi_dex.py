#!/usr/bin/env python3
"""
Comprehensive Multi-DEX Integration Test

Tests the complete multi-DEX trading system including:
- DEX discovery and selection
- Token availability across chains
- Trade execution simulation
- Gas fee estimation
"""

from multi_dex_integration import (
    execute_multi_dex_trade, 
    get_supported_tokens, 
    get_dex_info, 
    find_token_availability,
    multi_dex_trader
)

def test_multi_dex_integration():
    """Test the complete multi-DEX system"""
    print("🚀 MULTI-DEX INTEGRATION TEST")
    print("=" * 60)
    
    # Test 1: DEX Information
    print("1️⃣ SUPPORTED DEX INFORMATION:")
    dex_info = get_dex_info()
    
    for dex_name, info in dex_info.items():
        print(f"  • {info['name']} ({info['chain']})")
        print(f"    Fee: {info['fee_tier']}, Type: {info['type']}")
    
    print(f"\n📊 Total DEXs supported: {len(dex_info)}")
    
    # Test 2: Supported Tokens
    print("\n" + "-" * 60)
    print("2️⃣ SUPPORTED TOKENS BY CHAIN:")
    supported_tokens = get_supported_tokens()
    
    for chain, tokens in supported_tokens.items():
        print(f"  🔗 {chain.upper()}: {len(tokens)} tokens")
        print(f"    {', '.join(list(tokens.keys())[:8])}{'...' if len(tokens) > 8 else ''}")
    
    # Test 3: Token Availability Search
    print("\n" + "-" * 60)
    print("3️⃣ TOKEN AVAILABILITY TESTING:")
    
    test_tokens = ['BTC', 'ETH', 'USDC', 'LINK', 'MATIC', 'BNB', 'AVAX', 'FTM']
    
    for token in test_tokens:
        availability = find_token_availability(token)
        chains = [info['chain'] for info in availability] if availability else []
        print(f"  🪙 {token}: Available on {len(chains)} chains {chains}")
    
    # Test 4: Trade Execution Simulation
    print("\n" + "-" * 60)
    print("4️⃣ TRADE EXECUTION SIMULATION:")
    
    test_trades = [
        {'token': 'BTC', 'amount': 50.0, 'action': 'BUY'},
        {'token': 'ETH', 'amount': 25.0, 'action': 'BUY'},
        {'token': 'USDC', 'amount': 100.0, 'action': 'BUY'},
        {'token': 'MATIC', 'amount': 30.0, 'action': 'BUY'},
        {'token': 'LINK', 'amount': 20.0, 'action': 'BUY'},
        {'token': 'UNKNOWN_TOKEN', 'amount': 10.0, 'action': 'BUY'}  # Test error handling
    ]
    
    successful_trades = 0
    total_gas_fees = 0
    
    for trade in test_trades:
        print(f"\n  🔄 Testing: {trade['action']} ${trade['amount']:.0f} of {trade['token']}")
        
        result = execute_multi_dex_trade(
            action=trade['action'],
            token_symbol=trade['token'],
            amount_usd=trade['amount']
        )
        
        if result['success']:
            successful_trades += 1
            total_gas_fees += result.get('gas_fee_usd', 0)
            print(f"  ✅ Success: {result['dex_used']} on {result['chain_used']}")
            print(f"      Gas: ${result.get('gas_fee_usd', 0):.2f}, Slippage: {result.get('slippage_percent', 0):.1f}%")
            print(f"      Execution time: {result.get('execution_time', 0):.1f}s")
        else:
            print(f"  ❌ Failed: {result.get('error', 'Unknown error')}")
    
    print(f"\n📈 SIMULATION RESULTS:")
    print(f"  • Successful trades: {successful_trades}/{len(test_trades)}")
    print(f"  • Total estimated gas fees: ${total_gas_fees:.2f}")
    print(f"  • Average gas per trade: ${total_gas_fees/successful_trades:.2f}" if successful_trades > 0 else "")
    
    # Test 5: Web3 Connections
    print("\n" + "-" * 60)
    print("5️⃣ BLOCKCHAIN CONNECTIONS:")
    
    for chain_name, w3_instance in multi_dex_trader.web3_instances.items():
        try:
            block_number = w3_instance.eth.block_number
            print(f"  ✅ {chain_name.upper()}: Connected (Block #{block_number})")
        except Exception as e:
            print(f"  ❌ {chain_name.upper()}: Connection failed - {e}")
    
    # Test 6: Gas Fee Estimates
    print("\n" + "-" * 60)
    print("6️⃣ GAS FEE ESTIMATES (for $100 trades):")
    
    chains = ['ethereum', 'polygon', 'bsc', 'avalanche', 'fantom']
    for chain in chains:
        gas_fee = multi_dex_trader._estimate_gas_fee(chain, 100.0)
        percentage = (gas_fee / 100.0) * 100
        print(f"  ⛽ {chain.upper()}: ${gas_fee:.2f} ({percentage:.1f}% of trade)")
    
    print("\n🎯 MULTI-DEX INTEGRATION TEST COMPLETED!")
    print("=" * 60)
    
    # Summary
    total_supported_tokens = sum(len(tokens) for tokens in supported_tokens.values())
    connected_chains = len(multi_dex_trader.web3_instances)
    
    print(f"📊 SYSTEM SUMMARY:")
    print(f"  • {len(dex_info)} DEX protocols supported")
    print(f"  • {len(supported_tokens)} blockchain networks")
    print(f"  • {total_supported_tokens} total tokens available")
    print(f"  • {connected_chains}/{len(supported_tokens)} chains connected")
    print(f"  • {successful_trades}/{len(test_trades)} test trades successful")

def test_specific_gems():
    """Test trading some of the gems we discovered"""
    print("\n💎 TESTING GEM TRADING CAPABILITIES")
    print("=" * 60)
    
    # Test some smaller cap tokens that might be gems
    gem_tokens = ['DOGE', 'SHIB', 'PEPE', 'BONK']  # Popular meme coins often available
    
    for token in gem_tokens:
        print(f"\n🔍 Checking {token} availability:")
        availability = find_token_availability(token)
        
        if availability:
            print(f"  ✅ {token} found on {len(availability)} chains:")
            for info in availability:
                dex_names = ', '.join(info['dexs'])
                print(f"    • {info['chain'].upper()}: {dex_names}")
            
            # Simulate a small trade
            result = execute_multi_dex_trade('BUY', token, 10.0)
            if result['success']:
                print(f"  🚀 Trade simulation successful on {result['dex_used']}")
            else:
                print(f"  ⚠️  Trade would fail: {result.get('error')}")
        else:
            print(f"  ❌ {token} not available on supported DEXs")

if __name__ == "__main__":
    test_multi_dex_integration()
    test_specific_gems()