#!/bin/bash

# Overnight Real Trading Test Script
# This script runs the crypto bot with real trading enabled

echo "🚀 Starting LLM Crypto Bot for Overnight Real Trading Test"
echo "================================================="
echo "⚠️  WARNING: This will execute REAL trades with REAL money!"
echo "⚠️  Only high confidence trades (≥70%) will be executed"
echo "⚠️  Trade amounts are conservative (15% of portfolio max)"
echo "================================================="
echo ""

# Check if .env file exists and has wallet configuration
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    echo "Please create .env file with wallet credentials before running with real trades"
    exit 1
fi

# Check if wallet credentials are in .env
if ! grep -q "WALLET_ADDRESS=" .env || ! grep -q "PRIVATE_KEY=" .env; then
    echo "❌ Error: WALLET_ADDRESS and PRIVATE_KEY must be set in .env"
    echo "Please configure your wallet credentials before running with real trades"
    exit 1
fi

# Load environment variables
set -a
source .env
set +a

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "❌ Error: Ollama is not running on localhost:11434"
    echo "Please start Ollama before running the bot"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

echo "✅ Virtual environment activated"

# Verify DEX trading readiness
echo "🔍 Verifying DEX trading system..."
python3 verify_dex_ready.py
if [ $? -ne 0 ]; then
    echo "❌ System verification failed. Please fix issues before trading."
    exit 1
fi

echo ""
echo "✅ Starting bot with REAL DEX trading enabled..."
echo "🔄 Connected to QuickSwap on Polygon network"
echo ""

# Create log file with timestamp
LOG_FILE="overnight_trading_$(date +%Y%m%d_%H%M%S).log"

# Run the bot with real trading enabled, logging output
python3 main.py --real 2>&1 | tee "$LOG_FILE"

echo ""
echo "🏁 Bot execution completed"
echo "📄 Full log saved to: $LOG_FILE"

# Show trade summary if real trades were executed
if [ -f "real_trades.log" ]; then
    echo ""
    echo "📊 REAL TRADES SUMMARY:"
    echo "======================="
    wc -l real_trades.log | awk '{print "Total real trades executed: " $1}'
    echo ""
    echo "Last 5 trades:"
    tail -5 real_trades.log | python3 -c "
import json
import sys
for line in sys.stdin:
    try:
        trade = json.loads(line.strip())
        print(f\"  {trade['timestamp'][:19]} | {trade['action']} {trade['token']} | \${trade['amount_usd']:.2f} | {trade['confidence']:.1%}\")
    except:
        pass
"
fi