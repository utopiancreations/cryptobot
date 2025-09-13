#!/usr/bin/env python3
"""
Test to see the detailed gem opportunities we're finding
"""

from connectors.new_coins import get_new_coin_opportunities

def test_gem_details():
    """Show detailed information about the gems we're finding"""
    print("💎 DETAILED GEM ANALYSIS")
    print("=" * 50)
    
    try:
        new_coins = get_new_coin_opportunities()
        print(f"✅ Found {len(new_coins)} total opportunities\n")
        
        # Categorize opportunities
        trending = [coin for coin in new_coins if coin.get('type') == 'trending']
        listings = [coin for coin in new_coins if coin.get('type') == 'new_listing']
        
        print(f"🔥 TRENDING COINS: {len(trending)}")
        for coin in trending:
            print(f"  • {coin['name']} ({coin['symbol']}) - Score: {coin.get('score', 0)}, Rank: #{coin.get('market_cap_rank', 'N/A')}")
        
        if listings:
            print(f"\n🆕 NEW LISTINGS: {len(listings)}")
            
            # Group by opportunity type
            gems = [coin for coin in listings if coin.get('opportunity_type') == 'low_volume_gem']
            momentum = [coin for coin in listings if coin.get('opportunity_type') == 'medium_volume_momentum']
            high_vol = [coin for coin in listings if coin.get('opportunity_type') == 'high_volume_opportunity']
            
            if gems:
                print(f"\n💎 LOW VOLUME GEMS ({len(gems)}):")
                for coin in gems:
                    print(f"  • {coin['name']} ({coin['symbol']})")
                    print(f"    Price: ${coin['current_price']:.6f}, Change: {coin['price_change_24h']:+.1f}%")
                    print(f"    Volume: ${coin['total_volume']:,.0f}, Rank: #{coin['market_cap_rank']}")
                    print(f"    Potential: {coin['potential_return']}, Risk: {coin['risk_level']}\n")
            
            if momentum:
                print(f"🚀 MOMENTUM PLAYS ({len(momentum)}):")
                for coin in momentum:
                    print(f"  • {coin['name']} ({coin['symbol']})")
                    print(f"    Price: ${coin['current_price']:.6f}, Change: {coin['price_change_24h']:+.1f}%")
                    print(f"    Volume: ${coin['total_volume']:,.0f}, Rank: #{coin['market_cap_rank']}")
                    print(f"    Potential: {coin['potential_return']}, Risk: {coin['risk_level']}\n")
            
            if high_vol:
                print(f"🆕 HIGH VOLUME OPPORTUNITIES ({len(high_vol)}):")
                for coin in high_vol:
                    print(f"  • {coin['name']} ({coin['symbol']})")
                    print(f"    Price: ${coin['current_price']:.6f}, Change: {coin['price_change_24h']:+.1f}%")
                    print(f"    Volume: ${coin['total_volume']:,.0f}, Rank: #{coin['market_cap_rank']}")
                    print(f"    Potential: {coin['potential_return']}, Risk: {coin['risk_level']}\n")
        else:
            print("\n❌ No new listing opportunities found")
        
        print("=" * 50)
        print(f"📊 SUMMARY: {len(trending)} trending + {len(listings)} listings = {len(new_coins)} total opportunities")
        
        if listings:
            gems_count = len([c for c in listings if c.get('opportunity_type') == 'low_volume_gem'])
            momentum_count = len([c for c in listings if c.get('opportunity_type') == 'medium_volume_momentum'])
            high_vol_count = len([c for c in listings if c.get('opportunity_type') == 'high_volume_opportunity'])
            
            print(f"💎 Low Volume Gems: {gems_count} (50x-100x potential)")
            print(f"🚀 Momentum Plays: {momentum_count} (10x-50x potential)")
            print(f"🆕 High Volume Opps: {high_vol_count} (2x-10x potential)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gem_details()