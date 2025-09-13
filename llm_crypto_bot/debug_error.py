#!/usr/bin/env python3
"""
Debug the sequence error in main loop
"""

from connectors.realtime_feeds import get_combined_realtime_feed, format_realtime_feed_for_llm
from connectors.news import get_market_sentiment
from utils.wallet import get_wallet_balance
from datetime import datetime

def debug_main_loop():
    """Debug the exact main loop sequence"""
    print("🔍 DEBUGGING MAIN LOOP ERROR")
    print("=" * 50)
    
    try:
        # Step 1: Fetch crypto news
        print("📰 Step 1: Fetching crypto news...")
        realtime_feed = get_combined_realtime_feed(max_total_items=30)
        
        if not realtime_feed:
            print("❌ No news available")
            return
        
        print(f"✅ Fetched {len(realtime_feed)} items")
        
        # Step 2: Get market sentiment analysis
        print("📊 Step 2: Analyzing market sentiment...")
        market_sentiment = get_market_sentiment()
        print(f"✅ Market sentiment: {market_sentiment}")
        
        # Step 3: Format news for LLM
        print("📝 Step 3: Formatting data for LLM...")
        formatted_data = format_realtime_feed_for_llm(realtime_feed)
        print(f"✅ Formatted data type: {type(formatted_data)}")
        print(f"✅ Formatted data length: {len(formatted_data)}")
        
        # Step 4: Add market context to prompt
        print("🔧 Step 4: Enhancing prompt with context...")
        
        # Get current wallet balance for context
        wallet_balance = get_wallet_balance()
        
        context_prompt = f"""
MARKET SENTIMENT ANALYSIS:
Overall Sentiment: {market_sentiment['overall'].upper()}
Confidence: {market_sentiment['confidence']:.1%}
Articles Analyzed: {market_sentiment['article_count']}
Sentiment Breakdown: {str(market_sentiment.get('breakdown', {}))}

WALLET STATUS:
"""
        
        if wallet_balance:
            if wallet_balance.get('wallet_address') != 'mock_address':
                context_prompt += f"Connected Wallet: {wallet_balance['wallet_address']}\n"
                context_prompt += f"Native Balance: {wallet_balance['native_token']['balance']:.4f} {wallet_balance['native_token']['symbol']}\n"
                context_prompt += f"Estimated Total Value: ${wallet_balance['total_usd_estimate']:.2f}\n"
            else:
                context_prompt += "Running in SIMULATION MODE (no real wallet connected)\n"
        else:
            context_prompt += "Wallet not available\n"
        
        context_prompt += f"\nTIME CONTEXT:\nCurrent Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        context_prompt += f"Bot Running For: test\n"
        context_prompt += f"Total Loops: 1\n\n"
        
        # This is where the error might occur
        print("🔗 Step 5: Concatenating context and data...")
        enhanced_prompt = context_prompt + formatted_data
        
        print("✅ ALL STEPS COMPLETED SUCCESSFULLY!")
        print(f"Final prompt length: {len(enhanced_prompt)}")
        
    except Exception as e:
        print(f"❌ ERROR CAUGHT: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_main_loop()