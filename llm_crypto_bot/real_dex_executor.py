"""
Real DEX Executor - Actual Blockchain Trading
Executes real transactions on multiple DEX protocols across different chains
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from web3 import Web3
try:
    from web3.middleware import geth_poa_middleware
except ImportError:
    try:
        from web3.middleware.geth_poa import geth_poa_middleware
    except ImportError:
        # For newer Web3 versions that don't need POA middleware
        geth_poa_middleware = None
import config

class RealDEXExecutor:
    """Real blockchain DEX trading executor"""

    def __init__(self):
        self.web3_connections = {}
        self.router_abis = {}
        self.token_abis = {}
        self._initialize_chains()

        # DEX Router Contracts by Chain
        self.dex_routers = {
            'ethereum': {
                'uniswap_v3': '0xE592427A0AEce92De3Edee1F18E0157C05861564',
                'uniswap_v2': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
                'sushiswap': '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F'
            },
            'bsc': {
                'pancakeswap_v3': '0x13f4EA83D0bd40E75C8222255bc855a974568Dd4',
                'pancakeswap_v2': '0x10ED43C718714eb63d5aA57B78B54704E256024E',
                'biswap': '0x3a6d8cA21D1CF76F653A67577FA0D27453350dD8'
            },
            'polygon': {
                'quickswap': '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff',
                'sushiswap': '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506'
            },
            'base': {
                'baseswap': '0x327Df1E6de05895d2ab08513aaDD9313Fe505d86',
                'aerodrome': '0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43'
            },
            'arbitrum': {
                'sushiswap': '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506',
                'uniswap_v3': '0xE592427A0AEce92De3Edee1F18E0157C05861564'
            }
        }

    def _initialize_chains(self):
        """Initialize Web3 connections for all supported chains"""
        for chain, rpc_url in config.CHAIN_RPC_URLS.items():
            try:
                w3 = Web3(Web3.HTTPProvider(rpc_url))

                # Add PoA middleware for BSC and other PoA chains (if available)
                if chain in ['bsc', 'polygon'] and geth_poa_middleware is not None:
                    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

                if w3.is_connected():
                    self.web3_connections[chain] = w3
                    print(f"✅ Connected to {chain.upper()} blockchain")
                else:
                    print(f"❌ Failed to connect to {chain.upper()} blockchain")

            except Exception as e:
                print(f"❌ Error connecting to {chain}: {e}")

        self._load_abis()

    def _load_abis(self):
        """Load essential ABIs for DEX trading"""
        # Uniswap V2 Router ABI (simplified)
        self.router_abis['uniswap_v2'] = [
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                    {"internalType": "address[]", "name": "path", "type": "address[]"},
                    {"internalType": "address", "name": "to", "type": "address"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"}
                ],
                "name": "swapExactTokensForTokens",
                "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                    {"internalType": "address[]", "name": "path", "type": "address[]"},
                    {"internalType": "address", "name": "to", "type": "address"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"}
                ],
                "name": "swapExactETHForTokens",
                "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
                "stateMutability": "payable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                    {"internalType": "address[]", "name": "path", "type": "address[]"},
                    {"internalType": "address", "name": "to", "type": "address"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"}
                ],
                "name": "swapExactTokensForETH",
                "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "address[]", "name": "path", "type": "address[]"}
                ],
                "name": "getAmountsOut",
                "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]

        # ERC-20 Token ABI (simplified)
        self.token_abis['erc20'] = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": False,
                "inputs": [
                    {"name": "_spender", "type": "address"},
                    {"name": "_value", "type": "uint256"}
                ],
                "name": "approve",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [
                    {"name": "_owner", "type": "address"},
                    {"name": "_spender", "type": "address"}
                ],
                "name": "allowance",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "type": "function"
            }
        ]

    def execute_real_dex_trade(self, action: str, token_symbol: str, amount_usd: float,
                              contract_address: str, chain: str) -> Dict:
        """Execute real DEX trade on blockchain"""
        try:
            print(f"🚀 EXECUTING REAL {action} TRADE: {token_symbol} on {chain.upper()}")
            print(f"💰 Amount: ${amount_usd:.2f}")
            print(f"📍 Contract: {contract_address}")

            # Get Web3 connection for chain
            if chain not in self.web3_connections:
                return self._create_error_result(f"Chain {chain} not supported")

            w3 = self.web3_connections[chain]

            # Get wallet info
            wallet_address = Web3.to_checksum_address(config.WALLET_ADDRESS)
            private_key = config.PRIVATE_KEY

            if not wallet_address or not private_key:
                return self._create_error_result("Wallet not configured")

            # CHECK GAS BALANCE FIRST
            gas_balance = w3.eth.get_balance(wallet_address)
            gas_balance_eth = w3.from_wei(gas_balance, 'ether')

            print(f"⛽ Gas Balance: {gas_balance_eth:.6f} {self._get_native_symbol(chain)}")

            if gas_balance_eth < 0.001:  # Need at least 0.001 ETH/BNB for gas
                return self._create_error_result(f"Insufficient gas: {gas_balance_eth:.6f} {self._get_native_symbol(chain)} < 0.001 minimum")

            # Select best DEX for this chain
            best_router = self._select_best_router(chain, token_symbol)
            if not best_router:
                return self._create_error_result(f"No DEX router available for {chain}")

            router_address = best_router['address']
            router_name = best_router['name']

            print(f"🎯 Selected DEX: {router_name}")

            # Get router contract
            router_contract = w3.eth.contract(
                address=Web3.to_checksum_address(router_address),
                abi=self.router_abis['uniswap_v2']  # Most DEXs use Uniswap V2 compatible interface
            )

            # For BUY orders, use native ETH/BNB directly (no approval needed)
            if action.upper() == 'BUY':
                print(f"🔄 BUY Trade: Using native {self._get_native_symbol(chain)} to buy {token_symbol}")

                # Convert USD to native token amount with better price estimates
                if chain == 'bsc':
                    native_amount_eth = amount_usd / 600  # BNB ~$600
                elif chain == 'ethereum':
                    native_amount_eth = amount_usd / 3000  # ETH ~$3000
                elif chain == 'polygon':
                    native_amount_eth = amount_usd / 0.85  # MATIC ~$0.85
                else:
                    native_amount_eth = amount_usd / 2500  # Default estimate

                native_amount_wei = w3.to_wei(native_amount_eth, 'ether')

                print(f"💱 Trade Conversion: ${amount_usd:.2f} → {native_amount_eth:.6f} {self._get_native_symbol(chain)}")

                # Check minimum trade size (avoid dust trades)
                if native_amount_wei < w3.to_wei(0.0001, 'ether'):  # Minimum 0.0001 native token
                    return self._create_error_result(f"Trade too small: {native_amount_eth:.6f} {self._get_native_symbol(chain)} < 0.0001 minimum")

                # Check we have enough native token (including gas buffer)
                # Use dynamic gas buffer based on chain (Ethereum needs more, BSC/Polygon need less)
                if chain in ['ethereum', 'base', 'arbitrum']:
                    gas_buffer = w3.to_wei(0.003, 'ether')  # 0.003 ETH for Ethereum-based chains
                else:
                    gas_buffer = w3.to_wei(0.001, 'ether')  # 0.001 for BSC, Polygon (cheaper gas)

                if native_amount_wei + gas_buffer > gas_balance:
                    available_for_trade = max(0, gas_balance - gas_buffer)
                    native_price = 600 if chain == 'bsc' else 3000  # Estimate native token price
                    available_usd = w3.from_wei(available_for_trade, 'ether') * native_price
                    gas_buffer_eth = w3.from_wei(gas_buffer, 'ether')
                    return self._create_error_result(f"Insufficient balance: need {native_amount_eth:.6f} + {gas_buffer_eth:.3f} gas, have {gas_balance_eth:.6f}. Max trade: ${available_usd:.2f}")

                # Execute ETH->Token swap (no approval needed)
                swap_result = self._execute_eth_to_token_swap(
                    w3, router_contract, contract_address,
                    native_amount_wei, wallet_address, private_key
                )
            else:
                # For SELL orders, use token->ETH swap (approval needed)
                print(f"🔄 SELL Trade: {token_symbol} to native {self._get_native_symbol(chain)}")
                return self._create_error_result("SELL trades not yet implemented - focusing on BUY first")

            if swap_result['success']:
                # Estimate execution price (for position tracking)
                native_price = 600 if chain == 'bsc' else 3000  # Estimate
                execution_price = native_price / (amount_usd / native_amount_eth)  # Rough estimate

                return {
                    'status': 'SUCCESS',
                    'trade_executed': True,
                    'tx_hash': swap_result['tx_hash'],
                    'amount_usd': amount_usd,
                    'token_symbol': token_symbol,
                    'contract_address': contract_address,
                    'chain': chain,
                    'router': router_name,
                    'gas_used': swap_result.get('gas_used', 0),
                    'gas_price': swap_result.get('gas_price', 0),
                    'execution_price': execution_price,  # Add execution price for position tracking
                    'timestamp': datetime.now().isoformat(),
                    'execution_note': f'Real DEX trade executed on {chain} via {router_name}',
                    'block_explorer_url': self._get_block_explorer_url(chain, swap_result['tx_hash'])
                }
            else:
                return self._create_error_result(f"Swap execution failed: {swap_result['error']}")

        except Exception as e:
            return self._create_error_result(f"Real DEX trade failed: {str(e)}")

    def _select_best_router(self, chain: str, token_symbol: str) -> Optional[Dict]:
        """Select best DEX router for the chain and token"""
        if chain not in self.dex_routers:
            return None

        routers = self.dex_routers[chain]

        # Priority selection - Use V2 routers for better compatibility
        priority_order = {
            'ethereum': ['uniswap_v2', 'sushiswap', 'uniswap_v3'],
            'bsc': ['pancakeswap_v2', 'biswap', 'pancakeswap_v3'],
            'polygon': ['quickswap', 'sushiswap'],
            'base': ['baseswap', 'aerodrome'],
            'arbitrum': ['sushiswap', 'uniswap_v3']
        }

        for router_name in priority_order.get(chain, routers.keys()):
            if router_name in routers:
                return {
                    'name': router_name,
                    'address': routers[router_name]
                }

        # Fallback to first available
        if routers:
            first_router = list(routers.keys())[0]
            return {
                'name': first_router,
                'address': routers[first_router]
            }

        return None

    def _get_buy_pair(self, chain: str, token_contract: str) -> Tuple[str, str]:
        """Get token pair for buy operation - use native tokens for simplicity"""

        # For now, use native token (ETH/BNB) to buy tokens directly
        # This avoids stablecoin balance issues
        native_tokens = {
            'ethereum': '0x0000000000000000000000000000000000000000',  # ETH
            'bsc': '0x0000000000000000000000000000000000000000',      # BNB
            'polygon': '0x0000000000000000000000000000000000000000',   # MATIC
            'arbitrum': '0x0000000000000000000000000000000000000000',  # ETH
            'optimism': '0x0000000000000000000000000000000000000000',  # ETH
            'base': '0x0000000000000000000000000000000000000000',      # ETH
            'avalanche': '0x0000000000000000000000000000000000000000'  # AVAX
        }

        # Use wrapped version for actual contract calls
        wrapped_natives = {
            'ethereum': config.CHAIN_TOKEN_CONTRACTS['ethereum']['WETH'],
            'bsc': config.CHAIN_TOKEN_CONTRACTS['bsc']['WBNB'],
            'polygon': config.CHAIN_TOKEN_CONTRACTS['polygon']['WMATIC'],
            'arbitrum': config.CHAIN_TOKEN_CONTRACTS['arbitrum']['WETH'],
            'base': '0x4200000000000000000000000000000000000006',  # WETH on Base
        }

        token_in = wrapped_natives.get(chain, wrapped_natives['ethereum'])
        token_out = Web3.to_checksum_address(token_contract)

        return token_in, token_out

    def _get_sell_pair(self, chain: str, token_contract: str) -> Tuple[str, str]:
        """Get token pair for sell operation (token -> stablecoin)"""
        # Use primary stablecoin for each chain
        stablecoins = {
            'ethereum': config.CHAIN_TOKEN_CONTRACTS['ethereum']['USDC'],
            'bsc': config.CHAIN_TOKEN_CONTRACTS['bsc']['BUSD'],
            'polygon': config.CHAIN_TOKEN_CONTRACTS['polygon']['USDC'],
            'base': config.CHAIN_TOKEN_CONTRACTS['base']['USDC'],
            'arbitrum': config.CHAIN_TOKEN_CONTRACTS['arbitrum']['USDC']
        }

        token_in = Web3.to_checksum_address(token_contract)
        token_out = stablecoins.get(chain, stablecoins['ethereum'])

        return token_in, token_out

    def _calculate_trade_amounts(self, w3: Web3, token_in: str, token_out: str,
                               amount_usd: float, trade_type: str) -> Optional[Dict]:
        """Calculate trade amounts with slippage protection"""
        try:
            # For simplification, we'll use the amount_usd directly
            # In production, you'd want to:
            # 1. Get token decimals
            # 2. Get current token prices
            # 3. Calculate exact token amounts
            # 4. Add slippage protection (1-3%)

            if trade_type == "buy":
                # Convert USD to token amount (simplified)
                amount_in = int(amount_usd * 1e6)  # Assuming USDC (6 decimals)
                amount_out_min = int(amount_usd * 0.97 * 1e18)  # 3% slippage, assuming 18 decimals
            else:  # sell
                # This would require getting current token balance and price
                amount_in = int(amount_usd * 1e18)  # Assuming 18 decimals
                amount_out_min = int(amount_usd * 0.97 * 1e6)  # 3% slippage, USDC

            return {
                'amount_in': amount_in,
                'amount_out_min': amount_out_min
            }

        except Exception as e:
            print(f"❌ Error calculating trade amounts: {e}")
            return None

    def _handle_token_approval(self, w3: Web3, token_address: str, router_address: str,
                             amount: int, wallet_address: str, private_key: str) -> Dict:
        """Handle ERC-20 token approval for DEX router"""
        try:
            # Validate contract address format
            if not token_address or len(token_address) != 42:
                return {'success': False, 'error': 'Invalid token contract address'}

            # Get token contract
            token_contract = w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=self.token_abis['erc20']
            )

            # Validate contract exists
            try:
                # Try to call a view function to verify contract exists
                token_contract.functions.decimals().call()
            except Exception as e:
                return {'success': False, 'error': f'Contract not found or invalid: {e}'}

            # Check current allowance
            current_allowance = token_contract.functions.allowance(
                wallet_address, router_address
            ).call()

            if current_allowance >= amount:
                print("✅ Token already approved")
                return {'success': True}

            # Build approval transaction
            nonce = w3.eth.get_transaction_count(wallet_address)
            gas_price = w3.eth.gas_price

            approve_txn = token_contract.functions.approve(
                router_address, amount
            ).build_transaction({
                'from': wallet_address,
                'gas': 100000,
                'gasPrice': gas_price,
                'nonce': nonce
            })

            # Sign and send approval
            signed_txn = w3.eth.account.sign_transaction(approve_txn, private_key)
            approval_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)

            # Wait for confirmation
            receipt = w3.eth.wait_for_transaction_receipt(approval_hash, timeout=300)

            if receipt['status'] == 1:
                print(f"✅ Token approved: {approval_hash.hex()}")
                return {'success': True}
            else:
                return {'success': False, 'error': 'Approval transaction failed'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _execute_swap(self, w3: Web3, router_contract, token_in: str, token_out: str,
                     amount_in: int, amount_out_min: int, wallet_address: str, private_key: str) -> Dict:
        """Execute the actual swap transaction"""
        try:
            # Build swap transaction
            nonce = w3.eth.get_transaction_count(wallet_address)
            gas_price = w3.eth.gas_price
            deadline = int(time.time()) + 300  # 5 minutes

            path = [Web3.to_checksum_address(token_in), Web3.to_checksum_address(token_out)]

            swap_txn = router_contract.functions.swapExactTokensForTokens(
                amount_in,
                amount_out_min,
                path,
                wallet_address,
                deadline
            ).build_transaction({
                'from': wallet_address,
                'gas': 300000,
                'gasPrice': gas_price,
                'nonce': nonce
            })

            # Sign and send transaction
            signed_txn = w3.eth.account.sign_transaction(swap_txn, private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)

            print(f"📡 Transaction sent: {tx_hash.hex()}")

            # Wait for confirmation
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)

            if receipt['status'] == 1:
                print(f"✅ Swap successful!")
                return {
                    'success': True,
                    'tx_hash': tx_hash.hex(),
                    'gas_used': receipt['gasUsed'],
                    'gas_price': gas_price
                }
            else:
                return {'success': False, 'error': 'Swap transaction failed'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _execute_eth_to_token_swap(self, w3: Web3, router_contract, token_address: str,
                                  native_amount_wei: int, wallet_address: str, private_key: str) -> Dict:
        """Execute ETH/BNB to Token swap using swapExactETHForTokens"""
        try:
            # Path: Native -> Token - get correct wrapped token address first
            wrapped_addresses = {
                'ethereum': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',  # WETH
                'bsc': '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c',      # WBNB
                'polygon': '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270',   # WMATIC
                'arbitrum': '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',  # WETH
                'base': '0x4200000000000000000000000000000000000006',      # WETH
                'avalanche': '0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7'  # WAVAX
            }

            # Detect chain from Web3 provider
            chain_id = w3.eth.chain_id
            chain_map = {1: 'ethereum', 56: 'bsc', 137: 'polygon', 42161: 'arbitrum', 8453: 'base', 43114: 'avalanche'}
            detected_chain = chain_map.get(chain_id, 'ethereum')

            weth_address = wrapped_addresses.get(detected_chain, wrapped_addresses['ethereum'])

            print(f"🔄 Executing native token swap: {w3.from_wei(native_amount_wei, 'ether'):.6f} -> {token_address[:10]}...")
            print(f"📍 Trading Path: {weth_address[:10]}... -> {token_address[:10]}...")
            print(f"⚙️  Chain ID: {chain_id} ({detected_chain})")

            path = [weth_address, Web3.to_checksum_address(token_address)]

            # Build swap transaction - swapExactETHForTokens
            nonce = w3.eth.get_transaction_count(wallet_address)
            gas_price = w3.eth.gas_price
            deadline = int(time.time()) + 300  # 5 minutes

            # Minimum tokens out (with generous slippage for volatile tokens)
            amount_out_min = 0  # Accept any amount - maximum slippage tolerance

            swap_txn = router_contract.functions.swapExactETHForTokens(
                amount_out_min,
                path,
                wallet_address,
                deadline
            ).build_transaction({
                'from': wallet_address,
                'value': native_amount_wei,
                'gas': 300000,
                'gasPrice': gas_price,
                'nonce': nonce
            })

            # Sign and send transaction
            signed_txn = w3.eth.account.sign_transaction(swap_txn, private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)

            print(f"📡 Swap transaction sent: {tx_hash.hex()}")

            # Wait for confirmation
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)

            if receipt['status'] == 1:
                print(f"✅ Native token swap successful!")
                return {
                    'success': True,
                    'tx_hash': tx_hash.hex(),
                    'gas_used': receipt['gasUsed'],
                    'gas_price': gas_price
                }
            else:
                return {'success': False, 'error': 'Swap transaction failed'}

        except Exception as e:
            error_msg = str(e)
            print(f"❌ Native swap error: {error_msg}")

            # Provide specific error guidance
            if "INSUFFICIENT_OUTPUT_AMOUNT" in error_msg:
                print("💡 Hint: Slippage too low or liquidity pool doesn't exist")
            elif "INSUFFICIENT_INPUT_AMOUNT" in error_msg:
                print("💡 Hint: Trade amount too small")
            elif "execution reverted" in error_msg:
                print("💡 Hint: Contract execution failed - check token/path validity")
            elif "insufficient funds" in error_msg:
                print("💡 Hint: Not enough ETH/BNB for trade + gas")

            return {'success': False, 'error': error_msg}

    def _get_block_explorer_url(self, chain: str, tx_hash: str) -> str:
        """Get block explorer URL for transaction"""
        explorers = {
            'ethereum': f'https://etherscan.io/tx/{tx_hash}',
            'bsc': f'https://bscscan.com/tx/{tx_hash}',
            'polygon': f'https://polygonscan.com/tx/{tx_hash}',
            'base': f'https://basescan.org/tx/{tx_hash}',
            'arbitrum': f'https://arbiscan.io/tx/{tx_hash}'
        }

        return explorers.get(chain, f'Transaction: {tx_hash}')

    def _create_error_result(self, error_message: str) -> Dict:
        """Create standardized error result"""
        return {
            'status': 'ERROR',
            'trade_executed': False,
            'error': error_message,
            'timestamp': datetime.now().isoformat()
        }

    def _get_native_symbol(self, chain: str) -> str:
        """Get native token symbol for chain"""
        symbols = {
            'ethereum': 'ETH',
            'bsc': 'BNB',
            'polygon': 'MATIC',
            'arbitrum': 'ETH',
            'optimism': 'ETH',
            'base': 'ETH',
            'avalanche': 'AVAX'
        }
        return symbols.get(chain, 'ETH')

# Global instance
_real_dex_executor = None

def get_real_dex_executor() -> RealDEXExecutor:
    """Get global real DEX executor instance"""
    global _real_dex_executor
    if _real_dex_executor is None:
        _real_dex_executor = RealDEXExecutor()
    return _real_dex_executor