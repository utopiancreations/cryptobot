#!/usr/bin/env python3
"""
Debug the gem detection to see what coins are available and why they're not matching
"""

import requests
from datetime import datetime

def debug_gem_detection():
    """Debug what coins are available in the market data"""
    print("🔍 DEBUGGING GEM DETECTION")
    print("=" * 50)
    
    try:
        # Get market data like the real function does
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': 100,  # Get more coins to analyze
            'page': 1,
            'sparkline': False,
            'price_change_percentage': '24h,7d'
        }
        
        print("📡 Fetching market data...")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Got {len(data)} coins from CoinGecko")
        
        # Analyze the data to understand volume and price change distributions
        print("\n📊 ANALYZING COIN DATA:")
        
        gems_found = 0
        momentum_found = 0
        high_vol_found = 0
        
        print("\n🔬 Sample coins analysis (first 20):")
        for i, coin in enumerate(data[:20]):
            market_cap_rank = coin.get('market_cap_rank', 999999)
            volume_24h = coin.get('total_volume', 0)
            price_change_24h = coin.get('price_change_percentage_24h', 0)
            
            # Check our criteria
            high_volume_opportunity = (volume_24h > 100000 and abs(price_change_24h) > 10)
            
            low_volume_gem = (volume_24h >= 25000 and volume_24h <= 75000 and
                            abs(price_change_24h) > 20 and
                            market_cap_rank > 200)
            
            medium_volume_momentum = (volume_24h > 75000 and volume_24h <= 200000 and
                                    abs(price_change_24h) > 15)
            
            status = ""
            if low_volume_gem and market_cap_rank > 100:
                status = "💎 GEM!"
                gems_found += 1
            elif medium_volume_momentum and market_cap_rank > 100:
                status = "🚀 MOMENTUM!"
                momentum_found += 1
            elif high_volume_opportunity and market_cap_rank > 100:
                status = "🆕 HIGH VOL!"
                high_vol_found += 1
            
            print(f"{i+1:2d}. {coin['name']} ({coin['symbol']})")
            print(f"    Rank: #{market_cap_rank}, Vol: ${volume_24h:,.0f}, Change: {price_change_24h:+.1f}% {status}")
        
        print(f"\n📈 SUMMARY FROM FIRST 20 COINS:")
        print(f"💎 Low Volume Gems: {gems_found}")
        print(f"🚀 Momentum Plays: {momentum_found}")
        print(f"🆕 High Volume Opportunities: {high_vol_found}")
        
        # Now check all 100 coins for gems
        print(f"\n🔍 SCANNING ALL {len(data)} COINS FOR GEMS:")
        total_gems = 0
        total_momentum = 0
        total_high_vol = 0
        
        potential_gems = []
        
        for coin in data:
            market_cap_rank = coin.get('market_cap_rank', 999999)
            volume_24h = coin.get('total_volume', 0)
            price_change_24h = coin.get('price_change_percentage_24h', 0)
            
            # Check criteria
            high_volume_opportunity = (volume_24h > 100000 and abs(price_change_24h) > 10)
            
            low_volume_gem = (volume_24h >= 25000 and volume_24h <= 75000 and
                            abs(price_change_24h) > 20 and
                            market_cap_rank > 200)
            
            medium_volume_momentum = (volume_24h > 75000 and volume_24h <= 200000 and
                                    abs(price_change_24h) > 15)
            
            if market_cap_rank > 100:  # Outside top 100
                if low_volume_gem:
                    total_gems += 1
                    potential_gems.append((coin['name'], coin['symbol'], volume_24h, price_change_24h, market_cap_rank, 'GEM'))
                elif medium_volume_momentum:
                    total_momentum += 1
                    potential_gems.append((coin['name'], coin['symbol'], volume_24h, price_change_24h, market_cap_rank, 'MOMENTUM'))
                elif high_volume_opportunity:
                    total_high_vol += 1
                    potential_gems.append((coin['name'], coin['symbol'], volume_24h, price_change_24h, market_cap_rank, 'HIGH_VOL'))
        
        print(f"💎 Total Low Volume Gems Found: {total_gems}")
        print(f"🚀 Total Momentum Plays Found: {total_momentum}")
        print(f"🆕 Total High Volume Opportunities Found: {total_high_vol}")
        
        if potential_gems:
            print(f"\n🎯 TOP OPPORTUNITIES FOUND ({len(potential_gems)} total):")
            for name, symbol, volume, change, rank, type in potential_gems[:10]:
                emoji = "💎" if type == "GEM" else "🚀" if type == "MOMENTUM" else "🆕"
                print(f"  {emoji} {name} ({symbol}) - Rank #{rank}, Vol: ${volume:,.0f}, Change: {change:+.1f}%")
        else:
            print("\n❌ NO OPPORTUNITIES FOUND matching our criteria")
            
            # Show what volume ranges we actually have
            volumes = [coin.get('total_volume', 0) for coin in data if coin.get('market_cap_rank', 0) > 100]
            changes = [abs(coin.get('price_change_percentage_24h', 0)) for coin in data if coin.get('market_cap_rank', 0) > 100]
            
            if volumes and changes:
                print(f"\n📊 ACTUAL DATA RANGES (coins ranked >100):")
                print(f"Volume range: ${min(volumes):,.0f} - ${max(volumes):,.0f}")
                print(f"Avg volume: ${sum(volumes)/len(volumes):,.0f}")
                print(f"Price change range: {min(changes):.1f}% - {max(changes):.1f}%")
                print(f"Avg abs price change: {sum(changes)/len(changes):.1f}%")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_gem_detection()