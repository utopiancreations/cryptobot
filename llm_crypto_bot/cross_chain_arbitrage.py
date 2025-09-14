"""
Cross-Chain Arbitrage Detection and Execution
Identifies price differences between Polygon and BSC for profitable opportunities
"""

import asyncio
import time
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
import requests
from multi_router_dex import multi_router
from bsc_dex_integration import bsc_trader

class CrossChainArbitrage:
    """Cross-chain arbitrage detection and execution system"""

    def __init__(self):
        self.supported_tokens = self._get_cross_chain_tokens()
        self.min_profit_threshold = 0.02  # 2% minimum profit after fees
        self.max_trade_size_usd = 1000  # Max $1000 per arbitrage trade
        self.arbitrage_history: List[Dict] = []

    def _get_cross_chain_tokens(self) -> List[str]:
        """Get tokens that exist on both Polygon and BSC"""
        return [
            'USDT',   # Most liquid stablecoin on both chains
            'USDC',   # Good liquidity on both
            'ETH',    # Wrapped ETH exists on both
            'BTC',    # Wrapped BTC exists on both (WBTC vs BTCB)
            'MATIC',  # MATIC exists on BSC as well
            'BNB',    # BNB exists on Polygon through bridges
            'LINK',   # Chainlink token on both
            'UNI',    # Uniswap token bridged to both
            'AAVE',   # AAVE protocol token on both
            'COMP',   # Compound token on both
            'YFI',    # Yearn Finance on both
            'MKR',    # Maker DAO on both
            'SNX',    # Synthetix on both
            'CRV',    # Curve DAO on both
            'SUSHI',  # SushiSwap native to both
            'DOGE',   # Dogecoin wrapped on both
            'SHIB',   # Shiba Inu popular on both
            'AXS',    # Axie Infinity popular in Asia (both chains)
        ]

    async def scan_arbitrage_opportunities(self) -> List[Dict]:
        """
        Scan for arbitrage opportunities between Polygon and BSC
        Returns list of profitable opportunities
        """
        opportunities = []

        print("🔍 Scanning cross-chain arbitrage opportunities...")

        for token in self.supported_tokens:
            try:
                # Get prices on both chains simultaneously
                polygon_price = await self._get_polygon_price(token)
                bsc_price = await self._get_bsc_price(token)

                if polygon_price and bsc_price and polygon_price > 0 and bsc_price > 0:
                    opportunity = self._analyze_arbitrage_opportunity(
                        token, polygon_price, bsc_price
                    )

                    if opportunity and opportunity['profit_percentage'] >= self.min_profit_threshold:
                        opportunities.append(opportunity)
                        print(f"💰 Arbitrage opportunity: {token} - {opportunity['profit_percentage']:.2%} profit")

            except Exception as e:
                print(f"⚠️ Error scanning {token}: {e}")
                continue

        # Sort by profit percentage descending
        opportunities.sort(key=lambda x: x['profit_percentage'], reverse=True)

        print(f"✅ Found {len(opportunities)} arbitrage opportunities")
        return opportunities[:3]  # Return top 3 opportunities

    async def _get_polygon_price(self, token: str) -> Optional[float]:
        """Get token price on Polygon"""
        try:
            # Use our multi-router system to get quote for $100 worth
            test_amount = 100.0
            route = multi_router.get_best_route('USDC', token, test_amount)

            if route and route['expected_output'] > 0:
                # Price per token = input amount / output tokens
                price_per_token = test_amount / route['expected_output']
                return price_per_token

            return None

        except Exception as e:
            print(f"⚠️ Polygon price error for {token}: {e}")
            return None

    async def _get_bsc_price(self, token: str) -> Optional[float]:
        """Get token price on BSC"""
        try:
            # Use BSC trader to get quote for $100 worth
            test_amount = 100.0
            route = bsc_trader.get_best_bsc_route('BUSD', token, test_amount)

            if route and route['expected_output'] > 0:
                # Price per token = input amount / output tokens
                price_per_token = test_amount / route['expected_output']
                return price_per_token

            return None

        except Exception as e:
            print(f"⚠️ BSC price error for {token}: {e}")
            return None

    def _analyze_arbitrage_opportunity(self, token: str, polygon_price: float, bsc_price: float) -> Optional[Dict]:
        """Analyze if there's a profitable arbitrage opportunity"""

        if not polygon_price or not bsc_price:
            return None

        # Calculate price difference
        price_diff = abs(polygon_price - bsc_price)
        cheaper_chain = 'polygon' if polygon_price < bsc_price else 'bsc'
        expensive_chain = 'bsc' if cheaper_chain == 'polygon' else 'polygon'

        cheaper_price = min(polygon_price, bsc_price)
        expensive_price = max(polygon_price, bsc_price)

        # Calculate profit percentage (before fees)
        gross_profit_pct = (expensive_price - cheaper_price) / cheaper_price

        # Estimate total fees
        # Cross-chain bridge fees + DEX fees + gas fees
        estimated_fees_pct = self._estimate_arbitrage_fees(cheaper_chain, expensive_chain)

        # Net profit after fees
        net_profit_pct = gross_profit_pct - estimated_fees_pct

        # Calculate optimal trade size
        optimal_trade_size = min(
            self.max_trade_size_usd,
            self._calculate_optimal_trade_size(token, net_profit_pct)
        )

        if net_profit_pct <= self.min_profit_threshold:
            return None

        return {
            'token': token,
            'polygon_price': polygon_price,
            'bsc_price': bsc_price,
            'buy_on': cheaper_chain,
            'sell_on': expensive_chain,
            'gross_profit_percentage': gross_profit_pct,
            'estimated_fees_percentage': estimated_fees_pct,
            'profit_percentage': net_profit_pct,
            'optimal_trade_size_usd': optimal_trade_size,
            'estimated_profit_usd': optimal_trade_size * net_profit_pct,
            'confidence_score': self._calculate_arbitrage_confidence(token, net_profit_pct),
            'time_sensitivity': 'HIGH',  # Arbitrage opportunities are time-sensitive
            'execution_complexity': 'HIGH',  # Cross-chain requires multiple steps
            'timestamp': time.time()
        }

    def _estimate_arbitrage_fees(self, chain1: str, chain2: str) -> float:
        """Estimate total fees for cross-chain arbitrage"""

        # DEX fees (both chains)
        dex_fees = 0.003 + 0.003  # 0.3% on each chain

        # Gas fees
        if chain1 == 'polygon' or chain2 == 'polygon':
            gas_fees_usd = 0.01  # Polygon gas ~$0.01
        if chain1 == 'bsc' or chain2 == 'bsc':
            gas_fees_usd += 0.003  # BSC gas ~$0.003

        # Cross-chain bridge fees (estimated)
        bridge_fees_pct = 0.001  # ~0.1% bridge fee

        # Slippage (estimated)
        slippage_pct = 0.005  # 0.5% slippage

        # Total fees as percentage
        total_fees_pct = dex_fees + bridge_fees_pct + slippage_pct

        return total_fees_pct

    def _calculate_optimal_trade_size(self, token: str, profit_pct: float) -> float:
        """Calculate optimal trade size based on liquidity and profit"""

        base_size = 100.0  # Start with $100

        # Increase size for higher profit opportunities
        if profit_pct > 0.05:  # > 5% profit
            base_size = 500.0
        elif profit_pct > 0.03:  # > 3% profit
            base_size = 300.0

        # Adjust for token liquidity (major tokens can handle larger sizes)
        major_tokens = ['USDT', 'USDC', 'ETH', 'BTC', 'BNB', 'MATIC']
        if token in major_tokens:
            base_size *= 2

        return min(base_size, self.max_trade_size_usd)

    def _calculate_arbitrage_confidence(self, token: str, profit_pct: float) -> float:
        """Calculate confidence score for arbitrage opportunity"""

        confidence = 0.5  # Base confidence 50%

        # Higher profit = higher confidence
        if profit_pct > 0.05:
            confidence += 0.3
        elif profit_pct > 0.03:
            confidence += 0.2
        elif profit_pct > 0.02:
            confidence += 0.1

        # Major tokens = higher confidence
        major_tokens = ['USDT', 'USDC', 'ETH', 'BTC', 'BNB']
        if token in major_tokens:
            confidence += 0.2

        return min(confidence, 0.95)  # Cap at 95%

    def execute_arbitrage(self, opportunity: Dict) -> Dict:
        """
        Execute cross-chain arbitrage opportunity
        This is complex and requires bridge integration
        """

        print(f"🚀 Executing arbitrage: {opportunity['token']} ({opportunity['profit_percentage']:.2%})")

        try:
            # Step 1: Buy on cheaper chain
            buy_chain = opportunity['buy_on']
            sell_chain = opportunity['sell_on']
            token = opportunity['token']
            trade_size = opportunity['optimal_trade_size_usd']

            print(f"1️⃣ Buying ${trade_size:.2f} of {token} on {buy_chain}")

            if buy_chain == 'polygon':
                buy_result = multi_router.execute_best_swap('BUY', token, trade_size)
            else:  # BSC
                buy_result = bsc_trader.execute_bsc_swap('BUY', token, trade_size)

            if 'error' in buy_result:
                return {'error': f'Buy failed on {buy_chain}: {buy_result["error"]}', 'status': 'FAILED'}

            # Step 2: Bridge tokens (simplified - in production needs actual bridge)
            print(f"2️⃣ Bridging {token} from {buy_chain} to {sell_chain}")
            bridge_result = self._simulate_bridge(buy_result, buy_chain, sell_chain)

            if 'error' in bridge_result:
                return {'error': f'Bridge failed: {bridge_result["error"]}', 'status': 'FAILED'}

            # Step 3: Sell on expensive chain
            print(f"3️⃣ Selling {token} on {sell_chain}")

            if sell_chain == 'polygon':
                sell_result = multi_router.execute_best_swap('SELL', token, trade_size)
            else:  # BSC
                sell_result = bsc_trader.execute_bsc_swap('SELL', token, trade_size)

            if 'error' in sell_result:
                return {'error': f'Sell failed on {sell_chain}: {sell_result["error"]}', 'status': 'FAILED'}

            # Calculate actual profit
            actual_profit = self._calculate_actual_profit(buy_result, sell_result, opportunity)

            result = {
                'status': 'SUCCESS',
                'token': token,
                'buy_chain': buy_chain,
                'sell_chain': sell_chain,
                'trade_size_usd': trade_size,
                'expected_profit_usd': opportunity['estimated_profit_usd'],
                'actual_profit_usd': actual_profit,
                'buy_tx': buy_result.get('tx_hash'),
                'sell_tx': sell_result.get('tx_hash'),
                'execution_time': time.time() - opportunity['timestamp'],
                'arbitrage_id': f"ARB_{int(time.time())}"
            }

            # Record arbitrage
            self.arbitrage_history.append(result)

            print(f"✅ Arbitrage completed! Profit: ${actual_profit:.2f}")
            return result

        except Exception as e:
            error_result = {
                'status': 'ERROR',
                'error': f'Arbitrage execution failed: {e}',
                'token': opportunity['token']
            }
            print(f"❌ Arbitrage failed: {e}")
            return error_result

    def _simulate_bridge(self, buy_result: Dict, from_chain: str, to_chain: str) -> Dict:
        """
        Simulate cross-chain bridge (in production, integrate with actual bridges)
        """
        # This is a simplified simulation
        # Real implementation would use bridges like:
        # - Polygon Bridge for MATIC/ETH
        # - Binance Bridge for BNB
        # - Multichain/Anyswap for various tokens
        # - LayerZero for omnichain tokens

        bridge_fee = 0.001  # 0.1% bridge fee
        bridge_time = 300   # 5 minutes estimated

        return {
            'status': 'SUCCESS',
            'bridge_fee_percentage': bridge_fee,
            'estimated_time_seconds': bridge_time,
            'bridge_provider': 'Simulated Bridge',
            'bridge_tx': f'0xbridge{int(time.time())}'
        }

    def _calculate_actual_profit(self, buy_result: Dict, sell_result: Dict, opportunity: Dict) -> float:
        """Calculate actual profit from arbitrage execution"""

        buy_amount = buy_result.get('amount_out', 0)
        sell_amount = sell_result.get('amount_out', 0)
        trade_size = opportunity['optimal_trade_size_usd']

        # Simplified profit calculation
        profit_percentage = (sell_amount - trade_size) / trade_size
        actual_profit_usd = trade_size * profit_percentage

        return actual_profit_usd

    def get_arbitrage_statistics(self) -> Dict:
        """Get arbitrage trading statistics"""

        if not self.arbitrage_history:
            return {'message': 'No arbitrage trades executed yet'}

        successful_trades = [t for t in self.arbitrage_history if t['status'] == 'SUCCESS']
        total_profit = sum(t['actual_profit_usd'] for t in successful_trades)
        total_volume = sum(t['trade_size_usd'] for t in self.arbitrage_history)

        return {
            'total_arbitrage_trades': len(self.arbitrage_history),
            'successful_trades': len(successful_trades),
            'success_rate': len(successful_trades) / len(self.arbitrage_history) * 100,
            'total_profit_usd': total_profit,
            'total_volume_usd': total_volume,
            'average_profit_per_trade': total_profit / len(successful_trades) if successful_trades else 0,
            'most_profitable_token': self._get_most_profitable_token(),
            'best_chain_pair': self._get_best_chain_pair()
        }

    def _get_most_profitable_token(self) -> str:
        """Get most profitable token for arbitrage"""
        if not self.arbitrage_history:
            return 'N/A'

        token_profits = {}
        for trade in self.arbitrage_history:
            if trade['status'] == 'SUCCESS':
                token = trade['token']
                token_profits[token] = token_profits.get(token, 0) + trade['actual_profit_usd']

        if token_profits:
            return max(token_profits, key=token_profits.get)
        return 'N/A'

    def _get_best_chain_pair(self) -> str:
        """Get most profitable chain pair combination"""
        if not self.arbitrage_history:
            return 'N/A'

        pair_profits = {}
        for trade in self.arbitrage_history:
            if trade['status'] == 'SUCCESS':
                pair = f"{trade['buy_chain']} → {trade['sell_chain']}"
                pair_profits[pair] = pair_profits.get(pair, 0) + trade['actual_profit_usd']

        if pair_profits:
            return max(pair_profits, key=pair_profits.get)
        return 'N/A'

# Global arbitrage instance
cross_chain_arbitrage = CrossChainArbitrage()

async def scan_arbitrage_opportunities() -> List[Dict]:
    """Scan for cross-chain arbitrage opportunities"""
    return await cross_chain_arbitrage.scan_arbitrage_opportunities()

def execute_arbitrage_opportunity(opportunity: Dict) -> Dict:
    """Execute a cross-chain arbitrage opportunity"""
    return cross_chain_arbitrage.execute_arbitrage(opportunity)

def get_arbitrage_stats() -> Dict:
    """Get arbitrage trading statistics"""
    return cross_chain_arbitrage.get_arbitrage_statistics()

def get_supported_arbitrage_tokens() -> List[str]:
    """Get tokens supported for cross-chain arbitrage"""
    return cross_chain_arbitrage.supported_tokens