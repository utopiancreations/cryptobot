"""
RAG Learning System for Cryptocurrency Trading Bot

This module provides Retrieval-Augmented Generation (RAG) capabilities
to learn from past trading sessions and improve decision making over time.
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import glob

class TradingRAG:
    """RAG system for learning from trading history"""

    def __init__(self, learning_data_dir: str = "learning_data"):
        self.learning_data_dir = learning_data_dir
        self.session_history: List[Dict] = []
        self.performance_patterns: Dict = defaultdict(list)
        self.token_performance: Dict = defaultdict(dict)
        self._ensure_data_directory()
        self._load_existing_data()

    def _ensure_data_directory(self):
        """Ensure learning data directory exists"""
        os.makedirs(self.learning_data_dir, exist_ok=True)

    def _load_existing_data(self):
        """Load existing learning data from previous sessions"""
        try:
            # Load session history
            sessions_file = os.path.join(self.learning_data_dir, "session_history.json")
            if os.path.exists(sessions_file):
                with open(sessions_file, 'r') as f:
                    self.session_history = json.load(f)
                print(f"📚 Loaded {len(self.session_history)} previous trading sessions")

            # Load performance patterns
            patterns_file = os.path.join(self.learning_data_dir, "performance_patterns.json")
            if os.path.exists(patterns_file):
                with open(patterns_file, 'r') as f:
                    data = json.load(f)
                    self.performance_patterns = defaultdict(list, data)
                print(f"🧠 Loaded performance patterns from previous sessions")

            # Load token performance
            tokens_file = os.path.join(self.learning_data_dir, "token_performance.json")
            if os.path.exists(tokens_file):
                with open(tokens_file, 'r') as f:
                    self.token_performance = defaultdict(dict, json.load(f))
                print(f"🎯 Loaded token performance data")

        except Exception as e:
            print(f"⚠️ Error loading existing data: {e}")

    def record_session(self, session_data: Dict):
        """Record a completed trading session for learning"""
        session_data['recorded_at'] = datetime.now().isoformat()
        self.session_history.append(session_data)

        # Extract and analyze patterns
        self._analyze_session_patterns(session_data)

        # Save updated data
        self._save_learning_data()

        print(f"📝 Recorded trading session with {session_data.get('total_trades', 0)} trades")

    def _analyze_session_patterns(self, session_data: Dict):
        """Analyze patterns from a trading session"""

        # Track time-based performance
        hour = datetime.fromisoformat(session_data['recorded_at']).hour
        win_rate = session_data.get('win_rate_percent', 0)
        self.performance_patterns[f'hour_{hour}'].append({
            'win_rate': win_rate,
            'trades': session_data.get('total_trades', 0),
            'pnl': session_data.get('daily_pnl', 0)
        })

        # Track market condition performance
        if 'market_sentiment' in session_data:
            sentiment = session_data['market_sentiment']
            self.performance_patterns[f'sentiment_{sentiment}'].append({
                'win_rate': win_rate,
                'trades': session_data.get('total_trades', 0)
            })

        # Track individual token performance
        if 'executed_trades' in session_data:
            for trade in session_data['executed_trades']:
                token = trade.get('token', 'UNKNOWN')
                if token not in self.token_performance:
                    self.token_performance[token] = {
                        'total_trades': 0,
                        'successful_trades': 0,
                        'avg_confidence': 0.0,
                        'avg_amount': 0.0
                    }

                self.token_performance[token]['total_trades'] += 1
                if trade.get('profitable', False):
                    self.token_performance[token]['successful_trades'] += 1

                # Update averages
                current_conf = self.token_performance[token]['avg_confidence']
                current_amt = self.token_performance[token]['avg_amount']
                total = self.token_performance[token]['total_trades']

                new_conf = trade.get('confidence', 0)
                new_amt = trade.get('amount_usd', 0)

                self.token_performance[token]['avg_confidence'] = (
                    (current_conf * (total - 1) + new_conf) / total
                )
                self.token_performance[token]['avg_amount'] = (
                    (current_amt * (total - 1) + new_amt) / total
                )

    def get_learning_insights(self) -> Dict:
        """Get learning insights to improve trading decisions"""
        insights = {
            'best_trading_hours': [],
            'optimal_market_sentiment': '',
            'high_performing_tokens': [],
            'low_performing_tokens': [],
            'recommended_adjustments': []
        }

        # Analyze best trading hours
        hour_performance = {}
        for key, performances in self.performance_patterns.items():
            if key.startswith('hour_'):
                hour = int(key.split('_')[1])
                if performances:
                    avg_win_rate = sum(p['win_rate'] for p in performances) / len(performances)
                    avg_trades = sum(p['trades'] for p in performances) / len(performances)
                    hour_performance[hour] = {
                        'win_rate': avg_win_rate,
                        'avg_trades': avg_trades,
                        'sessions': len(performances)
                    }

        # Find top 3 hours
        top_hours = sorted(hour_performance.items(),
                          key=lambda x: x[1]['win_rate'], reverse=True)[:3]
        insights['best_trading_hours'] = [
            f"{hour}:00 (Win Rate: {data['win_rate']:.1f}%)"
            for hour, data in top_hours if data['sessions'] >= 2
        ]

        # Analyze sentiment performance
        sentiment_performance = {}
        for key, performances in self.performance_patterns.items():
            if key.startswith('sentiment_'):
                sentiment = key.split('_')[1]
                if performances:
                    avg_win_rate = sum(p['win_rate'] for p in performances) / len(performances)
                    sentiment_performance[sentiment] = avg_win_rate

        if sentiment_performance:
            best_sentiment = max(sentiment_performance, key=sentiment_performance.get)
            insights['optimal_market_sentiment'] = f"{best_sentiment} ({sentiment_performance[best_sentiment]:.1f}% win rate)"

        # Analyze token performance
        token_scores = {}
        for token, data in self.token_performance.items():
            if data['total_trades'] >= 2:  # Only consider tokens with multiple trades
                win_rate = (data['successful_trades'] / data['total_trades']) * 100
                confidence_factor = data['avg_confidence'] * 100
                score = (win_rate * 0.7) + (confidence_factor * 0.3)  # Weighted score
                token_scores[token] = {
                    'score': score,
                    'win_rate': win_rate,
                    'trades': data['total_trades']
                }

        # Top and bottom performing tokens
        if token_scores:
            sorted_tokens = sorted(token_scores.items(), key=lambda x: x[1]['score'], reverse=True)

            insights['high_performing_tokens'] = [
                f"{token} (Score: {data['score']:.1f}, Win Rate: {data['win_rate']:.1f}%)"
                for token, data in sorted_tokens[:3]
            ]

            insights['low_performing_tokens'] = [
                f"{token} (Score: {data['score']:.1f}, Win Rate: {data['win_rate']:.1f}%)"
                for token, data in sorted_tokens[-3:] if data['score'] < 50
            ]

        # Generate recommendations
        recommendations = []

        if len(self.session_history) >= 3:
            recent_sessions = self.session_history[-3:]
            avg_recent_win_rate = sum(s.get('win_rate_percent', 0) for s in recent_sessions) / 3

            if avg_recent_win_rate < 40:
                recommendations.append("Consider reducing trade frequency - recent performance below 40%")
            elif avg_recent_win_rate > 70:
                recommendations.append("Consider increasing position sizes - strong recent performance")

        if insights['best_trading_hours']:
            recommendations.append(f"Focus trading during: {', '.join(insights['best_trading_hours'])}")

        if insights['low_performing_tokens']:
            recommendations.append(f"Consider avoiding: {insights['low_performing_tokens'][0].split(' ')[0]}")

        insights['recommended_adjustments'] = recommendations

        return insights

    def get_contextual_advice(self, current_decision: Dict) -> str:
        """Get contextual advice for a current trading decision"""
        advice = []

        token = current_decision.get('token', '').upper()
        confidence = current_decision.get('confidence', 0)
        action = current_decision.get('action', '')

        # Check token performance history
        if token in self.token_performance:
            token_data = self.token_performance[token]
            if token_data['total_trades'] >= 2:
                win_rate = (token_data['successful_trades'] / token_data['total_trades']) * 100
                if win_rate < 30:
                    advice.append(f"⚠️ {token} has low historical win rate ({win_rate:.1f}%) - consider reducing position size")
                elif win_rate > 70:
                    advice.append(f"✅ {token} has strong historical performance ({win_rate:.1f}%) - good choice")

        # Check current time vs best performing hours
        current_hour = datetime.now().hour
        hour_key = f'hour_{current_hour}'
        if hour_key in self.performance_patterns and self.performance_patterns[hour_key]:
            performances = self.performance_patterns[hour_key]
            avg_win_rate = sum(p['win_rate'] for p in performances) / len(performances)
            if avg_win_rate > 60:
                advice.append(f"📈 Current hour ({current_hour}:00) shows good historical performance")
            elif avg_win_rate < 35:
                advice.append(f"📉 Current hour ({current_hour}:00) shows poor historical performance - be cautious")

        # Confidence-based advice
        if confidence < 0.6:
            advice.append("🤔 Low confidence detected - consider waiting for higher confidence opportunities")
        elif confidence > 0.8:
            advice.append("🚀 High confidence trade - historical data suggests good execution timing")

        return " | ".join(advice) if advice else "No specific historical insights available for this trade"

    def _save_learning_data(self):
        """Save learning data to files"""
        try:
            # Save session history
            sessions_file = os.path.join(self.learning_data_dir, "session_history.json")
            with open(sessions_file, 'w') as f:
                json.dump(self.session_history, f, indent=2)

            # Save performance patterns
            patterns_file = os.path.join(self.learning_data_dir, "performance_patterns.json")
            with open(patterns_file, 'w') as f:
                json.dump(dict(self.performance_patterns), f, indent=2)

            # Save token performance
            tokens_file = os.path.join(self.learning_data_dir, "token_performance.json")
            with open(tokens_file, 'w') as f:
                json.dump(dict(self.token_performance), f, indent=2)

        except Exception as e:
            print(f"⚠️ Error saving learning data: {e}")

# Global RAG instance
trading_rag = TradingRAG()

def record_trading_session(session_data: Dict):
    """Record a trading session for learning"""
    trading_rag.record_session(session_data)

def get_learning_insights() -> Dict:
    """Get learning insights to improve trading"""
    return trading_rag.get_learning_insights()

def get_contextual_advice(decision: Dict) -> str:
    """Get contextual advice for a trading decision"""
    return trading_rag.get_contextual_advice(decision)

def analyze_past_sessions(days: int = 7) -> Dict:
    """Analyze performance over the past N days"""
    cutoff_date = datetime.now() - timedelta(days=days)

    recent_sessions = [
        s for s in trading_rag.session_history
        if datetime.fromisoformat(s['recorded_at']) > cutoff_date
    ]

    if not recent_sessions:
        return {"message": f"No sessions found in the past {days} days"}

    total_trades = sum(s.get('total_trades', 0) for s in recent_sessions)
    avg_win_rate = sum(s.get('win_rate_percent', 0) for s in recent_sessions) / len(recent_sessions)
    total_pnl = sum(s.get('daily_pnl', 0) for s in recent_sessions)

    return {
        'sessions_analyzed': len(recent_sessions),
        'total_trades': total_trades,
        'average_win_rate': avg_win_rate,
        'total_pnl': total_pnl,
        'avg_trades_per_session': total_trades / len(recent_sessions) if recent_sessions else 0
    }