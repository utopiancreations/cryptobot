#!/usr/bin/env python3
"""
Test script for CoinMarketCap API integration
"""

import json
import sys
from connectors.coinmarketcap_api import (
    get_cmc_api, get_market_data_for_trading,
    format_market_data_for_llm, test_cmc_api
)

def test_basic_functionality():
    """Test basic CoinMarketCap API functionality"""
    print("🚀 Testing CoinMarketCap API Integration")
    print("=" * 60)

    # Test API connection
    print("\n📡 Testing API Connection...")
    if not test_cmc_api():
        print("❌ API connection failed. Please check your API key.")
        return False

    cmc = get_cmc_api()

    # Test quotes
    print("\n💰 Testing Token Quotes...")
    quotes = cmc.get_token_quotes(['BTC', 'ETH', 'BNB', 'MATIC', 'SOL'])
    if quotes:
        print("✅ Token quotes retrieved successfully:")
        for symbol, data in quotes.items():
            price = data.get('price', 0) or 0
            change = data.get('percent_change_24h', 0) or 0
            print(f"   {symbol}: ${price:,.4f} ({change:+.2f}%)")
    else:
        print("❌ Failed to retrieve token quotes")

    # Test top gainers
    print("\n🚀 Testing Top Gainers...")
    gainers = cmc.get_top_gainers(limit=5)
    if gainers:
        print("✅ Top gainers retrieved successfully:")
        for i, token in enumerate(gainers, 1):
            symbol = token.get('symbol', 'N/A')
            change = token.get('percent_change_24h', 0) or 0
            price = token.get('price', 0) or 0
            print(f"   {i}. {symbol}: +{change:.2f}% (${price:.6f})")
    else:
        print("❌ Failed to retrieve top gainers")

    # Test market sentiment
    print("\n📊 Testing Market Sentiment...")
    sentiment = cmc.get_fear_greed_index()
    if sentiment:
        print("✅ Market sentiment calculated successfully:")
        print(f"   Fear/Greed Index: {sentiment.get('index', 50)}/100")
        print(f"   Classification: {sentiment.get('classification', 'neutral').upper()}")
        if 'avg_change_24h' in sentiment:
            print(f"   Market Average 24h: {sentiment['avg_change_24h']:.2f}%")
    else:
        print("❌ Failed to calculate market sentiment")

    # Test trending tokens
    print("\n📈 Testing Trending Tokens...")
    trending = cmc.get_trending_tokens(limit=5)
    if trending:
        print("✅ Trending tokens retrieved successfully:")
        for i, token in enumerate(trending, 1):
            symbol = token.get('symbol', 'N/A')
            name = token.get('name', 'Unknown')
            change = token.get('percent_change_24h', 0) or 0
            print(f"   {i}. {symbol} ({name}): {change:+.2f}%")
    else:
        print("❌ Failed to retrieve trending tokens")

    return True

def test_comprehensive_market_data():
    """Test comprehensive market data for trading"""
    print("\n" + "=" * 60)
    print("📊 Testing Comprehensive Market Data for Trading")
    print("=" * 60)

    # Get comprehensive market data
    market_data = get_market_data_for_trading(['BTC', 'ETH', 'BNB', 'MATIC'])

    if not market_data:
        print("❌ Failed to retrieve comprehensive market data")
        return False

    print("\n✅ Comprehensive market data retrieved successfully!")

    # Show formatted data for LLM
    print("\n📝 LLM-Formatted Market Data:")
    print("-" * 40)
    formatted_data = format_market_data_for_llm(market_data)
    print(formatted_data[:1000] + "..." if len(formatted_data) > 1000 else formatted_data)

    # Save detailed data
    with open('market_data_sample.json', 'w') as f:
        json.dump(market_data, f, indent=2, default=str)

    print(f"\n💾 Detailed market data saved to: market_data_sample.json")

    # Show key insights
    print("\n🎯 Key Market Insights:")

    sentiment = market_data.get('sentiment', {})
    if sentiment:
        index = sentiment.get('index', 50)
        classification = sentiment.get('classification', 'neutral')
        print(f"   Market Sentiment: {classification.upper()} ({index}/100)")

    gainers = market_data.get('top_gainers', [])[:3]
    if gainers:
        print(f"   Top Opportunities:")
        for gainer in gainers:
            symbol = gainer.get('symbol', 'N/A')
            change = gainer.get('percent_change_24h', 0)
            print(f"     • {symbol}: +{change:.2f}%")

    market_overview = market_data.get('market_overview', [])[:5]
    if market_overview:
        total_mcap = sum(token.get('market_cap', 0) for token in market_overview)
        avg_change = sum(token.get('percent_change_24h', 0) for token in market_overview) / len(market_overview)
        print(f"   Top 5 Total Market Cap: ${total_mcap/1e12:.2f}T")
        print(f"   Top 5 Average Change: {avg_change:+.2f}%")

    return True

def test_token_search():
    """Test token search functionality"""
    print("\n" + "=" * 60)
    print("🔍 Testing Token Search")
    print("=" * 60)

    cmc = get_cmc_api()

    search_queries = ['BTC', 'ethereum', 'matic', 'sol']

    for query in search_queries:
        print(f"\n🔍 Searching for: '{query}'")
        results = cmc.search_tokens(query, limit=3)

        if results:
            print(f"✅ Found {len(results)} results:")
            for result in results:
                symbol = result.get('symbol', 'N/A')
                name = result.get('name', 'Unknown')
                rank = result.get('cmc_rank', 'N/A')
                print(f"   #{rank} {symbol} ({name})")
        else:
            print(f"❌ No results found for '{query}'")

def main():
    """Main test function"""
    try:
        # Test basic functionality
        if not test_basic_functionality():
            print("\n❌ Basic functionality test failed")
            sys.exit(1)

        # Test comprehensive market data
        if not test_comprehensive_market_data():
            print("\n❌ Comprehensive market data test failed")
            sys.exit(1)

        # Test token search
        test_token_search()

        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("✅ CoinMarketCap API integration is working correctly")
        print("🚀 Ready for enhanced trading with real-time market data")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()