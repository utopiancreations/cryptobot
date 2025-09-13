import json
from datetime import datetime
from typing import Dict, Optional, List
import config
from utils.wallet import get_wallet_balance

class TradeSimulator:
    """Simulated trading executor for safe testing"""
    
    def __init__(self):
        self.trade_history: List[Dict] = []
        self.daily_pnl = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        
    def execute_simulated_trade(self, decision_json: Dict) -> Dict:
        """
        Execute a simulated trade based on LLM decision
        
        Args:
            decision_json: Trading decision from LLM
            
        Returns:
            Trade execution result
        """
        if not decision_json:
            return self._create_error_result("Invalid decision data")
        
        # Validate decision structure
        required_fields = ['action', 'token', 'amount_usd', 'confidence']
        for field in required_fields:
            if field not in decision_json:
                return self._create_error_result(f"Missing required field: {field}")
        
        action = decision_json['action'].upper()
        
        # Skip HOLD actions
        if action == 'HOLD':
            return self._create_hold_result(decision_json)
        
        # Check risk limits
        risk_check = self._check_risk_limits(decision_json)
        if not risk_check['allowed']:
            return self._create_error_result(risk_check['reason'])
        
        # Execute the simulated trade
        if action in ['BUY', 'SELL']:
            return self._execute_trade_simulation(decision_json)
        else:
            return self._create_error_result(f"Unknown action: {action}")
    
    def _execute_trade_simulation(self, decision: Dict) -> Dict:
        """Execute the actual trade simulation"""
        
        trade_id = f"SIM_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.total_trades + 1}"
        
        # Get current wallet balance for context
        wallet_balance = get_wallet_balance()
        
        # Simulate trade execution
        trade_result = {
            'trade_id': trade_id,
            'timestamp': datetime.now().isoformat(),
            'action': decision['action'],
            'token': decision['token'],
            'amount_usd': decision['amount_usd'],
            'confidence': decision['confidence'],
            'reasoning': decision['reasoning'],
            'risk_level': decision.get('risk_level', 'MEDIUM'),
            'status': 'EXECUTED_SIMULATION',
            'execution_price': self._get_mock_price(decision['token']),
            'gas_fee_estimate': 0.005,  # Mock gas fee
            'slippage_estimate': 0.5,   # Mock slippage percentage
            'stop_loss_percent': decision.get('stop_loss_percent', 5.0),
            'take_profit_percent': decision.get('take_profit_percent', 10.0)
        }
        
        # Calculate estimated tokens received/sold
        price = trade_result['execution_price']
        if decision['action'] == 'BUY':
            tokens_amount = decision['amount_usd'] / price
            trade_result['tokens_amount'] = tokens_amount
            trade_result['estimated_value_change'] = f"+{tokens_amount:.6f} {decision['token']}"
        else:  # SELL
            tokens_amount = decision['amount_usd'] / price
            trade_result['tokens_amount'] = tokens_amount
            trade_result['estimated_value_change'] = f"-{tokens_amount:.6f} {decision['token']}"
        
        # Log the simulation
        self._log_trade_simulation(trade_result)
        
        # Update internal tracking
        self.trade_history.append(trade_result)
        self.total_trades += 1
        
        # Simulate a win/loss for tracking (60% win rate simulation)
        import random
        if random.random() < 0.6:
            self.winning_trades += 1
        
        return trade_result
    
    def _log_trade_simulation(self, trade: Dict):
        """Log simulated trade to console"""
        action_emoji = "🟢" if trade['action'] == 'BUY' else "🔴"
        
        print(f"\n{action_emoji} [SIMULATION] Trade Executed:")
        print(f"   Trade ID: {trade['trade_id']}")
        print(f"   Action: {trade['action']} {trade['token']}")
        print(f"   Amount: ${trade['amount_usd']:.2f} USD")
        print(f"   Price: ${trade['execution_price']:.6f}")
        print(f"   Tokens: {trade['tokens_amount']:.6f} {trade['token']}")
        print(f"   Confidence: {trade['confidence']:.1%}")
        print(f"   Risk Level: {trade['risk_level']}")
        print(f"   Stop Loss: {trade['stop_loss_percent']:.1f}%")
        print(f"   Take Profit: {trade['take_profit_percent']:.1f}%")
        print(f"   Reasoning: {trade['reasoning']}")
        print(f"   Gas Fee: ${trade['gas_fee_estimate']:.3f}")
        print(f"   Est. Slippage: {trade['slippage_estimate']:.1f}%")
        print("   �  THIS IS A SIMULATION - NO REAL TRADES EXECUTED")
    
    def _check_risk_limits(self, decision: Dict) -> Dict:
        """Check if trade meets risk management criteria"""
        risk_params = config.get_risk_params()
        
        # Check maximum trade amount
        if decision['amount_usd'] > risk_params['MAX_TRADE_USD']:
            return {
                'allowed': False,
                'reason': f"Trade amount ${decision['amount_usd']:.2f} exceeds limit ${risk_params['MAX_TRADE_USD']:.2f}"
            }
        
        # Check token whitelist
        if decision['token'] not in risk_params['TOKEN_WHITELIST']:
            return {
                'allowed': False,
                'reason': f"Token {decision['token']} not in approved whitelist"
            }
        
        # Check daily loss limit (simplified simulation)
        if abs(self.daily_pnl) > (risk_params['DAILY_LOSS_LIMIT_PERCENT'] / 100) * 1000:  # Assume $1000 portfolio
            return {
                'allowed': False,
                'reason': "Daily loss limit exceeded"
            }
        
        # Check confidence threshold
        if decision.get('confidence', 0) < 0.3:
            return {
                'allowed': False,
                'reason': f"Confidence {decision.get('confidence', 0):.1%} below minimum threshold"
            }
        
        return {'allowed': True, 'reason': 'Risk checks passed'}
    
    def _get_mock_price(self, token: str) -> float:
        """Get mock price for simulation"""
        mock_prices = {
            'BTC': 45000.0,
            'BTCB': 45000.0,
            'ETH': 2500.0,
            'BNB': 300.0,
            'WBNB': 300.0,
            'USDT': 1.0,
            'USDC': 1.0,
            'BUSD': 1.0
        }
        
        base_price = mock_prices.get(token, 100.0)
        
        # Add small random variation for realism
        import random
        variation = random.uniform(-0.02, 0.02)  # �2% variation
        return base_price * (1 + variation)
    
    def _create_error_result(self, reason: str) -> Dict:
        """Create error result"""
        return {
            'status': 'ERROR',
            'timestamp': datetime.now().isoformat(),
            'error': reason,
            'trade_executed': False
        }
    
    def _create_hold_result(self, decision: Dict) -> Dict:
        """Create hold result"""
        print(f"\n�  [SIMULATION] HOLD Decision:")
        print(f"   Token: {decision['token']}")
        print(f"   Confidence: {decision.get('confidence', 0):.1%}")
        print(f"   Reasoning: {decision.get('reasoning', 'No reasoning provided')}")
        
        return {
            'status': 'HOLD',
            'timestamp': datetime.now().isoformat(),
            'action': 'HOLD',
            'token': decision['token'],
            'reasoning': decision.get('reasoning', ''),
            'confidence': decision.get('confidence', 0),
            'trade_executed': False
        }
    
    def get_trading_stats(self) -> Dict:
        """Get trading statistics"""
        if self.total_trades == 0:
            win_rate = 0.0
        else:
            win_rate = (self.winning_trades / self.total_trades) * 100
        
        return {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'win_rate_percent': win_rate,
            'daily_pnl': self.daily_pnl,
            'recent_trades': self.trade_history[-5:] if self.trade_history else []
        }
    
    def reset_daily_stats(self):
        """Reset daily statistics"""
        self.daily_pnl = 0.0
        print("=� Daily trading statistics reset")

# Global simulator instance
trade_simulator = TradeSimulator()

def execute_simulated_trade(decision_json: Dict) -> Dict:
    """
    Main function to execute simulated trades
    
    Args:
        decision_json: Trading decision from LLM
        
    Returns:
        Trade execution result
    """
    return trade_simulator.execute_simulated_trade(decision_json)

def get_trading_statistics() -> Dict:
    """Get current trading statistics"""
    return trade_simulator.get_trading_stats()

def reset_daily_trading_stats():
    """Reset daily trading statistics"""
    trade_simulator.reset_daily_stats()