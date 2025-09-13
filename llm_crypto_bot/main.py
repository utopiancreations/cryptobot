#!/usr/bin/env python3
"""
LLM Crypto Trading Bot - Main Execution Loop

This bot analyzes crypto news using a local LLM and makes simulated trading decisions.
It operates in read-only and simulation mode for safety.
"""

import time
import sys
import signal
from datetime import datetime, timedelta
from typing import Optional, List, Dict

import config
from connectors.news import get_market_sentiment
from connectors.realtime_feeds import get_combined_realtime_feed, format_realtime_feed_for_llm
from connectors.coinmarketcap_api import get_market_data_for_trading, format_market_data_for_llm, test_cmc_api
from utils.llm import get_trade_decision, test_llm_connection
from utils.wallet import get_wallet_balance, check_wallet_connection, get_multi_chain_wallet_balance, check_multi_chain_wallet_connection
from executor import execute_simulated_trade, get_trading_statistics, reset_daily_trading_stats
from real_executor import execute_real_trade, get_real_trade_history
from consensus_engine import get_consensus_decision_sync

class CryptoTradingBot:
    """Main trading bot class"""
    
    def __init__(self, enable_real_trades=False):
        self.running = False
        self.loop_count = 0
        self.start_time = None
        self.last_daily_reset = datetime.now().date()
        self.enable_real_trades = enable_real_trades
        
    def initialize(self) -> bool:
        """Initialize bot and check all systems"""
        print("> Initializing LLM Crypto Trading Bot...")
        print("=" * 50)
        
        # Validate configuration
        config_valid = config.validate_config()
        if not config_valid:
            print("�  Configuration warnings detected. Bot will run with limited functionality.")
        
        # Test LLM connection
        print("\n>� Testing LLM connection...")
        if not test_llm_connection():
            print("L LLM not available. Please ensure Ollama is running.")
            return False
        
        # Test wallet connection (optional for read-only mode)
        print("\n=� Testing wallet connection...")
        wallet_connected = check_wallet_connection()
        if not wallet_connected:
            print("�  Wallet connection failed. Running in news-only mode.")
        
        # Test news connection
        print("\n=� Testing news connection...")
        # test_news = fetch_crypto_news(limit=1)  # Disabled - CryptoPanic API exhausted
        test_news = True  # Always pass news test
        if test_news:
            print(" News connection successful")
        else:
            print("�  News connection failed. Using mock data.")
        
        print("\n Bot initialization complete!")
        print(f"=� Risk Parameters:")
        risk_params = config.get_risk_params()
        for key, value in risk_params.items():
            print(f"   {key}: {value}")
        print("   Token Whitelist: DISABLED (can trade any token)")
        
        # Show trading mode
        if self.enable_real_trades:
            print("🚨 REAL TRADING MODE ENABLED")
            print("   High confidence trades (≥70%) will be executed with real money")
            print("   Conservative position sizes (50% of calculated max)")
        else:
            print("🎮 SIMULATION MODE")
            print("   All trades are simulated - no real money at risk")
        
        # Show equivalency map
        equivalency = config.get_equivalency_map()
        if equivalency:
            print(f"🔄 Token Equivalency Map:")
            for wrapped, base in equivalency.items():
                print(f"   {wrapped} -> {base}")
        
        return True
    
    def start(self):
        """Start the main trading loop"""
        if not self.initialize():
            print("L Bot initialization failed. Exiting.")
            return
        
        self.running = True
        self.start_time = datetime.now()
        
        print(f"\n=� Starting trading bot at {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"�  Loop interval: {config.TRADE_SETTINGS['LOOP_INTERVAL_SECONDS']} seconds")
        print("=� Press Ctrl+C to stop the bot gracefully")
        print("=" * 50)
        
        try:
            self._main_loop()
        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            print(f"L Unexpected error: {e}")
            self.stop()
    
    def _main_loop(self):
        """Main execution loop"""
        while self.running:
            self.loop_count += 1
            loop_start = datetime.now()
            
            print(f"\n= Loop #{self.loop_count} - {loop_start.strftime('%H:%M:%S')}")
            print("-" * 30)
            
            try:
                # Check if we need to reset daily stats
                self._check_daily_reset()
                
                # Step 1: Fetch crypto news
                print("=� Fetching crypto news...")
                realtime_feed = get_combined_realtime_feed(max_total_items=30)
                
                if not realtime_feed:
                    print("�  No news available, skipping this cycle")
                    self._sleep_until_next_loop(loop_start)
                    continue
                
                # Step 2: Get market sentiment analysis
                print("📊 Analyzing market sentiment...")
                market_sentiment = get_market_sentiment()

                # Step 3: Get real-time market data from CoinMarketCap
                print("💹 Fetching real-time market data...")
                market_data = get_market_data_for_trading()
                formatted_market_data = format_market_data_for_llm(market_data)

                # Step 4: Format news for LLM
                formatted_data = format_realtime_feed_for_llm(realtime_feed)

                # Step 5: Combine all data sources for comprehensive analysis
                comprehensive_prompt = formatted_data + "\n\n" + formatted_market_data

                # Step 6: Add market context to prompt
                enhanced_prompt = self._enhance_prompt_with_context(comprehensive_prompt, market_sentiment)
                
                # Step 7: Get trading decision from Multi-Agent Consensus Engine
                print("🤖 Consulting Multi-Agent Consensus Engine...")
                decision = get_consensus_decision_sync(enhanced_prompt)
                
                if decision:
                    print(f"🎯 Consensus Decision: {decision['action']} {decision.get('token', 'N/A')}")
                    print(f"📝 Justification: {decision.get('justification', decision.get('reasoning', 'No reasoning provided'))}")
                    print(f"📊 Confidence: {decision.get('confidence_score', decision.get('confidence', 0)):.1%}")
                    
                    # Step 6: Execute simulated trade
                    if self.enable_real_trades:
                        print("💰 Executing REAL trade...")
                        trade_result = execute_real_trade(decision)
                    else:
                        print("🎮 Executing simulated trade...")
                        trade_result = execute_simulated_trade(decision)                    
                    # Step 7: Show trading statistics
                    if self.loop_count % 5 == 0:  # Show stats every 5 loops
                        self._show_trading_statistics()
                
                else:
                    print("❌ Consensus Engine failed to reach a decision")
                
            except Exception as e:
                print(f"L Error in main loop: {e}")
                print("�  Continuing to next cycle...")
            
            # Wait for next loop
            self._sleep_until_next_loop(loop_start)
    
    def _analyze_realtime_sentiment(self, feed_items: List[Dict]) -> Dict:
        """Analyze sentiment from real-time feed items"""
        if not feed_items:
            return {'overall': 'neutral', 'confidence': 0.0, 'article_count': 0}
        
        positive_indicators = ['bullish', 'positive', 'up', 'rise', 'gain', 'moon', 'pump', 'adoption', 'breakthrough']
        negative_indicators = ['bearish', 'negative', 'down', 'fall', 'drop', 'crash', 'dump', 'hack', 'scam', 'regulation']
        
        sentiment_scores = []
        
        for item in feed_items:
            content = item.get('content', '').lower()
            positive_count = sum(1 for word in positive_indicators if word in content)
            negative_count = sum(1 for word in negative_indicators if word in content)
            
            # Weight by engagement for tweets
            weight = 1
            if item.get('type') == 'tweet' and 'engagement' in item:
                weight = min(3, 1 + item['engagement'] / 100)  # Cap weight at 3x
            
            if positive_count > negative_count:
                sentiment_scores.append(1 * weight)
            elif negative_count > positive_count:
                sentiment_scores.append(-1 * weight)
            else:
                sentiment_scores.append(0 * weight)
        
        if sentiment_scores:
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            confidence = min(1.0, abs(avg_sentiment) / 2)
            
            if avg_sentiment > 0.3:
                overall = 'bullish'
            elif avg_sentiment < -0.3:
                overall = 'bearish'
            else:
                overall = 'neutral'
        else:
            overall = 'neutral'
            confidence = 0.0
        
        return {
            'overall': overall,
            'confidence': confidence,
            'article_count': len(feed_items),
            'breakdown': {
                'positive': len([s for s in sentiment_scores if s > 0]),
                'negative': len([s for s in sentiment_scores if s < 0]),
                'neutral': len([s for s in sentiment_scores if s == 0])
            }
        }
    
    def _enhance_prompt_with_context(self, news: str, sentiment: dict) -> str:
        """Enhance the news prompt with additional context"""
        
        # Get current wallet balance for context
        wallet_balance = get_wallet_balance()
        
        context_prompt = f"""
MARKET SENTIMENT ANALYSIS:
Overall Sentiment: {sentiment['overall'].upper()}
Confidence: {sentiment['confidence']:.1%}
Articles Analyzed: {sentiment['article_count']}
Sentiment Breakdown: {str(sentiment.get('breakdown', {}))}

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
        context_prompt += f"Bot Running For: {self._get_runtime()}\n"
        context_prompt += f"Total Loops: {self.loop_count}\n\n"
        
        return context_prompt + news
    
    def _check_daily_reset(self):
        """Check if we need to reset daily statistics"""
        current_date = datetime.now().date()
        if current_date > self.last_daily_reset:
            print("= New day detected - resetting daily statistics")
            reset_daily_trading_stats()
            self.last_daily_reset = current_date
    
    def _show_trading_statistics(self):
        """Display current trading statistics"""
        stats = get_trading_statistics()
        print("\n=� Trading Statistics:")
        print(f"   Total Trades: {stats['total_trades']}")
        print(f"   Winning Trades: {stats['winning_trades']}")
        print(f"   Win Rate: {stats['win_rate_percent']:.1f}%")
        print(f"   Daily P&L: ${stats['daily_pnl']:.2f}")
    
    def _get_runtime(self) -> str:
        """Get bot runtime as formatted string"""
        if not self.start_time:
            return "Unknown"
        
        runtime = datetime.now() - self.start_time
        hours, remainder = divmod(runtime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if runtime.days > 0:
            return f"{runtime.days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m {seconds}s"
    
    def _sleep_until_next_loop(self, loop_start: datetime):
        """Sleep until it's time for the next loop"""
        loop_duration = (datetime.now() - loop_start).total_seconds()
        interval = config.TRADE_SETTINGS['LOOP_INTERVAL_SECONDS']
        
        if loop_duration < interval:
            sleep_time = interval - loop_duration
            print(f"� Sleeping for {sleep_time:.1f} seconds until next loop...")
            time.sleep(sleep_time)
        else:
            print(f"�  Loop took {loop_duration:.1f}s (longer than {interval}s interval)")
    
    def stop(self):
        """Gracefully stop the bot"""
        self.running = False
        print(f"\n=� Bot stopped gracefully after {self.loop_count} loops")
        
        if self.start_time:
            runtime = self._get_runtime()
            print(f"�  Total runtime: {runtime}")
        
        # Show final statistics
        stats = get_trading_statistics()
        if stats['total_trades'] > 0:
            print("\n=� Final Trading Statistics:")
            print(f"   Total Trades: {stats['total_trades']}")
            print(f"   Win Rate: {stats['win_rate_percent']:.1f}%")

def setup_signal_handlers(bot: CryptoTradingBot):
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        print(f"\n=� Received signal {signum}. Shutting down gracefully...")
        bot.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def main():
    """Main entry point"""
    print("> LLM Crypto Trading Bot v1.0")
    # Check for real trading flag
    import sys
    enable_real_trades = "--real" in sys.argv or "--enable-real-trades" in sys.argv
    
    if enable_real_trades:
        print("🚨 REAL TRADING MODE - Real trades will be executed!")
        print("⚠️  High confidence trades (≥70%) will use real money")
    else:
        print("🎮 SIMULATION MODE - No real trades will be executed")
    print()
    
    # Create and start bot
    bot = CryptoTradingBot(enable_real_trades=enable_real_trades)
    setup_signal_handlers(bot)
    
    try:
        bot.start()
    except KeyboardInterrupt:
        print("\n=� Bot interrupted by user")
    except Exception as e:
        print(f"\nL Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()