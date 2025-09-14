"""
DEX Integration Module for Real Trading

This module integrates with QuickSwap (Polygon's leading DEX) to execute real trades.
Supports token swaps using QuickSwap's router contracts.
"""

from web3 import Web3
from typing import Dict, Optional, List, Tuple
import json
import time
from decimal import Decimal
import config
from utils.wallet import get_wallet_balance

# QuickSwap Router Contract on Polygon
QUICKSWAP_ROUTER_ADDRESS = "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff"
WMATIC_ADDRESS = "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"

# ERC-20 Token Addresses on Polygon
POLYGON_TOKENS = {
    'USDC': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
    'USDT': '0xc2132D05D31c914a87C6611C10748AEb04B58e8F',
    'WETH': '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619',
    'WBTC': '0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6',
    'DAI': '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063',
    'WMATIC': WMATIC_ADDRESS,
    # Add more popular tokens on Polygon
    'MATIC': WMATIC_ADDRESS,  # Native MATIC = WMATIC for trading
    'BTC': '0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6',  # Same as WBTC
    'ETH': '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619',  # Same as WETH
    'LINK': '0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39',
    'UNI': '0xb33EaAd8d922B1083446DC23f610c2567fB5180f',
    'AAVE': '0xD6DF932A45C0f255f85145f286eA0b292B21C90B',
    'CRV': '0x172370d5Cd63279eFa6d502DAB29171933a610AF',
    'SUSHI': '0x0b3F868E0BE5597D5DB7fEB59E1CADBb0fdDa50a',
    # Popular DeFi tokens
    'COMP': '0x8505b9d2254A7Ae468c0E9dd10Ccea3A837aef5c',
    'YFI': '0xDA537104D6A5edd53c6fBba9A898708E465260b6',
    'MKR': '0x6f7C932e7684666C9fd1d44527765433e01fF61d',
    'SNX': '0x50B728D8D964fd00C2d0AAD81718b71311feF68a'
}

# QuickSwap Router ABI (simplified)
ROUTER_ABI = [
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
        "name": "swapExactTokensForTokens",
        "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
        "stateMutability": "nonpayable",
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
            {"internalType": "uint256", "name": "amountOut", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"}
        ],
        "name": "getAmountsIn",
        "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
        "stateMutability": "view",
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

# ERC-20 ABI (simplified)
ERC20_ABI = [
    {
        "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]

class QuickSwapIntegration:
    """QuickSwap DEX integration for real trading on Polygon"""
    
    def __init__(self):
        self.w3 = None
        self.account = None
        self.private_key = None
        self.router_contract = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Web3 and contracts"""
        try:
            # Connect to Polygon network
            self.w3 = Web3(Web3.HTTPProvider(config.RPC_URL))
            if not self.w3.is_connected():
                raise Exception("Cannot connect to Polygon network")
            
            # Set up account
            self.private_key = config.PRIVATE_KEY
            self.account = self.w3.eth.account.from_key(self.private_key)
            
            # Initialize router contract
            self.router_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(QUICKSWAP_ROUTER_ADDRESS),
                abi=ROUTER_ABI
            )
            
            print("✅ QuickSwap integration initialized")
            
        except Exception as e:
            print(f"❌ Failed to initialize QuickSwap integration: {e}")
            raise
    
    def execute_swap(self, action: str, token_symbol: str, amount_usd: float) -> Dict:
        """
        Execute a token swap on QuickSwap
        
        Args:
            action: 'BUY' or 'SELL'
            token_symbol: Token symbol (e.g., 'WBTC', 'USDC')
            amount_usd: USD amount to trade
            
        Returns:
            Transaction result dictionary
        """
        try:
            print(f"🔄 Executing {action} {token_symbol} for ${amount_usd:.2f}")
            
            # Convert token symbol to address
            if token_symbol not in POLYGON_TOKENS:
                return {'error': f'Token {token_symbol} not supported'}
            
            token_address = POLYGON_TOKENS[token_symbol]
            
            # Calculate MATIC amount to swap
            matic_amount = self._usd_to_matic(amount_usd)
            
            if action == 'BUY':
                return self._buy_token(token_address, matic_amount, token_symbol)
            elif action == 'SELL':
                return self._sell_token(token_address, amount_usd, token_symbol)
            else:
                return {'error': f'Unknown action: {action}'}
                
        except Exception as e:
            return {'error': f'Swap execution failed: {e}'}
    
    def _buy_token(self, token_address: str, matic_amount: float, token_symbol: str) -> Dict:
        """Buy tokens using MATIC"""
        try:
            # Convert MATIC amount to Wei
            matic_wei = self.w3.to_wei(matic_amount, 'ether')
            
            # Set up swap path: WMATIC -> Token
            path = [WMATIC_ADDRESS, Web3.to_checksum_address(token_address)]
            
            # Get expected output amount
            amounts_out = self.router_contract.functions.getAmountsOut(
                matic_wei, path
            ).call()
            
            expected_tokens = amounts_out[-1]
            
            # Set minimum output (95% of expected for 5% slippage tolerance)
            min_tokens_out = int(expected_tokens * 0.95)
            
            # Set deadline (10 minutes from now)
            deadline = int(time.time()) + 600
            
            # Build transaction
            swap_function = self.router_contract.functions.swapExactETHForTokens(
                min_tokens_out,
                path,
                self.account.address,
                deadline
            )
            
            # Get gas estimate
            gas_estimate = swap_function.estimate_gas({'from': self.account.address, 'value': matic_wei})
            
            # Add 20% buffer to gas estimate
            gas_limit = int(gas_estimate * 1.2)
            
            # Get current gas price
            gas_price = self.w3.eth.gas_price
            
            # Build transaction parameters
            tx_params = {
                'from': self.account.address,
                'value': matic_wei,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
            }
            
            # Build and sign transaction
            transaction = swap_function.build_transaction(tx_params)
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
            
            # Send transaction - handle Web3 version compatibility
            raw_transaction = getattr(signed_txn, 'rawTransaction', getattr(signed_txn, 'raw_transaction', None))
            if raw_transaction is None:
                raise Exception("Could not get raw transaction data")
            tx_hash = self.w3.eth.send_raw_transaction(raw_transaction)
            
            print(f"📤 Transaction sent: {tx_hash.hex()}")
            print("⏳ Waiting for confirmation...")
            
            # Wait for transaction receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt.status == 1:
                print("✅ Swap successful!")
                return {
                    'status': 'SUCCESS',
                    'tx_hash': tx_hash.hex(),
                    'gas_used': receipt.gasUsed,
                    'matic_spent': matic_amount,
                    'expected_tokens': self._wei_to_tokens(expected_tokens, token_address),
                    'action': 'BUY',
                    'token': token_symbol
                }
            else:
                return {'error': 'Transaction failed', 'tx_hash': tx_hash.hex()}
                
        except Exception as e:
            return {'error': f'Buy transaction failed: {e}'}
    
    def _sell_token(self, token_address: str, amount_usd: float, token_symbol: str) -> Dict:
        """Sell tokens for MATIC"""
        try:
            # Get token contract
            token_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=ERC20_ABI
            )
            
            # Get token decimals
            decimals = token_contract.functions.decimals().call()
            
            # Get token balance
            token_balance_raw = token_contract.functions.balanceOf(self.account.address).call()
            token_balance = token_balance_raw / (10 ** decimals)
            
            if token_balance == 0:
                return {'error': f'No {token_symbol} balance to sell'}
            
            # Calculate how many tokens to sell based on USD amount
            # This is simplified - in production you'd get real token price
            estimated_token_price = self._get_estimated_token_price(token_address)
            tokens_to_sell = amount_usd / estimated_token_price
            
            if tokens_to_sell > token_balance:
                tokens_to_sell = token_balance
                print(f"⚠️ Selling entire balance: {token_balance:.6f} {token_symbol}")
            
            # Convert to Wei
            tokens_to_sell_wei = int(tokens_to_sell * (10 ** decimals))
            
            # Check allowance and approve if necessary
            allowance = token_contract.functions.allowance(
                self.account.address, QUICKSWAP_ROUTER_ADDRESS
            ).call()
            
            if allowance < tokens_to_sell_wei:
                print("🔓 Approving token spending...")
                self._approve_token(token_contract, tokens_to_sell_wei)
            
            # Set up swap path: Token -> WMATIC
            path = [Web3.to_checksum_address(token_address), WMATIC_ADDRESS]
            
            # Get expected output amount
            amounts_out = self.router_contract.functions.getAmountsOut(
                tokens_to_sell_wei, path
            ).call()
            
            expected_matic_wei = amounts_out[-1]
            
            # Set minimum output (95% of expected for 5% slippage tolerance)
            min_matic_out = int(expected_matic_wei * 0.95)
            
            # Set deadline (10 minutes from now)
            deadline = int(time.time()) + 600
            
            # Build transaction
            swap_function = self.router_contract.functions.swapExactTokensForETH(
                tokens_to_sell_wei,
                min_matic_out,
                path,
                self.account.address,
                deadline
            )
            
            # Execute swap
            return self._execute_token_swap(swap_function, token_symbol, 'SELL', tokens_to_sell)
            
        except Exception as e:
            return {'error': f'Sell transaction failed: {e}'}
    
    def _approve_token(self, token_contract, amount_wei: int):
        """Approve token spending"""
        try:
            approve_function = token_contract.functions.approve(QUICKSWAP_ROUTER_ADDRESS, amount_wei)
            
            tx_params = {
                'from': self.account.address,
                'gas': 100000,  # Standard gas limit for approval
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
            }
            
            transaction = approve_function.build_transaction(tx_params)
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
            # Handle Web3 version compatibility
            raw_transaction = getattr(signed_txn, 'rawTransaction', getattr(signed_txn, 'raw_transaction', None))
            if raw_transaction is None:
                raise Exception("Could not get raw transaction data")
            tx_hash = self.w3.eth.send_raw_transaction(raw_transaction)
            
            # Wait for approval
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            if receipt.status != 1:
                raise Exception("Token approval failed")
            
            print("✅ Token approved for spending")
            
        except Exception as e:
            raise Exception(f"Token approval failed: {e}")
    
    def _execute_token_swap(self, swap_function, token_symbol: str, action: str, token_amount: float) -> Dict:
        """Execute a token swap transaction"""
        try:
            # Get gas estimate
            gas_estimate = swap_function.estimate_gas({'from': self.account.address})
            gas_limit = int(gas_estimate * 1.2)
            
            # Build transaction parameters
            tx_params = {
                'from': self.account.address,
                'gas': gas_limit,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
            }
            
            # Build and sign transaction
            transaction = swap_function.build_transaction(tx_params)
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
            
            # Send transaction - handle Web3 version compatibility
            raw_transaction = getattr(signed_txn, 'rawTransaction', getattr(signed_txn, 'raw_transaction', None))
            if raw_transaction is None:
                raise Exception("Could not get raw transaction data")
            tx_hash = self.w3.eth.send_raw_transaction(raw_transaction)
            
            print(f"📤 Transaction sent: {tx_hash.hex()}")
            print("⏳ Waiting for confirmation...")
            
            # Wait for transaction receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt.status == 1:
                print("✅ Swap successful!")
                return {
                    'status': 'SUCCESS',
                    'tx_hash': tx_hash.hex(),
                    'gas_used': receipt.gasUsed,
                    'token_amount': token_amount,
                    'action': action,
                    'token': token_symbol
                }
            else:
                return {'error': 'Transaction failed', 'tx_hash': tx_hash.hex()}
                
        except Exception as e:
            return {'error': f'Token swap failed: {e}'}
    
    def _usd_to_matic(self, usd_amount: float) -> float:
        """Convert USD amount to MATIC (simplified)"""
        # Using mock price - in production, get real MATIC price
        matic_price = 0.8  # $0.80 per MATIC
        return usd_amount / matic_price
    
    def _get_estimated_token_price(self, token_address: str) -> float:
        """Get estimated token price in USD (simplified)"""
        # This is a simplified implementation
        # In production, you'd query price oracles or DEX reserves
        mock_prices = {
            POLYGON_TOKENS['USDC']: 1.0,
            POLYGON_TOKENS['USDT']: 1.0,
            POLYGON_TOKENS['WETH']: 2500.0,
            POLYGON_TOKENS['WBTC']: 45000.0,
            POLYGON_TOKENS['DAI']: 1.0
        }
        return mock_prices.get(token_address.lower(), 100.0)
    
    def _wei_to_tokens(self, wei_amount: int, token_address: str) -> float:
        """Convert Wei amount to human-readable tokens"""
        try:
            token_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=ERC20_ABI
            )
            decimals = token_contract.functions.decimals().call()
            return wei_amount / (10 ** decimals)
        except:
            return wei_amount / (10 ** 18)  # Default to 18 decimals
    
    def get_token_balance(self, token_symbol: str) -> float:
        """Get current token balance"""
        try:
            if token_symbol not in POLYGON_TOKENS:
                return 0.0
            
            token_address = POLYGON_TOKENS[token_symbol]
            token_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=ERC20_ABI
            )
            
            balance_raw = token_contract.functions.balanceOf(self.account.address).call()
            decimals = token_contract.functions.decimals().call()
            
            return balance_raw / (10 ** decimals)
            
        except Exception as e:
            print(f"Error getting {token_symbol} balance: {e}")
            return 0.0

# Global instance
quickswap = QuickSwapIntegration()

def execute_dex_trade(action: str, token_symbol: str, amount_usd: float) -> Dict:
    """
    Execute a trade on QuickSwap DEX
    
    Args:
        action: 'BUY' or 'SELL'
        token_symbol: Token symbol to trade
        amount_usd: USD amount to trade
        
    Returns:
        Trade execution result
    """
    try:
        return quickswap.execute_swap(action, token_symbol, amount_usd)
    except Exception as e:
        return {'error': f'DEX trade failed: {e}'}

def get_supported_tokens() -> List[str]:
    """Get list of supported tokens"""
    return list(POLYGON_TOKENS.keys())