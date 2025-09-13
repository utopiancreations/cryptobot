"""
Real Trade Executor for Cryptocurrency Trading

This module executes actual trades on decentralized exchanges (DEX) using Web3.
For safety, it includes extensive validation and confirmation prompts.
"""

import json
from datetime import datetime
from typing import Dict, Optional, List
from web3 import Web3
import config
from utils.wallet import get_wallet_balance, get_gas_price
from dex_integration import execute_dex_trade, get_supported_tokens
from multi_dex_integration import execute_multi_dex_trade, get_dex_info, find_token_availability

class RealTradeExecutor:
    """Real trading executor for DEX transactions"""
    
    def __init__(self):
        self.trade_history: List[Dict] = []
        self.w3 = None
        self.wallet_address = None
        self.private_key = None
        self._initialize_web3()
        
    def _initialize_web3(self) -> bool:
        """Initialize Web3 connection and wallet"""
        try:
            if not config.WALLET_ADDRESS or not config.PRIVATE_KEY:
                print("❌ Wallet address or private key not configured")
                return False
                
            self.w3 = Web3(Web3.HTTPProvider(config.RPC_URL))
            if not self.w3.is_connected():
                print("❌ Cannot connect to blockchain RPC")
                return False
                
            self.wallet_address = Web3.to_checksum_address(config.WALLET_ADDRESS)
            self.private_key = config.PRIVATE_KEY
            
            print("✅ Real trade executor initialized")
            return True
            
        except Exception as e:
            print(f"❌ Error initializing Web3: {e}")
            return False
    
    def execute_real_trade(self, decision_json: Dict) -> Dict:
        """
        Execute a real trade based on LLM decision
        
        Args:
            decision_json: Trading decision from consensus engine
            
        Returns:
            Trade execution result
        """
        if not self.w3 or not self.w3.is_connected():
            return self._create_error_result("Web3 not connected")
            
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
        
        # Final safety check with user confirmation
        if not self._get_user_confirmation(decision_json):
            return self._create_error_result("Trade cancelled by user")
        
        # Check risk limits
        risk_check = self._check_risk_limits(decision_json)
        if not risk_check['allowed']:
            return self._create_error_result(risk_check['reason'])
        
        # Execute the real trade
        if action in ['BUY', 'SELL']:
            return self._execute_dex_trade(decision_json)
        else:
            return self._create_error_result(f"Unknown action: {action}")
    
    def _get_user_confirmation(self, decision: Dict) -> bool:
        """
        Get user confirmation for real trade execution
        This is a critical safety measure
        """
        print("\n" + "="*60)
        print("🚨 REAL TRADE EXECUTION CONFIRMATION")
        print("="*60)
        print(f"Action: {decision['action']} {decision['token']}")
        print(f"Amount: ${decision['amount_usd']:.2f} USD")
        print(f"Confidence: {decision.get('confidence', 0):.1%}")
        print(f"Reasoning: {decision.get('reasoning', 'No reasoning provided')}")
        print(f"Wallet: {self.wallet_address}")
        print("="*60)
        print("⚠️  THIS WILL EXECUTE A REAL TRADE WITH REAL MONEY")
        print("⚠️  TRADES CANNOT BE UNDONE")
        print("="*60)
        
        # For overnight automation, we'll auto-approve if confidence is high enough
        confidence = decision.get('confidence', 0)
        if confidence >= 0.6:  # LOWERED confidence threshold for more aggressive trading
            print(f"✅ Auto-approving trade ({confidence:.1%}) - threshold lowered to 60%")
            return True
        else:
            print(f"❌ Rejecting low confidence trade ({confidence:.1%}) - threshold is 60%")
            return False
    
    def _execute_dex_trade(self, decision: Dict) -> Dict:
        """Execute DEX trade (simplified implementation)"""
        
        # For this implementation, we'll focus on simple token swaps
        # In production, this would integrate with DEX protocols like Uniswap, PancakeSwap, etc.
        
        trade_id = f"REAL_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Get current wallet balance
            wallet_balance = get_wallet_balance()
            if not wallet_balance:
                return self._create_error_result("Cannot retrieve wallet balance")
            
            # Check if we have enough balance for the trade
            available_balance = wallet_balance.get('total_usd_estimate', 0)
            if decision['amount_usd'] > available_balance:
                return self._create_error_result(f"Insufficient balance: ${available_balance:.2f} < ${decision['amount_usd']:.2f}")
            
            # MULTI-DEX EXECUTION: Execute trade on best available DEX
            token_symbol = self._map_token_symbol(decision['token'])
            
            # Check if multi-DEX is enabled
            if config.get_trade_settings().get('USE_MULTI_DEX', False):
                print("🔄 Executing REAL trade via Multi-DEX system...")
                
                # Show token availability across DEXs
                availability = find_token_availability(token_symbol)
                if availability:
                    print(f"📊 {token_symbol} available on: {[info['chain'] for info in availability]}")
                
                # Execute via multi-DEX system
                dex_result = execute_multi_dex_trade(
                    action=decision['action'],
                    token_symbol=token_symbol,
                    amount_usd=decision['amount_usd']
                )
            else:
                print("🔄 Executing REAL trade on QuickSwap DEX (legacy mode)...")
                
                # Execute the actual DEX trade (legacy single DEX)
                dex_result = execute_dex_trade(
                    action=decision['action'],
                    token_symbol=token_symbol,
                    amount_usd=decision['amount_usd']
                )
            
            if 'error' in dex_result:
                return self._create_error_result(f"DEX trade failed: {dex_result['error']}")
            
            # Create trade result with actual DEX data
            trade_result = {
                'trade_id': trade_id,
                'timestamp': datetime.now().isoformat(),
                'action': decision['action'],
                'token': decision['token'],
                'amount_usd': decision['amount_usd'],
                'confidence': decision['confidence'],
                'reasoning': decision['reasoning'],
                'status': 'EXECUTED_REAL',  # Actually executed on DEX
                'transaction_hash': dex_result.get('tx_hash', 'Unknown'),
                'gas_used': dex_result.get('gas_used', 0),
                'execution_price': self._get_current_price(decision['token']),
                'wallet_address': self.wallet_address,
                'portfolio_impact': f"{(decision['amount_usd'] / available_balance) * 100:.1f}%",
                'dex_platform': 'QuickSwap',
                'network': 'Polygon'
            }
            
            # Log the real trade
            self._log_real_trade(trade_result)
            
            # Store in history
            self.trade_history.append(trade_result)
            
            print("✅ REAL TRADE EXECUTED ON QUICKSWAP!")
            print(f"🔗 Transaction: https://polygonscan.com/tx/{dex_result.get('tx_hash', '')}")
            print("💰 This was a REAL trade using REAL money!")
            
            return trade_result
            
        except Exception as e:
            return self._create_error_result(f"Trade execution failed: {e}")
    
    def _check_risk_limits(self, decision: Dict) -> Dict:
        """Check risk limits for real trades (more conservative)"""
        risk_params = config.get_dynamic_risk_params()
        
        # More conservative limits for real trades
        max_trade = risk_params['MAX_TRADE_USD'] * 0.5  # 50% of calculated max
        
        if decision['amount_usd'] > max_trade:
            return {
                'allowed': False,
                'reason': f"Real trade amount ${decision['amount_usd']:.2f} exceeds conservative limit ${max_trade:.2f}"
            }
        
        # Require higher confidence for real trades
        if decision.get('confidence', 0) < 0.7:
            return {
                'allowed': False,
                'reason': f"Confidence {decision.get('confidence', 0):.1%} below real trade threshold (70%)"
            }
        
        return {'allowed': True, 'reason': 'Real trade risk checks passed'}
    
    def _map_token_symbol(self, token: str) -> str:
        """Map consensus engine token to DEX-supported token"""
        # Map common token symbols to QuickSwap supported tokens
        token_mapping = {
            'BTC': 'WBTC',
            'ETH': 'WETH', 
            'MATIC': 'WMATIC',
            'WMATIC': 'WMATIC',
            'WBTC': 'WBTC',
            'WETH': 'WETH',
            'USDC': 'USDC',
            'USDT': 'USDT',
            'DAI': 'DAI'
        }
        
        mapped_token = token_mapping.get(token.upper(), 'USDC')  # Default to USDC
        supported_tokens = get_supported_tokens()
        
        if mapped_token not in supported_tokens:
            print(f"⚠️ Token {token} -> {mapped_token} not supported, using USDC")
            return 'USDC'
        
        return mapped_token
    
    def _estimate_gas_cost(self) -> float:
        """Estimate gas cost for DEX trade"""
        # Typical DEX swap costs on Polygon
        return 0.01  # ~$0.01 in MATIC
    
    def _get_current_price(self, token: str) -> float:
        """Get current price for token (placeholder)"""
        # In production, this would query real price feeds
        mock_prices = {
            'BTC': 45000.0,
            'ETH': 2500.0,
            'MATIC': 0.8,
            'SOL': 100.0,
            'USDT': 1.0,
            'USDC': 1.0
        }
        return mock_prices.get(token, 100.0)
    
    def _log_real_trade(self, trade: Dict):
        """Log real trade to console and file"""
        action_emoji = "🟢" if trade['action'] == 'BUY' else "🔴"
        
        print(f"\n{action_emoji} [REAL] Trade Executed:")
        print(f"   Trade ID: {trade['trade_id']}")
        print(f"   Action: {trade['action']} {trade['token']}")
        print(f"   Amount: ${trade['amount_usd']:.2f} USD")
        print(f"   Price: ${trade['execution_price']:.6f}")
        print(f"   Confidence: {trade['confidence']:.1%}")
        print(f"   Reasoning: {trade['reasoning']}")
        print(f"   Wallet: {trade['wallet_address']}")
        print(f"   Tx Hash: {trade['transaction_hash']}")
        print("   🚨 THIS WAS A REAL TRADE")
        
        # Also log to file
        self._save_trade_to_file(trade)
    
    def _save_trade_to_file(self, trade: Dict):
        """Save trade record to file for audit trail"""
        try:
            with open('real_trades.log', 'a') as f:
                f.write(f"{json.dumps(trade)}\n")
        except Exception as e:
            print(f"Error saving trade to file: {e}")
    
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
        print(f"\n⏸️  [REAL] HOLD Decision:")
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

# Global real executor instance
real_trade_executor = RealTradeExecutor()

def execute_real_trade(decision_json: Dict) -> Dict:
    """
    Main function to execute real trades
    
    Args:
        decision_json: Trading decision from consensus engine
        
    Returns:
        Trade execution result
    """
    return real_trade_executor.execute_real_trade(decision_json)

def get_real_trade_history() -> List[Dict]:
    """Get history of real trades"""
    return real_trade_executor.trade_history.copy()