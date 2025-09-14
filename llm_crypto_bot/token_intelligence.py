"""
Advanced Token Intelligence System
Uses CoinMarketCap as primary data source with comprehensive risk assessment
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from connectors.coinmarketcap_api import get_cmc_api
from auditor import audit_contract
import config

class TokenIntelligence:
    """Advanced token intelligence with CoinMarketCap integration"""

    def __init__(self):
        self.cmc_api = get_cmc_api()
        self.intelligence_cache = {}
        self.contract_cache = {}

    def get_comprehensive_token_analysis(self, token_symbol: str, force_refresh: bool = False) -> Dict:
        """
        Get comprehensive token analysis using CoinMarketCap as primary source

        Returns:
            Complete token intelligence with risk scoring
        """
        cache_key = f"{token_symbol.upper()}_{datetime.now().strftime('%Y%m%d_%H')}"

        # Check cache (1 hour TTL)
        if not force_refresh and cache_key in self.intelligence_cache:
            print(f"📋 Using cached intelligence for {token_symbol}")
            return self.intelligence_cache[cache_key]

        print(f"🔍 Analyzing {token_symbol} with comprehensive intelligence...")

        analysis = {
            'token_symbol': token_symbol.upper(),
            'timestamp': datetime.now().isoformat(),
            'cmc_data': {},
            'contract_info': {},
            'security_audit': {},
            'legitimacy_score': 0,
            'risk_assessment': {},
            'trading_recommendation': 'UNKNOWN',
            'confidence_level': 0.0,
            'data_sources': [],
            'red_flags': [],
            'green_flags': []
        }

        # Step 1: Get CoinMarketCap data (primary source)
        cmc_data = self._get_cmc_intelligence(token_symbol)
        analysis['cmc_data'] = cmc_data

        if cmc_data:
            analysis['data_sources'].append('CoinMarketCap')
            print(f"✅ Found {token_symbol} on CoinMarketCap (Rank #{cmc_data.get('cmc_rank', 'N/A')})")

            # Step 2: Get contract information
            contract_address = self._extract_contract_address(cmc_data)
            if contract_address:
                platform = cmc_data.get('platform') or {}
                analysis['contract_info'] = {
                    'address': contract_address,
                    'blockchain': platform.get('name', 'Unknown'),
                    'verified': True  # If on CMC, it's verified
                }

                # Step 3: Perform security audit if we have contract
                security_audit = self._perform_security_audit(contract_address, token_symbol)
                analysis['security_audit'] = security_audit
                analysis['data_sources'].append('Contract Audit')

            # Step 4: Calculate comprehensive risk assessment
            risk_assessment = self._calculate_comprehensive_risk(cmc_data, analysis.get('security_audit', {}))
            analysis['risk_assessment'] = risk_assessment
            analysis['legitimacy_score'] = risk_assessment['legitimacy_score']
            analysis['trading_recommendation'] = risk_assessment['recommendation']
            analysis['confidence_level'] = risk_assessment['confidence']
            analysis['red_flags'] = risk_assessment['red_flags']
            analysis['green_flags'] = risk_assessment['green_flags']

        else:
            print(f"❌ {token_symbol} not found on CoinMarketCap")
            analysis['red_flags'].append('Token not listed on CoinMarketCap')

            # For unlisted tokens, use gem-friendly scoring
            # Many gems are not on CoinMarketCap before they explode
            analysis['legitimacy_score'] = 60  # Moderate score - let LLM analysis drive decision
            analysis['trading_recommendation'] = 'MODERATE_BUY'  # Moderate risk - good for gems
            analysis['confidence_level'] = 0.4  # Lower confidence, but let LLM confidence take priority

        # Cache the result
        self.intelligence_cache[cache_key] = analysis

        print(f"📊 Intelligence Analysis Complete:")
        print(f"   Legitimacy Score: {analysis['legitimacy_score']}/100")
        print(f"   Recommendation: {analysis['trading_recommendation']}")
        print(f"   Confidence: {analysis['confidence_level']:.1%}")

        return analysis

    def _get_cmc_intelligence(self, token_symbol: str) -> Dict:
        """Get comprehensive data from CoinMarketCap"""
        try:
            # Get basic quote data
            quotes = self.cmc_api.get_token_quotes([token_symbol])
            quote_data = quotes.get(token_symbol.upper(), {})

            # Get detailed token info
            token_info = self.cmc_api.get_token_info(token_symbol)

            # Combine data
            combined_data = {**quote_data, **token_info}

            if combined_data and combined_data.get('symbol'):
                return combined_data

            # Fallback: search for the token
            search_results = self.cmc_api.search_tokens(token_symbol, limit=5)
            if search_results:
                # Take the first exact match or best match
                for result in search_results:
                    if result.get('symbol', '').upper() == token_symbol.upper():
                        return result
                # If no exact match, return first result
                return search_results[0]

            return {}

        except Exception as e:
            print(f"⚠️ Error getting CMC data for {token_symbol}: {e}")
            return {}

    def _extract_contract_address(self, cmc_data: Dict) -> Optional[str]:
        """Extract contract address from CMC data"""
        try:
            # From token info platform data
            platform = cmc_data.get('platform')
            if platform and isinstance(platform, dict):
                contract_address = platform.get('token_address')
                if contract_address and contract_address.startswith('0x') and len(contract_address) == 42:
                    return contract_address

            # From URLs (sometimes contract address is in explorer URLs)
            urls = cmc_data.get('urls', {})
            for url_type, url_list in urls.items():
                if url_type in ['explorer'] and url_list:
                    for url in url_list:
                        # Extract address from etherscan/bscscan URLs
                        match = re.search(r'0x[a-fA-F0-9]{40}', url)
                        if match:
                            return match.group()

            return None

        except Exception as e:
            print(f"⚠️ Error extracting contract address: {e}")
            return None

    def _perform_security_audit(self, contract_address: str, token_symbol: str) -> Dict:
        """Perform security audit on the contract"""
        try:
            print(f"🛡️ Performing security audit for {token_symbol}...")
            audit_result = audit_contract(contract_address, force_refresh=False)

            if audit_result and audit_result.get('status') != 'ERROR':
                return audit_result
            else:
                return {
                    'status': 'UNAVAILABLE',
                    'reason': 'Contract audit not available',
                    'risk_assessment': {
                        'overall_risk': 'UNKNOWN',
                        'risk_score': 50,  # Neutral
                        'honeypot_detected': False
                    }
                }

        except Exception as e:
            print(f"⚠️ Security audit error: {e}")
            return {
                'status': 'ERROR',
                'error': str(e),
                'risk_assessment': {
                    'overall_risk': 'UNKNOWN',
                    'risk_score': 50
                }
            }

    def _calculate_comprehensive_risk(self, cmc_data: Dict, security_audit: Dict) -> Dict:
        """Calculate comprehensive risk assessment"""

        legitimacy_score = 50  # Start with neutral
        red_flags = []
        green_flags = []
        risk_factors = []

        # CoinMarketCap factors (60% weight)
        cmc_rank = cmc_data.get('cmc_rank', 9999)
        market_cap = cmc_data.get('market_cap') or 0
        volume_24h = cmc_data.get('volume_24h') or 0
        price = cmc_data.get('price') or 0

        # Market Cap Assessment
        if market_cap > 1_000_000_000:  # $1B+
            legitimacy_score += 25
            green_flags.append('Large market cap ($1B+)')
        elif market_cap > 100_000_000:  # $100M+
            legitimacy_score += 20
            green_flags.append('Significant market cap ($100M+)')
        elif market_cap > 10_000_000:  # $10M+
            legitimacy_score += 10
            green_flags.append('Moderate market cap ($10M+)')
        elif market_cap < 1_000_000:  # < $1M
            legitimacy_score -= 15
            red_flags.append('Very low market cap (<$1M)')

        # CMC Rank Assessment
        if cmc_rank <= 100:
            legitimacy_score += 20
            green_flags.append('Top 100 token by market cap')
        elif cmc_rank <= 500:
            legitimacy_score += 10
            green_flags.append('Top 500 token')
        elif cmc_rank <= 1000:
            legitimacy_score += 5
        elif cmc_rank > 3000:
            legitimacy_score -= 10
            red_flags.append('Low market cap ranking (>3000)')

        # Volume Assessment
        if volume_24h > 10_000_000:  # $10M+ daily volume
            legitimacy_score += 10
            green_flags.append('High trading volume ($10M+)')
        elif volume_24h < 100_000:  # < $100K daily volume
            legitimacy_score -= 5
            red_flags.append('Low trading volume (<$100K)')

        # Price Assessment
        if price > 1000:
            legitimacy_score += 5
            green_flags.append('High token price ($1000+)')
        elif price < 0.000001:  # Very low price tokens are often scams
            legitimacy_score -= 10
            red_flags.append('Extremely low token price')

        # Platform Assessment
        platform = cmc_data.get('platform', {})
        if platform:
            platform_name = platform.get('name', '').lower()
            if platform_name in ['ethereum', 'binance smart chain', 'polygon']:
                legitimacy_score += 5
                green_flags.append(f'Listed on major blockchain ({platform.get("name")})')

        # Security Audit factors (40% weight)
        security_risk = security_audit.get('risk_assessment', {})
        security_score = security_risk.get('risk_score', 50)
        overall_risk = security_risk.get('overall_risk', 'UNKNOWN')
        is_honeypot = security_risk.get('honeypot_detected', False)

        if is_honeypot:
            legitimacy_score = 0  # Immediate disqualification
            red_flags.append('HONEYPOT DETECTED - Cannot sell tokens')
        elif overall_risk == 'CRITICAL':
            legitimacy_score -= 30
            red_flags.append('Critical security vulnerabilities found')
        elif overall_risk == 'HIGH':
            legitimacy_score -= 15
            red_flags.append('High security risk')
        elif overall_risk == 'MEDIUM':
            legitimacy_score -= 5
            red_flags.append('Medium security risk')
        elif overall_risk == 'LOW':
            legitimacy_score += 5
            green_flags.append('Low security risk')
        elif overall_risk == 'VERY_LOW':
            legitimacy_score += 10
            green_flags.append('Very low security risk')

        # Time-based factors
        date_added = cmc_data.get('date_added')
        if date_added:
            try:
                added_date = datetime.fromisoformat(date_added.replace('Z', '+00:00'))
                age_days = (datetime.now() - added_date.replace(tzinfo=None)).days

                if age_days > 365:  # > 1 year old
                    legitimacy_score += 10
                    green_flags.append('Established token (>1 year)')
                elif age_days < 30:  # < 1 month old
                    legitimacy_score -= 10
                    red_flags.append('Very new token (<1 month)')
                elif age_days < 90:  # < 3 months old
                    legitimacy_score -= 5
                    red_flags.append('New token (<3 months)')
            except:
                pass

        # Final score adjustment
        legitimacy_score = max(0, min(100, legitimacy_score))

        # Determine recommendation
        if is_honeypot:
            recommendation = 'AVOID'
            confidence = 0.95
        elif legitimacy_score >= 80:
            recommendation = 'STRONG_BUY'
            confidence = 0.85
        elif legitimacy_score >= 65:
            recommendation = 'BUY'
            confidence = 0.75
        elif legitimacy_score >= 50:
            recommendation = 'MODERATE_BUY'
            confidence = 0.65
        elif legitimacy_score >= 35:
            recommendation = 'CAUTION'
            confidence = 0.70
        elif legitimacy_score >= 20:
            recommendation = 'HIGH_RISK'
            confidence = 0.75
        else:
            recommendation = 'AVOID'
            confidence = 0.80

        return {
            'legitimacy_score': legitimacy_score,
            'recommendation': recommendation,
            'confidence': confidence,
            'red_flags': red_flags,
            'green_flags': green_flags,
            'risk_factors': {
                'market_cap': market_cap,
                'cmc_rank': cmc_rank,
                'volume_24h': volume_24h,
                'security_risk': overall_risk,
                'is_honeypot': is_honeypot
            }
        }

    def get_contract_address(self, token_symbol: str) -> Optional[str]:
        """Get contract address for a token"""
        analysis = self.get_comprehensive_token_analysis(token_symbol)
        return analysis.get('contract_info', {}).get('address')

    def is_token_safe_to_trade(self, token_symbol: str, min_score: int = 40) -> Tuple[bool, str]:
        """
        Quick safety check for trading

        Returns:
            (is_safe, reason)
        """
        analysis = self.get_comprehensive_token_analysis(token_symbol)

        legitimacy_score = analysis['legitimacy_score']
        is_honeypot = analysis.get('security_audit', {}).get('risk_assessment', {}).get('honeypot_detected', False)

        if is_honeypot:
            return False, "Honeypot detected"
        elif legitimacy_score >= min_score:
            return True, f"Score: {legitimacy_score}/100"
        else:
            return False, f"Low legitimacy score: {legitimacy_score}/100"

    def get_position_size_multiplier(self, token_symbol: str, llm_confidence: float = None) -> Tuple[float, str]:
        """
        Get position size multiplier based on token intelligence

        Returns:
            (multiplier, reason) where multiplier is 0.0-1.0
        """
        analysis = self.get_comprehensive_token_analysis(token_symbol)

        legitimacy_score = analysis['legitimacy_score']
        recommendation = analysis['trading_recommendation']
        is_honeypot = analysis.get('security_audit', {}).get('risk_assessment', {}).get('honeypot_detected', False)

        if is_honeypot:
            return 0.0, "Honeypot detected - cannot trade"
        elif recommendation == 'STRONG_BUY' and legitimacy_score >= 80:
            return 1.0, f"High confidence token (score: {legitimacy_score}/100)"
        elif recommendation == 'BUY' and legitimacy_score >= 65:
            return 0.8, f"Good token with minor risks (score: {legitimacy_score}/100)"
        elif recommendation == 'MODERATE_BUY' and legitimacy_score >= 50:
            # For unlisted tokens classified as MODERATE_BUY, boost with LLM confidence
            token_analysis = self.get_comprehensive_token_analysis(token_symbol)
            if 'Token not listed on CoinMarketCap' in token_analysis.get('red_flags', []) and llm_confidence:
                if llm_confidence >= 0.8:
                    return 0.7, f"Unlisted gem with high LLM confidence {llm_confidence:.0%} - boosted position"
                elif llm_confidence >= 0.6:
                    return 0.6, f"Unlisted gem with good LLM confidence {llm_confidence:.0%} - moderate boost"
            return 0.5, f"Moderate risk token (score: {legitimacy_score}/100)"
        elif recommendation == 'CAUTION' and legitimacy_score >= 35:
            return 0.25, f"High risk token (score: {legitimacy_score}/100)"
        elif recommendation == 'HIGH_RISK' and legitimacy_score >= 20:
            # For HIGH_RISK tokens (like unlisted ones), consider LLM confidence
            base_multiplier = 0.1
            if llm_confidence and llm_confidence >= 0.8:
                # If LLM is highly confident, allow larger position
                base_multiplier = 0.3  # 30% instead of 10%
                return base_multiplier, f"High-risk unlisted token but LLM confidence {llm_confidence:.0%} - moderate position"
            elif llm_confidence and llm_confidence >= 0.6:
                base_multiplier = 0.2  # 20% instead of 10%
                return base_multiplier, f"High-risk unlisted token with moderate LLM confidence {llm_confidence:.0%}"
            else:
                return base_multiplier, f"Very high risk token (score: {legitimacy_score}/100)"
        else:
            return 0.0, f"Avoid trading - too risky (score: {legitimacy_score}/100)"

# Global instance
_token_intelligence = None

def get_token_intelligence() -> TokenIntelligence:
    """Get global token intelligence instance"""
    global _token_intelligence
    if _token_intelligence is None:
        _token_intelligence = TokenIntelligence()
    return _token_intelligence

def analyze_token_comprehensive(token_symbol: str) -> Dict:
    """Analyze token comprehensively using CoinMarketCap and security audits"""
    return get_token_intelligence().get_comprehensive_token_analysis(token_symbol)

def get_token_contract_address(token_symbol: str) -> Optional[str]:
    """Get verified contract address for token from CoinMarketCap"""
    return get_token_intelligence().get_contract_address(token_symbol)

def calculate_smart_position_size(token_symbol: str, base_amount: float, llm_confidence: float = None) -> Tuple[float, str]:
    """Calculate smart position size based on token intelligence"""
    multiplier, reason = get_token_intelligence().get_position_size_multiplier(token_symbol, llm_confidence)
    adjusted_amount = base_amount * multiplier
    return adjusted_amount, reason

def test_token_intelligence():
    """Test the token intelligence system"""
    test_tokens = ['EIGEN', 'BTC', 'ETH', 'DOGE', 'SHIB']

    ti = get_token_intelligence()

    for token in test_tokens:
        print(f"\n🔍 Testing {token}:")
        analysis = ti.get_comprehensive_token_analysis(token)

        print(f"   Score: {analysis['legitimacy_score']}/100")
        print(f"   Recommendation: {analysis['trading_recommendation']}")
        print(f"   CMC Rank: #{analysis['cmc_data'].get('cmc_rank', 'N/A')}")
        print(f"   Market Cap: ${analysis['cmc_data'].get('market_cap', 0):,.0f}")

        multiplier, reason = ti.get_position_size_multiplier(token)
        print(f"   Position Multiplier: {multiplier:.1%} - {reason}")