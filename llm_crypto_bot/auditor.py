import requests
import json
from typing import Dict, Optional, List
from datetime import datetime
import config
from utils.llm import analyze_contract_security

class ContractAuditor:
    """Smart contract security auditor using LLM analysis"""
    
    def __init__(self):
        self.audit_cache: Dict[str, Dict] = {}
        self.audit_history: List[Dict] = []
    
    def audit_contract(self, token_address: str, force_refresh: bool = False) -> Optional[Dict]:
        """
        Audit a smart contract for security vulnerabilities
        
        Args:
            token_address: Contract address to audit
            force_refresh: Force fresh audit even if cached
            
        Returns:
            Security audit results
        """
        if not token_address:
            return self._create_error_result("Invalid token address")
        
        # Check cache first (unless force refresh)
        if not force_refresh and token_address in self.audit_cache:
            cached_result = self.audit_cache[token_address]
            cache_age = datetime.now() - datetime.fromisoformat(cached_result['timestamp'])
            
            if cache_age.total_seconds() < 3600:  # 1 hour cache
                print(f"📋 Using cached audit for {token_address}")
                return cached_result
        
        print(f"🔍 Starting security audit for contract: {token_address}")
        
        try:
            # Step 1: Fetch contract source code
            contract_source = self._fetch_contract_source(token_address)
            
            if not contract_source:
                return self._create_error_result("Could not fetch contract source code")
            
            # Step 2: Analyze with LLM
            print("🧠 Analyzing contract with LLM...")
            security_analysis = analyze_contract_security(contract_source, token_address)
            
            if not security_analysis:
                return self._create_error_result("LLM analysis failed")
            
            # Step 3: Add metadata and validation
            audit_result = self._create_audit_result(
                token_address, 
                contract_source, 
                security_analysis
            )
            
            # Step 4: Cache and store result
            self.audit_cache[token_address] = audit_result
            self.audit_history.append(audit_result)
            
            # Step 5: Log results
            self._log_audit_result(audit_result)
            
            return audit_result
            
        except Exception as e:
            error_result = self._create_error_result(f"Audit failed: {str(e)}")
            print(f"❌ Contract audit error: {e}")
            return error_result
    
    def _fetch_contract_source(self, token_address: str) -> Optional[str]:
        """Fetch contract source code from block explorer"""
        
        if not config.POLYGONSCAN_API_KEY:
            print("⚠️  PolygonScan API key not configured. Using mock contract data.")
            return self._get_mock_contract_source()
        
        # Determine API endpoint based on network
        if 'bsc' in config.RPC_URL.lower():
            api_url = "https://api.bscscan.com/api"
        elif 'polygon' in config.RPC_URL.lower() or 'matic' in config.RPC_URL.lower():
            api_url = "https://api.polygonscan.com/api"
        else:
            api_url = "https://api.etherscan.io/api"
        
        params = {
            'module': 'contract',
            'action': 'getsourcecode',
            'address': token_address,
            'apikey': config.POLYGONSCAN_API_KEY
        }
        
        try:
            response = requests.get(api_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == '1' and data['result']:
                source_code = data['result'][0].get('SourceCode', '')
                contract_name = data['result'][0].get('ContractName', 'Unknown')
                
                if source_code:
                    print(f" Retrieved source code for {contract_name}")
                    return source_code
                else:
                    print("⚠️  Source code not verified on explorer")
                    return None
            else:
                print(f"❌ API error: {data.get('message', 'Unknown error')}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching contract source: {e}")
            return None
    
    def _get_mock_contract_source(self) -> str:
        """Return mock contract source for testing"""
        return """
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract MockToken is ERC20, Ownable {
    uint256 private constant TOTAL_SUPPLY = 1000000 * 10**18;
    
    constructor() ERC20("MockToken", "MOCK") {
        _mint(msg.sender, TOTAL_SUPPLY);
    }
    
    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
    }
    
    function burn(uint256 amount) external {
        _burn(msg.sender, amount);
    }
}
"""
    
    def _create_audit_result(self, address: str, source: str, analysis: Dict) -> Dict:
        """Create comprehensive audit result"""
        
        result = {
            'contract_address': address,
            'timestamp': datetime.now().isoformat(),
            'source_code_length': len(source),
            'analysis': analysis,
            'audit_version': '1.0',
            'auditor': 'LLM Crypto Bot'
        }
        
        # Add risk assessment
        result['risk_assessment'] = self._assess_overall_risk(analysis)
        
        # Add trading recommendation
        result['trading_recommendation'] = self._get_trading_recommendation(analysis)
        
        return result
    
    def _assess_overall_risk(self, analysis: Dict) -> Dict:
        """Assess overall risk based on LLM analysis"""
        
        security_score = analysis.get('security_score', 50)
        risk_level = analysis.get('risk_level', 'MEDIUM')
        is_honeypot = analysis.get('is_honeypot', False)
        vulnerabilities = analysis.get('vulnerabilities', [])
        
        if is_honeypot:
            overall_risk = 'CRITICAL'
            risk_score = 0
        elif risk_level == 'CRITICAL' or security_score < 30:
            overall_risk = 'HIGH'
            risk_score = 25
        elif risk_level == 'HIGH' or security_score < 50:
            overall_risk = 'MEDIUM'
            risk_score = 50
        elif risk_level == 'MEDIUM' or security_score < 70:
            overall_risk = 'LOW'
            risk_score = 75
        else:
            overall_risk = 'VERY_LOW'
            risk_score = 90
        
        return {
            'overall_risk': overall_risk,
            'risk_score': risk_score,
            'vulnerability_count': len(vulnerabilities),
            'honeypot_detected': is_honeypot
        }
    
    def _get_trading_recommendation(self, analysis: Dict) -> str:
        """Get trading recommendation based on analysis"""
        
        recommendation = analysis.get('recommendation', 'CAUTION')
        security_score = analysis.get('security_score', 50)
        is_honeypot = analysis.get('is_honeypot', False)
        
        if is_honeypot:
            return "AVOID - Honeypot detected"
        elif recommendation == 'AVOID' or security_score < 30:
            return "AVOID - High security risk"
        elif recommendation == 'CAUTION' or security_score < 60:
            return "CAUTION - Medium security risk"
        else:
            return "ACCEPTABLE - Low security risk"
    
    def _log_audit_result(self, result: Dict):
        """Log audit result to console"""
        analysis = result['analysis']
        risk = result['risk_assessment']
        
        print(f"\n= Security Audit Complete:")
        print(f"✅   Contract: {result['contract_address']}")
        print(f"✅   Security Score: {analysis.get('security_score', 'N/A')}/100")
        print(f"✅   Risk Level: {analysis.get('risk_level', 'UNKNOWN')}")
        print(f"✅   Overall Risk: {risk['overall_risk']}")
        print(f"✅   Honeypot: {'YES' if analysis.get('is_honeypot', False) else 'NO'}")
        print(f"✅   Vulnerabilities: {risk['vulnerability_count']}")
        print(f"✅   Recommendation: {result['trading_recommendation']}")
        
        if analysis.get('vulnerabilities'):
            print(f"✅   Issues Found:")
            for vuln in analysis['vulnerabilities'][:3]:  # Show top 3
                print(f"✅     - {vuln}")
        
        print(f"✅   Summary: {analysis.get('summary', 'No summary available')}")
    
    def _create_error_result(self, error_message: str) -> Dict:
        """Create error result"""
        return {
            'status': 'ERROR',
            'timestamp': datetime.now().isoformat(),
            'error': error_message,
            'risk_assessment': {
                'overall_risk': 'UNKNOWN',
                'risk_score': 0,
                'vulnerability_count': 0,
                'honeypot_detected': False
            },
            'trading_recommendation': 'AVOID - Audit failed'
        }
    
    def get_audit_history(self, limit: int = 10) -> List[Dict]:
        """Get recent audit history"""
        return self.audit_history[-limit:] if self.audit_history else []
    
    def clear_cache(self):
        """Clear audit cache"""
        self.audit_cache.clear()
        print("📋  Audit cache cleared")

# Global auditor instance
contract_auditor = ContractAuditor()

def audit_contract(token_address: str, force_refresh: bool = False) -> Optional[Dict]:
    """
    Main function to audit a contract
    
    Args:
        token_address: Contract address to audit
        force_refresh: Force fresh audit
        
    Returns:
        Audit results
    """
    return contract_auditor.audit_contract(token_address, force_refresh)

def get_audit_history(limit: int = 10) -> List[Dict]:
    """Get audit history"""
    return contract_auditor.get_audit_history(limit)

def is_contract_safe(token_address: str, min_security_score: int = 60) -> bool:
    """
    Quick safety check for a contract
    
    Args:
        token_address: Contract to check
        min_security_score: Minimum acceptable security score
        
    Returns:
        True if contract appears safe
    """
    audit_result = audit_contract(token_address)
    
    if not audit_result or audit_result.get('status') == 'ERROR':
        return False
    
    analysis = audit_result.get('analysis', {})
    security_score = analysis.get('security_score', 0)
    is_honeypot = analysis.get('is_honeypot', True)
    
    return security_score >= min_security_score and not is_honeypot

def batch_audit_tokens(token_addresses: List[str]) -> Dict[str, Dict]:
    """
    Audit multiple tokens in batch
    
    Args:
        token_addresses: List of contract addresses
        
    Returns:
        Dictionary mapping addresses to audit results
    """
    results = {}
    
    print(f"🔍 Starting batch audit of {len(token_addresses)} contracts...")
    
    for i, address in enumerate(token_addresses, 1):
        print(f"\n📋 Auditing {i}/{len(token_addresses)}: {address}")
        results[address] = audit_contract(address)
    
    print(f"\n Batch audit complete. {len(results)} contracts audited.")
    return results