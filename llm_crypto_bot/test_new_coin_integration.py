#!/usr/bin/env python3
"""
Test the new coin integration into the realtime feed
"""

from connectors.realtime_feeds import get_combined_realtime_feed, format_realtime_feed_for_llm
from connectors.new_coins import get_new_coin_opportunities, format_new_coins_for_llm

def test_new_coin_integration():
    """Test the new coin integration"""
    print("🧪 TESTING NEW COIN INTEGRATION")
    print("=" * 50)
    
    try:
        # Test new coin monitoring directly
        print("1️⃣ Testing new coin monitoring directly...")
        new_coins = get_new_coin_opportunities()
        print(f"✅ Found {len(new_coins)} new coin opportunities")
        
        if new_coins:
            print("📝 New coin formatted output:")
            formatted_new_coins = format_new_coins_for_llm(new_coins)
            print(formatted_new_coins[:500] + "..." if len(formatted_new_coins) > 500 else formatted_new_coins)
        
        print("\n" + "-" * 50)
        
        # Test combined realtime feed with new coins
        print("2️⃣ Testing combined realtime feed with new coins...")
        combined_feed = get_combined_realtime_feed(max_total_items=10)  # Small test
        print(f"✅ Combined feed has {len(combined_feed)} items")
        
        # Check if new coins are included
        new_coin_items = [item for item in combined_feed if item.get('type') == 'new_coin']
        print(f"🆕 Found {len(new_coin_items)} new coin items in feed")
        
        # Show feed breakdown by type
        feed_types = {}
        for item in combined_feed:
            item_type = item.get('type', 'unknown')
            feed_types[item_type] = feed_types.get(item_type, 0) + 1
        print(f"📊 Feed breakdown: {feed_types}")
        
        print("\n" + "-" * 50)
        
        # Test LLM formatting with new coins
        print("3️⃣ Testing LLM formatting with new coins...")
        formatted_feed = format_realtime_feed_for_llm(combined_feed)
        print(f"✅ Formatted feed length: {len(formatted_feed)} characters")
        
        # Look for new coin indicators in formatted output
        new_coin_indicators = ['[TRENDING COIN]', '[NEW OPPORTUNITY]', '[NEW COIN DETECTED]']
        found_indicators = [indicator for indicator in new_coin_indicators if indicator in formatted_feed]
        
        if found_indicators:
            print(f"🎯 New coin formatting detected: {', '.join(found_indicators)}")
            
            # Show a snippet with new coin data
            for indicator in found_indicators:
                start_idx = formatted_feed.find(indicator)
                if start_idx != -1:
                    snippet = formatted_feed[start_idx:start_idx+200]
                    print(f"📋 Sample {indicator}:")
                    print(snippet + "...")
                    break
        else:
            print("⚠️  No new coin formatting detected in output")
        
        print("\n✅ NEW COIN INTEGRATION TEST COMPLETED!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_new_coin_integration()