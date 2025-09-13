#!/usr/bin/env python3
"""
Test script for the multi-agent consensus engine
"""

import sys
from consensus_engine import get_consensus_decision_sync
from connectors.realtime_feeds import get_combined_realtime_feed, format_realtime_feed_for_llm

def main():
    print("🤖 Testing Multi-Agent Consensus Engine")
    print("=" * 60)
    
    print("📡 Fetching real-time market data...")
    
    # Get real market data
    feed = get_combined_realtime_feed(max_total_items=10)
    if not feed:
        print("❌ Failed to fetch market data")
        return
    
    print(f"✅ Fetched {len(feed)} market data items")
    
    # Format data for LLM
    formatted_data = format_realtime_feed_for_llm(feed)
    print("✅ Data formatted for multi-agent analysis")
    
    print("\n🤖 Starting Multi-Agent Consensus Process...")
    print("⏳ This may take several minutes as agents debate...")
    print("-" * 60)
    
    # Get consensus decision
    decision = get_consensus_decision_sync(formatted_data)
    
    if decision:
        print("\n" + "=" * 60)
        print("🎯 MULTI-AGENT CONSENSUS REACHED!")
        print("=" * 60)
        print(f"📊 Final Decision: {decision['action']}")
        print(f"🪙 Token: {decision.get('token', 'N/A')}")
        print(f"💰 Amount: ${decision.get('amount_usd', 0):.2f}")
        print(f"📈 Confidence: {decision.get('confidence_score', decision.get('confidence', 0)):.1%}")
        print(f"💭 Justification: {decision.get('justification', decision.get('reasoning', 'No reasoning'))}")
        
        print("\n🎉 Consensus Engine Test SUCCESSFUL!")
        
    else:
        print("\n❌ Consensus Engine failed to reach a decision")
        print("Check the logs above for detailed error information")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)