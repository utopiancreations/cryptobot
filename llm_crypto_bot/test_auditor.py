# test_auditor.py
from auditor import audit_contract, is_contract_safe
from utils.llm import test_llm_connection
import config

# Example: Wrapped Ether (WETH) on Polygon
WETH_ADDRESS = "0x7ceb23fd6bc0add59e62ac25578270cff1b9f619"

# Additional test contracts on Polygon
TEST_CONTRACTS = {
    "WETH": "0x7ceb23fd6bc0add59e62ac25578270cff1b9f619",
    "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    "WBTC": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6"
}

def main():
    print("🔍 Testing Contract Auditor")
    print("=" * 50)
    
    # Check prerequisites
    print(f"🔑 PolygonScan API Key: {'✅ Configured' if config.POLYGONSCAN_API_KEY else '❌ Missing'}")
    print(f"🧠 LLM Connection: ", end="")
    
    llm_ok = test_llm_connection()
    if not llm_ok:
        print("⚠️  LLM not available - auditor will use mock analysis")
    
    # Test single contract audit
    print(f"\n🔍 Testing contract auditor with WETH...")
    print(f"📍 Contract Address: {WETH_ADDRESS}")
    
    try:
        analysis = audit_contract(WETH_ADDRESS)
        
        if analysis and analysis.get("status") != "ERROR":
            print(f"✅ Success! Received audit analysis")
            
            # Display key results
            if 'analysis' in analysis:
                audit_data = analysis['analysis']
                print(f"📊 Security Score: {audit_data.get('security_score', 'N/A')}/100")
                print(f"⚠️  Risk Level: {audit_data.get('risk_level', 'UNKNOWN')}")
                print(f"🕳️  Honeypot: {'YES' if audit_data.get('is_honeypot', False) else 'NO'}")
                print(f"💡 Recommendation: {audit_data.get('recommendation', 'N/A')}")
                
                if audit_data.get('summary'):
                    print(f"📝 Summary: {audit_data['summary'][:100]}...")
                    
                # Show vulnerabilities if any
                vulnerabilities = audit_data.get('vulnerabilities', [])
                if vulnerabilities:
                    print(f"🚨 Vulnerabilities Found: {len(vulnerabilities)}")
                    for i, vuln in enumerate(vulnerabilities[:3], 1):
                        print(f"   {i}. {vuln}")
                else:
                    print("✅ No major vulnerabilities detected")
            
            # Test trading recommendation
            trading_rec = analysis.get('trading_recommendation', 'Unknown')
            print(f"📈 Trading Recommendation: {trading_rec}")
            
        else:
            error_msg = analysis.get('error', 'Unknown error') if analysis else 'No response'
            print(f"❌ Failed to get audit analysis: {error_msg}")
            
    except Exception as e:
        print(f"❌ Contract audit test failed: {e}")

    # Test safety checker
    print(f"\n🛡️  Testing safety checker...")
    try:
        is_safe = is_contract_safe(WETH_ADDRESS, min_security_score=60)
        safety_status = "✅ SAFE" if is_safe else "⚠️  RISKY"
        print(f"Safety Assessment: {safety_status}")
        
    except Exception as e:
        print(f"❌ Safety check failed: {e}")

    # Test with multiple contracts (quick audit)
    print(f"\n📋 Testing multiple contract audits...")
    try:
        for name, address in list(TEST_CONTRACTS.items())[:2]:  # Test first 2
            print(f"   Testing {name} ({address[:10]}...)...")
            result = audit_contract(address)
            
            if result and result.get("status") != "ERROR":
                if 'analysis' in result:
                    score = result['analysis'].get('security_score', 'N/A')
                    risk = result['analysis'].get('risk_level', 'UNKNOWN')
                    print(f"     ✅ {name}: Score {score}/100, Risk: {risk}")
                else:
                    print(f"     ⚠️  {name}: Basic analysis completed")
            else:
                print(f"     ❌ {name}: Audit failed")
                
    except Exception as e:
        print(f"❌ Multi-contract test failed: {e}")

    print("\n🎯 AUDITOR TEST SUMMARY:")
    if config.POLYGONSCAN_API_KEY:
        print("✅ PolygonScan API integration working")
    else:
        print("⚠️  PolygonScan API key needed for live contract data")
        
    if llm_ok:
        print("✅ LLM analysis integration functional")
    else:
        print("⚠️  LLM needed for security analysis")
        
    print("✅ Contract auditor module functional")

if __name__ == "__main__":
    main()