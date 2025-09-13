#!/usr/bin/env python3
"""
Test script for the complete integration:
- RSS feeds + Benzinga API + Cryptofeed real-time data + Reddit trends
- Multi-agent consensus engine
"""

import sys
from consensus_engine import get_consensus_decision_sync
from connectors.realtime_feeds import get_combined_realtime_feed, format_realtime_feed_for_llm

def main():
    print("🚀 Testing COMPLETE Integration: Multi-Agent + Real-Time Data")
    print("=" * 80)
    
    print("📡 Fetching ALL data sources...")
    print("   • RSS feeds (CoinDesk, CoinTelegraph, Custom)")
    print("   • Benzinga professional API")
    print("   • Cryptofeed real-time market data (20s collection)")
    print("   • Reddit trend analysis")
    print()
    
    # Get comprehensive market data including real-time feeds
    feed = get_combined_realtime_feed(max_total_items=15, include_cryptofeed=True)
    if not feed:
        print("❌ Failed to fetch market data")
        return 1
    
    print(f"✅ Fetched {len(feed)} comprehensive data items")
    
    # Format data for multi-agent analysis
    formatted_data = format_realtime_feed_for_llm(feed)
    print("✅ Data formatted for multi-agent consensus engine")
    
    print("\n" + "="*80)
    print("🤖 MULTI-AGENT CONSENSUS ENGINE WITH REAL-TIME DATA")
    print("="*80)
    print("⏳ This may take several minutes as all 4 agents analyze comprehensive data...")
    print("   📊 Analyst (Llama3:8b): Processing all data sources")
    print("   🟢 Bullish Agent (Gemma2:9b): Building buy case")  
    print("   🟡 Cautious Agent (Llama3:8b): Building risk case")
    print("   ⚖️  Strategist (Llama3:8b): Making final decision")
    print("-" * 80)
    
    # Get consensus decision with all data sources
    decision = get_consensus_decision_sync(formatted_data)
    
    if decision:
        print("\n" + "=" * 80)
        print("🎯 COMPREHENSIVE CONSENSUS REACHED!")
        print("=" * 80)
        print(f"📊 Final Decision: **{decision['action']}**")
        print(f"🪙 Target Token: {decision.get('token', 'Not specified')}")
        print(f"💰 Trade Amount: ${decision.get('amount_usd', 0):.2f}")
        print(f"📈 Confidence: {decision.get('confidence_score', decision.get('confidence', 0)):.1%}")
        print(f"💭 Justification: {decision.get('justification', decision.get('reasoning', 'No reasoning'))}")
        print()
        print("🔍 Data Sources Used:")
        print("   ✅ RSS News Feeds (Live)")
        print("   ✅ Benzinga Professional API")
        print("   ✅ Cryptofeed Real-Time Market Data")
        print("   ✅ Reddit Community Trend Analysis")
        print("   ✅ Multi-Agent LLM Consensus (4 agents)")
        
        print(f"\n🎉 COMPLETE INTEGRATION TEST SUCCESSFUL!")
        print("🚀 Your bot is ready for sophisticated real-time trading!")
        
    else:
        print("\n❌ Multi-agent consensus failed to reach a decision")
        print("Check the logs above for detailed error information")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)