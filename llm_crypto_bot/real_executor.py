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
from multi_router_dex import execute_multi_router_trade, find_token_contract
from bsc_dex_integration import execute_bsc_trade, find_bsc_token_contract
from auditor import audit_contract, is_contract_safe
from whitepaper_analyzer import find_contract_via_research, get_project_legitimacy
from token_intelligence import analyze_token_comprehensive, get_token_contract_address, calculate_smart_position_size
from real_dex_executor import get_real_dex_executor
from profit_maximizer import get_profit_maximizer, motivate_for_maximum_profit
from position_monitor import get_position_monitor, record_position_entry

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
        token = decision_json['token'].upper()

        # Skip HOLD actions
        if action == 'HOLD':
            return self._create_hold_result(decision_json)

        # Prevent meaningless stablecoin-to-stablecoin trades
        stablecoins = ['USDC', 'USDT', 'DAI', 'BUSD', 'FRAX']
        if action == 'BUY' and token in stablecoins:
            return self._create_error_result(f"Skipping meaningless {action} {token} trade (already stablecoin)")

        # Final safety check with user confirmation
        if not self._get_user_confirmation(decision_json):
            return self._create_error_result("Trade cancelled by user")

        # Check risk limits
        risk_check = self._check_risk_limits(decision_json)
        if not risk_check['allowed']:
            return self._create_error_result(risk_check['reason'])

        # 💰 PROFIT MAXIMIZATION: Motivate bot for maximum wealth accumulation
        print(f"\n💰 ACTIVATING PROFIT MAXIMIZATION SYSTEM...")
        try:
            # Get market data for profit analysis
            from connectors.coinmarketcap_api import get_market_data_for_trading
            market_data = get_market_data_for_trading([token])

            # Apply wealth-driven motivation and optimization
            optimized_decision = motivate_for_maximum_profit(decision_json, market_data)
            print(f"🎯 PROFIT-OPTIMIZED DECISION: ${optimized_decision.get('amount_usd', 0):.2f} (was ${decision_json.get('amount_usd', 0):.2f})")

        except Exception as e:
            print(f"⚠️  Profit maximizer error: {e}")
            optimized_decision = decision_json  # Fall back to original decision

        # Execute the real trade with profit optimization
        if action in ['BUY', 'SELL']:
            return self._execute_dex_trade(optimized_decision)
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
        
        # Auto-approve based on confidence and profit motivation
        confidence = decision.get('confidence', 0)
        profit_score = decision.get('profit_score', 5.0)

        # Get profit maximizer status for dynamic approval
        try:
            profit_maximizer = get_profit_maximizer()
            wealth_status = profit_maximizer.get_wealth_status()
            win_streak = wealth_status['consecutive_wins']
            success_rate = wealth_status['success_rate']

            # Dynamic approval threshold based on performance
            if win_streak >= 3 and success_rate >= 60:
                threshold = 0.5  # More aggressive when winning
                print(f"🔥 HOT STREAK MODE: Lowered threshold to 50% (Streak: {win_streak})")
            elif success_rate >= 70:
                threshold = 0.55  # Aggressive when successful
                print(f"💪 HIGH SUCCESS MODE: Threshold 55% (Success: {success_rate:.1f}%)")
            elif profit_score >= 7.0:
                threshold = 0.55  # Aggressive for high-profit opportunities
                print(f"💰 HIGH PROFIT MODE: Threshold 55% (Profit Score: {profit_score:.1f}/10)")
            else:
                threshold = 0.6  # Standard threshold

        except:
            threshold = 0.6  # Fallback

        if confidence >= threshold:
            print(f"✅ AUTO-APPROVED: {confidence:.1%} confidence ≥ {threshold:.1%} threshold")
            print(f"💰 PROFIT MOTIVATION: Bot is hungry for wealth accumulation!")
            return True
        else:
            print(f"❌ REJECTED: {confidence:.1%} confidence < {threshold:.1%} threshold")
            print(f"🛡️  RISK PROTECTION: Preserving capital for better opportunities")
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
            
            # MULTI-CHAIN EXECUTION: Execute trade using best available router
            original_token = decision['token']

            # Step 1: Intelligent token discovery using CoinMarketCap as primary source
            contract_address = None
            selected_chain = None

            print(f"🔍 Intelligent token discovery for {original_token}...")

            # Method 1: CoinMarketCap intelligence (primary and most reliable)
            try:
                print(f"🌟 Checking CoinMarketCap for {original_token}...")
                contract_address = get_token_contract_address(original_token)

                if contract_address:
                    # Determine chain from the contract discovery process
                    selected_chain = 'ethereum'  # Most CMC tokens are on Ethereum

                    # Quick chain detection based on known patterns
                    cmc_intelligence = analyze_token_comprehensive(original_token)
                    platform = cmc_intelligence.get('cmc_data', {}).get('platform', {})
                    if platform:
                        platform_name = platform.get('name', '').lower()
                        if 'binance' in platform_name:
                            selected_chain = 'bsc'
                        elif 'polygon' in platform_name:
                            selected_chain = 'polygon'
                        elif 'ethereum' in platform_name:
                            selected_chain = 'ethereum'
                        elif 'base' in platform_name:
                            selected_chain = 'base'
                        elif 'arbitrum' in platform_name:
                            selected_chain = 'arbitrum'

                    print(f"✅ Found {original_token} on CoinMarketCap: {contract_address} ({selected_chain})")

            except Exception as e:
                print(f"⚠️ CoinMarketCap lookup failed: {e}")

            # Method 2: Fallback to local token lists (for speed and backup)
            if not contract_address:
                print(f"🔄 Fallback: Checking local token lists...")

                # Try Polygon first
                contract_address = find_token_contract(original_token)
                if contract_address:
                    selected_chain = 'polygon'
                    print(f"✅ Found {original_token} on Polygon via token list: {contract_address}")

                # Try BSC if not on Polygon
                if not contract_address:
                    contract_address = find_bsc_token_contract(original_token)
                    if contract_address:
                        selected_chain = 'bsc'
                        print(f"✅ Found {original_token} on BSC via token list: {contract_address}")

            # Method 3: Deep research as last resort (for very new or obscure tokens)
            if not contract_address:
                print(f"📄 Deep research: Analyzing whitepapers and documentation...")

                try:
                    research_address = find_contract_via_research(original_token)
                    if research_address:
                        contract_address = research_address
                        selected_chain = 'bsc'  # Most new tokens launch on BSC first
                        print(f"✅ Found {original_token} via research: {contract_address}")
                except Exception as e:
                    print(f"⚠️ Research failed: {e}")

            # Final check: If no contract found anywhere
            if not contract_address:
                # Special handling for major native tokens that might be wrapped
                native_tokens = {
                    'SOL': 'Solana',
                    'BTC': 'Bitcoin',
                    'ETH': 'Ethereum',
                    'BNB': 'Binance Coin'
                }

                if original_token in native_tokens:
                    return self._create_error_result(
                        f"{original_token} is a native {native_tokens[original_token]} token. "
                        f"Native token trading not yet supported. Use wrapped versions like W{original_token}."
                    )
                else:
                    return self._create_error_result(
                        f"Token {original_token} not found. Searched CoinMarketCap, token lists, and documentation. "
                        f"Token may not exist, be too new, or be on unsupported chains."
                    )

            # Step 2: RISK-ADJUSTED SECURITY ASSESSMENT
            risk_adjustment = self._assess_trading_risk(contract_address, original_token, decision)

            if risk_adjustment['action'] == 'REJECT':
                return self._create_error_result(risk_adjustment['reason'])
            elif risk_adjustment['action'] == 'ADJUST':
                # Adjust trade size based on risk
                original_amount = decision['amount_usd']
                decision['amount_usd'] = risk_adjustment['adjusted_amount']
                print(f"⚖️ Risk adjustment: ${original_amount:.2f} → ${decision['amount_usd']:.2f} ({risk_adjustment['risk_level']})")
                print(f"📝 Reason: {risk_adjustment['reason']}")

            # Determine actual chain for research-found contracts
            if selected_chain == 'research_found':
                # Try to determine chain from contract address or use BSC as default for new tokens
                selected_chain = 'bsc'  # Many new tokens launch on BSC first
                print(f"🔄 Research-found contract, defaulting to BSC for execution")

            # INTELLIGENT CHAIN SELECTION: Override chain if we have better gas availability
            # Many tokens exist on multiple chains, choose based on our balance
            from real_dex_executor import get_real_dex_executor
            dex_executor = get_real_dex_executor()

            # Check gas balance on different chains
            chain_balances = {}
            for chain in ['bsc', 'ethereum', 'polygon']:
                if chain in dex_executor.web3_connections:
                    try:
                        w3 = dex_executor.web3_connections[chain]
                        balance = w3.eth.get_balance(self.wallet_address)
                        balance_eth = w3.from_wei(balance, 'ether')
                        chain_balances[chain] = balance_eth
                    except:
                        chain_balances[chain] = 0

            # If current chain has insufficient gas, try alternatives for common multi-chain tokens
            current_balance = chain_balances.get(selected_chain, 0)

            # Multi-chain token overrides (these exist on multiple chains)
            multi_chain_tokens = {
                'CAKE': 'bsc',     # PancakeSwap native to BSC
                'UNI': 'ethereum',  # Uniswap native to Ethereum
                'MATIC': 'polygon', # Polygon native
                'BNB': 'bsc',      # BSC native
                'AVAX': 'avalanche' # Avalanche native
            }

            if original_token.upper() in multi_chain_tokens:
                preferred_chain = multi_chain_tokens[original_token.upper()]
                preferred_balance = chain_balances.get(preferred_chain, 0)

                # If preferred chain has better balance, switch to it
                if preferred_balance > current_balance and preferred_balance > 0.002:
                    print(f"💡 SMART CHAIN SELECTION: Switching from {selected_chain} to {preferred_chain}")
                    print(f"   {selected_chain.upper()} balance: {current_balance:.6f}")
                    print(f"   {preferred_chain.upper()} balance: {preferred_balance:.6f}")
                    selected_chain = preferred_chain

                    # Update contract address for new chain if needed
                    if preferred_chain == 'bsc' and original_token.upper() == 'CAKE':
                        contract_address = '0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82'  # CAKE on BSC

            # Step 3: Execute trade on selected chain
            token_symbol = original_token

            print(f"🚀 EXECUTING REAL BLOCKCHAIN TRADE: {decision['action']} {token_symbol}")
            print(f"💰 Amount: ${decision['amount_usd']:.2f}")
            print(f"🔗 Chain: {selected_chain}")
            print(f"📍 Contract: {contract_address}")

            # Execute real DEX trade on blockchain
            real_dex = get_real_dex_executor()
            dex_result = real_dex.execute_real_dex_trade(
                action=decision['action'],
                token_symbol=token_symbol,
                amount_usd=decision['amount_usd'],
                contract_address=contract_address,
                chain=selected_chain
            )

            # Check if trade was successful
            if dex_result.get('status') == 'SUCCESS' and dex_result.get('trade_executed'):
                print(f"✅ REAL BLOCKCHAIN TRADE EXECUTED SUCCESSFULLY!")
                print(f"📄 Transaction Hash: {dex_result.get('tx_hash', 'Unknown')}")
                print(f"💎 Portfolio: +${decision['amount_usd']:.2f} {token_symbol}")
                print(f"🔗 Chain: {selected_chain} | Router: {dex_result.get('router', 'Unknown')}")
                print(f"🌐 Block Explorer: {dex_result.get('block_explorer_url', 'N/A')}")
                print("💰 This was a REAL trade with REAL money on the blockchain!")
            else:
                print(f"❌ REAL TRADE FAILED: {dex_result.get('error', 'Unknown error')}")
                print(f"🚫 NO FALLBACK - Trade will be recorded as failed")
                return self._create_error_result(f"Real DEX execution failed: {dex_result.get('error', 'Unknown')}")
            
            if 'error' in dex_result:
                return self._create_error_result(f"DEX trade failed: {dex_result['error']}")
            
            # Create trade result with real blockchain data
            trade_result = {
                'trade_id': trade_id,
                'timestamp': dex_result.get('timestamp', datetime.now().isoformat()),
                'action': decision['action'],
                'token': decision['token'],
                'amount_usd': decision['amount_usd'],
                'confidence': decision['confidence'],
                'reasoning': decision.get('reasoning', decision.get('justification', 'No reasoning provided')),
                'status': dex_result.get('status', 'SUCCESS'),
                'trade_executed': dex_result.get('trade_executed', True),
                'transaction_hash': dex_result.get('tx_hash', 'Unknown'),
                'gas_used': dex_result.get('gas_used', 0),
                'gas_price': dex_result.get('gas_price', 0),
                'router_used': dex_result.get('router', 'Unknown'),
                'wallet_address': self.wallet_address,
                'portfolio_impact': f"{(decision['amount_usd'] / available_balance) * 100:.1f}%",
                'dex_platform': dex_result.get('router', 'Unknown'),
                'network': selected_chain,
                'contract_address': dex_result.get('contract_address', contract_address),
                'block_explorer_url': dex_result.get('block_explorer_url', 'N/A'),
                'execution_note': dex_result.get('execution_note', 'Real blockchain trade executed')
            }
            
            # Log the real trade
            self._log_real_trade(trade_result)

            # Store in history
            self.trade_history.append(trade_result)

            # 💰 RECORD PROFIT PERFORMANCE: Update wealth accumulation tracking
            try:
                profit_maximizer = get_profit_maximizer()
                profit_maximizer.record_trade_result(decision, dex_result)

                # Display wealth status
                wealth_status = profit_maximizer.get_wealth_status()
                print(f"\n💎 WEALTH ACCUMULATION UPDATE:")
                print(f"   • Total Profit: ${wealth_status['total_realized_profits']:,.2f}")
                print(f"   • Success Rate: {wealth_status['success_rate']:.1f}%")
                print(f"   • Win Streak: {wealth_status['consecutive_wins']} trades")
                print(f"   • Risk Appetite: {wealth_status['risk_appetite']:.1%}")

            except Exception as e:
                print(f"⚠️  Error updating profit tracking: {e}")

            # 📍 RECORD POSITION ENTRY: Track position for future sell decisions
            if decision['action'].upper() == 'BUY' and dex_result.get('trade_executed'):
                try:
                    # Calculate entry price from trade data - fix the missing key error
                    entry_price = dex_result.get('execution_price')
                    if not entry_price:
                        # Estimate from current market price
                        from connectors.coinmarketcap_api import get_cmc_api
                        try:
                            cmc = get_cmc_api()
                            quotes = cmc.get_token_quotes([original_token])
                            if original_token in quotes:
                                entry_price = quotes[original_token].get('price', 1)
                            else:
                                entry_price = 1  # Default fallback
                        except:
                            entry_price = 1

                    # Record the position entry for monitoring
                    record_position_entry(
                        token_symbol=original_token,
                        amount_usd=decision['amount_usd'],
                        entry_price=entry_price
                    )

                    print(f"📈 POSITION TRACKING: Recorded BUY entry for {original_token}")

                except Exception as e:
                    print(f"⚠️  Error recording position entry: {e}")
            
            print(f"✅ REAL BLOCKCHAIN TRADE EXECUTED via {dex_result.get('router', 'Unknown DEX').upper()}!")
            print(f"🔗 Block Explorer: {dex_result.get('block_explorer_url', 'N/A')}")
            print(f"📊 Execution Details:")
            print(f"   • Chain: {selected_chain.upper()}")
            print(f"   • DEX Router: {dex_result.get('router', 'Unknown')}")
            print(f"   • Gas Used: {dex_result.get('gas_used', 0):,}")
            print(f"   • Transaction Hash: {dex_result.get('tx_hash', 'Unknown')}")
            print("💰 This was a REAL blockchain transaction using REAL money!")
            print("🔍 You can verify this transaction on the block explorer above!")
            
            return trade_result
            
        except Exception as e:
            return self._create_error_result(f"Trade execution failed: {e}")
    
    def _check_risk_limits(self, decision: Dict) -> Dict:
        """Adaptive risk limits that scale with bot performance and profit motivation"""
        risk_params = config.get_dynamic_risk_params()

        try:
            # Get profit maximizer performance data
            profit_maximizer = get_profit_maximizer()
            wealth_status = profit_maximizer.get_wealth_status()

            success_rate = wealth_status['success_rate']
            win_streak = wealth_status['consecutive_wins']
            risk_appetite = wealth_status['risk_appetite']

            # ADAPTIVE RISK SCALING: Successful bots get higher limits
            base_max = risk_params['MAX_TRADE_USD']

            # Performance multiplier (more aggressive when successful)
            if success_rate >= 80:
                performance_multiplier = 1.5  # 50% increase for exceptional performance
                print(f"🏆 ELITE PERFORMANCE: +50% risk limit (Success: {success_rate:.1f}%)")
            elif success_rate >= 70:
                performance_multiplier = 1.3  # 30% increase for great performance
                print(f"💪 STRONG PERFORMANCE: +30% risk limit (Success: {success_rate:.1f}%)")
            elif success_rate >= 60:
                performance_multiplier = 1.1  # 10% increase for good performance
                print(f"✅ GOOD PERFORMANCE: +10% risk limit (Success: {success_rate:.1f}%)")
            elif success_rate >= 40:
                performance_multiplier = 0.9  # 10% reduction for poor performance
                print(f"⚠️  POOR PERFORMANCE: -10% risk limit (Success: {success_rate:.1f}%)")
            else:
                performance_multiplier = 0.7  # 30% reduction for very poor performance
                print(f"🚨 VERY POOR PERFORMANCE: -30% risk limit (Success: {success_rate:.1f}%)")

            # Win streak bonus
            if win_streak >= 5:
                streak_multiplier = 1.2  # 20% bonus for amazing streak
                print(f"🔥 AMAZING STREAK: +20% bonus (Streak: {win_streak})")
            elif win_streak >= 3:
                streak_multiplier = 1.1  # 10% bonus for good streak
                print(f"🔥 HOT STREAK: +10% bonus (Streak: {win_streak})")
            else:
                streak_multiplier = 1.0

            # Calculate final adaptive limit
            adaptive_max = base_max * performance_multiplier * streak_multiplier * risk_appetite

            print(f"📊 ADAPTIVE RISK CALCULATION:")
            print(f"   • Base Limit: ${base_max:.2f}")
            print(f"   • Performance Multiplier: {performance_multiplier:.1f}x")
            print(f"   • Streak Multiplier: {streak_multiplier:.1f}x")
            print(f"   • Risk Appetite: {risk_appetite:.1f}x")
            print(f"   • Final Limit: ${adaptive_max:.2f}")

        except Exception as e:
            print(f"⚠️  Error in adaptive risk calculation: {e}")
            adaptive_max = risk_params['MAX_TRADE_USD'] * 0.85  # Conservative fallback

        if decision['amount_usd'] > adaptive_max:
            return {
                'allowed': False,
                'reason': f"Trade amount ${decision['amount_usd']:.2f} exceeds adaptive limit ${adaptive_max:.2f}"
            }
        
        # Require moderate confidence for real trades
        if decision.get('confidence', 0) < 0.55:
            return {
                'allowed': False,
                'reason': f"Confidence {decision.get('confidence', 0):.1%} below real trade threshold (55%)"
            }
        
        return {'allowed': True, 'reason': 'Real trade risk checks passed'}
    
    def _map_token_symbol(self, token: str) -> str:
        """Map consensus engine token to tradeable token - accepts any token"""
        # Check if token looks like a contract address
        if len(token) == 42 and token.startswith('0x'):
            print(f"🔗 Using contract address directly: {token}")
            return token

        # Map common token symbols to preferred versions
        token_mapping = {
            'BTC': 'WBTC',
            'ETH': 'WETH',
            'MATIC': 'WMATIC',
            'BITCOIN': 'WBTC',
            'ETHEREUM': 'WETH',
        }

        token_upper = token.upper()

        # First try direct mapping
        if token_upper in token_mapping:
            mapped_token = token_mapping[token_upper]
            print(f"🔄 Token mapping: {token} -> {mapped_token}")
            return mapped_token

        # Then try to find the token in our known list
        supported_tokens = get_supported_tokens()
        if token_upper in supported_tokens:
            return token_upper

        # For unknown tokens, try to find the best trading pair
        # Most liquid pairs are usually with WETH, USDC, or WMATIC
        preferred_pairs = ['WETH', 'USDC', 'WMATIC']

        print(f"🔍 Unknown token {token} - attempting to trade via liquid pairs")

        # Try to trade through most liquid pairs instead of defaulting to USDC
        # This allows us to trade any token that has liquidity with major pairs
        for pair in preferred_pairs:
            if pair in supported_tokens:
                print(f"🔄 Will attempt {token} -> {pair} trade route")
                return token_upper  # Return original token, let DEX handle routing

        # Final fallback - but this should rarely happen now
        print(f"⚠️ No liquid pairs found for {token}, using WETH as intermediate")
        return 'WETH'

    def _assess_trading_risk(self, contract_address: Optional[str], token_symbol: str, decision: Dict) -> Dict:
        """
        Assess trading risk using comprehensive token intelligence
        Returns action: PROCEED/ADJUST/REJECT with reasoning
        """
        original_amount = decision['amount_usd']

        print(f"🧠 COMPREHENSIVE ANALYSIS: Analyzing {token_symbol} with market intelligence...")

        # Use the new comprehensive token intelligence system
        try:
            token_analysis = analyze_token_comprehensive(token_symbol)

            # Extract key metrics
            legitimacy_score = token_analysis['legitimacy_score']
            recommendation = token_analysis['trading_recommendation']
            confidence = token_analysis['confidence_level']
            cmc_data = token_analysis.get('cmc_data', {})
            security_audit = token_analysis.get('security_audit', {})
            red_flags = token_analysis.get('red_flags', [])
            green_flags = token_analysis.get('green_flags', [])

            # Display comprehensive analysis
            print(f"📊 Token Intelligence Results:")
            print(f"   • Token: {cmc_data.get('name', token_symbol)} ({token_symbol})")
            if cmc_data.get('cmc_rank'):
                print(f"   • CMC Rank: #{cmc_data['cmc_rank']}")
            if cmc_data.get('market_cap'):
                print(f"   • Market Cap: ${cmc_data['market_cap']:,.0f}")
            if cmc_data.get('volume_24h'):
                print(f"   • 24h Volume: ${cmc_data['volume_24h']:,.0f}")
            print(f"   • Legitimacy Score: {legitimacy_score}/100")
            print(f"   • Recommendation: {recommendation}")
            print(f"   • Analysis Confidence: {confidence:.1%}")

            if green_flags:
                print(f"   • ✅ Green Flags: {', '.join(green_flags[:3])}" + ("..." if len(green_flags) > 3 else ""))
            if red_flags:
                print(f"   • ⚠️ Red Flags: {', '.join(red_flags[:3])}" + ("..." if len(red_flags) > 3 else ""))

            # Check for honeypot (absolute deal breaker)
            is_honeypot = False
            if security_audit.get('risk_assessment', {}).get('honeypot_detected', False):
                is_honeypot = True
            if any('honeypot' in flag.lower() for flag in red_flags):
                is_honeypot = True

            if is_honeypot:
                return {
                    'action': 'REJECT',
                    'risk_level': 'CRITICAL',
                    'adjusted_amount': 0,
                    'reason': f'HONEYPOT DETECTED: {token_symbol} cannot be sold after purchase'
                }

            # Use smart position sizing based on comprehensive analysis
            # Pass LLM confidence from decision to help with unlisted token sizing
            llm_confidence = decision.get('confidence', decision.get('confidence_score', None))
            adjusted_amount, sizing_reason = calculate_smart_position_size(token_symbol, original_amount, llm_confidence)

            # Determine action based on adjusted amount
            if adjusted_amount == 0:
                return {
                    'action': 'REJECT',
                    'risk_level': 'CRITICAL',
                    'adjusted_amount': 0,
                    'reason': sizing_reason
                }
            elif adjusted_amount < original_amount:
                reduction = ((original_amount - adjusted_amount) / original_amount) * 100
                return {
                    'action': 'ADJUST',
                    'risk_level': recommendation,
                    'adjusted_amount': adjusted_amount,
                    'reason': f'{sizing_reason} (Reduced by {reduction:.0f}% for risk management)'
                }
            else:
                return {
                    'action': 'PROCEED',
                    'risk_level': recommendation,
                    'adjusted_amount': adjusted_amount,
                    'reason': f'{sizing_reason} (Full position approved)'
                }

        except Exception as e:
            print(f"❌ Error in comprehensive analysis: {e}")
            print(f"⚠️ Falling back to conservative position sizing...")

            # Fallback to conservative sizing if analysis fails
            return {
                'action': 'ADJUST',
                'risk_level': 'HIGH',
                'adjusted_amount': original_amount * 0.15,  # 15% of original
                'reason': f'Analysis error - using conservative 15% position for safety'
            }

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