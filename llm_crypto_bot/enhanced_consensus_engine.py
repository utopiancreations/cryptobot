"""
Enhanced Multi-Agent Consensus Engine for Crypto Trading Bot

This enhanced version can:
1. Analyze ALL available market signals (not just top 3)
2. Generate multiple trade recommendations per cycle (up to 3)
3. Prioritize opportunities based on confidence and risk/reward
4. Handle complex multi-asset analysis from rich market data
"""

import json
import asyncio
from typing import Dict, List, Optional, Any
from utils.llm import get_llm_response
import config

# Define model names for different agents
ANALYST_MODEL = "llama3:8b"
OPPORTUNITIES_MODEL = "gemma2:9b"
RISK_ASSESSMENT_MODEL = "llama3:8b"
PORTFOLIO_STRATEGIST_MODEL = "llama3:8b"

def get_enhanced_consensus_decisions(raw_data: str) -> List[Dict]:
    """
    Enhanced multi-agent consensus that can generate multiple trade opportunities

    Args:
        raw_data: Raw market data formatted as string

    Returns:
        List of up to 3 trading decisions, prioritized by confidence and opportunity
    """
    print("🚀 Enhanced Consensus Engine Activated...")

    try:
        # Step 1: Comprehensive Market Analysis
        print("📊 Step 1: Comprehensive market analysis...")
        market_analysis = _get_comprehensive_market_analysis(raw_data)
        if not market_analysis:
            print("❌ Failed to get comprehensive market analysis")
            return []

        print("✅ Comprehensive market analysis completed")

        # Step 2: Opportunity Identification
        print("🔍 Step 2: Identifying trading opportunities...")
        opportunities = _identify_trading_opportunities(market_analysis, raw_data)
        if not opportunities:
            print("❌ No trading opportunities identified")
            return []

        print(f"✅ Found {len(opportunities)} potential opportunities")

        # Step 3: Risk Assessment
        print("⚠️  Step 3: Comprehensive risk assessment...")
        risk_assessed_opportunities = _assess_opportunity_risks(opportunities, market_analysis)
        if not risk_assessed_opportunities:
            print("❌ Risk assessment failed")
            return []

        print("✅ Risk assessment completed")

        # Step 4: Portfolio Strategy & Final Selection
        print("🎯 Step 4: Portfolio strategy and final selection...")
        final_decisions = _get_portfolio_strategy_decisions(risk_assessed_opportunities, market_analysis)

        if final_decisions:
            print(f"🎉 Generated {len(final_decisions)} trading decisions")
            for i, decision in enumerate(final_decisions, 1):
                print(f"   {i}. {decision.get('action', 'N/A')} {decision.get('token', 'N/A')} - {decision.get('confidence_score', 0):.1%} confidence")
        else:
            print("❌ No final trading decisions generated")

        return final_decisions or []

    except Exception as e:
        print(f"❌ Enhanced Consensus Engine Error: {e}")
        return []

def _get_comprehensive_market_analysis(raw_data: str) -> Optional[Dict]:
    """Step 1: Get comprehensive market analysis covering all signals"""

    analyst_prompt = f"""You are a senior quantitative analyst for a professional crypto trading firm. Analyze ALL available market data comprehensively and respond ONLY with a JSON object.

Raw Market Data:
{raw_data}

Analyze EVERYTHING in the data - don't limit to just 3 signals. Look for:
- Price movements and trends across all mentioned tokens
- Market sentiment indicators and fear/greed signals
- Volume patterns and trading activity
- News sentiment and market catalysts
- Technical indicators and market structure
- Cross-asset correlations and sector rotations

IMPORTANT: Respond with ONLY the JSON object below, no other text:

{{
  "market_sentiment": {{"overall": "bullish/neutral/bearish", "strength": 0.0-1.0, "reasoning": "explanation"}},
  "top_opportunities": [
    {{"token": "BTC", "signal_strength": 0.85, "reasoning": "Strong bullish signals due to..."}},
    {{"token": "ETH", "signal_strength": 0.72, "reasoning": "Moderate opportunity because..."}},
    {{"token": "SOL", "signal_strength": 0.91, "reasoning": "High confidence due to..."}}
  ],
  "risk_factors": [
    "Risk factor 1 explanation",
    "Risk factor 2 explanation",
    "Risk factor 3 explanation"
  ],
  "market_catalysts": [
    "Positive catalyst 1",
    "Positive catalyst 2"
  ],
  "technical_outlook": {{"trend": "bullish/neutral/bearish", "strength": 0.0-1.0}},
  "recommended_position_sizing": {{"conservative": 0.3, "moderate": 0.5, "aggressive": 0.8}}
}}"""

    try:
        response = get_llm_response(analyst_prompt, ANALYST_MODEL)
        if not response:
            return None

        # Extract and parse JSON
        json_start = response.find('{')
        json_end = response.rfind('}') + 1

        if json_start != -1 and json_end != -1:
            json_part = response[json_start:json_end]
            market_analysis = json.loads(json_part)

            # Validate structure
            required_keys = ['market_sentiment', 'top_opportunities', 'risk_factors']
            if all(key in market_analysis for key in required_keys):
                return market_analysis
            else:
                print(f"⚠️  Invalid market analysis structure")
                return None
        else:
            return None

    except json.JSONDecodeError as e:
        print(f"⚠️  Failed to parse market analysis: {e}")
        return None

def _identify_trading_opportunities(market_analysis: Dict, raw_data: str) -> Optional[List[Dict]]:
    """Step 2: Identify specific trading opportunities from analysis"""

    opportunities_prompt = f"""You are an aggressive opportunity-focused crypto trader with access to comprehensive market data. Your job is to identify the TOP TRADING OPPORTUNITIES right now.

Market Analysis Summary:
{json.dumps(market_analysis, indent=2)}

Full Raw Data Available:
{raw_data[:1500]}...

Based on this analysis, identify SPECIFIC TRADING OPPORTUNITIES (up to 5 maximum). Focus on:
- Tokens with strongest bullish signals
- High-probability setups with good risk/reward
- Momentum plays and breakout opportunities
- Undervalued assets with catalyst potential

IMPORTANT: Respond with ONLY the JSON object below, no other text:

{{
  "opportunities": [
    {{
      "token": "BTC",
      "action": "BUY",
      "confidence_score": 0.85,
      "reasoning": "Specific reason for this trade",
      "expected_return": 0.15,
      "time_horizon": "short/medium/long",
      "catalyst": "What will drive this move",
      "entry_strategy": "How to enter this position"
    }},
    {{
      "token": "ETH",
      "action": "BUY",
      "confidence_score": 0.72,
      "reasoning": "Another specific opportunity",
      "expected_return": 0.12,
      "time_horizon": "medium",
      "catalyst": "Key driver",
      "entry_strategy": "Entry approach"
    }}
  ]
}}"""

    try:
        response = get_llm_response(opportunities_prompt, OPPORTUNITIES_MODEL)
        if not response:
            return None

        # Extract and parse JSON
        json_start = response.find('{')
        json_end = response.rfind('}') + 1

        if json_start != -1 and json_end != -1:
            json_part = response[json_start:json_end]
            opportunities_data = json.loads(json_part)

            if 'opportunities' in opportunities_data:
                return opportunities_data['opportunities']

        return None

    except json.JSONDecodeError as e:
        print(f"⚠️  Failed to parse opportunities: {e}")
        return None

def _assess_opportunity_risks(opportunities: List[Dict], market_analysis: Dict) -> Optional[List[Dict]]:
    """Step 3: Comprehensive risk assessment for each opportunity"""

    risk_prompt = f"""You are a senior risk manager for a crypto trading firm. Your job is to assess and enhance these trading opportunities with comprehensive risk analysis.

Identified Opportunities:
{json.dumps(opportunities, indent=2)}

Market Context:
{json.dumps(market_analysis, indent=2)}

For EACH opportunity, provide detailed risk assessment and enhanced parameters. Consider:
- Maximum drawdown potential
- Volatility and position sizing
- Market correlation risks
- Liquidity considerations
- Stop-loss and take-profit levels

IMPORTANT: Respond with ONLY the JSON object below, no other text:

{{
  "risk_assessed_opportunities": [
    {{
      "token": "BTC",
      "action": "BUY",
      "confidence_score": 0.85,
      "reasoning": "Enhanced reasoning with risk context",
      "expected_return": 0.15,
      "max_drawdown": 0.08,
      "volatility_score": 0.6,
      "recommended_position_size": 0.4,
      "stop_loss_percent": 5.0,
      "take_profit_percent": 12.0,
      "risk_level": "MEDIUM",
      "priority_score": 0.88,
      "time_horizon": "short"
    }}
  ]
}}"""

    try:
        response = get_llm_response(risk_prompt, RISK_ASSESSMENT_MODEL)
        if not response:
            return None

        # Extract and parse JSON
        json_start = response.find('{')
        json_end = response.rfind('}') + 1

        if json_start != -1 and json_end != -1:
            json_part = response[json_start:json_end]
            risk_data = json.loads(json_part)

            if 'risk_assessed_opportunities' in risk_data:
                return risk_data['risk_assessed_opportunities']

        return None

    except json.JSONDecodeError as e:
        print(f"⚠️  Failed to parse risk assessment: {e}")
        return None

def _get_portfolio_strategy_decisions(opportunities: List[Dict], market_analysis: Dict) -> Optional[List[Dict]]:
    """Step 4: Final portfolio strategy and trade selection (up to 3 trades)"""

    portfolio_prompt = f"""You are the Chief Investment Officer of a crypto trading firm. Make the final decision on which trades to execute. You can execute UP TO 3 TRADES maximum per cycle.

Risk-Assessed Opportunities:
{json.dumps(opportunities, indent=2)}

Market Context:
{json.dumps(market_analysis, indent=2)}

SELECTION CRITERIA:
1. Choose only the HIGHEST QUALITY opportunities (confidence ≥ 65%)
2. Prioritize by risk-adjusted returns and probability of success
3. Ensure portfolio diversification (don't over-concentrate)
4. Consider correlation between selected assets
5. Execute UP TO 3 trades maximum - quality over quantity

IMPORTANT: Respond with ONLY the JSON object below, no other text:

{{
  "final_decisions": [
    {{
      "action": "BUY",
      "token": "BTC",
      "justification": "Primary reason for selection",
      "confidence_score": 0.85,
      "amount_usd": 25.0,
      "confidence": 0.85,
      "reasoning": "Detailed reasoning",
      "risk_level": "MEDIUM",
      "stop_loss_percent": 5.0,
      "take_profit_percent": 12.0,
      "priority": 1,
      "execution_urgency": "high/medium/low"
    }}
  ]
}}"""

    try:
        response = get_llm_response(portfolio_prompt, PORTFOLIO_STRATEGIST_MODEL)
        if not response:
            return None

        # Extract and parse JSON
        json_start = response.find('{')
        json_end = response.rfind('}') + 1

        if json_start != -1 and json_end != -1:
            json_part = response[json_start:json_end]
            decisions_data = json.loads(json_part)

            if 'final_decisions' in decisions_data:
                final_decisions = decisions_data['final_decisions']

                # Process and enhance each decision
                processed_decisions = []
                risk_params = config.get_dynamic_risk_params()

                for i, decision in enumerate(final_decisions[:3]):  # Maximum 3 trades
                    if decision.get('action') in ['BUY', 'SELL'] and decision.get('confidence_score', 0) >= 0.65:
                        # Set appropriate amount based on position in priority
                        # Use 70% of max for more substantial trades
                        base_amount = risk_params['MAX_TRADE_USD'] * 0.70  # 70% of max per trade (more aggressive)

                        # Scale down for secondary/tertiary positions
                        if i == 1:  # Second trade gets 80% of base
                            decision['amount_usd'] = round(base_amount * 0.8, 2)
                        elif i == 2:  # Third trade gets 60% of base
                            decision['amount_usd'] = round(base_amount * 0.6, 2)
                        else:  # First trade gets full amount
                            decision['amount_usd'] = round(base_amount, 2)

                        # Ensure minimum trade size with more aggressive limit
                        conservative_limit = risk_params['MAX_TRADE_USD'] * 0.85  # 85% of max trade limit
                        decision['amount_usd'] = max(min(decision['amount_usd'], conservative_limit), 5.0)

                        # Set defaults for missing fields
                        decision.setdefault('confidence', decision.get('confidence_score', 0.7))
                        decision.setdefault('reasoning', decision.get('justification', 'Enhanced consensus decision'))
                        decision.setdefault('risk_level', 'MEDIUM')
                        decision.setdefault('stop_loss_percent', 5.0)
                        decision.setdefault('take_profit_percent', 10.0)

                        processed_decisions.append(decision)

                return processed_decisions

        return None

    except json.JSONDecodeError as e:
        print(f"⚠️  Failed to parse portfolio decisions: {e}")
        return None

# Backward compatibility function that returns single decision (highest priority)
def get_consensus_decision_sync(raw_data: str) -> Optional[Dict]:
    """
    Backward compatibility function that returns the highest priority decision
    """
    decisions = get_enhanced_consensus_decisions(raw_data)
    if decisions:
        # Return the highest priority decision
        return max(decisions, key=lambda x: x.get('confidence_score', 0))
    return None