# LLM Crypto Trading Bot

An AI-powered cryptocurrency trading bot that uses a local Large Language Model (LLM) to analyze real-time market data, news, and sentiment to make informed trading decisions. The bot supports both simulation mode for testing and real trading with customizable risk parameters.

## Features

- **Multi-Agent Consensus Engine**: Uses multiple AI agents to reach trading decisions
- **Real-Time Market Analysis**: Integrates RSS feeds, news sources, and market sentiment
- **Multi-DEX Support**: Trade across multiple decentralized exchanges
- **Risk Management**: Configurable risk parameters and daily loss limits
- **Simulation Mode**: Test strategies without risking real money
- **Cross-Chain Trading**: Support for Polygon, BSC, Ethereum, Avalanche, and Fantom

## Prerequisites

- **Python 3.8+** (Python 3.9+ recommended)
- **Ollama** - Local LLM runtime environment
- **Git** - For cloning the repository
- **A crypto wallet** with private key access (MetaMask, hardware wallet, etc.)
- **API keys** for data sources (optional but recommended for full functionality)
- **Sufficient system resources** - 8GB+ RAM recommended for LLM operations

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/utopiancreations/cryptobot.git
cd cryptobot
```

### 2. Set up Python Environment (Recommended)
```bash
# Create virtual environment
python3 -m venv crypto_bot_env

# Activate virtual environment
# On Linux/Mac:
source crypto_bot_env/bin/activate
# On Windows:
crypto_bot_env\Scripts\activate
```

### 3. Install Python Dependencies
```bash
# Upgrade pip first
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

### 4. Install and Configure Ollama

#### 4a. Install Ollama

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**macOS:**
```bash
# Using Homebrew
brew install ollama

# Or download from https://ollama.ai/download
```

**Windows:**
- Download the installer from [ollama.ai/download](https://ollama.ai/download)
- Run the installer and follow the setup wizard

#### 4b. Start Ollama Service
```bash
# Start Ollama (will run in background)
ollama serve
```

#### 4c. Download and Configure LLM Model

**Recommended Models by System Specs:**

| Model | Size | RAM Needed | Performance | Use Case |
|-------|------|------------|-------------|----------|
| `llama3:3b` | ~2GB | 4GB+ | Good | Low-end systems, testing |
| `llama3:8b` | ~4.7GB | 8GB+ | Excellent | **Recommended default** |
| `llama3:70b` | ~40GB | 64GB+ | Outstanding | High-end systems only |
| `mistral:7b` | ~4.1GB | 8GB+ | Very Good | Alternative to Llama3:8b |
| `qwen2:7b` | ~4.4GB | 8GB+ | Very Good | Good reasoning abilities |

```bash
# Download the recommended model (Llama3 8B - best balance of performance/resource usage)
ollama pull llama3:8b

# Alternative models:
# For systems with limited RAM (4-6GB):
ollama pull llama3:3b

# For high-performance systems (64GB+ RAM):
ollama pull llama3:70b

# Alternative model with good performance:
ollama pull mistral:7b
```

**Custom Model Configuration:**
To use a different model, update your `.env` file:
```env
# Use a smaller model
OLLAMA_MODEL=llama3:3b

# Use alternative model
OLLAMA_MODEL=mistral:7b

# Use larger model (if you have sufficient RAM)
OLLAMA_MODEL=llama3:70b
```

#### 4d. Test Ollama Installation
```bash
# Test that Ollama is working
ollama run llama3:8b
# Type a test message and press Enter
# Type /bye to exit

# Check available models
ollama list
```

### 5. Verify Installation
```bash
# Test Python imports
python3 -c "import web3, ollama, eth_account; print('All dependencies installed successfully!')"

# Test Ollama connectivity
python3 -c "import ollama; client = ollama.Client(); print('Ollama connection successful!')"
```

## Configuration

### 1. Environment Variables

Create a `.env` file in the project root with the following configuration:

```env
# Blockchain Configuration
RPC_URL=https://polygon-rpc.com/
WALLET_ADDRESS=your_wallet_address_here
PRIVATE_KEY=your_private_key_here

# API Keys (Optional but recommended)
CRYPTO_PANIC_API_KEY=your_cryptopanic_api_key
POLYGONSCAN_API_KEY=your_polygonscan_api_key
BENZINGA_API_KEY=your_benzinga_api_key

# LLM Configuration
OLLAMA_MODEL=llama3:8b
OLLAMA_HOST=http://localhost:11434

# Risk Management
MAX_TRADE_USD=25
DAILY_LOSS_LIMIT_PERCENT=5
```

### 2. Wallet Setup

**⚠️ SECURITY WARNING: Never share your private key. Keep it secure and never commit it to version control.**

To set up your wallet:

1. **MetaMask/Hardware Wallet**: Export your private key from your wallet
2. **Create New Wallet**: Use a tool like `web3.py` to generate a new wallet
3. **Add to .env**: Set `WALLET_ADDRESS` and `PRIVATE_KEY` in your `.env` file

Example of creating a new wallet with Python:
```python
from eth_account import Account
import secrets

# Generate a new account
priv = secrets.token_hex(32)
private_key = "0x" + priv
account = Account.from_key(private_key)

print(f"Address: {account.address}")
print(f"Private Key: {private_key}")
```

### 3. API Keys Setup

#### CryptoPanic API (News Data)
1. Visit [CryptoPanic API](https://cryptopanic.com/developers/api/)
2. Sign up and get your free API key
3. Add to `.env`: `CRYPTO_PANIC_API_KEY=your_key_here`

#### PolygonScan API (Blockchain Data)
1. Visit [PolygonScan](https://polygonscan.com/apis)
2. Create account and generate API key
3. Add to `.env`: `POLYGONSCAN_API_KEY=your_key_here`

#### Benzinga API (Financial News)
1. Visit [Benzinga API](https://www.benzinga.com/apis/)
2. Sign up for an account
3. Add to `.env`: `BENZINGA_API_KEY=your_key_here`

### 4. Network Configuration

The bot defaults to Polygon network. To use other networks, update the `RPC_URL` in your `.env` file:

```env
# Polygon (default)
RPC_URL=https://polygon-rpc.com/

# BSC
RPC_URL=https://bsc-dataseed.binance.org/

# Ethereum
RPC_URL=https://mainnet.infura.io/v3/your_project_id

# Avalanche
RPC_URL=https://api.avax.network/ext/bc/C/rpc

# Fantom
RPC_URL=https://rpc.ftm.tools/
```

### 5. Risk Parameters

Customize risk management in `config.py` or via environment variables:

- `MAX_TRADE_USD`: Maximum USD amount per trade (default: $25)
- `DAILY_LOSS_LIMIT_PERCENT`: Daily loss limit as percentage (default: 5%)
- `LOOP_INTERVAL_SECONDS`: Time between analysis cycles (default: 120 seconds)
- `SLIPPAGE_TOLERANCE`: Maximum slippage tolerance (default: 1%)

## Usage

### Simulation Mode (Recommended for testing)
```bash
python3 main.py
```

### Real Trading Mode
```bash
python3 main.py --real
```

**⚠️ WARNING: Real trading mode will execute actual trades with your funds. Start with small amounts and test thoroughly in simulation mode first.**

## Project Structure

```
llm_crypto_bot/
├── main.py                    # Main bot execution
├── config.py                  # Configuration management
├── executor.py               # Simulated trade execution
├── real_executor.py          # Real trade execution
├── consensus_engine.py       # Multi-agent decision making
├── auditor.py               # Trade validation and auditing
├── connectors/
│   ├── news.py              # News sentiment analysis
│   ├── realtime_feeds.py    # Real-time data feeds
│   └── simple_market_data.py # Market data connector
├── utils/
│   ├── llm.py              # LLM interaction utilities
│   └── wallet.py           # Wallet management utilities
└── requirements.txt        # Python dependencies
```

## Customization

### Adding New Data Sources

1. Create a new connector in `connectors/`
2. Implement data fetching and formatting functions
3. Update `main.py` to integrate the new source

### Modifying Trading Logic

- Edit `consensus_engine.py` to change decision-making logic
- Modify risk parameters in `config.py`
- Update trade execution logic in `executor.py` or `real_executor.py`

### Adding New Networks

1. Update `PREFERRED_CHAINS` in `config.py`
2. Add RPC endpoints for new networks
3. Update DEX router addresses in trade execution modules

## Monitoring and Logs

The bot provides detailed logging during operation:

- Trade decisions and reasoning
- Market sentiment analysis
- Portfolio performance metrics
- Error handling and debugging info

## Safety Features

- **Simulation Mode**: Test strategies without financial risk
- **Risk Limits**: Configurable position sizing and loss limits
- **Multi-Agent Validation**: Consensus required for trade execution
- **High Confidence Threshold**: Only executes trades with ≥70% confidence
- **Conservative Position Sizing**: Uses 50% of calculated maximum position

## Troubleshooting

### Common Installation Issues

1. **Python Version Issues**:
   ```bash
   # Check Python version
   python3 --version
   # Should be 3.8 or higher
   ```

2. **Pip Installation Failures**:
   ```bash
   # If you get permission errors, try:
   pip install --user -r requirements.txt

   # Or use virtual environment (recommended)
   python3 -m venv crypto_bot_env
   source crypto_bot_env/bin/activate
   pip install -r requirements.txt
   ```

3. **Ollama Connection Issues**:
   ```bash
   # Check if Ollama is running
   curl http://localhost:11434/api/version

   # If not running, start it:
   ollama serve

   # Check available models:
   ollama list
   ```

4. **Memory Issues with Large Models**:
   - Use smaller models if you have limited RAM:
   ```bash
   ollama pull llama3:3b  # ~2GB instead of 4.7GB
   ```
   - Update your `.env` file:
   ```env
   OLLAMA_MODEL=llama3:3b
   ```

### Common Runtime Issues

1. **"LLM not available"**: Ensure Ollama is running and the model is installed
2. **"Wallet connection failed"**: Check private key and RPC URL configuration
3. **"News connection failed"**: Verify API keys are correctly set
4. **Gas estimation failures**: Check network RPC connectivity
5. **Model loading slow**: First run downloads the model, subsequent runs are faster

### Debug Mode

Run with verbose logging:
```bash
python3 -u main.py --real 2>&1 | tee trading.log
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is for educational purposes. Use at your own risk. Always test thoroughly before trading with real funds.

## Disclaimer

**⚠️ IMPORTANT DISCLAIMER ⚠️**

This software is provided for educational and experimental purposes only. Cryptocurrency trading involves substantial risk of loss. The developers are not responsible for any financial losses incurred through the use of this bot.

- Never trade more than you can afford to lose
- Thoroughly test in simulation mode before real trading
- Keep your private keys secure and never share them
- Monitor the bot's performance regularly
- The cryptocurrency market is highly volatile and unpredictable

By using this software, you acknowledge that you understand these risks and use it at your own discretion.