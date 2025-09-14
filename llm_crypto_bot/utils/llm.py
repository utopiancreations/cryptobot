import json
import requests
from typing import Dict, Optional, Any
import config
import asyncio

def get_trade_decision(prompt: str) -> Optional[Dict]:
    """
    Get trading decision from local LLM using Ollama
    
    Args:
        prompt: The prompt containing news and market data
        
    Returns:
        Dictionary with trade decision or None if error
    """
    try:
        # Construct the full prompt with instructions
        full_prompt = _build_trading_prompt(prompt)
        
        # Make request to Ollama API
        response = requests.post(
            f"{config.OLLAMA_HOST}/api/generate",
            json={
                "model": config.OLLAMA_MODEL,
                "prompt": full_prompt,
                "format": "json",
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 1000  # Much higher for local model with comprehensive data
                }
            },
            timeout=300  # 5 minutes for local model to process comprehensive data
        )
        
        if response.status_code != 200:
            print(f"Ollama API error: {response.status_code}")
            return None
            
        response_data = response.json()
        llm_response = response_data.get('response', '').strip()
        
        print(f"Raw LLM Response: {llm_response}")
        
        # Try to parse as JSON
        try:
            decision = json.loads(llm_response)
            return _validate_decision(decision)
        except json.JSONDecodeError as e:
            print(f"Failed to parse LLM response as JSON: {e}")
            # Try to extract JSON from text
            return _extract_json_from_text(llm_response)
            
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to Ollama. Make sure Ollama is running at " + config.OLLAMA_HOST)
        return None
    except requests.exceptions.Timeout:
        print("Error: LLM request timed out")
        return None
    except Exception as e:
        print(f"Unexpected error calling LLM: {e}")
        return None

def _build_trading_prompt(news_data: str) -> str:
    """Build the complete prompt for the LLM"""
    
    risk_params = config.get_risk_params()
    
    prompt = f"""
You are a crypto trading AI analyzing market news to make trading decisions.

RISK PARAMETERS:
- Maximum trade amount: ${risk_params['MAX_TRADE_USD']} USD
- Daily loss limit: {risk_params['DAILY_LOSS_LIMIT_PERCENT']}%
- Token restrictions: DISABLED (can trade any token)

MARKET DATA:
{news_data}

INSTRUCTIONS:
Based on the news sentiment and market data, provide a trading decision in JSON format.
Only trade tokens from the approved whitelist.
Consider risk management and current market sentiment.

RESPONSE FORMAT (JSON only):
{{
    "action": "BUY|SELL|HOLD",
    "token": "SYMBOL",
    "amount_usd": 0.00,
    "confidence": 0.85,
    "reasoning": "Brief explanation of decision",
    "risk_level": "LOW|MEDIUM|HIGH",
    "stop_loss_percent": 5.0,
    "take_profit_percent": 10.0
}}

Respond with ONLY valid JSON, no additional text.
"""
    return prompt

def _validate_decision(decision: Dict) -> Optional[Dict]:
    """Validate the trading decision structure"""
    required_fields = ['action', 'token', 'amount_usd', 'confidence', 'reasoning']
    
    # Check required fields
    for field in required_fields:
        if field not in decision:
            print(f"Invalid decision: missing field '{field}'")
            return None
    
    # Validate action
    if decision['action'] not in ['BUY', 'SELL', 'HOLD']:
        print(f"Invalid action: {decision['action']}")
        return None
    
    # Token whitelist check removed - all tokens allowed
    # Note: Token restrictions are now handled by equivalency map in executor
    
    # Validate amount
    max_trade = config.RISK_PARAMETERS['MAX_TRADE_USD']
    if decision['amount_usd'] > max_trade:
        print(f"Trade amount ${decision['amount_usd']} exceeds limit ${max_trade}")
        decision['amount_usd'] = max_trade
        decision['reasoning'] += f" (Amount capped at ${max_trade})"
    
    # Validate confidence
    if not 0 <= decision['confidence'] <= 1:
        decision['confidence'] = max(0, min(1, decision['confidence']))
    
    # Set defaults for optional fields
    decision.setdefault('risk_level', 'MEDIUM')
    decision.setdefault('stop_loss_percent', 5.0)
    decision.setdefault('take_profit_percent', 10.0)
    
    return decision

def _extract_json_from_text(text: str) -> Optional[Dict]:
    """Try to extract JSON from text that might contain other content"""
    import re
    
    # Look for JSON-like structure
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    
    print("Could not extract valid JSON from LLM response")
    return None

def analyze_contract_security(contract_code: str, token_address: str) -> Optional[Dict]:
    """
    Analyze contract security using LLM
    
    Args:
        contract_code: Solidity contract source code
        token_address: Contract address for reference
        
    Returns:
        Security analysis results
    """
    if not contract_code.strip():
        return None
    
    prompt = f"""
You are a smart contract security auditor. Analyze the following Solidity contract for security vulnerabilities.

CONTRACT ADDRESS: {token_address}

CONTRACT CODE:
{contract_code[:2000]}  // Truncated for analysis

ANALYSIS REQUIRED:
1. Common vulnerabilities (reentrancy, overflow, etc.)
2. Honeypot indicators
3. Centralization risks
4. Unusual functions or behavior
5. Overall security rating

RESPONSE FORMAT (JSON only):
{{
    "security_score": 85,
    "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
    "vulnerabilities": ["list of issues found"],
    "warnings": ["potential concerns"],
    "is_honeypot": false,
    "recommendation": "SAFE|CAUTION|AVOID",
    "summary": "Brief security assessment"
}}

Respond with ONLY valid JSON, no additional text.
"""
    
    try:
        response = requests.post(
            f"{config.OLLAMA_HOST}/api/generate",
            json={
                "model": config.OLLAMA_MODEL,
                "prompt": prompt,
                "format": "json",
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 300
                }
            },
            timeout=60
        )
        
        if response.status_code != 200:
            return None
            
        response_data = response.json()
        llm_response = response_data.get('response', '').strip()
        
        try:
            return json.loads(llm_response)
        except json.JSONDecodeError:
            return _extract_json_from_text(llm_response)
            
    except Exception as e:
        print(f"Error analyzing contract security: {e}")
        return None

def analyze_text(prompt: str) -> Optional[str]:
    """
    Analyze text using local LLM

    Args:
        prompt: The text analysis prompt

    Returns:
        LLM analysis response or None if error
    """
    try:
        # Make request to Ollama API
        response = requests.post(
            f"{config.OLLAMA_HOST}/api/generate",
            json={
                "model": config.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 500
                }
            },
            timeout=60
        )

        if response.status_code != 200:
            print(f"Ollama API error in analyze_text: {response.status_code}")
            return None

        response_data = response.json()
        return response_data.get('response', '').strip()

    except Exception as e:
        print(f"Error in analyze_text: {e}")
        return None

def test_llm_connection() -> bool:
    """Test if LLM is accessible and responding"""
    try:
        response = requests.get(f"{config.OLLAMA_HOST}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [model['name'] for model in models]
            if config.OLLAMA_MODEL in model_names:
                print(f"✅ LLM connection successful. Model {config.OLLAMA_MODEL} is available.")
                return True
            else:
                print(f"⚠️  LLM connected but model {config.OLLAMA_MODEL} not found.")
                print(f"Available models: {', '.join(model_names)}")
                return False
        else:
            print(f"❌ LLM connection failed. Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to LLM: {e}")
        return False

def get_llm_response(prompt: str, model_name: str = None) -> Optional[str]:
    """
    Generic function to get response from any Ollama model
    
    Args:
        prompt: The prompt to send to the model
        model_name: Name of the model to use (defaults to config.OLLAMA_MODEL)
        
    Returns:
        String response from the model or None if error
    """
    if model_name is None:
        model_name = config.OLLAMA_MODEL
    
    try:
        # Make request to Ollama API
        response = requests.post(
            f"{config.OLLAMA_HOST}/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 1000
                }
            },
            timeout=300
        )
        
        if response.status_code != 200:
            print(f"Ollama API error for {model_name}: {response.status_code}")
            return None
            
        response_data = response.json()
        llm_response = response_data.get('response', '').strip()
        
        if not llm_response:
            print(f"⚠️  Empty response from {model_name}")
            print(f"🔍 Raw API response: {response_data}")
        
        return llm_response
        
    except Exception as e:
        print(f"Error getting response from {model_name}: {e}")
        return None