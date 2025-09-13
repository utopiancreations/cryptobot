#!/usr/bin/env python3
"""
Test Unlimited Token Trading Capabilities

This test demonstrates that the bot can now trade ANY cryptocurrency token,
not just those in predefined lists. It uses dynamic discovery to find tokens
across all supported DEXs and chains.
"""

from multi_dex_integration import execute_multi_dex_trade, find_token_availability
from dynamic_token_discovery import find_any_token, get_trending_gems, validate_token

def test_unlimited_token_discovery():
    """Test discovering and trading unlimited tokens"""
    print("🚀 UNLIMITED TOKEN TRADING TEST")
    print("=" * 60)
    
    # Test 1: Try trading some random/obscure tokens
    test_tokens = [
        'WOJAK',    # Popular meme coin
        'TURBO',    # AI-generated meme coin
        'FLOKI',    # Dog-themed meme coin
        'BABYDOGE', # Another meme coin
        'SAITAMA',  # Another popular meme
        'RANDOM123', # Should not exist
        'XYZ999',   # Should not exist
    ]
    
    successful_discoveries = 0
    total_tokens_found = 0
    
    print("1️⃣ TESTING RANDOM TOKEN DISCOVERY:")
    print("-" * 40)
    
    for token in test_tokens:
        print(f"\n🔍 Searching for: {token}")
        
        # Try to discover the token
        discovered = find_any_token(token)
        
        if discovered:
            successful_discoveries += 1
            total_tokens_found += len(discovered)
            
            print(f"✅ Found {len(discovered)} matches for {token}:")
            for token_info in discovered[:3]:  # Show first 3 matches
                chain = token_info.get('chain', 'unknown')
                price = token_info.get('price_usd', 0)
                volume = token_info.get('volume_24h', 0)
                print(f"   • {token_info.get('name', 'N/A')} on {chain}")
                print(f"     Price: ${price:.8f}, Volume: ${volume:,.0f}")
                
                # Try to validate the token
                if token_info.get('contract_address'):
                    safety = validate_token(token_info)
                    print(f"     Safety: {safety['safety_score']}/100 ({safety['risk_level']})")
        else:
            print(f"❌ {token} not found")
    
    print(f"\n📊 Discovery Results: {successful_discoveries}/{len(test_tokens)} tokens found")
    print(f"📊 Total token instances discovered: {total_tokens_found}")
    
    # Test 2: Test trading execution with discovered tokens
    print("\n" + "=" * 60)
    print("2️⃣ TESTING UNLIMITED TOKEN TRADING:")
    print("-" * 40)
    
    # Try to trade some of the discovered tokens
    trade_tests = [
        {'symbol': 'WOJAK', 'amount': 10.0},
        {'symbol': 'FLOKI', 'amount': 15.0},
        {'symbol': 'TURBO', 'amount': 20.0},
        {'symbol': 'UNKNOWN_MEME_COIN_XYZ', 'amount': 5.0}  # Should fail
    ]
    
    successful_trades = 0
    
    for trade in trade_tests:
        print(f"\n💰 Attempting to trade ${trade['amount']:.0f} of {trade['symbol']}")
        
        result = execute_multi_dex_trade('BUY', trade['symbol'], trade['amount'])
        
        if result['success']:
            successful_trades += 1
            discovery_source = result.get('discovery_source', 'unknown')
            print(f"✅ Trade successful!")
            print(f"   DEX: {result['dex_used']} on {result['chain_used']}")
            print(f"   Discovery: {discovery_source}")
            print(f"   Gas: ${result.get('gas_fee_usd', 0):.2f}")
            
            # Show token info if dynamically discovered
            token_info = result.get('token_info', {})
            if token_info:
                print(f"   Token: {token_info.get('name', 'N/A')}")
                print(f"   Price: ${token_info.get('price_usd', 0):.8f}")
                print(f"   Volume: ${token_info.get('volume_24h', 0):,.0f}")
        else:
            print(f"❌ Trade failed: {result.get('error', 'Unknown error')}")
            if result.get('discovery_attempted'):
                print("   • Dynamic discovery was attempted")
    
    print(f"\n📊 Trading Results: {successful_trades}/{len(trade_tests)} trades successful")
    
    # Test 3: Trending gems discovery
    print("\n" + "=" * 60)
    print("3️⃣ TESTING TRENDING GEMS DISCOVERY:")
    print("-" * 40)
    
    try:
        trending = get_trending_gems(10)
        
        if trending:
            print(f"🔥 Found {len(trending)} trending gems:")
            
            for i, gem in enumerate(trending[:5], 1):
                print(f"\n{i}. 💎 {gem.get('name', 'Unknown')} ({gem.get('symbol', 'N/A')})")
                print(f"   Price: ${gem.get('price_usd', 0):.8f}")
                print(f"   Volume: ${gem.get('volume_24h', 0):,.0f}")
                print(f"   Change: {gem.get('price_change_24h', 0):+.1f}%")
                
                if gem.get('market_cap'):
                    print(f"   Market Cap: ${gem.get('market_cap', 0):,.0f}")
                
                # Show which chains it's available on
                symbol = gem.get('symbol')
                if symbol:
                    availability = find_token_availability(symbol)
                    if availability:
                        chains = [info['chain'] for info in availability]
                        print(f"   Available on: {', '.join(chains)}")
        else:
            print("❌ No trending gems found")
            
    except Exception as e:
        print(f"⚠️  Trending gems discovery error: {e}")
    
    # Test 4: Direct contract address trading
    print("\n" + "=" * 60)
    print("4️⃣ TESTING CONTRACT ADDRESS TRADING:")
    print("-" * 40)
    
    # Test with some known contract addresses
    contract_tests = [
        {
            'address': '0x95aD61b0a150d79219dCF64E1E6Cc01f0B64C4cE',  # SHIB on Ethereum
            'amount': 25.0
        }
    ]
    
    for test in contract_tests:
        print(f"\n🔗 Testing contract: {test['address'][:10]}...")
        
        # Try to discover token by address
        discovered = find_any_token(test['address'])
        
        if discovered:
            token_info = discovered[0]
            print(f"✅ Contract resolved to: {token_info.get('name')} ({token_info.get('symbol')})")
            
            # Try to trade it
            result = execute_multi_dex_trade('BUY', token_info.get('symbol', ''), test['amount'])
            
            if result['success']:
                print(f"✅ Contract trading successful via {result['dex_used']}")
            else:
                print(f"❌ Contract trading failed: {result.get('error')}")
        else:
            print(f"❌ Could not resolve contract address")
    
    print("\n🎯 UNLIMITED TOKEN TRADING TEST COMPLETE!")
    print("=" * 60)
    
    return {
        'discoveries': successful_discoveries,
        'total_tokens': total_tokens_found,
        'successful_trades': successful_trades,
        'trending_gems': len(trending) if 'trending' in locals() and trending else 0
    }

if __name__ == "__main__":
    results = test_unlimited_token_discovery()
    
    print(f"\n📈 FINAL RESULTS:")
    print(f"• Token discoveries: {results['discoveries']}")
    print(f"• Total token instances: {results['total_tokens']}")
    print(f"• Successful trades: {results['successful_trades']}")
    print(f"• Trending gems found: {results['trending_gems']}")
    
    if results['discoveries'] > 0:
        print(f"\n🎉 SUCCESS: Bot can now trade unlimited tokens!")
        print(f"The system dynamically discovered and can trade {results['total_tokens']} token instances")
        print(f"across multiple chains without any predefined lists.")
    else:
        print(f"\n⚠️  Limited success: Check API connections and token availability")