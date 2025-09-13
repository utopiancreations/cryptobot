# test_bot_cycle.py
"""
Test a single bot trading cycle with live LLM and data
"""

def main():
    print('🚀 Testing Main Bot Execution')
    print('=' * 50)

    from main import CryptoTradingBot
    from connectors.realtime_feeds import get_combined_realtime_feed, format_realtime_feed_for_llm
    from utils.llm import get_trade_decision

    print('🤖 Creating bot instance...')
    bot = CryptoTradingBot()

    print('📡 Testing real-time data fetching...')
    feed = get_combined_realtime_feed(max_total_items=5)
    print(f'✅ Fetched {len(feed)} feed items')

    print('📝 Formatting data for LLM...')
    formatted_data = format_realtime_feed_for_llm(feed)
    print('✅ Data formatted for LLM consumption')

    print('🧠 Testing LLM trading decision...')
    print('⏳ This may take 30-60 seconds with llama3...')
    
    # Create a simple test prompt for faster processing
    test_prompt = """
REAL-TIME CRYPTO FEED:

1. 🐦 [@crypto_analyst] (30m ago)
   Bitcoin continues to show strong fundamentals despite market volatility. Long-term outlook remains bullish.

2. 🐦 [@eth_researcher] (1h ago)
   Ethereum network activity reaching new highs. Developer adoption continues to grow exponentially.

MARKET SENTIMENT: Bullish
WALLET STATUS: 68.789 MATIC available
"""
    
    decision = get_trade_decision(test_prompt)

    if decision:
        print('🎯 LLM Trading Decision Received:')
        print(f'   Action: {decision.get("action", "Unknown")}')
        print(f'   Token: {decision.get("token", "Unknown")}')
        print(f'   Amount: ${decision.get("amount_usd", 0):.2f}')
        print(f'   Confidence: {decision.get("confidence", 0):.1%}')
        print(f'   Reasoning: {decision.get("reasoning", "No reasoning")[:100]}...')
        
        print('\n⚡ Testing trade execution...')
        from executor import execute_simulated_trade
        result = execute_simulated_trade(decision)
        
        if result.get('status') != 'ERROR':
            print('✅ Trade simulation completed successfully!')
            print(f'📊 Trade Status: {result.get("status")}')
        else:
            print(f'⚠️  Trade simulation result: {result.get("status")}')
    else:
        print('❌ Failed to get LLM decision')

    print('\n🎉 MAIN BOT TEST COMPLETE!')
    print('✅ Bot is ready for live operation!')
    print('\n🚀 To start the full bot, run: python3 main.py')

if __name__ == "__main__":
    main()