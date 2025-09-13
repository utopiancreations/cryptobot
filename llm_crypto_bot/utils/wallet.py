from web3 import Web3
from typing import Dict, Optional, List
import config
import requests

def get_wallet_balance() -> Optional[Dict]:
    """
    Get wallet balance for native token (BNB/ETH) and common tokens
    
    Returns:
        Dictionary with balance information
    """
    if not config.WALLET_ADDRESS:
        print("Warning: WALLET_ADDRESS not configured. Using mock data.")
        return _get_mock_balance()
    
    try:
        # Connect to blockchain
        w3 = Web3(Web3.HTTPProvider(config.RPC_URL))
        
        if not w3.is_connected():
            print("Error: Cannot connect to blockchain RPC")
            return None
        
        wallet_address = Web3.to_checksum_address(config.WALLET_ADDRESS)
        
        # Get native token balance (BNB for BSC, ETH for Ethereum)
        native_balance_wei = w3.eth.get_balance(wallet_address)
        native_balance = w3.from_wei(native_balance_wei, 'ether')
        
        # Determine native token symbol based on RPC URL
        native_symbol = _get_native_token_symbol(config.RPC_URL)
        
        balance_info = {
            'wallet_address': config.WALLET_ADDRESS,
            'native_token': {
                'symbol': native_symbol,
                'balance': float(native_balance),
                'balance_wei': native_balance_wei
            },
            'tokens': {},
            'total_usd_estimate': 0.0
        }
        
        # Get token balances for common tokens
        token_contracts = _get_common_token_contracts()
        
        for symbol, contract_address in token_contracts.items():
            try:
                token_balance = get_token_balance(wallet_address, contract_address, w3)
                if token_balance > 0:
                    balance_info['tokens'][symbol] = {
                        'balance': token_balance,
                        'contract_address': contract_address
                    }
            except Exception as e:
                print(f"Error getting {symbol} balance: {e}")
        
        # Estimate total USD value (simplified)
        balance_info['total_usd_estimate'] = _estimate_total_usd_value(balance_info)
        
        print(f"✅ Retrieved wallet balance for {config.WALLET_ADDRESS}")
        return balance_info
        
    except Exception as e:
        print(f"Error retrieving wallet balance: {e}")
        return _get_mock_balance()

def get_token_balance(wallet_address: str, token_contract: str, w3: Web3) -> float:
    """
    Get balance of a specific ERC-20 token
    
    Args:
        wallet_address: Wallet address to check
        token_contract: Token contract address
        w3: Web3 instance
        
    Returns:
        Token balance as float
    """
    # Standard ERC-20 ABI for balanceOf and decimals
    erc20_abi = [
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
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
    
    try:
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(token_contract),
            abi=erc20_abi
        )
        
        # Get balance in smallest unit
        balance_raw = contract.functions.balanceOf(wallet_address).call()
        
        # Get decimals to convert to human readable format
        decimals = contract.functions.decimals().call()
        
        # Convert to human readable balance
        balance = balance_raw / (10 ** decimals)
        
        return balance
        
    except Exception as e:
        print(f"Error getting token balance for {token_contract}: {e}")
        return 0.0

def _get_common_token_contracts() -> Dict[str, str]:
    """Get contract addresses for common tokens based on network"""
    # BSC Mainnet token contracts
    if 'bsc' in config.RPC_URL.lower():
        return {
            'USDT': '0x55d398326f99059fF775485246999027B3197955',
            'USDC': '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d',
            'BUSD': '0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56',
            'BTCB': '0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c',
            'ETH': '0x2170Ed0880ac9A755fd29B2688956BD959F933F8'
        }
    # Ethereum Mainnet token contracts
    elif 'ethereum' in config.RPC_URL.lower() or 'eth' in config.RPC_URL.lower():
        return {
            'USDT': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
            'USDC': '0xA0b86a33E6441f8e532b1d7C9Ed1575b56D8C64d',
            'WBTC': '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599'
        }
    else:
        return {}

def _get_native_token_symbol(rpc_url: str) -> str:
    """Determine native token symbol based on RPC URL"""
    if 'bsc' in rpc_url.lower():
        return 'BNB'
    elif 'ethereum' in rpc_url.lower() or 'eth' in rpc_url.lower():
        return 'ETH'
    elif 'polygon' in rpc_url.lower() or 'matic' in rpc_url.lower():
        return 'MATIC'
    else:
        return 'ETH'  # Default

def _estimate_total_usd_value(balance_info: Dict) -> float:
    """
    Estimate total USD value of wallet (simplified estimation)
    In production, this would use real price APIs
    """
    # Mock prices for estimation
    mock_prices = {
        'BNB': 300.0,
        'ETH': 2500.0,
        'BTCB': 45000.0,
        'WBTC': 45000.0,
        'USDT': 1.0,
        'USDC': 1.0,
        'BUSD': 1.0
    }
    
    total_usd = 0.0
    
    # Native token value
    native_symbol = balance_info['native_token']['symbol']
    native_balance = balance_info['native_token']['balance']
    native_price = mock_prices.get(native_symbol, 0.0)
    total_usd += native_balance * native_price
    
    # Token values
    for symbol, token_info in balance_info['tokens'].items():
        token_balance = token_info['balance']
        token_price = mock_prices.get(symbol, 0.0)
        total_usd += token_balance * token_price
    
    return round(total_usd, 2)

def _get_mock_balance() -> Dict:
    """Return mock balance data for testing"""
    return {
        'wallet_address': 'mock_address',
        'native_token': {
            'symbol': 'BNB',
            'balance': 0.5,
            'balance_wei': 500000000000000000
        },
        'tokens': {
            'USDT': {
                'balance': 100.0,
                'contract_address': '0x55d398326f99059fF775485246999027B3197955'
            },
            'USDC': {
                'balance': 50.0,
                'contract_address': '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d'
            }
        },
        'total_usd_estimate': 300.0
    }

def check_wallet_connection() -> bool:
    """Test wallet connection and configuration"""
    try:
        if not config.WALLET_ADDRESS:
            print("❌ Wallet address not configured")
            return False
        
        if not config.RPC_URL:
            print("❌ RPC URL not configured")
            return False
        
        # Test RPC connection
        w3 = Web3(Web3.HTTPProvider(config.RPC_URL))
        if not w3.is_connected():
            print("❌ Cannot connect to blockchain RPC")
            return False
        
        # Test wallet address format
        try:
            Web3.to_checksum_address(config.WALLET_ADDRESS)
        except Exception:
            print("❌ Invalid wallet address format")
            return False
        
        print("✅ Wallet connection test successful")
        return True
        
    except Exception as e:
        print(f"❌ Wallet connection test failed: {e}")
        return False

def get_gas_price() -> Optional[int]:
    """Get current gas price for transactions"""
    try:
        w3 = Web3(Web3.HTTPProvider(config.RPC_URL))
        if w3.is_connected():
            gas_price = w3.eth.gas_price
            return gas_price
        return None
    except Exception as e:
        print(f"Error getting gas price: {e}")
        return None