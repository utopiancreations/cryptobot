import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Primary EVM Chain Configuration (backwards compatibility)
RPC_URL = os.getenv('RPC_URL', 'https://polygon-rpc.com/')  # Default to Polygon for better fees
WALLET_ADDRESS = os.getenv('WALLET_ADDRESS')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')

# Multi-Wallet Configuration
ADDITIONAL_WALLETS = os.getenv('ADDITIONAL_WALLETS', '').split(',') if os.getenv('ADDITIONAL_WALLETS') else []
WALLET_NAMES = os.getenv('WALLET_NAMES', '').split(',') if os.getenv('WALLET_NAMES') else []

# Multi-Chain RPC Configuration
CHAIN_RPC_URLS = {
    'ethereum': os.getenv('ETHEREUM_RPC_URL', 'https://eth.llamarpc.com'),
    'polygon': os.getenv('POLYGON_RPC_URL', 'https://polygon-rpc.com/'),
    'bsc': os.getenv('BSC_RPC_URL', 'https://bsc-dataseed.binance.org/'),
    'arbitrum': os.getenv('ARBITRUM_RPC_URL', 'https://arb1.arbitrum.io/rpc'),
    'optimism': os.getenv('OPTIMISM_RPC_URL', 'https://mainnet.optimism.io'),
    'base': os.getenv('BASE_RPC_URL', 'https://mainnet.base.org'),
    'avalanche': os.getenv('AVALANCHE_RPC_URL', 'https://api.avax.network/ext/bc/C/rpc'),
    'fantom': os.getenv('FANTOM_RPC_URL', 'https://rpc.ftm.tools/')
}

# Solana Configuration
SOLANA_RPC_URL = os.getenv('SOLANA_RPC_URL', 'https://api.mainnet-beta.solana.com')
SOLANA_WALLET_ADDRESS = os.getenv('SOLANA_WALLET_ADDRESS', 'HjdaAMe5dZdMAWjqW9uArE2viDBGHG2GQ6Bno7XvmXe5')
SOLANA_PRIVATE_KEY = os.getenv('SOLANA_PRIVATE_KEY')

# API Keys
CRYPTO_PANIC_API_KEY = os.getenv('CRYPTO_PANIC_API_KEY')
POLYGONSCAN_API_KEY = os.getenv('POLYGONSCAN_API_KEY')
BENZINGA_API_KEY = os.getenv('BENZINGA_API_KEY')
COINMARKETCAP_API_KEY = os.getenv('COINMARKETCAP_DEX_API_KEY')

# LLM Configuration
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3:8b')
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')

# Token Equivalency Map (wrapped tokens to base assets)
EQUIVALENCY_MAP = {
    'WMATIC': 'MATIC',
    'WETH': 'ETH',
    'WBTC': 'BTC',
    'WBNB': 'BNB',
    'WAVAX': 'AVAX',
    'WFTM': 'FTM',
    'BUSD': 'USD',
    'USDT': 'USD',
    'USDC': 'USD',
    'DAI': 'USD',
    'WSOL': 'SOL',  # Wrapped SOL
    'mSOL': 'SOL',  # Marinade staked SOL
    'stSOL': 'SOL'  # Lido staked SOL
}

# Chain-Specific Token Contracts
CHAIN_TOKEN_CONTRACTS = {
    'ethereum': {
        'USDT': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
        'USDC': '0xA0b86a33E6441f8e532b1d7C9Ed1575b56D8C64d',
        'WBTC': '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599',
        'WETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
        'DAI': '0x6B175474E89094C44Da98b954EedeAC495271d0F'
    },
    'polygon': {
        'USDT': '0xc2132D05D31c914a87C6611C10748AEb04B58e8F',
        'USDC': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
        'WBTC': '0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6',
        'WETH': '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619',
        'DAI': '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063',
        'WMATIC': '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270'
    },
    'bsc': {
        'USDT': '0x55d398326f99059fF775485246999027B3197955',
        'USDC': '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d',
        'BUSD': '0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56',
        'BTCB': '0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c',
        'ETH': '0x2170Ed0880ac9A755fd29B2688956BD959F933F8',
        'WBNB': '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c'
    },
    'arbitrum': {
        'USDT': '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9',
        'USDC': '0xaf88d065e77c8cC2239327C5EDb3A432268e5831',
        'WETH': '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',
        'WBTC': '0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f',
        'DAI': '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1'
    },
    'optimism': {
        'USDT': '0x94b008aA00579c1307B0EF2c499aD98a8ce58e58',
        'USDC': '0x7F5c764cBc14f9669B88837ca1490cCa17c31607',
        'WETH': '0x4200000000000000000000000000000000000006',
        'WBTC': '0x68f180fcCe6836688e9084f035309E29Bf0A2095',
        'DAI': '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1'
    },
    'base': {
        'USDC': '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913',
        'WETH': '0x4200000000000000000000000000000000000006',
        'DAI': '0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb'
    },
    'avalanche': {
        'USDT': '0x9702230A8Ea53601f5cD2dc00fDBc13d4dF4A8c7',
        'USDC': '0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E',
        'WETH': '0x49D5c2BdFfac6CE2BFdB6640F4F80f226bc10bAB',
        'WBTC': '0x50b7545627a5162F82A992c33b87aDc75187B218',
        'WAVAX': '0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7'
    },
    'fantom': {
        'USDC': '0x04068DA6C83AFCFA0e13ba15A6696662335D5B75',
        'WETH': '0x74b23882a30290451A17c44f4F05243b6b58C76d',
        'WBTC': '0x321162Cd933E2Be498Cd2267a90534A804051b11',
        'WFTM': '0x21be370D5312f44cB42ce377BC9b8a0cEF1A4C83'
    }
}

# Risk Parameters
RISK_PARAMETERS = {
    'MAX_TRADE_USD': float(os.getenv('MAX_TRADE_USD', '25')),  # Reduced to match wallet balance
    'DAILY_LOSS_LIMIT_PERCENT': float(os.getenv('DAILY_LOSS_LIMIT_PERCENT', '5')),
    # Token whitelist removed - can trade any token
}

# Trading Configuration
TRADE_SETTINGS = {
    'LOOP_INTERVAL_SECONDS': 120,  # 2 minutes cooldown after completion (regardless of execution time)
    'SLIPPAGE_TOLERANCE': 0.01,  # 1%
    'GAS_PRICE_GWEI': 5,
    'USE_MULTI_DEX': True,  # Enable multi-DEX trading
    'PREFERRED_CHAINS': ['arbitrum', 'base', 'polygon', 'bsc', 'solana', 'optimism', 'avalanche', 'ethereum', 'fantom']  # Chain priority order (by opportunity/cost)
}

def validate_config():
    """Validate that required configuration is present"""
    required_vars = []
    
    if not CRYPTO_PANIC_API_KEY:
        required_vars.append('CRYPTO_PANIC_API_KEY')
    
    if not POLYGONSCAN_API_KEY:
        required_vars.append('POLYGONSCAN_API_KEY')
    
    if not BENZINGA_API_KEY:
        required_vars.append('BENZINGA_API_KEY')
    
    if required_vars:
        print(f"Warning: Missing required environment variables: {', '.join(required_vars)}")
        print("The bot will run in limited mode without these variables.")
    
    return len(required_vars) == 0

def get_risk_params():
    """Get risk management parameters"""
    return RISK_PARAMETERS.copy()

def get_dynamic_risk_params():
    """Get risk management parameters adjusted for current wallet balance"""
    from utils.wallet import get_wallet_balance
    
    base_params = RISK_PARAMETERS.copy()
    
    # Get current wallet balance
    wallet_balance = get_wallet_balance()
    
    if wallet_balance and wallet_balance.get('total_usd_estimate', 0) > 0:
        total_balance_usd = wallet_balance['total_usd_estimate']
        
        # Set max trade to 15% of total portfolio value (conservative)
        dynamic_max_trade = min(
            total_balance_usd * 0.15,  # 15% of portfolio
            100.0  # Hard cap at $100
        )
        
        # Minimum trade amount of $5 to avoid dust trades
        dynamic_max_trade = max(dynamic_max_trade, 5.0)
        
        base_params['MAX_TRADE_USD'] = round(dynamic_max_trade, 2)
        base_params['TOTAL_PORTFOLIO_USD'] = total_balance_usd
        
        print(f"📊 Dynamic risk params: Max trade ${dynamic_max_trade:.2f} (15% of ${total_balance_usd:.2f})")
    else:
        print("⚠️  Using static risk params - wallet balance unavailable")
    
    return base_params

def get_trade_settings():
    """Get trading configuration settings"""
    return TRADE_SETTINGS.copy()

def get_equivalency_map():
    """Get token equivalency mapping"""
    return EQUIVALENCY_MAP.copy()