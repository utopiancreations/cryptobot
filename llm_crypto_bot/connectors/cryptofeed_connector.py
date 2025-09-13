"""
Cryptofeed Connector for Real-Time Cryptocurrency Market Data

This module integrates the Cryptofeed library to provide real-time market data
including trades, tickers, and order book information from multiple exchanges.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from threading import Thread
import queue

# Cryptofeed imports
from cryptofeed import FeedHandler
from cryptofeed.exchanges import Coinbase, Binance, Kraken
from cryptofeed.defines import TICKER, TRADES, L2_BOOK
from cryptofeed.types import Ticker, Trade, OrderBook

class CryptofeedConnector:
    """Real-time cryptocurrency market data collector using Cryptofeed"""
    
    def __init__(self):
        self.feed_handler = None
        self.data_queue = queue.Queue(maxsize=1000)
        self.is_running = False
        self.last_data = {}
        self.thread = None
        
        # Track recent data for analysis
        self.recent_trades = []
        self.recent_tickers = {}
        self.recent_orderbooks = {}
        
    def start_feeds(self, symbols: List[str] = None, duration_seconds: int = 30):
        """
        Start collecting real-time market data
        
        Args:
            symbols: List of trading pairs to monitor (e.g. ['BTC-USD', 'ETH-USD'])
            duration_seconds: How long to collect data for
        """
        if symbols is None:
            symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'MATIC-USD']
            
        print(f"🔴 Starting Cryptofeed for {len(symbols)} symbols for {duration_seconds}s...")
        
        # Clear previous data
        self.recent_trades.clear()
        self.recent_tickers.clear()
        self.recent_orderbooks.clear()
        
        # Start data collection in a separate thread
        self.is_running = True
        self.thread = Thread(target=self._run_feed_handler, args=(symbols, duration_seconds))
        self.thread.start()
        
        # Wait for collection to complete
        self.thread.join()
        
        print(f"✅ Cryptofeed collection complete")
        
    def _run_feed_handler(self, symbols: List[str], duration_seconds: int):
        """Run the feed handler in a separate thread with asyncio"""
        asyncio.run(self._async_run_feeds(symbols, duration_seconds))
        
    async def _async_run_feeds(self, symbols: List[str], duration_seconds: int):
        """Async function to run feeds for specified duration"""
        
        # Create feed handler
        fh = FeedHandler()
        
        # Add Coinbase feed (most reliable for these symbols)
        try:
            fh.add_feed(
                Coinbase(
                    symbols=symbols,
                    channels=[TICKER, TRADES],
                    callbacks={
                        TICKER: self._ticker_callback,
                        TRADES: self._trade_callback
                    }
                )
            )
            print(f"📊 Added Coinbase feed for {', '.join(symbols)}")
        except Exception as e:
            print(f"⚠️  Error adding Coinbase feed: {e}")
            
        # Start the feed handler
        try:
            # Run for specified duration
            task = asyncio.create_task(fh.run())
            await asyncio.sleep(duration_seconds)
            
            # Stop the feed handler
            fh.stop()
            print("🔴 Stopping Cryptofeed collection...")
            
        except Exception as e:
            print(f"❌ Error running Cryptofeed: {e}")
        finally:
            self.is_running = False
            
    async def _ticker_callback(self, ticker: Ticker, receipt_timestamp: float):
        """Callback for ticker data"""
        try:
            ticker_data = {
                'symbol': ticker.symbol,
                'exchange': ticker.exchange,
                'bid': float(ticker.bid) if ticker.bid else None,
                'ask': float(ticker.ask) if ticker.ask else None,
                'timestamp': datetime.fromtimestamp(ticker.timestamp),
                'type': 'ticker'
            }
            
            # Store recent ticker
            self.recent_tickers[ticker.symbol] = ticker_data
            
        except Exception as e:
            print(f"⚠️  Error processing ticker: {e}")
            
    async def _trade_callback(self, trade: Trade, receipt_timestamp: float):
        """Callback for trade data"""
        try:
            trade_data = {
                'symbol': trade.symbol,
                'exchange': trade.exchange,
                'side': trade.side,
                'amount': float(trade.amount),
                'price': float(trade.price),
                'timestamp': datetime.fromtimestamp(trade.timestamp),
                'type': 'trade'
            }
            
            # Store recent trades (keep last 50 per symbol)
            self.recent_trades.append(trade_data)
            if len(self.recent_trades) > 200:  # Keep last 200 trades total
                self.recent_trades = self.recent_trades[-200:]
                
        except Exception as e:
            print(f"⚠️  Error processing trade: {e}")
            
    def get_market_summary(self) -> Dict[str, Any]:
        """
        Get a summary of recent market activity
        
        Returns:
            Dictionary with market analysis
        """
        if not self.recent_trades and not self.recent_tickers:
            return {'error': 'No recent market data available'}
            
        summary = {
            'timestamp': datetime.now().isoformat(),
            'data_sources': 'Cryptofeed Real-Time',
            'symbols_tracked': list(self.recent_tickers.keys()),
            'total_trades': len(self.recent_trades),
            'tickers': {},
            'trade_analysis': {},
            'market_activity': {}
        }
        
        # Process ticker data
        for symbol, ticker in self.recent_tickers.items():
            if ticker['bid'] and ticker['ask']:
                spread = ticker['ask'] - ticker['bid']
                spread_pct = (spread / ticker['bid']) * 100 if ticker['bid'] > 0 else 0
                
                summary['tickers'][symbol] = {
                    'bid': ticker['bid'],
                    'ask': ticker['ask'],
                    'spread': spread,
                    'spread_percent': spread_pct,
                    'last_update': ticker['timestamp'].isoformat()
                }
        
        # Process trade data by symbol
        symbol_trades = {}
        for trade in self.recent_trades:
            symbol = trade['symbol']
            if symbol not in symbol_trades:
                symbol_trades[symbol] = []
            symbol_trades[symbol].append(trade)
            
        for symbol, trades in symbol_trades.items():
            if not trades:
                continue
                
            # Calculate trade statistics
            prices = [t['price'] for t in trades]
            volumes = [t['amount'] for t in trades]
            buy_trades = [t for t in trades if t['side'] == 'buy']
            sell_trades = [t for t in trades if t['side'] == 'sell']
            
            summary['trade_analysis'][symbol] = {
                'trade_count': len(trades),
                'avg_price': sum(prices) / len(prices),
                'min_price': min(prices),
                'max_price': max(prices),
                'total_volume': sum(volumes),
                'buy_trades': len(buy_trades),
                'sell_trades': len(sell_trades),
                'buy_sell_ratio': len(buy_trades) / len(sell_trades) if sell_trades else float('inf'),
                'price_trend': 'up' if trades[-1]['price'] > trades[0]['price'] else 'down' if trades[-1]['price'] < trades[0]['price'] else 'flat'
            }
        
        # Overall market activity assessment
        total_trades = len(self.recent_trades)
        if total_trades > 50:
            activity_level = 'high'
        elif total_trades > 20:
            activity_level = 'medium'
        else:
            activity_level = 'low'
            
        summary['market_activity'] = {
            'level': activity_level,
            'total_trades': total_trades,
            'symbols_active': len(symbol_trades),
            'collection_duration': '30 seconds'
        }
        
        return summary
        
def get_cryptofeed_data(symbols: List[str] = None, duration: int = 30) -> Dict[str, Any]:
    """
    Convenience function to collect real-time market data
    
    Args:
        symbols: List of symbols to track
        duration: Collection duration in seconds
        
    Returns:
        Market summary dictionary
    """
    connector = CryptofeedConnector()
    connector.start_feeds(symbols=symbols, duration_seconds=duration)
    return connector.get_market_summary()

def format_cryptofeed_for_llm(market_data: Dict[str, Any]) -> str:
    """
    Format Cryptofeed market data for LLM consumption
    
    Args:
        market_data: Market data from get_cryptofeed_data
        
    Returns:
        Formatted string for LLM analysis
    """
    if 'error' in market_data:
        return f"Cryptofeed Error: {market_data['error']}"
        
    formatted = "REAL-TIME MARKET DATA (Cryptofeed):\n\n"
    
    # Market activity overview
    activity = market_data.get('market_activity', {})
    formatted += f"📊 Market Activity: {activity.get('level', 'unknown').upper()}\n"
    formatted += f"📈 Total Trades: {activity.get('total_trades', 0)} in {activity.get('collection_duration', 'unknown')}\n"
    formatted += f"🪙 Symbols Tracked: {len(market_data.get('symbols_tracked', []))}\n\n"
    
    # Current prices and spreads
    tickers = market_data.get('tickers', {})
    if tickers:
        formatted += "💰 CURRENT PRICES:\n"
        for symbol, ticker in tickers.items():
            formatted += f"   {symbol}: Bid ${ticker['bid']:.2f} | Ask ${ticker['ask']:.2f} | Spread {ticker['spread_percent']:.3f}%\n"
        formatted += "\n"
    
    # Trade analysis
    trade_analysis = market_data.get('trade_analysis', {})
    if trade_analysis:
        formatted += "📈 TRADE ANALYSIS:\n"
        for symbol, analysis in trade_analysis.items():
            formatted += f"   {symbol}:\n"
            formatted += f"     Price: ${analysis['avg_price']:.2f} (Range: ${analysis['min_price']:.2f}-${analysis['max_price']:.2f})\n"
            formatted += f"     Volume: {analysis['total_volume']:.2f} | Trades: {analysis['trade_count']}\n"
            formatted += f"     Buy/Sell Ratio: {analysis['buy_sell_ratio']:.2f} | Trend: {analysis['price_trend']}\n"
        formatted += "\n"
    
    formatted += f"Data collected at: {market_data.get('timestamp', 'unknown')}\n"
    
    return formatted