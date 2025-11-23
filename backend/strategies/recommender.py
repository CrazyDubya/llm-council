"""Strategy recommender combining query classification and analytics."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class StrategyRecommendation:
    """Recommendation for an ensemble strategy."""
    strategy: str
    confidence: float
    explanation: str
    fallback_options: List[str]
    query_category: str
    performance_data: Optional[Dict[str, Any]] = None


class StrategyRecommender:
    """
    Recommends ensemble strategies by combining:
    1. Query classification (type of question)
    2. Historical performance analytics (which strategies work best)
    """

    def __init__(self, query_classifier, analytics_engine):
        """
        Initialize recommender with classifier and analytics.

        Args:
            query_classifier: QueryClassifier instance
            analytics_engine: AnalyticsEngine instance
        """
        self.classifier = query_classifier
        self.analytics = analytics_engine

        # Base recommendations by category (from classifier)
        self.category_preferences = {
            'reasoning': ['reasoning_aware', 'multi_round', 'weighted_voting', 'simple'],
            'technical': ['multi_round', 'weighted_voting', 'reasoning_aware', 'simple'],
            'analytical': ['weighted_voting', 'multi_round', 'simple', 'reasoning_aware'],
            'creative': ['simple', 'multi_round', 'weighted_voting', 'reasoning_aware'],
            'factual': ['simple', 'weighted_voting', 'multi_round', 'reasoning_aware']
        }

    def recommend(self, query: str) -> StrategyRecommendation:
        """
        Recommend the best strategy for a given query.

        Args:
            query: The user's query text

        Returns:
            StrategyRecommendation with strategy, confidence, and explanation
        """
        # Step 1: Classify the query
        classification = self.classifier.classify(query)
        query_category = classification.category
        query_confidence = classification.confidence

        # Step 2: Get base preferences for this category
        preferences = self.category_preferences.get(
            query_category,
            ['simple', 'multi_round', 'weighted_voting', 'reasoning_aware']
        )

        # Step 3: Get historical performance data
        strategy_performance = self._get_strategy_performance()

        # Step 4: Combine preferences with performance data
        scored_strategies = self._score_strategies(
            preferences,
            strategy_performance,
            query_confidence
        )

        # Step 5: Select best strategy
        best_strategy = scored_strategies[0] if scored_strategies else 'simple'
        fallback_options = [s for s in scored_strategies[1:4]]

        # Build explanation
        explanation = self._build_explanation(
            query_category,
            best_strategy,
            strategy_performance.get(best_strategy),
            query_confidence
        )

        # Calculate overall confidence
        confidence = self._calculate_confidence(
            query_confidence,
            strategy_performance.get(best_strategy)
        )

        return StrategyRecommendation(
            strategy=best_strategy,
            confidence=round(confidence, 2),
            explanation=explanation,
            fallback_options=fallback_options,
            query_category=query_category,
            performance_data=strategy_performance.get(best_strategy)
        )

    def _get_strategy_performance(self) -> Dict[str, Dict[str, Any]]:
        """Get performance metrics for all strategies from analytics."""
        summary = self.analytics._load_summary()
        if not summary:
            # No data yet - return empty dict
            return {}

        strategy_stats = summary.get('strategy_stats', {})

        performance = {}
        for strategy, stats in strategy_stats.items():
            # Extract relevant metrics
            performance[strategy] = {
                'count': stats.get('count', 0),
                'avg_feedback': stats.get('avg_feedback'),
                'feedback_scores': stats.get('feedback_scores', [])
            }

        return performance

    def _score_strategies(
        self,
        preferences: List[str],
        performance: Dict[str, Dict[str, Any]],
        query_confidence: float
    ) -> List[str]:
        """
        Score and rank strategies based on preferences and performance.

        Args:
            preferences: Ordered list of strategies by category preference
            performance: Historical performance data
            query_confidence: Confidence in query classification

        Returns:
            Ordered list of strategy names
        """
        scores = {}

        for idx, strategy in enumerate(preferences):
            # Base score from position in preference list (1.0 for first, 0.7 for second, etc.)
            preference_score = 1.0 - (idx * 0.1)

            # Performance score (if available)
            perf_data = performance.get(strategy, {})
            avg_feedback = perf_data.get('avg_feedback')

            if avg_feedback is not None and perf_data.get('count', 0) >= 3:
                # Normalize feedback from [-1, 1] to [0, 1]
                performance_score = (avg_feedback + 1) / 2
                # Weight: 70% performance, 30% preference if we have good data
                combined_score = (0.7 * performance_score) + (0.3 * preference_score)
            else:
                # Not enough data - use preference only
                combined_score = preference_score

            # Adjust by query confidence
            # If we're very confident about the query type, trust preferences more
            final_score = combined_score * (0.5 + 0.5 * query_confidence)

            scores[strategy] = final_score

        # Sort by score descending
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [strategy for strategy, score in ranked]

    def _build_explanation(
        self,
        category: str,
        strategy: str,
        performance_data: Optional[Dict[str, Any]],
        query_confidence: float
    ) -> str:
        """Build human-readable explanation for the recommendation."""

        # Base explanations by strategy
        strategy_reasons = {
            'reasoning_aware': 'handles complex logical reasoning with explicit step-by-step analysis',
            'multi_round': 'allows iterative refinement through multiple deliberation rounds',
            'weighted_voting': 'leverages high-performing models with weighted influence',
            'simple': 'provides efficient consensus through direct peer ranking'
        }

        # Category-specific context
        category_context = {
            'reasoning': 'This appears to be a logical or mathematical problem',
            'technical': 'This looks like a technical or programming question',
            'analytical': 'This seems to require comparative analysis or evaluation',
            'creative': 'This appears to be a creative or open-ended task',
            'factual': 'This looks like a factual information request'
        }

        explanation = category_context.get(
            category,
            'Based on query analysis'
        )

        explanation += f", so the **{strategy.replace('_', ' ').title()}** strategy is recommended. "
        explanation += f"This strategy {strategy_reasons.get(strategy, 'is well-suited for this type of query')}."

        # Add performance context if available
        if performance_data and performance_data.get('avg_feedback') is not None:
            avg_feedback = performance_data['avg_feedback']
            count = performance_data.get('count', 0)
            if count >= 5:
                if avg_feedback > 0.5:
                    explanation += f" It has strong historical performance ({count} uses, avg rating: {avg_feedback:.1f})."
                elif avg_feedback > 0:
                    explanation += f" It has decent historical performance ({count} uses, avg rating: {avg_feedback:.1f})."

        return explanation

    def _calculate_confidence(
        self,
        query_confidence: float,
        performance_data: Optional[Dict[str, Any]]
    ) -> float:
        """
        Calculate overall confidence in the recommendation.

        Args:
            query_confidence: Confidence in query classification
            performance_data: Historical performance for recommended strategy

        Returns:
            Confidence score 0-1
        """
        # Start with query classification confidence
        confidence = query_confidence

        # Boost confidence if we have good performance data
        if performance_data and performance_data.get('avg_feedback') is not None:
            count = performance_data.get('count', 0)
            avg_feedback = performance_data['avg_feedback']

            # More data and positive feedback = higher confidence
            if count >= 5 and avg_feedback > 0.5:
                confidence = min(confidence + 0.2, 1.0)
            elif count >= 3 and avg_feedback > 0:
                confidence = min(confidence + 0.1, 1.0)

        return confidence
