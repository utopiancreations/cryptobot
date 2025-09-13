# test_wallet.py
from utils.wallet import get_wallet_balance, check_wallet_connection
import config

def main():
    print("🔧 Testing Polygon Wallet Connection")
    print("=" * 50)
    
    # Test basic wallet configuration
    print(f"📍 Wallet Address: {config.WALLET_ADDRESS}")
    print(f"🌐 RPC URL: {config.RPC_URL}")
    
    # Test wallet connection
    print("\n🔗 Testing wallet connection...")
    connection_ok = check_wallet_connection()
    
    if connection_ok:
        print("✅ Wallet connection test passed!")
        
        # Test balance retrieval
        print("\n💰 Testing balance retrieval...")
        balance = get_wallet_balance()
        
        if balance is not None:
            native_token = balance['native_token']
            print(f"✅ Success! Wallet Balance:")
            print(f"   Native Token: {native_token['balance']:.6f} {native_token['symbol']}")
            print(f"   USD Estimate: ${balance['total_usd_estimate']:.2f}")
            
            # Show token balances if any
            if balance['tokens']:
                print(f"   Token Balances:")
                for symbol, token_info in balance['tokens'].items():
                    print(f"     {symbol}: {token_info['balance']:.6f}")
            else:
                print("   No token balances detected")
                
        else:
            print("❌ Failed to retrieve wallet balance.")
    else:
        print("❌ Wallet connection test failed.")
        print("⚠️  Please check your RPC_URL and WALLET_ADDRESS configuration")

if __name__ == "__main__":
    main()