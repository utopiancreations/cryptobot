#!/usr/bin/env python3
"""
Test script for real trade functionality
"""

from consensus_engine import get_consensus_decision_sync
from real_executor import execute_real_trade

def main():
    # Simple test data with strong bullish signals
    test_data = """
MARKET DATA:
- BTC showing strong bullish momentum with 15% daily gain
- High volume indicating institutional buying
- Breaking through key resistance at $45,000
- Multiple technical indicators showing bullish divergence
- On-chain metrics showing accumulation phase
- Positive sentiment across social media and news
"""

    print("🧪 Testing complete real trade flow...")
    print("=" * 50)
    
    # Get consensus decision
    decision = get_consensus_decision_sync(test_data)
    
    if not decision:
        print("❌ No decision from consensus engine")
        return
    
    print(f"📋 Decision: {decision.get('action')} {decision.get('token')}")
    print(f"💰 Amount: ${decision.get('amount_usd', 0):.2f}")
    print(f"📊 Confidence: {decision.get('confidence', 0):.1%}")
    print(f"💭 Reasoning: {decision.get('reasoning', 'No reasoning')}")
    
    # Check if suitable for real trading
    confidence = decision.get('confidence', 0)
    if confidence >= 0.7 and decision.get('action') in ['BUY', 'SELL']:
        print(f"\n✅ High confidence trade ({confidence:.1%}) - executing real trade...")
        result = execute_real_trade(decision)
        
        if result.get('status') == 'VALIDATED_REAL':
            print("🎉 Real trade would be successfully executed!")
        else:
            print(f"❌ Real trade failed: {result.get('error', 'Unknown error')}")
    else:
        print(f"\n⏸️  Low confidence ({confidence:.1%}) - trade not suitable for real execution")
        print("Real trades require ≥70% confidence")

if __name__ == "__main__":
    main()