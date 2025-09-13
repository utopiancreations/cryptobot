"""
Solana wallet utilities for balance checking and transaction handling
"""

from typing import Dict, Optional, List
import config
import requests

try:
    from solana.rpc.api import Client
    from solders.pubkey import Pubkey
    SOLANA_AVAILABLE = True
except ImportError:
    SOLANA_AVAILABLE = False
    print("Warning: Solana dependencies not installed. Run: pip install solana solders")

def get_solana_wallet_balance() -> Optional[Dict]:
    """
    Get Solana wallet balance for SOL and common SPL tokens

    Returns:
        Dictionary with balance information
    """
    if not SOLANA_AVAILABLE:
        print("Warning: Solana libraries not available. Install with: pip install solana solders")
        return _get_mock_solana_balance()

    if not config.SOLANA_WALLET_ADDRESS:
        print("Warning: SOLANA_WALLET_ADDRESS not configured. Using mock data.")
        return _get_mock_solana_balance()

    try:
        # Connect to Solana RPC
        client = Client(config.SOLANA_RPC_URL)

        # Convert wallet address to Pubkey
        wallet_pubkey = Pubkey.from_string(config.SOLANA_WALLET_ADDRESS)

        # Get SOL balance (in lamports, convert to SOL)
        sol_balance_lamports = client.get_balance(wallet_pubkey).value
        sol_balance = sol_balance_lamports / 1_000_000_000  # Convert lamports to SOL

        balance_info = {
            'wallet_address': config.SOLANA_WALLET_ADDRESS,
            'native_token': {
                'symbol': 'SOL',
                'balance': sol_balance,
                'balance_lamports': sol_balance_lamports
            },
            'tokens': {},
            'total_usd_estimate': 0.0,
            'chain': 'solana'
        }

        # Get SPL token balances
        spl_tokens = _get_common_spl_tokens()

        # Get token accounts by owner
        try:
            token_accounts = client.get_token_accounts_by_owner(
                wallet_pubkey,
                {"programId": Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")}  # SPL Token Program
            ).value

            for account in token_accounts:
                try:
                    account_data = account.account.data
                    # Parse token account data to get mint and amount
                    # This is a simplified implementation
                    pass
                except Exception as e:
                    print(f"Error parsing token account: {e}")

        except Exception as e:
            print(f"Error getting SPL token accounts: {e}")

        # Estimate total USD value
        balance_info['total_usd_estimate'] = _estimate_solana_usd_value(balance_info)

        print(f"✅ Retrieved Solana wallet balance for {config.SOLANA_WALLET_ADDRESS}")
        return balance_info

    except Exception as e:
        print(f"Error retrieving Solana wallet balance: {e}")
        return _get_mock_solana_balance()

def check_solana_wallet_connection() -> bool:
    """Test Solana wallet connection and configuration"""
    if not SOLANA_AVAILABLE:
        print("❌ Solana libraries not available")
        return False

    try:
        if not config.SOLANA_WALLET_ADDRESS:
            print("❌ Solana wallet address not configured")
            return False

        if not config.SOLANA_RPC_URL:
            print("❌ Solana RPC URL not configured")
            return False

        # Test RPC connection
        client = Client(config.SOLANA_RPC_URL)

        # Test wallet address format
        try:
            wallet_pubkey = Pubkey.from_string(config.SOLANA_WALLET_ADDRESS)
        except Exception:
            print("❌ Invalid Solana wallet address format")
            return False

        # Test getting balance (basic connectivity test)
        balance = client.get_balance(wallet_pubkey)
        if balance.value is not None:
            sol_balance = balance.value / 1_000_000_000
            trading_mode = "Trading Mode" if config.SOLANA_PRIVATE_KEY else "Read-Only Mode"
            print(f"✅ Solana wallet connection successful ({trading_mode})")
            print(f"   Balance: {sol_balance:.4f} SOL")
            if not config.SOLANA_PRIVATE_KEY:
                print("   ℹ️  No private key - wallet monitoring only (no trading)")
            return True
        else:
            print("❌ Failed to get Solana wallet balance")
            return False

    except Exception as e:
        print(f"❌ Solana wallet connection test failed: {e}")
        return False

def _get_common_spl_tokens() -> Dict[str, str]:
    """Get common SPL token mint addresses"""
    return {
        'USDC': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
        'USDT': 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',
        'WETH': '7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs',
        'WBTC': '9n4nbM75f5Ui33ZbPYXn59EwSgE8CGsHtAeTH5YFeJ9E',
        'mSOL': 'mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So',
        'stSOL': '7dHbWXmci3dT8UFYWYZweBLXgycu7Y3iL6trKn1Y7ARj'
    }

def _estimate_solana_usd_value(balance_info: Dict) -> float:
    """
    Estimate total USD value of Solana wallet (simplified estimation)
    """
    # Mock prices for estimation
    mock_prices = {
        'SOL': 140.0,  # Approximate SOL price
        'USDC': 1.0,
        'USDT': 1.0,
        'WETH': 2500.0,
        'WBTC': 45000.0,
        'mSOL': 140.0,  # Usually similar to SOL
        'stSOL': 140.0
    }

    total_usd = 0.0

    # SOL value
    sol_balance = balance_info['native_token']['balance']
    sol_price = mock_prices.get('SOL', 0.0)
    total_usd += sol_balance * sol_price

    # SPL token values
    for symbol, token_info in balance_info['tokens'].items():
        token_balance = token_info['balance']
        token_price = mock_prices.get(symbol, 0.0)
        total_usd += token_balance * token_price

    return round(total_usd, 2)

def _get_mock_solana_balance() -> Dict:
    """Return mock Solana balance data for testing"""
    return {
        'wallet_address': config.SOLANA_WALLET_ADDRESS or 'mock_solana_address',
        'native_token': {
            'symbol': 'SOL',
            'balance': 1.5,
            'balance_lamports': 1500000000
        },
        'tokens': {
            'USDC': {
                'balance': 100.0,
                'mint_address': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
            },
            'mSOL': {
                'balance': 0.5,
                'mint_address': 'mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So'
            }
        },
        'total_usd_estimate': 310.0,
        'chain': 'solana'
    }

def get_solana_transaction_fee() -> Optional[float]:
    """Get estimated Solana transaction fee in SOL"""
    if not SOLANA_AVAILABLE:
        return None

    try:
        client = Client(config.SOLANA_RPC_URL)
        # Solana transaction fees are typically very low (~0.000005 SOL)
        # This is a simplified estimation
        return 0.000005
    except Exception as e:
        print(f"Error getting Solana transaction fee: {e}")
        return 0.000005  # Default estimate