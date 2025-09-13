import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Blockchain Configuration
RPC_URL = os.getenv('RPC_URL', 'https://bsc-dataseed.binance.org/')
WALLET_ADDRESS = os.getenv('WALLET_ADDRESS')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')

# API Keys
CRYPTO_PANIC_API_KEY = os.getenv('CRYPTO_PANIC_API_KEY')
POLYGONSCAN_API_KEY = os.getenv('POLYGONSCAN_API_KEY')
BENZINGA_API_KEY = os.getenv('BENZINGA_API_KEY')

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
    'DAI': 'USD'
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
    'PREFERRED_CHAINS': ['polygon', 'bsc', 'ethereum', 'avalanche', 'fantom']  # Chain priority order
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