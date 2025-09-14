"""
Trade Manager for Multi-Trade Execution
Handles conflict resolution, risk management, and execution optimization for multiple trades
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import config

class TradeManager:
    """Manages multiple trade execution with conflict resolution and risk management"""

    def __init__(self):
        self.executed_trades = []
        self.daily_exposure = 0.0
        self.daily_trade_count = 0
        self.last_reset_date = datetime.now().date()

    def process_and_prioritize_trades(self, raw_decisions: List[Dict]) -> List[Dict]:
        """
        Process raw trading decisions and apply conflict resolution, risk management

        Args:
            raw_decisions: List of raw trading decisions from consensus engine

        Returns:
            List of processed and prioritized trades ready for execution
        """
        # Reset daily counters if new day
        self._check_daily_reset()

        if not raw_decisions:
            print("📊 No trading decisions to process")
            return []

        print(f"🔄 Processing {len(raw_decisions)} raw trading decisions...")

        # Step 1: Basic validation and filtering
        valid_decisions = self._validate_decisions(raw_decisions)
        if not valid_decisions:
            print("❌ No valid decisions after validation")
            return []

        print(f"✅ {len(valid_decisions)} decisions passed validation")

        # Step 2: Conflict resolution
        resolved_decisions = self._resolve_conflicts(valid_decisions)
        print(f"⚖️  {len(resolved_decisions)} decisions after conflict resolution")

        # Step 3: Risk management checks
        risk_managed_decisions = self._apply_risk_management(resolved_decisions)
        print(f"🛡️  {len(risk_managed_decisions)} decisions after risk management")

        # Step 4: Final prioritization
        prioritized_decisions = self._prioritize_trades(risk_managed_decisions)
        print(f"🎯 Final {len(prioritized_decisions)} prioritized trades for execution")

        return prioritized_decisions

    def _validate_decisions(self, decisions: List[Dict]) -> List[Dict]:
        """Validate trading decisions for basic requirements"""
        valid_decisions = []

        for i, decision in enumerate(decisions):
            # Check required fields
            if not all(field in decision for field in ['action', 'token', 'confidence_score']):
                print(f"⚠️  Decision {i+1}: Missing required fields")
                continue

            # Check action validity
            if decision['action'] not in ['BUY', 'SELL']:
                print(f"⚠️  Decision {i+1}: Invalid action '{decision['action']}'")
                continue

            # Check confidence threshold
            confidence = decision.get('confidence_score', 0)
            if confidence < 0.65:  # 65% minimum confidence
                print(f"⚠️  Decision {i+1}: Low confidence {confidence:.1%} (minimum 65%)")
                continue

            # Check amount validity
            amount = decision.get('amount_usd', 0)
            if amount < 3.0:  # Minimum $3 trade
                print(f"⚠️  Decision {i+1}: Amount too small ${amount:.2f} (minimum $3)")
                continue

            # Normalize token symbol
            decision['token'] = decision['token'].upper().strip()

            valid_decisions.append(decision)

        return valid_decisions

    def _resolve_conflicts(self, decisions: List[Dict]) -> List[Dict]:
        """Resolve conflicts between trading decisions"""
        if len(decisions) <= 1:
            return decisions

        # Group decisions by token
        token_decisions = {}
        for decision in decisions:
            token = decision['token']
            if token not in token_decisions:
                token_decisions[token] = []
            token_decisions[token].append(decision)

        resolved_decisions = []

        for token, token_group in token_decisions.items():
            if len(token_group) == 1:
                # No conflict for this token
                resolved_decisions.append(token_group[0])
            else:
                # Multiple decisions for same token - resolve conflict
                print(f"⚠️  Conflict detected for {token}: {len(token_group)} decisions")

                # Check for opposing actions (BUY vs SELL)
                buy_decisions = [d for d in token_group if d['action'] == 'BUY']
                sell_decisions = [d for d in token_group if d['action'] == 'SELL']

                if buy_decisions and sell_decisions:
                    print(f"🚫 Opposing BUY/SELL signals for {token} - skipping token")
                    continue

                # Multiple decisions with same action - pick highest confidence
                best_decision = max(token_group, key=lambda x: x.get('confidence_score', 0))
                print(f"✅ Selected highest confidence decision for {token}: {best_decision['confidence_score']:.1%}")
                resolved_decisions.append(best_decision)

        return resolved_decisions

    def _apply_risk_management(self, decisions: List[Dict]) -> List[Dict]:
        """Apply risk management rules to trading decisions"""
        risk_params = config.get_dynamic_risk_params()
        max_daily_exposure = risk_params['MAX_TRADE_USD'] * 3  # Max 3x single trade size per day
        max_trades_per_cycle = 3

        # Check daily exposure limit
        total_proposed_exposure = sum(d.get('amount_usd', 0) for d in decisions)
        remaining_daily_capacity = max_daily_exposure - self.daily_exposure

        if total_proposed_exposure > remaining_daily_capacity:
            print(f"⚠️  Daily exposure limit: Proposed ${total_proposed_exposure:.2f}, Available ${remaining_daily_capacity:.2f}")

            # Scale down trade sizes proportionally if needed
            if remaining_daily_capacity > 10:  # Only if we have meaningful capacity left
                scale_factor = remaining_daily_capacity / total_proposed_exposure
                for decision in decisions:
                    new_amount = decision['amount_usd'] * scale_factor
                    if new_amount >= 3.0:  # Keep minimum trade size
                        decision['amount_usd'] = round(new_amount, 2)
                        print(f"📉 Scaled {decision['token']} trade to ${decision['amount_usd']:.2f}")
                    else:
                        print(f"🚫 Removed {decision['token']} trade (too small after scaling)")
                        decisions = [d for d in decisions if d != decision]
            else:
                print("🚫 Insufficient daily capacity - skipping all trades")
                return []

        # Limit to maximum trades per cycle
        if len(decisions) > max_trades_per_cycle:
            print(f"⚠️  Too many trades ({len(decisions)}), limiting to {max_trades_per_cycle}")
            # Keep highest confidence trades
            decisions = sorted(decisions, key=lambda x: x.get('confidence_score', 0), reverse=True)
            decisions = decisions[:max_trades_per_cycle]

        # Check individual trade size limits
        max_single_trade = risk_params['MAX_TRADE_USD']
        for decision in decisions:
            if decision['amount_usd'] > max_single_trade:
                print(f"⚠️  {decision['token']} trade size reduced from ${decision['amount_usd']:.2f} to ${max_single_trade:.2f}")
                decision['amount_usd'] = max_single_trade

        return decisions

    def _prioritize_trades(self, decisions: List[Dict]) -> List[Dict]:
        """Prioritize trades for optimal execution order"""
        if len(decisions) <= 1:
            return decisions

        # Calculate priority score for each trade
        for decision in decisions:
            confidence = decision.get('confidence_score', 0)
            amount = decision.get('amount_usd', 0)
            urgency_multiplier = {
                'high': 1.2,
                'medium': 1.0,
                'low': 0.8
            }.get(decision.get('execution_urgency', 'medium'), 1.0)

            # Priority score combines confidence, amount, and urgency
            priority_score = (confidence * 0.6 + (amount / 100) * 0.2) * urgency_multiplier
            decision['priority_score'] = round(priority_score, 3)

        # Sort by priority score (highest first)
        prioritized_decisions = sorted(decisions, key=lambda x: x.get('priority_score', 0), reverse=True)

        print("📊 Trade execution order:")
        for i, decision in enumerate(prioritized_decisions, 1):
            print(f"   {i}. {decision['token']} - Priority: {decision.get('priority_score', 0):.3f} "
                  f"(Confidence: {decision.get('confidence_score', 0):.1%})")

        return prioritized_decisions

    def record_executed_trade(self, decision: Dict, execution_result: Dict):
        """Record an executed trade for tracking"""
        trade_record = {
            'timestamp': datetime.now(),
            'token': decision.get('token'),
            'action': decision.get('action'),
            'amount_usd': decision.get('amount_usd', 0),
            'confidence': decision.get('confidence_score', 0),
            'execution_result': execution_result
        }

        self.executed_trades.append(trade_record)

        # Only count exposure and trades if execution was successful
        trade_executed = execution_result.get('trade_executed', False)
        status = execution_result.get('status', 'ERROR')

        if trade_executed and status == 'SUCCESS':
            self.daily_exposure += decision.get('amount_usd', 0)
            self.daily_trade_count += 1
            print(f"✅ Recorded SUCCESSFUL trade: {trade_record['action']} ${trade_record['amount_usd']:.2f} {trade_record['token']}")
        else:
            print(f"📝 Recorded FAILED trade: {trade_record['action']} ${trade_record['amount_usd']:.2f} {trade_record['token']}")

        print(f"📊 Daily stats: {self.daily_trade_count} successful trades, ${self.daily_exposure:.2f} actual exposure")

    def get_daily_statistics(self) -> Dict:
        """Get daily trading statistics"""
        return {
            'daily_trade_count': self.daily_trade_count,
            'daily_exposure': self.daily_exposure,
            'executed_trades': len(self.executed_trades),
            'last_reset_date': self.last_reset_date
        }

    def _check_daily_reset(self):
        """Reset daily counters if new day"""
        current_date = datetime.now().date()
        if current_date > self.last_reset_date:
            print(f"🗓️  New trading day - resetting counters")
            self.daily_exposure = 0.0
            self.daily_trade_count = 0
            self.last_reset_date = current_date
            # Keep executed_trades for historical tracking

# Global trade manager instance
_trade_manager = None

def get_trade_manager() -> TradeManager:
    """Get global trade manager instance"""
    global _trade_manager
    if _trade_manager is None:
        _trade_manager = TradeManager()
    return _trade_manager