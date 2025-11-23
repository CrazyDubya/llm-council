"""Analytics engine for tracking model and strategy performance."""

import json
import os
from typing import Dict, List, Any, Optional
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from .storage import get_conversation, list_conversations
from .config import DATA_DIR


class AnalyticsEngine:
    """
    Analyzes conversation data to compute model performance metrics
    and strategy effectiveness.
    """

    def __init__(self, cache_ttl_seconds: int = 300):
        """
        Initialize analytics engine with optional caching.

        Args:
            cache_ttl_seconds: Time-to-live for cached analytics (default: 5 minutes)
        """
        self.analytics_dir = os.path.join(DATA_DIR, 'analytics')
        self.summary_path = os.path.join(self.analytics_dir, 'summary.json')
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache = None
        self._cache_timestamp = None
        Path(self.analytics_dir).mkdir(parents=True, exist_ok=True)

    def compute_all_analytics(self) -> Dict[str, Any]:
        """
        Scan all conversations and compute comprehensive analytics.

        Returns:
            Dictionary containing all analytics data
        """
        # Get all conversations
        conversations_list = list_conversations()

        # Initialize accumulators
        total_queries = 0
        strategy_stats = defaultdict(lambda: {
            'count': 0,
            'feedback_scores': [],
            'avg_feedback': None
        })
        model_stats = defaultdict(lambda: {
            'total_evaluations': 0,
            'wins': 0,  # Times ranked #1
            'top_3': 0,  # Times in top 3
            'positions': [],  # All rank positions
            'avg_rank': None,
            'win_rate': 0.0,
            'by_strategy': defaultdict(lambda: {
                'evaluations': 0,
                'wins': 0,
                'positions': []
            })
        })

        # Process each conversation
        for conv_meta in conversations_list:
            conv = get_conversation(conv_meta['id'])
            if not conv:
                continue

            # Process each assistant message
            for msg in conv['messages']:
                if msg['role'] != 'assistant':
                    continue

                total_queries += 1
                metadata = msg.get('metadata', {})
                strategy = metadata.get('strategy', 'unknown')

                # Track strategy usage
                strategy_stats[strategy]['count'] += 1

                # Track user feedback
                if msg.get('user_feedback') is not None:
                    strategy_stats[strategy]['feedback_scores'].append(
                        msg['user_feedback']
                    )

                # Track model performance
                aggregate_rankings = metadata.get('aggregate_rankings', [])
                if aggregate_rankings:
                    for idx, rank_data in enumerate(aggregate_rankings):
                        model = rank_data['model']
                        position = idx + 1  # 1-indexed rank
                        avg_rank = rank_data.get('average_rank', position)

                        # Update model stats
                        model_stats[model]['total_evaluations'] += 1
                        model_stats[model]['positions'].append(avg_rank)

                        # Track wins (ranked #1)
                        if position == 1:
                            model_stats[model]['wins'] += 1
                            model_stats[model]['by_strategy'][strategy]['wins'] += 1

                        # Track top 3
                        if position <= 3:
                            model_stats[model]['top_3'] += 1

                        # Track by strategy
                        model_stats[model]['by_strategy'][strategy]['evaluations'] += 1
                        model_stats[model]['by_strategy'][strategy]['positions'].append(avg_rank)

        # Calculate derived metrics
        for strategy, stats in strategy_stats.items():
            if stats['feedback_scores']:
                stats['avg_feedback'] = round(
                    sum(stats['feedback_scores']) / len(stats['feedback_scores']),
                    2
                )

        for model, stats in model_stats.items():
            if stats['positions']:
                stats['avg_rank'] = round(
                    sum(stats['positions']) / len(stats['positions']),
                    2
                )

            if stats['total_evaluations'] > 0:
                stats['win_rate'] = round(
                    stats['wins'] / stats['total_evaluations'],
                    3
                )

            # Calculate per-strategy metrics
            for strategy, strat_stats in stats['by_strategy'].items():
                if strat_stats['positions']:
                    strat_stats['avg_rank'] = round(
                        sum(strat_stats['positions']) / len(strat_stats['positions']),
                        2
                    )
                if strat_stats['evaluations'] > 0:
                    strat_stats['win_rate'] = round(
                        strat_stats['wins'] / strat_stats['evaluations'],
                        3
                    )

        # Build final analytics summary
        summary = {
            'total_conversations': len(conversations_list),
            'total_queries': total_queries,
            'last_updated': datetime.utcnow().isoformat(),
            'strategy_stats': dict(strategy_stats),
            'model_stats': dict(model_stats)
        }

        # Save summary
        self._save_summary(summary)

        return summary

    def _is_cache_valid(self) -> bool:
        """Check if in-memory cache is still valid."""
        if self._cache is None or self._cache_timestamp is None:
            return False

        elapsed = (datetime.utcnow() - self._cache_timestamp).total_seconds()
        return elapsed < self.cache_ttl_seconds

    def _get_summary(self) -> Dict[str, Any]:
        """Get analytics summary with caching."""
        # Check in-memory cache first
        if self._is_cache_valid():
            return self._cache

        # Try loading from disk
        summary = self._load_summary()
        if summary:
            # Update cache
            self._cache = summary
            self._cache_timestamp = datetime.utcnow()
            return summary

        # Recompute if no valid cache or disk data
        summary = self.compute_all_analytics()
        self._cache = summary
        self._cache_timestamp = datetime.utcnow()
        return summary

    def invalidate_cache(self):
        """Force cache invalidation (call after new feedback)."""
        self._cache = None
        self._cache_timestamp = None

    def get_model_performance(self, model: str) -> Optional[Dict[str, Any]]:
        """
        Get performance metrics for a specific model.

        Args:
            model: Model identifier

        Returns:
            Performance metrics or None if model not found
        """
        summary = self._get_summary()
        return summary.get('model_stats', {}).get(model)

    def get_strategy_performance(self, strategy: str) -> Optional[Dict[str, Any]]:
        """
        Get performance metrics for a specific strategy.

        Args:
            strategy: Strategy identifier

        Returns:
            Strategy metrics or None if not found
        """
        summary = self._get_summary()
        return summary.get('strategy_stats', {}).get(strategy)

    def get_model_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top-performing models ranked by win rate.

        Args:
            limit: Maximum number of models to return

        Returns:
            List of models with performance metrics
        """
        summary = self._get_summary()
        model_stats = summary.get('model_stats', {})

        # Convert to list and sort by win rate
        leaderboard = []
        for model, stats in model_stats.items():
            total_evals = stats.get('total_evaluations', 0)
            leaderboard.append({
                'model': model,
                'win_rate': stats.get('win_rate', 0.0),
                'wins': stats.get('wins', 0),
                'total_evaluations': total_evals,
                'avg_rank': stats.get('avg_rank', 0.0),
                'top_3_rate': round(stats.get('top_3', 0) / total_evals, 3)
                if total_evals > 0 else 0.0
            })

        # Sort by win rate first, then by total evaluations for tiebreaking
        leaderboard.sort(key=lambda x: (x['win_rate'], x['total_evaluations']), reverse=True)

        return leaderboard[:limit]

    def get_best_strategy_for_query_type(self, query_type: str = 'general') -> str:
        """
        Recommend best strategy based on historical performance.

        Args:
            query_type: Type of query (for future categorization)

        Returns:
            Strategy identifier
        """
        summary = self._get_summary()
        strategy_stats = summary.get('strategy_stats', {})

        # Sort by average feedback (if available), otherwise by usage count
        best_strategy = 'simple'  # Default fallback
        best_score = -2  # Worst possible feedback

        for strategy, stats in strategy_stats.items():
            if stats['avg_feedback'] is not None:
                if stats['avg_feedback'] > best_score:
                    best_score = stats['avg_feedback']
                    best_strategy = strategy

        return best_strategy

    def _save_summary(self, summary: Dict[str, Any]):
        """Save analytics summary to disk."""
        with open(self.summary_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)

    def _load_summary(self) -> Optional[Dict[str, Any]]:
        """Load analytics summary from disk."""
        if not os.path.exists(self.summary_path):
            return None

        try:
            with open(self.summary_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
