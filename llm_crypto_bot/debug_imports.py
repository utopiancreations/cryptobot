#!/usr/bin/env python3
"""
Debug script to test imports and see what's actually being called
"""

print("🔍 DEBUGGING IMPORTS AND FUNCTIONS")
print("=" * 50)

try:
    print("1. Testing enhanced_consensus_engine import...")
    from enhanced_consensus_engine import get_enhanced_consensus_decisions, get_consensus_decision_sync
    print("✅ Enhanced consensus engine imported successfully")

    print("2. Testing function signatures...")
    print(f"   get_enhanced_consensus_decisions: {get_enhanced_consensus_decisions}")
    print(f"   get_consensus_decision_sync: {get_consensus_decision_sync}")

    print("3. Testing basic functionality...")
    test_data = "BTC: $45000, trending up. Market sentiment: bullish."

    print("   Testing enhanced engine with short timeout...")
    import signal

    def timeout_handler(signum, frame):
        raise TimeoutError("Function call timed out")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(30)  # 30 second timeout

    try:
        decisions = get_enhanced_consensus_decisions(test_data)
        signal.alarm(0)  # Cancel timeout

        print(f"✅ Enhanced engine returned: {type(decisions)}")
        if isinstance(decisions, list):
            print(f"   Number of decisions: {len(decisions)}")
            for i, decision in enumerate(decisions):
                print(f"   Decision {i+1}: {decision.get('action')} {decision.get('token')}")
        else:
            print(f"   Single decision: {decisions}")

    except TimeoutError:
        signal.alarm(0)
        print("⚠️  Enhanced engine timed out after 30 seconds")

        print("4. Testing fallback function...")
        try:
            decision = get_consensus_decision_sync(test_data)
            print(f"✅ Fallback returned: {type(decision)} -> {decision}")
        except Exception as e:
            print(f"❌ Fallback also failed: {e}")

    except Exception as e:
        signal.alarm(0)
        print(f"❌ Enhanced engine error: {e}")
        import traceback
        traceback.print_exc()

except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()