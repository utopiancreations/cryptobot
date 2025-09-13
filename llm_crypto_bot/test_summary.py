# test_summary.py
"""
Comprehensive test summary for LLM Crypto Trading Bot
Runs all integration tests and provides a complete status report
"""

import subprocess
import sys

def run_test(test_name, test_file):
    """Run a test and capture results"""
    print(f"\n{'='*60}")
    print(f"🧪 RUNNING TEST: {test_name}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(result.stdout)
            return True, "PASSED"
        else:
            print(f"❌ Test failed with return code {result.returncode}")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False, "FAILED"
            
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    except Exception as e:
        return False, f"ERROR: {e}"

def main():
    print("🤖 LLM Crypto Trading Bot - Integration Test Suite")
    print("=" * 70)
    
    tests = [
        ("Wallet & Blockchain Connection", "test_wallet.py"),
        ("Real-Time News Feeds", "test_feeds.py"),
        ("Contract Security Auditor", "test_auditor.py")
    ]
    
    results = {}
    
    for test_name, test_file in tests:
        success, status = run_test(test_name, test_file)
        results[test_name] = {"success": success, "status": status}
    
    # Final summary
    print(f"\n{'='*70}")
    print("🎯 INTEGRATION TEST SUMMARY")
    print(f"{'='*70}")
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status_emoji = "✅" if result["success"] else "❌"
        print(f"{status_emoji} {test_name}: {result['status']}")
        if result["success"]:
            passed += 1
    
    print(f"\n📊 Overall Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Bot is ready for deployment.")
        print("\n🚀 Next Steps:")
        print("   1. Configure API keys in .env file")
        print("   2. Fund wallet with MATIC for gas fees")
        print("   3. Start Ollama with llama3:8b model")
        print("   4. Run the bot: python3 main.py")
    else:
        print("⚠️  Some tests failed. Please review configuration.")
        print("\n🔧 Troubleshooting:")
        print("   - Check API keys in .env file")
        print("   - Verify RPC URL connectivity")
        print("   - Ensure Ollama is running with correct model")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)