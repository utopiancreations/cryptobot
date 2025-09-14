"""
Wealth Dashboard - Display Bot Performance and Profit Motivation
Shows real-time wealth accumulation, success metrics, and trading performance
"""

from datetime import datetime, timedelta
from typing import Dict
from profit_maximizer import get_profit_maximizer
from utils.wallet import get_wallet_balance

def display_wealth_dashboard():
    """Display comprehensive wealth and performance dashboard"""

    try:
        profit_maximizer = get_profit_maximizer()
        wealth_status = profit_maximizer.get_wealth_status()

        print("\n" + "=" * 80)
        print("💰 BOT WEALTH ACCUMULATION DASHBOARD")
        print("=" * 80)

        # Current Performance Section
        print(f"📊 CURRENT PERFORMANCE:")
        print(f"   💎 Portfolio Value: ${wealth_status['current_portfolio_value']:,.2f}")
        print(f"   📈 Total Profit: ${wealth_status['total_realized_profits']:,.2f}")
        print(f"   🎯 Success Rate: {wealth_status['success_rate']:.1f}%")
        print(f"   🔥 Win Streak: {wealth_status['consecutive_wins']} trades")
        print(f"   🏆 Max Streak: {wealth_status['max_consecutive_wins']} trades")
        print(f"   📊 Successful Trades: {wealth_status['successful_trades']}")
        print(f"   ❌ Failed Trades: {wealth_status['failed_trades']}")

        # Growth Metrics
        growth_rate = wealth_status['wealth_growth_rate'] * 100
        if growth_rate > 0:
            print(f"   🚀 Wealth Growth: +{growth_rate:.1f}%")
        else:
            print(f"   📉 Wealth Growth: {growth_rate:.1f}%")

        # Risk and Confidence
        print(f"\n🎲 RISK & CONFIDENCE:")
        print(f"   🌡️  Risk Appetite: {wealth_status['risk_appetite']:.1%}")
        print(f"   💪 Confidence Multiplier: {wealth_status['confidence_multiplier']:.2f}x")

        # Performance Rating
        success_rate = wealth_status['success_rate']
        if success_rate >= 80:
            rating = "🏆 ELITE TRADER"
            motivation = "MAXIMUM AGGRESSION MODE"
        elif success_rate >= 70:
            rating = "💪 STRONG PERFORMER"
            motivation = "HIGH CONFIDENCE MODE"
        elif success_rate >= 60:
            rating = "✅ GOOD TRADER"
            motivation = "STEADY GROWTH MODE"
        elif success_rate >= 40:
            rating = "⚠️  NEEDS IMPROVEMENT"
            motivation = "CONSERVATIVE MODE"
        else:
            rating = "🚨 POOR PERFORMANCE"
            motivation = "SURVIVAL MODE"

        print(f"\n🏅 BOT RATING: {rating}")
        print(f"💡 MOTIVATION STATUS: {motivation}")

        # Profit Motivation Message
        total_profit = wealth_status['total_realized_profits']
        win_streak = wealth_status['consecutive_wins']

        print(f"\n💰 PROFIT MOTIVATION:")
        if total_profit > 1000:
            print(f"   🎉 INCREDIBLE! You've made over $1,000 in profits!")
            print(f"   🚀 Keep this momentum going - maximize every opportunity!")
        elif total_profit > 500:
            print(f"   💪 EXCELLENT! ${total_profit:.2f} in profits - you're crushing it!")
            print(f"   🎯 Push harder to break the $1,000 barrier!")
        elif total_profit > 100:
            print(f"   ✅ GOOD PROGRESS! ${total_profit:.2f} in profits!")
            print(f"   📈 Scale up positions to accelerate wealth building!")
        elif total_profit > 0:
            print(f"   🌱 POSITIVE START! ${total_profit:.2f} in profits!")
            print(f"   💡 Time to get more aggressive and grow this fortune!")
        else:
            print(f"   🔥 HUNGRY FOR PROFITS! Time to make some money!")
            print(f"   🎯 Every trade is an opportunity to build wealth!")

        if win_streak >= 5:
            print(f"   🔥 UNSTOPPABLE! {win_streak} wins in a row!")
            print(f"   🚀 You're in the ZONE - maximize this hot streak!")
        elif win_streak >= 3:
            print(f"   🎯 HOT STREAK! {win_streak} consecutive wins!")
            print(f"   💪 Keep the momentum - bigger positions for bigger profits!")
        elif win_streak == 0:
            print(f"   ⚡ READY TO WIN! Next trade starts your winning streak!")
            print(f"   🎯 Focus and determination will build your fortune!")

        # Trading Goals
        print(f"\n🎯 WEALTH ACCUMULATION GOALS:")
        current_value = wealth_status['current_portfolio_value']

        goals = [
            (current_value * 1.1, "10% Portfolio Growth"),
            (current_value * 1.25, "25% Portfolio Growth"),
            (current_value * 1.5, "50% Portfolio Growth"),
            (current_value * 2.0, "DOUBLE YOUR MONEY!")
        ]

        for goal_amount, goal_name in goals:
            needed = goal_amount - current_value
            print(f"   📊 {goal_name}: ${needed:,.2f} more needed")

        # Motivation Footer
        print(f"\n" + "=" * 80)
        print("🎯 REMEMBER: Every trade is an opportunity to build wealth!")
        print("💰 Be aggressive with high-confidence opportunities!")
        print("🚀 Your goal is to MAXIMIZE PROFITS and GROW YOUR FORTUNE!")
        print("=" * 80 + "\n")

        return wealth_status

    except Exception as e:
        print(f"❌ Error displaying wealth dashboard: {e}")
        return {}

def display_compact_wealth_status():
    """Display compact wealth status for regular updates"""

    try:
        profit_maximizer = get_profit_maximizer()
        wealth_status = profit_maximizer.get_wealth_status()

        total_profit = wealth_status['total_realized_profits']
        success_rate = wealth_status['success_rate']
        win_streak = wealth_status['consecutive_wins']
        risk_appetite = wealth_status['risk_appetite']

        print(f"💰 WEALTH: ${total_profit:,.2f} | ✅ SUCCESS: {success_rate:.1f}% | 🔥 STREAK: {win_streak} | 🎲 RISK: {risk_appetite:.1%}")

        return wealth_status

    except Exception as e:
        print(f"❌ Error displaying compact wealth status: {e}")
        return {}

def get_profit_motivation_message(decision: Dict) -> str:
    """Generate profit-motivated message for trading decision"""

    try:
        profit_maximizer = get_profit_maximizer()
        wealth_status = profit_maximizer.get_wealth_status()

        amount = decision.get('amount_usd', 0)
        token = decision.get('token', 'TOKEN')
        action = decision.get('action', 'TRADE')
        confidence = decision.get('confidence_score', 0)

        total_profit = wealth_status['total_realized_profits']
        win_streak = wealth_status['consecutive_wins']

        messages = [
            f"💰 {action} {token} for ${amount:.2f} - Building wealth one trade at a time!",
            f"🚀 High confidence {action} - This could add to our ${total_profit:.2f} profit streak!",
            f"🎯 {action} {token} - Every successful trade grows our fortune!",
            f"💎 Portfolio expansion trade - {action} {token} to maximize returns!",
            f"🔥 Profit opportunity detected - {action} {token} with {confidence:.1%} confidence!"
        ]

        if win_streak >= 3:
            messages.append(f"🏆 WIN STREAK TRADE #{win_streak + 1} - {action} {token} to keep momentum!")

        if amount > 100:
            messages.append(f"🎯 BIG MONEY MOVE - ${amount:.2f} {action} on {token} for maximum impact!")

        import random
        return random.choice(messages)

    except Exception as e:
        return f"💰 {decision.get('action', 'TRADE')} {decision.get('token', 'TOKEN')} - Profit-focused trading!"

if __name__ == "__main__":
    # Test the wealth dashboard
    display_wealth_dashboard()