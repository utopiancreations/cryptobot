#!/usr/bin/env python3

from consensus_engine import get_consensus_decision_sync

# Test with very bullish data to see if we can get a high confidence decision
test_data = '''
BREAKING: Bitcoin surges 20% in massive institutional buying wave!
- MicroStrategy purchases additional $2B in Bitcoin
- BlackRock announces new Bitcoin ETF with $10B backing  
- Coinbase reports highest trading volume in 2 years
- Technical analysis shows breakout above $50,000 resistance
- On-chain metrics indicate massive accumulation phase
- Social sentiment extremely bullish across all platforms
- Whale wallets accumulating at record pace
- Options market shows massive call buying
'''

print('Testing with extremely bullish data...')
decision = get_consensus_decision_sync(test_data)
if decision:
    print(f'Action: {decision.get("action")}')
    print(f'Token: {decision.get("token")}') 
    print(f'Confidence: {decision.get("confidence", 0):.1%}')
    print(f'Amount: ${decision.get("amount_usd", 0):.2f}')
    
    if decision.get('confidence', 0) >= 0.7:
        print('✅ Would trigger real trade (≥70% confidence)')
    else:
        print('❌ Below real trade threshold (70%)')
else:
    print('No decision made')