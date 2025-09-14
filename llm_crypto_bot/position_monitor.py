"""
Position Monitor - Track and Manage Wallet Positions
Continuously monitors wallet positions and generates sell signals for profit/loss management
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from web3 import Web3
import config
from utils.wallet import get_wallet_balance, get_token_balance
from connectors.coinmarketcap_api import get_market_data_for_trading
from profit_maximizer import get_profit_maximizer

class PositionMonitor:
    """Monitor wallet positions and generate intelligent sell signals"""

    def __init__(self):
        self.positions = {}  # Current positions
        self.position_history = []  # Historical position data
        self.price_cache = {}  # Cache for price lookups
        self.last_update = None
        self.monitoring_enabled = True

        # Load existing positions
        self._load_positions()

    def update_positions(self, force_refresh: bool = False) -> Dict:
        """Update current positions by scanning wallet"""

        if not force_refresh and self.last_update:
            # Don't update too frequently
            time_since_update = datetime.now() - self.last_update
            if time_since_update.seconds < 30:  # Update every 30 seconds max
                return self.positions

        try:
            print("🔍 SCANNING WALLET POSITIONS...")

            # Get current wallet balance with all tokens
            wallet_data = get_wallet_balance()
            if not wallet_data:
                print("❌ Could not retrieve wallet data")
                return self.positions

            current_positions = {}

            # Process native token (BNB, ETH, etc.)
            native_token = wallet_data.get('native_token', {})
            if native_token.get('balance', 0) > 0.01:  # Ignore dust
                symbol = native_token.get('symbol', 'UNKNOWN')
                current_positions[symbol] = {
                    'token_symbol': symbol,
                    'balance': native_token['balance'],
                    'contract_address': 'NATIVE',
                    'type': 'native',
                    'last_seen': datetime.now().isoformat()
                }

            # Process ERC-20 tokens
            tokens = wallet_data.get('tokens', {})
            for token_symbol, token_data in tokens.items():
                balance = token_data.get('balance', 0)
                if balance and balance > 0:  # Any positive balance
                    current_positions[token_symbol] = {
                        'token_symbol': token_symbol,
                        'balance': balance,
                        'contract_address': token_data.get('contract_address', 'UNKNOWN'),
                        'type': 'erc20',
                        'last_seen': datetime.now().isoformat()
                    }

            # Update positions with price and profit/loss data
            for symbol, position in current_positions.items():
                # Get existing position data if any
                existing_position = self.positions.get(symbol, {})

                # Preserve historical data
                position['first_seen'] = existing_position.get('first_seen', position['last_seen'])
                position['entry_price'] = existing_position.get('entry_price', 0)
                position['entry_amount_usd'] = existing_position.get('entry_amount_usd', 0)

                # Get current market price
                current_price = self._get_token_price(symbol)
                position['current_price'] = current_price or 0

                # Calculate current USD value (handle None values)
                balance = position.get('balance', 0) or 0
                price = position.get('current_price', 0) or 0
                position['current_value_usd'] = balance * price

                # Calculate P&L if we have entry data
                if position['entry_amount_usd'] > 0:
                    position['unrealized_pnl'] = position['current_value_usd'] - position['entry_amount_usd']
                    position['unrealized_pnl_pct'] = (position['unrealized_pnl'] / position['entry_amount_usd']) * 100
                else:
                    position['unrealized_pnl'] = 0
                    position['unrealized_pnl_pct'] = 0

                # Market performance metrics
                position['price_change_24h'] = self._get_price_change_24h(symbol)

                # Position age
                if existing_position.get('first_seen'):
                    first_seen = datetime.fromisoformat(existing_position['first_seen'])
                    position['age_hours'] = (datetime.now() - first_seen).total_seconds() / 3600
                else:
                    position['age_hours'] = 0

                # Generate sell signals
                position['sell_signals'] = self._generate_sell_signals(position)

            # Update our positions tracking
            self.positions = current_positions
            self.last_update = datetime.now()

            # Save positions
            self._save_positions()

            print(f"💎 POSITION UPDATE: {len(current_positions)} positions tracked")
            return current_positions

        except Exception as e:
            print(f"❌ Error updating positions: {e}")
            return self.positions

    def _get_token_price(self, symbol: str) -> float:
        """Get current token price with caching"""

        # Check cache first
        cache_key = f"{symbol}_price"
        cached_data = self.price_cache.get(cache_key)

        if cached_data:
            cached_time, cached_price = cached_data
            if (datetime.now() - cached_time).seconds < 60:  # Cache for 1 minute
                return cached_price

        try:
            # Get market data
            from connectors.coinmarketcap_api import get_cmc_api
            cmc = get_cmc_api()
            quotes = cmc.get_token_quotes([symbol])

            if symbol in quotes:
                price = quotes[symbol].get('price', 0)
                self.price_cache[cache_key] = (datetime.now(), price)
                return price

        except Exception as e:
            print(f"⚠️  Error getting price for {symbol}: {e}")

        return 0.0

    def _get_price_change_24h(self, symbol: str) -> float:
        """Get 24h price change percentage"""

        try:
            from connectors.coinmarketcap_api import get_cmc_api
            cmc = get_cmc_api()
            quotes = cmc.get_token_quotes([symbol])

            if symbol in quotes:
                return quotes[symbol].get('percent_change_24h', 0)

        except Exception as e:
            print(f"⚠️  Error getting 24h change for {symbol}: {e}")

        return 0.0

    def _generate_sell_signals(self, position: Dict) -> List[Dict]:
        """Generate sell signals based on position performance and market conditions"""

        signals = []
        symbol = position['token_symbol']
        current_pnl_pct = position['unrealized_pnl_pct']
        age_hours = position['age_hours']
        price_change_24h = position['price_change_24h']
        current_value = position['current_value_usd']

        # PROFIT TAKING SIGNALS
        if current_pnl_pct >= 50:
            signals.append({
                'type': 'TAKE_PROFIT',
                'urgency': 'HIGH',
                'reason': f'Massive profit: +{current_pnl_pct:.1f}% - Take profits now!',
                'suggested_sell_pct': 75,  # Sell 75% to lock in profits
                'confidence': 0.9
            })
        elif current_pnl_pct >= 25:
            signals.append({
                'type': 'TAKE_PROFIT',
                'urgency': 'MEDIUM',
                'reason': f'Strong profit: +{current_pnl_pct:.1f}% - Consider taking some profits',
                'suggested_sell_pct': 50,  # Sell 50%
                'confidence': 0.75
            })
        elif current_pnl_pct >= 15:
            signals.append({
                'type': 'TAKE_PROFIT',
                'urgency': 'LOW',
                'reason': f'Good profit: +{current_pnl_pct:.1f}% - Partial profit taking recommended',
                'suggested_sell_pct': 25,  # Sell 25%
                'confidence': 0.6
            })

        # STOP LOSS SIGNALS
        if current_pnl_pct <= -20:
            signals.append({
                'type': 'STOP_LOSS',
                'urgency': 'HIGH',
                'reason': f'Major loss: {current_pnl_pct:.1f}% - Cut losses immediately!',
                'suggested_sell_pct': 100,  # Sell everything
                'confidence': 0.95
            })
        elif current_pnl_pct <= -15:
            signals.append({
                'type': 'STOP_LOSS',
                'urgency': 'MEDIUM',
                'reason': f'Significant loss: {current_pnl_pct:.1f}% - Consider cutting losses',
                'suggested_sell_pct': 75,  # Sell most of position
                'confidence': 0.8
            })
        elif current_pnl_pct <= -10:
            signals.append({
                'type': 'STOP_LOSS',
                'urgency': 'LOW',
                'reason': f'Moderate loss: {current_pnl_pct:.1f}% - Monitor closely',
                'suggested_sell_pct': 0,  # Just monitor for now
                'confidence': 0.5
            })

        # MARKET MOMENTUM SIGNALS
        if price_change_24h <= -15:
            signals.append({
                'type': 'MOMENTUM',
                'urgency': 'HIGH',
                'reason': f'Market crash: {price_change_24h:.1f}% drop in 24h - Consider selling',
                'suggested_sell_pct': 50,
                'confidence': 0.8
            })
        elif price_change_24h <= -10:
            signals.append({
                'type': 'MOMENTUM',
                'urgency': 'MEDIUM',
                'reason': f'Strong decline: {price_change_24h:.1f}% drop in 24h',
                'suggested_sell_pct': 25,
                'confidence': 0.6
            })

        # TIME-BASED SIGNALS
        if age_hours >= 168:  # 1 week old
            if current_pnl_pct > 5:
                signals.append({
                    'type': 'TIME_BASED',
                    'urgency': 'LOW',
                    'reason': f'Position aged {age_hours/24:.1f} days with +{current_pnl_pct:.1f}% profit - Consider taking profits',
                    'suggested_sell_pct': 30,
                    'confidence': 0.6
                })
            elif current_pnl_pct < -5:
                signals.append({
                    'type': 'TIME_BASED',
                    'urgency': 'MEDIUM',
                    'reason': f'Position aged {age_hours/24:.1f} days with {current_pnl_pct:.1f}% loss - Review strategy',
                    'suggested_sell_pct': 50,
                    'confidence': 0.7
                })

        # POSITION SIZE SIGNALS
        if current_value > 1000:  # Large position
            if current_pnl_pct > 10:
                signals.append({
                    'type': 'RISK_MANAGEMENT',
                    'urgency': 'MEDIUM',
                    'reason': f'Large position ${current_value:.0f} with +{current_pnl_pct:.1f}% profit - De-risk partially',
                    'suggested_sell_pct': 40,
                    'confidence': 0.75
                })

        return signals

    def get_sell_recommendations(self, min_urgency: str = 'LOW') -> List[Dict]:
        """Get positions that have sell signals"""

        urgency_levels = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3}
        min_level = urgency_levels.get(min_urgency, 1)

        recommendations = []

        for symbol, position in self.positions.items():
            sell_signals = position.get('sell_signals', [])

            for signal in sell_signals:
                signal_level = urgency_levels.get(signal['urgency'], 1)

                if signal_level >= min_level:
                    recommendation = {
                        'token_symbol': symbol,
                        'current_balance': position['balance'],
                        'current_value_usd': position['current_value_usd'],
                        'unrealized_pnl': position['unrealized_pnl'],
                        'unrealized_pnl_pct': position['unrealized_pnl_pct'],
                        'contract_address': position['contract_address'],
                        'signal': signal
                    }
                    recommendations.append(recommendation)

        # Sort by urgency and confidence
        recommendations.sort(key=lambda x: (
            urgency_levels[x['signal']['urgency']],
            x['signal']['confidence']
        ), reverse=True)

        return recommendations

    def record_entry_position(self, token_symbol: str, amount_usd: float, entry_price: float):
        """Record when we enter a new position"""

        position_data = {
            'token_symbol': token_symbol,
            'entry_amount_usd': amount_usd,
            'entry_price': entry_price,
            'entry_time': datetime.now().isoformat(),
            'first_seen': datetime.now().isoformat()
        }

        # If position already exists, update entry data
        if token_symbol in self.positions:
            self.positions[token_symbol].update(position_data)
        else:
            # Create new position tracking
            self.positions[token_symbol] = position_data

        self._save_positions()
        print(f"📈 POSITION ENTRY RECORDED: {token_symbol} ${amount_usd:.2f} at ${entry_price:.6f}")

    def create_sell_decision(self, recommendation: Dict) -> Dict:
        """Create a sell trading decision from a position recommendation"""

        signal = recommendation['signal']

        # Calculate sell amount
        sell_pct = signal['suggested_sell_pct'] / 100.0
        sell_amount_usd = recommendation['current_value_usd'] * sell_pct

        decision = {
            'action': 'SELL',
            'token': recommendation['token_symbol'],
            'amount_usd': sell_amount_usd,
            'confidence_score': signal['confidence'],
            'reasoning': f"POSITION MANAGEMENT: {signal['reason']}",
            'source': 'position_monitor',
            'urgency': signal['urgency'],
            'sell_percentage': signal['suggested_sell_pct'],
            'current_pnl_pct': recommendation['unrealized_pnl_pct'],
            'position_management': True
        }

        return decision

    def display_position_dashboard(self):
        """Display comprehensive position monitoring dashboard"""

        print("\n" + "=" * 80)
        print("💎 POSITION MONITORING DASHBOARD")
        print("=" * 80)

        if not self.positions:
            print("📊 No positions currently tracked")
            return

        total_value = 0
        total_pnl = 0
        profitable_positions = 0
        losing_positions = 0

        for symbol, position in self.positions.items():
            value = position.get('current_value_usd', 0)
            pnl = position.get('unrealized_pnl', 0)
            pnl_pct = position.get('unrealized_pnl_pct', 0)

            total_value += value
            total_pnl += pnl

            if pnl > 0:
                profitable_positions += 1
                status = f"📈 +{pnl_pct:.1f}%"
            elif pnl < 0:
                losing_positions += 1
                status = f"📉 {pnl_pct:.1f}%"
            else:
                status = "➡️  0.0%"

            signals = position.get('sell_signals', [])
            signal_info = ""
            if signals:
                high_urgency = [s for s in signals if s['urgency'] == 'HIGH']
                if high_urgency:
                    signal_info = " 🚨 HIGH URGENCY SELL SIGNAL"

            print(f"   {symbol}: ${value:.2f} {status} (Balance: {position.get('balance', 0):.4f}){signal_info}")

        # Summary
        total_pnl_pct = (total_pnl / (total_value - total_pnl) * 100) if (total_value - total_pnl) > 0 else 0

        print(f"\n📊 PORTFOLIO SUMMARY:")
        print(f"   💎 Total Value: ${total_value:.2f}")
        print(f"   📈 Total P&L: ${total_pnl:.2f} ({total_pnl_pct:+.1f}%)")
        print(f"   ✅ Profitable: {profitable_positions} positions")
        print(f"   ❌ Losing: {losing_positions} positions")

        # Show sell recommendations
        recommendations = self.get_sell_recommendations('LOW')
        if recommendations:
            print(f"\n🎯 SELL RECOMMENDATIONS ({len(recommendations)}):")
            for rec in recommendations[:5]:  # Show top 5
                signal = rec['signal']
                print(f"   {signal['urgency']} - {rec['token_symbol']}: {signal['reason']}")
                print(f"      💰 Current: ${rec['current_value_usd']:.2f} | P&L: {rec['unrealized_pnl_pct']:+.1f}%")
                print(f"      🎯 Suggestion: Sell {signal['suggested_sell_pct']}% (${rec['current_value_usd'] * signal['suggested_sell_pct']/100:.2f})")

        print("=" * 80 + "\n")

    def _save_positions(self):
        """Save positions to file"""
        try:
            data = {
                'positions': self.positions,
                'last_update': self.last_update.isoformat() if self.last_update else None,
                'position_history': self.position_history[-100:]  # Keep last 100 entries
            }

            with open('position_monitor_data.json', 'w') as f:
                json.dump(data, f, indent=2, default=str)

        except Exception as e:
            print(f"Error saving positions: {e}")

    def _load_positions(self):
        """Load positions from file"""
        try:
            with open('position_monitor_data.json', 'r') as f:
                data = json.load(f)

            self.positions = data.get('positions', {})
            self.position_history = data.get('position_history', [])

            if data.get('last_update'):
                self.last_update = datetime.fromisoformat(data['last_update'])

            print(f"📊 Loaded {len(self.positions)} tracked positions")

        except FileNotFoundError:
            print("📊 No position history found - starting fresh")
        except Exception as e:
            print(f"Error loading positions: {e}")

# Global position monitor instance
_position_monitor = None

def get_position_monitor() -> PositionMonitor:
    """Get global position monitor instance"""
    global _position_monitor
    if _position_monitor is None:
        _position_monitor = PositionMonitor()
    return _position_monitor

def update_wallet_positions() -> Dict:
    """Update and return current wallet positions"""
    monitor = get_position_monitor()
    return monitor.update_positions(force_refresh=True)

def get_sell_recommendations(min_urgency: str = 'MEDIUM') -> List[Dict]:
    """Get positions that should be sold"""
    monitor = get_position_monitor()
    monitor.update_positions()  # Refresh first
    return monitor.get_sell_recommendations(min_urgency)

def record_position_entry(token_symbol: str, amount_usd: float, entry_price: float):
    """Record when bot enters a new position"""
    monitor = get_position_monitor()
    monitor.record_entry_position(token_symbol, amount_usd, entry_price)