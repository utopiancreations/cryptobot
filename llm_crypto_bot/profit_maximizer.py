"""
Profit Maximizer - Bot Motivation and Wealth Accumulation System
Drives bots to maximize earnings while maintaining survival instincts
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import config
from utils.wallet import get_wallet_balance

class ProfitMaximizer:
    """System to motivate bots for maximum wealth accumulation"""

    def __init__(self):
        self.profit_history = []
        self.starting_portfolio_value = 0
        self.current_portfolio_value = 0
        self.peak_portfolio_value = 0
        self.total_realized_profits = 0
        self.total_fees_paid = 0
        self.successful_trades = 0
        self.failed_trades = 0
        self.consecutive_wins = 0
        self.max_consecutive_wins = 0
        self.wealth_growth_rate = 0.0
        self.risk_appetite = 0.5  # Starts conservative, grows with success
        self.confidence_multiplier = 1.0
        self.last_evaluation = datetime.now()

        # Load historical performance
        self._load_performance_data()

    def evaluate_profit_opportunity(self, decision: Dict, market_data: Dict) -> Dict:
        """Evaluate and enhance trading decision for maximum profit potential"""

        # Calculate current portfolio value
        self._update_portfolio_metrics()

        # Assess profit potential
        profit_score = self._calculate_profit_potential(decision, market_data)

        # Apply wealth accumulation motivation
        motivated_decision = self._apply_wealth_motivation(decision, profit_score)

        # Adjust position sizing for maximum growth
        optimized_decision = self._optimize_position_size(motivated_decision, profit_score)

        print(f"💰 PROFIT MAXIMIZER ANALYSIS:")
        print(f"   • Portfolio Value: ${self.current_portfolio_value:,.2f}")
        print(f"   • Total Profit: ${self.total_realized_profits:,.2f}")
        print(f"   • Growth Rate: {self.wealth_growth_rate:.1%}")
        print(f"   • Win Streak: {self.consecutive_wins} trades")
        print(f"   • Risk Appetite: {self.risk_appetite:.1%}")
        print(f"   • Profit Score: {profit_score:.1f}/10")
        print(f"   • Confidence: {self.confidence_multiplier:.2f}x")

        return optimized_decision

    def _calculate_profit_potential(self, decision: Dict, market_data: Dict) -> float:
        """Calculate profit potential score (0-10)"""
        score = 5.0  # Base score

        # Market momentum scoring
        token_symbol = decision.get('token', '').upper()
        sentiment = market_data.get('sentiment', {})

        # Strong market sentiment boosts profit potential
        if sentiment.get('classification') == 'greed':
            score += 1.5
        elif sentiment.get('classification') == 'extreme_greed':
            score += 2.5
        elif sentiment.get('classification') == 'fear':
            score += 0.5  # Opportunity in fear
        elif sentiment.get('classification') == 'extreme_fear':
            score += 1.0  # Big opportunity in extreme fear

        # Check if token is in top gainers (high profit opportunity)
        top_gainers = market_data.get('top_gainers', [])
        for gainer in top_gainers[:10]:
            if gainer.get('symbol') == token_symbol:
                gain_percent = abs(gainer.get('percent_change_24h', 0))
                if gain_percent > 20:
                    score += 2.0  # Major momentum
                elif gain_percent > 10:
                    score += 1.0  # Good momentum
                break

        # Confidence in decision affects profit potential
        confidence = decision.get('confidence_score', 0)
        if confidence > 0.8:
            score += 1.5
        elif confidence > 0.7:
            score += 1.0
        elif confidence < 0.65:
            score -= 1.0

        # Our historical success with similar tokens
        score += self._get_token_success_bonus(token_symbol)

        return min(10.0, max(0.0, score))

    def _apply_wealth_motivation(self, decision: Dict, profit_score: float) -> Dict:
        """Apply wealth accumulation motivation to trading decisions"""
        motivated_decision = decision.copy()

        # Increase confidence for high-profit opportunities
        if profit_score >= 7.0:
            original_confidence = decision.get('confidence_score', 0)
            motivated_confidence = min(0.95, original_confidence * self.confidence_multiplier)
            motivated_decision['confidence_score'] = motivated_confidence
            motivated_decision['motivation_boost'] = f"High profit potential ({profit_score:.1f}/10)"

        # Add wealth-driven reasoning
        wealth_reasoning = self._generate_wealth_reasoning(profit_score)
        original_reasoning = decision.get('reasoning', decision.get('justification', ''))
        motivated_decision['reasoning'] = f"{original_reasoning}\n\n💰 WEALTH MOTIVATION: {wealth_reasoning}"

        # Set execution urgency based on profit potential
        if profit_score >= 8.0:
            motivated_decision['execution_urgency'] = 'high'
        elif profit_score >= 6.0:
            motivated_decision['execution_urgency'] = 'medium'
        else:
            motivated_decision['execution_urgency'] = 'low'

        return motivated_decision

    def _optimize_position_size(self, decision: Dict, profit_score: float) -> Dict:
        """Optimize position sizing for maximum wealth growth"""
        optimized_decision = decision.copy()

        base_amount = decision.get('amount_usd', 0)

        # Scale position based on profit potential and risk appetite
        size_multiplier = 1.0

        # High profit opportunities get bigger positions
        if profit_score >= 8.0:
            size_multiplier = 1.5 * self.risk_appetite + 0.5  # 0.5x to 2.0x
        elif profit_score >= 7.0:
            size_multiplier = 1.3 * self.risk_appetite + 0.4  # 0.4x to 1.7x
        elif profit_score >= 6.0:
            size_multiplier = 1.1 * self.risk_appetite + 0.3  # 0.3x to 1.4x
        else:
            size_multiplier = 0.8 * self.risk_appetite + 0.2  # 0.2x to 1.0x

        # Success streak bonus
        if self.consecutive_wins >= 3:
            size_multiplier *= 1.2  # 20% bonus for hot streak
        elif self.consecutive_wins >= 5:
            size_multiplier *= 1.4  # 40% bonus for amazing streak

        # Growth rate bonus - more aggressive when we're winning
        if self.wealth_growth_rate > 0.1:  # 10% growth
            size_multiplier *= 1.1
        elif self.wealth_growth_rate > 0.2:  # 20% growth
            size_multiplier *= 1.2

        # Safety check - never risk more than configured max
        max_trade = config.get_dynamic_risk_params()['MAX_TRADE_USD']
        optimized_amount = min(base_amount * size_multiplier, max_trade)

        # But also ensure minimum for high-profit opportunities
        if profit_score >= 7.0:
            min_trade = max_trade * 0.3  # At least 30% of max for good opportunities
            optimized_amount = max(optimized_amount, min_trade)

        optimized_decision['amount_usd'] = round(optimized_amount, 2)
        optimized_decision['size_multiplier'] = round(size_multiplier, 2)
        optimized_decision['profit_optimization'] = True

        if optimized_amount != base_amount:
            print(f"💵 POSITION SIZING: ${base_amount:.2f} → ${optimized_amount:.2f} ({size_multiplier:.1f}x multiplier)")

        return optimized_decision

    def record_trade_result(self, decision: Dict, result: Dict):
        """Record trade results to improve future profit maximization"""
        try:
            trade_successful = result.get('trade_executed', False) and result.get('status') == 'SUCCESS'
            amount_usd = decision.get('amount_usd', 0)

            # Update trade counters
            if trade_successful:
                self.successful_trades += 1
                self.consecutive_wins += 1
                self.max_consecutive_wins = max(self.max_consecutive_wins, self.consecutive_wins)

                # Estimate profit (simplified - would need actual price data for real profit)
                estimated_profit = amount_usd * 0.05  # Assume 5% profit for successful trades
                self.total_realized_profits += estimated_profit

                print(f"✅ PROFIT SUCCESS: +${estimated_profit:.2f} (Streak: {self.consecutive_wins})")

            else:
                self.failed_trades += 1
                self.consecutive_wins = 0

                # Estimate loss
                estimated_loss = amount_usd * 0.02  # Assume 2% loss for failed trades
                self.total_realized_profits -= estimated_loss

                print(f"❌ PROFIT LOSS: -${estimated_loss:.2f} (Streak broken)")

            # Update risk appetite based on performance
            self._update_risk_appetite(trade_successful)

            # Update confidence multiplier
            self._update_confidence_multiplier()

            # Record detailed trade data
            trade_record = {
                'timestamp': datetime.now().isoformat(),
                'token': decision.get('token'),
                'action': decision.get('action'),
                'amount_usd': amount_usd,
                'profit_score': decision.get('profit_score', 0),
                'successful': trade_successful,
                'consecutive_wins': self.consecutive_wins,
                'portfolio_value': self.current_portfolio_value
            }

            self.profit_history.append(trade_record)

            # Save performance data
            self._save_performance_data()

        except Exception as e:
            print(f"Error recording trade result: {e}")

    def _update_risk_appetite(self, trade_successful: bool):
        """Update risk appetite based on recent performance"""
        if trade_successful:
            # Increase risk appetite when winning (but cap it)
            self.risk_appetite = min(1.0, self.risk_appetite * 1.05)
        else:
            # Decrease risk appetite when losing (but keep minimum)
            self.risk_appetite = max(0.2, self.risk_appetite * 0.95)

        # Bonus for winning streaks
        if self.consecutive_wins >= 3:
            self.risk_appetite = min(1.0, self.risk_appetite * 1.1)

    def _update_confidence_multiplier(self):
        """Update confidence multiplier based on recent success rate"""
        if self.successful_trades + self.failed_trades == 0:
            return

        success_rate = self.successful_trades / (self.successful_trades + self.failed_trades)

        # High success rate increases confidence
        if success_rate >= 0.7:
            self.confidence_multiplier = 1.3
        elif success_rate >= 0.6:
            self.confidence_multiplier = 1.2
        elif success_rate >= 0.5:
            self.confidence_multiplier = 1.1
        else:
            self.confidence_multiplier = 0.9

    def _update_portfolio_metrics(self):
        """Update current portfolio value and growth metrics"""
        try:
            # Get current wallet balance
            wallet_balance = get_wallet_balance()
            if wallet_balance and isinstance(wallet_balance, dict):
                current_value = wallet_balance.get('total_usd_estimate', 0) or 0
            else:
                current_value = 0

            if self.starting_portfolio_value == 0:
                self.starting_portfolio_value = current_value

            self.current_portfolio_value = current_value
            self.peak_portfolio_value = max(self.peak_portfolio_value, current_value)

            # Calculate growth rate
            if self.starting_portfolio_value > 0:
                self.wealth_growth_rate = (current_value - self.starting_portfolio_value) / self.starting_portfolio_value

        except Exception as e:
            print(f"Error updating portfolio metrics: {e}")

    def _get_token_success_bonus(self, token_symbol: str) -> float:
        """Get bonus score based on historical success with this token"""
        token_trades = [t for t in self.profit_history if t.get('token') == token_symbol]

        if not token_trades:
            return 0.0

        successful_token_trades = [t for t in token_trades if t.get('successful')]
        success_rate = len(successful_token_trades) / len(token_trades)

        if success_rate >= 0.8:
            return 1.5  # We're very good with this token
        elif success_rate >= 0.6:
            return 1.0  # We're good with this token
        elif success_rate >= 0.4:
            return 0.0  # Neutral
        else:
            return -0.5  # We've struggled with this token

    def _generate_wealth_reasoning(self, profit_score: float) -> str:
        """Generate wealth-motivated reasoning"""
        if profit_score >= 8.0:
            return f"MAXIMUM PROFIT OPPORTUNITY detected! Portfolio growth potential is extreme. Current streak: {self.consecutive_wins} wins. Time to maximize position for wealth accumulation!"
        elif profit_score >= 7.0:
            return f"HIGH PROFIT opportunity identified. Risk appetite at {self.risk_appetite:.1%} - increasing position size to capitalize on wealth growth potential."
        elif profit_score >= 6.0:
            return f"GOOD PROFIT potential. Balanced approach for steady wealth building. Portfolio value: ${self.current_portfolio_value:,.2f}"
        elif profit_score >= 4.0:
            return f"MODERATE opportunity. Conservative sizing to preserve capital while seeking growth. Success rate: {self._get_success_rate():.1%}"
        else:
            return f"LOW PROFIT potential. Minimal position to limit downside while maintaining market exposure."

    def _get_success_rate(self) -> float:
        """Get current success rate"""
        total_trades = self.successful_trades + self.failed_trades
        if total_trades == 0:
            return 0.0
        return (self.successful_trades / total_trades) * 100

    def get_wealth_status(self) -> Dict:
        """Get current wealth accumulation status"""
        return {
            'current_portfolio_value': self.current_portfolio_value,
            'starting_portfolio_value': self.starting_portfolio_value,
            'peak_portfolio_value': self.peak_portfolio_value,
            'total_realized_profits': self.total_realized_profits,
            'wealth_growth_rate': self.wealth_growth_rate,
            'successful_trades': self.successful_trades,
            'failed_trades': self.failed_trades,
            'success_rate': self._get_success_rate(),
            'consecutive_wins': self.consecutive_wins,
            'max_consecutive_wins': self.max_consecutive_wins,
            'risk_appetite': self.risk_appetite,
            'confidence_multiplier': self.confidence_multiplier
        }

    def _save_performance_data(self):
        """Save performance data to file"""
        try:
            data = {
                'starting_portfolio_value': self.starting_portfolio_value,
                'total_realized_profits': self.total_realized_profits,
                'successful_trades': self.successful_trades,
                'failed_trades': self.failed_trades,
                'consecutive_wins': self.consecutive_wins,
                'max_consecutive_wins': self.max_consecutive_wins,
                'risk_appetite': self.risk_appetite,
                'confidence_multiplier': self.confidence_multiplier,
                'profit_history': self.profit_history[-100:]  # Keep last 100 trades
            }

            with open('profit_maximizer_data.json', 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"Error saving performance data: {e}")

    def _load_performance_data(self):
        """Load historical performance data"""
        try:
            with open('profit_maximizer_data.json', 'r') as f:
                data = json.load(f)

            self.starting_portfolio_value = data.get('starting_portfolio_value', 0)
            self.total_realized_profits = data.get('total_realized_profits', 0)
            self.successful_trades = data.get('successful_trades', 0)
            self.failed_trades = data.get('failed_trades', 0)
            self.consecutive_wins = data.get('consecutive_wins', 0)
            self.max_consecutive_wins = data.get('max_consecutive_wins', 0)
            self.risk_appetite = data.get('risk_appetite', 0.5)
            self.confidence_multiplier = data.get('confidence_multiplier', 1.0)
            self.profit_history = data.get('profit_history', [])

            print("📊 Loaded historical performance data")

        except FileNotFoundError:
            print("📊 No historical performance data found - starting fresh")
        except Exception as e:
            print(f"Error loading performance data: {e}")

# Global profit maximizer instance
_profit_maximizer = None

def get_profit_maximizer() -> ProfitMaximizer:
    """Get global profit maximizer instance"""
    global _profit_maximizer
    if _profit_maximizer is None:
        _profit_maximizer = ProfitMaximizer()
    return _profit_maximizer

def motivate_for_maximum_profit(decision: Dict, market_data: Dict) -> Dict:
    """Main function to motivate bots for maximum profit"""
    profit_maximizer = get_profit_maximizer()
    return profit_maximizer.evaluate_profit_opportunity(decision, market_data)