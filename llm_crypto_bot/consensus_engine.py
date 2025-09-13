"""
Multi-Agent Consensus Engine for Crypto Trading Bot

This module orchestrates a sophisticated debate between multiple LLM models
to arrive at robust trading decisions through a three-step process:
1. Analyst: Summarizes raw data into structured market brief
2. Debate: Bullish agent vs Cautious agent present opposing viewpoints  
3. Strategist: Makes final consensus decision based on all arguments
"""

import json
import asyncio
from typing import Dict, Optional, Any
from utils.llm import get_llm_response
import config

# Define model names for different agents
ANALYST_MODEL = "llama3:8b"
BULLISH_MODEL = "gemma2:9b"
CAUTIOUS_MODEL = "llama3:8b"
STRATEGIST_MODEL = "llama3:8b"

def get_consensus_decision(raw_data: str) -> Optional[Dict]:
    """
    Orchestrates a multi-agent debate to arrive at a trading decision.
    
    Args:
        raw_data: Raw market data formatted as string
        
    Returns:
        Final trading decision dictionary or None if error
    """
    print("🤖 Consensus Engine Activated...")
    
    try:
        # Step 1: Analyst Summarization
        print("📊 Step 1: Analyst analyzing market data...")
        market_brief = _get_analyst_summary(raw_data)
        if not market_brief:
            print("❌ Analyst failed to provide market brief")
            return None
        
        print("✅ Analyst completed market brief")
        
        # Step 2: The Debate
        print("💬 Step 2: Starting multi-agent debate...")
        
        # Get bullish arguments
        print("🟢 Bullish agent presenting case...")
        bullish_arguments = _get_bullish_arguments(market_brief)
        if not bullish_arguments:
            print("❌ Bullish agent failed to provide arguments")
            return None
        
        print("✅ Bullish case presented")
        
        # Get cautious rebuttal
        print("🟡 Cautious agent providing rebuttal...")
        cautious_arguments = _get_cautious_rebuttal(market_brief, bullish_arguments)
        if not cautious_arguments:
            print("❌ Cautious agent failed to provide rebuttal")
            return None
            
        print("✅ Cautious rebuttal completed")
        
        # Step 3: The Final Consensus
        print("⚖️  Step 3: Strategist making final decision...")
        final_decision = _get_strategist_consensus(market_brief, bullish_arguments, cautious_arguments)
        if not final_decision:
            print("❌ Strategist failed to reach consensus")
            return None
            
        print("✅ Consensus reached!")
        print(f"🎯 Final Decision: {final_decision.get('action', 'Unknown')}")
        
        return final_decision
        
    except Exception as e:
        print(f"❌ Consensus Engine Error: {e}")
        return None

def _get_analyst_summary(raw_data: str) -> Optional[Dict]:
    """Step 1: Get structured market analysis from analyst"""
    
    analyst_prompt = f"""You are a quantitative financial analyst for a crypto trading bot. Analyze this market data and respond ONLY with a JSON object containing the top 3 bullish and bearish signals.

Raw Data:
{raw_data}

IMPORTANT: Respond with ONLY the JSON object below, no other text:

{{
  "bullish_signals": [
    "Signal 1 explanation",
    "Signal 2 explanation", 
    "Signal 3 explanation"
  ],
  "bearish_signals": [
    "Signal 1 explanation",
    "Signal 2 explanation",
    "Signal 3 explanation"
  ]
}}"""

    try:
        response = get_llm_response(analyst_prompt, ANALYST_MODEL)
        if not response:
            print("❌ Analyst returned empty response")
            return None
            
        print(f"📝 Analyst raw response: {response[:200]}...")
        
        # Try to extract JSON from response
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        
        if json_start != -1 and json_end != -1:
            json_part = response[json_start:json_end]
            print(f"🔧 Extracted JSON: {json_part[:100]}...")
        else:
            print("❌ No JSON found in response")
            return None
        
        # Try to parse as JSON
        market_brief = json.loads(json_part)
        
        # Validate structure
        if "bullish_signals" in market_brief and "bearish_signals" in market_brief:
            return market_brief
        else:
            print(f"⚠️  Invalid analyst response structure: {market_brief}")
            return None
            
    except json.JSONDecodeError as e:
        print(f"⚠️  Failed to parse analyst response as JSON: {e}")
        return None

def _get_bullish_arguments(market_brief: Dict) -> Optional[str]:
    """Step 2a: Get bullish trading arguments"""
    
    bullish_prompt = f"""You are an aggressive, growth-focused crypto trader. Your persona is optimistic and your primary goal is to identify high-potential trading opportunities. You have received the following market brief from your analyst.

Market Brief:
{json.dumps(market_brief, indent=2)}

Based on this brief, construct the strongest possible argument for a **BUY** action. Focus exclusively on the bullish signals and the potential upside. Frame your argument clearly and concisely."""

    return get_llm_response(bullish_prompt, BULLISH_MODEL)

def _get_cautious_rebuttal(market_brief: Dict, bullish_arguments: str) -> Optional[str]:
    """Step 2b: Get cautious rebuttal to bullish arguments"""
    
    cautious_prompt = f"""You are a skeptical, risk-averse portfolio manager. Your primary goal is capital preservation. An aggressive junior trader has proposed a BUY action based on the following arguments and market brief. Your task is to be the devil's advocate.

Market Brief:
{json.dumps(market_brief, indent=2)}

Bullish Argument from Colleague:
{bullish_arguments}

Provide a strong, critical rebuttal. Systematically counter the bullish points and emphasize all potential risks, bearish signals, and reasons for caution. Conclude with your argument for a **SELL** or **HOLD** action."""

    return get_llm_response(cautious_prompt, CAUTIOUS_MODEL)

def _get_strategist_consensus(market_brief: Dict, bullish_arguments: str, cautious_arguments: str) -> Optional[Dict]:
    """Step 3: Get final consensus decision from strategist"""
    
    strategist_prompt = f"""You are the Lead Trading Strategist for a crypto trading firm. Your job is to make profitable decisions, not just preserve capital. Synthesize the debate between advisors and make a decision. Respond ONLY with a JSON object.

Market Brief: {json.dumps(market_brief, indent=2)}
Bullish Case: {bullish_arguments}
Cautious Case: {cautious_arguments}

TRADING PHILOSOPHY:
- We trade to PROFIT, not just to preserve capital
- Strong bullish signals with good fundamentals should trigger BUY decisions
- Only HOLD when signals are genuinely mixed or unclear
- Risk is managed through position sizing, not avoiding all trades
- Confidence should reflect the strength of signals, not fear of losses

CRITICAL INSTRUCTIONS:
1. Identify the primary asset being discussed (e.g., BTC, ETH, MATIC, SOL) in the analysis
2. Your final 'action' must be for that specific asset
3. If multiple strong bullish signals align, lean toward BUY with high confidence
4. If no specific asset can be identified from the data, the action must be HOLD
5. The 'token' field must contain the primary asset symbol (e.g., "BTC", "ETH", "MATIC")

IMPORTANT: Respond with ONLY the JSON object below, no other text:

{{
  "action": "BUY",
  "token": "BTC",
  "justification": "Your single sentence reasoning here",
  "confidence_score": 0.75
}}"""

    try:
        response = get_llm_response(strategist_prompt, STRATEGIST_MODEL)
        if not response:
            print("❌ Strategist returned empty response")
            return None
            
        print(f"📝 Strategist raw response: {response[:400]}...")
        print(f"🔍 Full response length: {len(response)} characters")
        
        # Try to extract JSON from response
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        
        if json_start != -1 and json_end != -1:
            json_part = response[json_start:json_end]
            print(f"🔧 Extracted JSON: {json_part[:100]}...")
        else:
            print("❌ No JSON found in strategist response")
            print(f"🔍 Raw response: '{response}'")
            # Try to extract the entire response as JSON if no braces found
            if response.strip():
                json_part = response.strip()
            else:
                return None
            
        # Try to parse as JSON
        decision = json.loads(json_part)
        
        # Validate required fields
        if "action" in decision:
            # Add additional fields expected by the executor
            if "action" in decision and decision["action"] in ["BUY", "SELL"]:
                # Use token from strategist decision, fallback to MATIC if not specified
                decision.setdefault("token", decision.get("token", "MATIC"))
                
                # Use dynamic trade amount based on wallet balance
                risk_params = config.get_dynamic_risk_params()
                # For real trades, use 40% of max (since real executor applies 50% limit)
                # For simulation, use 80% of max
                default_amount = max(risk_params['MAX_TRADE_USD'] * 0.4, 3.0)  # 40% of max, minimum $3
                decision.setdefault("amount_usd", round(default_amount, 2))
                decision.setdefault("confidence", decision.get("confidence_score", 0.5))
                decision.setdefault("reasoning", decision.get("justification", "Consensus decision"))
                decision.setdefault("risk_level", "MEDIUM")
                decision.setdefault("stop_loss_percent", 5.0)
                decision.setdefault("take_profit_percent", 10.0)
            
            return decision
        else:
            print(f"⚠️  Invalid strategist response: missing 'action' field")
            return None
            
    except json.JSONDecodeError as e:
        print(f"⚠️  Failed to parse strategist response as JSON: {e}")
        return None

# Alias for backward compatibility (function is now synchronous)
def get_consensus_decision_sync(raw_data: str) -> Optional[Dict]:
    """
    Alias for the consensus engine (now synchronous)
    
    Args:
        raw_data: Raw market data formatted as string
        
    Returns:
        Final trading decision dictionary or None if error
    """
    return get_consensus_decision(raw_data)