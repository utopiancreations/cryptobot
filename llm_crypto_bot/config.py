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
BSCSCAN_API_KEY = os.getenv('BSCSCAN_API_KEY')

# LLM Configuration
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3:8b')
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')

# Risk Parameters
RISK_PARAMETERS = {
    'MAX_TRADE_USD': float(os.getenv('MAX_TRADE_USD', '100')),
    'DAILY_LOSS_LIMIT_PERCENT': float(os.getenv('DAILY_LOSS_LIMIT_PERCENT', '5')),
    'TOKEN_WHITELIST': [
        'WBNB',
        'BTCB',
        'ETH',
        'USDT',
        'USDC',
        'BUSD'
    ]
}

# Trading Configuration
TRADE_SETTINGS = {
    'LOOP_INTERVAL_SECONDS': 30,
    'SLIPPAGE_TOLERANCE': 0.01,  # 1%
    'GAS_PRICE_GWEI': 5
}

def validate_config():
    """Validate that required configuration is present"""
    required_vars = []
    
    if not CRYPTO_PANIC_API_KEY:
        required_vars.append('CRYPTO_PANIC_API_KEY')
    
    if not BSCSCAN_API_KEY:
        required_vars.append('BSCSCAN_API_KEY')
    
    if required_vars:
        print(f"Warning: Missing required environment variables: {', '.join(required_vars)}")
        print("The bot will run in limited mode without these variables.")
    
    return len(required_vars) == 0

def get_risk_params():
    """Get risk management parameters"""
    return RISK_PARAMETERS.copy()

def get_trade_settings():
    """Get trading configuration settings"""
    return TRADE_SETTINGS.copy()