#!/usr/bin/env python3
"""
Verification script to check which trading system is actually being used
"""

import sys
import os

def check_system():
    print("🔍 SYSTEM VERIFICATION")
    print("=" * 50)

    # Check current directory
    print(f"Current directory: {os.getcwd()}")

    # Check if enhanced files exist
    enhanced_files = [
        'enhanced_consensus_engine.py',
        'utils/trade_manager.py',
        'test_enhanced_trading.py'
    ]

    for file in enhanced_files:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")

    # Check main.py content
    with open('main.py', 'r') as f:
        main_content = f.read()

    if 'get_enhanced_consensus_decisions' in main_content:
        print("✅ main.py imports enhanced consensus engine")
    else:
        print("❌ main.py does NOT import enhanced consensus engine")

    if 'Consulting Enhanced Multi-Agent Consensus Engine' in main_content:
        print("✅ main.py uses enhanced message")
    else:
        print("❌ main.py uses old message")

    if 'trade_manager' in main_content:
        print("✅ main.py includes trade manager")
    else:
        print("❌ main.py missing trade manager")

    # Check for old consensus engine calls
    if 'get_consensus_decision(' in main_content:
        print("⚠️  main.py still has old consensus calls")
    else:
        print("✅ main.py does not have old consensus calls")

if __name__ == "__main__":
    check_system()