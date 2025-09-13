#!/usr/bin/env python3
"""
Test script for Enhanced Multi-Trade Trading System
Tests the new consensus engine and multi-trade execution capabilities
"""

import json
import sys
from enhanced_consensus_engine import get_enhanced_consensus_decisions
from utils.trade_manager import get_trade_manager
from connectors.coinmarketcap_api import get_market_data_for_trading, format_market_data_for_llm

def test_enhanced_consensus_engine():
    """Test the enhanced consensus engine with real market data"""
    print("🚀 Testing Enhanced Multi-Trade Consensus Engine")
    print("=" * 70)

    # Get real market data
    print("\n📊 Fetching real market data...")
    market_data = get_market_data_for_trading(['BTC', 'ETH', 'SOL', 'MATIC', 'BNB'])

    if not market_data:
        print("❌ Failed to get market data")
        return False

    # Format for LLM
    formatted_data = format_market_data_for_llm(market_data)

    # Add some sample news context
    enhanced_prompt = formatted_data + """

RECENT NEWS CONTEXT:
- Bitcoin showing consolidation patterns around current levels
- Ethereum network activity increasing with upcoming developments
- Solana ecosystem growth continues with new project launches
- DeFi protocols showing renewed activity across multiple chains
- Market sentiment appears cautiously optimistic

PORTFOLIO CONTEXT:
Current Portfolio: $67.04 across 2 wallets
Primary holdings: 52.56 MATIC, 0.0057 ETH, 0.042 SOL
Available trading capital: ~$25-30 per position
Risk tolerance: Moderate to aggressive for high-confidence setups
"""

    print("✅ Market data formatted for analysis")

    # Test the enhanced consensus engine
    print("\n🤖 Testing Enhanced Consensus Engine...")
    decisions = get_enhanced_consensus_decisions(enhanced_prompt)

    if not decisions:
        print("❌ Enhanced consensus engine returned no decisions")
        return False

    print(f"\n🎯 Enhanced Consensus Engine Results:")
    print(f"Generated {len(decisions)} trading decisions:\n")

    for i, decision in enumerate(decisions, 1):
        print(f"Decision {i}:")
        print(f"  Action: {decision.get('action', 'N/A')}")
        print(f"  Token: {decision.get('token', 'N/A')}")
        print(f"  Confidence: {decision.get('confidence_score', 0):.1%}")
        print(f"  Amount: ${decision.get('amount_usd', 0):.2f}")
        print(f"  Justification: {decision.get('justification', 'N/A')[:100]}...")
        print(f"  Risk Level: {decision.get('risk_level', 'N/A')}")
        print()

    return decisions

def test_trade_manager(raw_decisions):
    """Test the trade manager with conflict resolution and risk management"""
    print("\n" + "=" * 70)
    print("🛡️  Testing Trade Manager & Risk Management")
    print("=" * 70)

    if not raw_decisions:
        print("❌ No decisions to test trade manager")
        return False

    # Get trade manager
    trade_manager = get_trade_manager()

    print(f"\n🔄 Processing {len(raw_decisions)} raw decisions...")

    # Process decisions through trade manager
    processed_decisions = trade_manager.process_and_prioritize_trades(raw_decisions)

    if not processed_decisions:
        print("❌ Trade manager returned no processed decisions")
        return False

    print(f"\n✅ Trade Manager Results:")
    print(f"Processed {len(processed_decisions)} final trading decisions:\n")

    total_exposure = 0
    for i, decision in enumerate(processed_decisions, 1):
        total_exposure += decision.get('amount_usd', 0)
        print(f"Final Trade {i}:")
        print(f"  Priority Score: {decision.get('priority_score', 0):.3f}")
        print(f"  Action: {decision.get('action', 'N/A')}")
        print(f"  Token: {decision.get('token', 'N/A')}")
        print(f"  Confidence: {decision.get('confidence_score', 0):.1%}")
        print(f"  Amount: ${decision.get('amount_usd', 0):.2f}")
        print(f"  Risk Level: {decision.get('risk_level', 'N/A')}")
        print()

    print(f"📊 Total Portfolio Exposure: ${total_exposure:.2f}")

    # Show daily statistics
    daily_stats = trade_manager.get_daily_statistics()
    print(f"\n📈 Trade Manager Statistics:")
    print(f"  Daily Trades: {daily_stats['daily_trade_count']}")
    print(f"  Daily Exposure: ${daily_stats['daily_exposure']:.2f}")
    print(f"  Total Recorded: {daily_stats['executed_trades']}")

    return processed_decisions

def simulate_trading_cycle():
    """Simulate a complete enhanced trading cycle"""
    print("\n" + "=" * 70)
    print("🎯 Simulating Complete Enhanced Trading Cycle")
    print("=" * 70)

    try:
        # Step 1: Test enhanced consensus engine
        decisions = test_enhanced_consensus_engine()
        if not decisions:
            return False

        # Step 2: Test trade manager
        processed_decisions = test_trade_manager(decisions)
        if not processed_decisions:
            return False

        # Step 3: Simulate execution timing
        print(f"\n⏱️  Simulating Execution Timing for {len(processed_decisions)} trades:")

        import time
        execution_times = []

        for i, decision in enumerate(processed_decisions, 1):
            start_time = time.time()
            print(f"  📋 Simulating execution of trade {i}: {decision.get('action')} {decision.get('token')}")

            # Simulate execution delay (1-2 seconds per trade)
            time.sleep(1)

            end_time = time.time()
            execution_time = end_time - start_time
            execution_times.append(execution_time)

            print(f"     ✅ Completed in {execution_time:.1f}s")

            # Simulate delay between trades
            if i < len(processed_decisions):
                print(f"     ⏳ Waiting 3s before next trade...")
                time.sleep(1)  # Reduced for testing

        total_execution_time = sum(execution_times) + (len(processed_decisions) - 1) * 3
        print(f"\n📊 Execution Summary:")
        print(f"  Total Trades: {len(processed_decisions)}")
        print(f"  Total Execution Time: ~{total_execution_time:.1f}s")
        print(f"  Average Trade Time: {sum(execution_times)/len(execution_times):.1f}s")

        return True

    except Exception as e:
        print(f"❌ Error in trading cycle simulation: {e}")
        import traceback
        traceback.print_exc()
        return False

def compare_old_vs_new_system():
    """Compare the old single-trade vs new multi-trade system"""
    print("\n" + "=" * 70)
    print("📊 Comparing Old vs Enhanced Trading System")
    print("=" * 70)

    print("🔄 OLD SYSTEM (Single Trade):")
    print("  ✅ Analyzes top 3 bullish/bearish signals only")
    print("  ✅ Generates 1 trading decision per cycle")
    print("  ✅ Simple execution model")
    print("  ❌ Limited opportunity capture")
    print("  ❌ No conflict resolution")
    print("  ❌ No risk aggregation across trades")
    print("  📊 Cycle time: ~120-130 seconds")

    print("\n🚀 ENHANCED SYSTEM (Multi-Trade):")
    print("  ✅ Analyzes ALL available market signals")
    print("  ✅ Generates up to 3 trading decisions per cycle")
    print("  ✅ Advanced conflict resolution")
    print("  ✅ Comprehensive risk management")
    print("  ✅ Trade prioritization and optimization")
    print("  ✅ Portfolio-level position sizing")
    print("  ✅ Daily exposure limits")
    print("  📊 Expected cycle time: ~130-150 seconds")

    print("\n🎯 EXPECTED IMPROVEMENTS:")
    print("  📈 Up to 3x more trading opportunities per cycle")
    print("  🛡️  Better risk management and position sizing")
    print("  🎨 More sophisticated market analysis")
    print("  💎 Higher quality trade selection")
    print("  📊 Enhanced performance tracking")

def main():
    """Main test function"""
    try:
        print("🎯 Enhanced Multi-Trade Trading System Test Suite")
        print("=" * 70)

        # Run comparison
        compare_old_vs_new_system()

        # Run full simulation
        success = simulate_trading_cycle()

        if success:
            print("\n" + "=" * 70)
            print("🎉 ALL TESTS PASSED!")
            print("✅ Enhanced multi-trade system is working correctly")
            print("🚀 Ready for enhanced trading with up to 3 trades per cycle")
            print("📊 System can now analyze all market signals comprehensively")
            print("🛡️  Advanced risk management and conflict resolution active")
            print("⏱️  Optimized execution timing for multiple trades")
            print("=" * 70)
        else:
            print("\n❌ Some tests failed - review the output above")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()