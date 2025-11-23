"""Query classifier for categorizing user queries to recommend strategies."""

import re
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class QueryCategory:
    """Category for a user query."""
    category: str
    confidence: float
    indicators: List[str]


class QueryClassifier:
    """
    Classifies user queries into categories to help recommend
    the most appropriate ensemble strategy.

    Categories:
    - technical: Programming, debugging, code-related queries
    - analytical: Data analysis, comparison, evaluation queries
    - creative: Writing, brainstorming, open-ended questions
    - factual: Information lookup, definitions, facts
    - reasoning: Complex logic, mathematics, multi-step problems
    """

    def __init__(self):
        # Keyword patterns for each category
        self.patterns = {
            'technical': {
                'keywords': [
                    r'\bcode\b', r'\bprogram(ming)?\b', r'\bdebug\b', r'\bfunction\b',
                    r'\bapi\b', r'\balgorithm\b', r'\bsyntax\b', r'\berror\b',
                    r'\bbug\b', r'\bframework\b', r'\blibrary\b', r'\bclass\b',
                    r'\bmethod\b', r'\bvariable\b', r'\bloop\b', r'\barray\b',
                    r'\bpython\b', r'\bjavascript\b', r'\breact\b', r'\bnode\b',
                    r'\bgit\b', r'\bdocker\b', r'\bsql\b', r'\bdatabase\b'
                ],
                'weight': 1.0
            },
            'reasoning': {
                'keywords': [
                    r'\bcalculate\b', r'\bprove\b', r'\bderive\b', r'\bsolve\b',
                    r'\btheorem\b', r'\bequation\b', r'\bsteps?\b', r'\blogic\b',
                    r'\bif.*then\b', r'\bgiven.*find\b', r'\bproof\b',
                    r'\bassume\b', r'\bconclude\b', r'\binfer\b', r'\bdeduce\b',
                    r'\bmathematics\b', r'\bcalculus\b', r'\balgebra\b',
                    r'\bstrategy\b', r'\bplan\b', r'\bapproach\b', r'\bmethod\b',
                    r'why\s+is\b', r'how\s+does\b', r'explain.*process'
                ],
                'weight': 1.2  # Higher weight for reasoning
            },
            'analytical': {
                'keywords': [
                    r'\bcompare\b', r'\bcontrast\b', r'\banalyze\b', r'\bevaluate\b',
                    r'\bassess\b', r'\btradeoff\b', r'\bpros\s+and\s+cons\b',
                    r'\bdifference\b', r'\bsimilarity\b', r'\bbetter\b', r'\bworse\b',
                    r'\badvantage\b', r'\bdisadvantage\b', r'\bmetric\b',
                    r'\bperformance\b', r'\bbenchmark\b', r'\bstatistic\b',
                    r'\btrend\b', r'\bpattern\b', r'\bcorrelation\b'
                ],
                'weight': 1.0
            },
            'creative': {
                'keywords': [
                    r'\bwrite\b', r'\bstory\b', r'\bpoem\b', r'\bessay\b',
                    r'\bbrainstorm\b', r'\bidea\b', r'\bimaginative\b', r'\bcreative\b',
                    r'\binvent\b', r'\bdesign\b', r'\bnovel\b', r'\boriginal\b',
                    r'\bnarrative\b', r'\bcharacter\b', r'\bplot\b', r'\bscenario\b',
                    r'\bslogan\b', r'\bmarketing\b', r'\bcampaign\b',
                    r'\bmetaphor\b', r'\banalogy\b'
                ],
                'weight': 0.9
            },
            'factual': {
                'keywords': [
                    r'\bwhat\s+is\b', r'\bwhen\s+did\b', r'\bwho\s+is\b',
                    r'\bwhere\s+is\b', r'\bdefine\b', r'\bdefinition\b',
                    r'\bexplain\b', r'\bdescribe\b', r'\blist\b', r'\bname\b',
                    r'\bhistory\b', r'\bfact\b', r'\binformation\b',
                    r'\bcapital\b', r'\bpopulation\b', r'\bdate\b',
                    r'\bmean\b', r'\brefer\b', r'\bstand for\b'
                ],
                'weight': 0.8
            }
        }

    def classify(self, query: str) -> QueryCategory:
        """
        Classify a query into a category.

        Args:
            query: The user's query text

        Returns:
            QueryCategory with category name, confidence, and matching indicators
        """
        # Input validation
        if not query or len(query.strip()) < 3:
            return QueryCategory(
                category='factual',
                confidence=0.0,
                indicators=[]
            )

        query_lower = query.lower()
        scores = {}
        matches = {}

        # Score each category
        for category, config in self.patterns.items():
            category_matches = []
            score = 0

            for pattern in config['keywords']:
                if re.search(pattern, query_lower):
                    category_matches.append(pattern)
                    score += config['weight']

            scores[category] = score
            matches[category] = category_matches

        # Find best category
        if not scores or max(scores.values()) == 0:
            # No matches - default to factual
            return QueryCategory(
                category='factual',
                confidence=0.3,
                indicators=[]
            )

        best_category = max(scores, key=scores.get)
        best_score = scores[best_category]
        total_score = sum(scores.values())

        # Calculate confidence (0-1)
        confidence = min(best_score / (total_score + 1e-6), 1.0)

        return QueryCategory(
            category=best_category,
            confidence=round(confidence, 2),
            indicators=matches[best_category]
        )

    def get_recommended_strategy(self, query: str) -> Dict[str, Any]:
        """
        Recommend an ensemble strategy based on query classification.

        Args:
            query: The user's query text

        Returns:
            Dict with recommended strategy and explanation
        """
        category = self.classify(query)

        # Strategy recommendations based on category
        recommendations = {
            'reasoning': {
                'strategy': 'reasoning_aware',
                'explanation': 'This query requires logical reasoning. The Reasoning-Aware strategy is optimized for complex multi-step problems.'
            },
            'technical': {
                'strategy': 'multi_round',
                'explanation': 'Technical queries benefit from iterative refinement. Multi-Round allows models to improve their solutions.'
            },
            'analytical': {
                'strategy': 'weighted_voting',
                'explanation': 'Analytical questions benefit from expert opinions. Weighted Voting gives more influence to high-performing models.'
            },
            'creative': {
                'strategy': 'simple',
                'explanation': 'Creative queries benefit from diverse perspectives. Simple Ranking captures varied creative approaches.'
            },
            'factual': {
                'strategy': 'simple',
                'explanation': 'Factual queries have clear correct answers. Simple Ranking is efficient for straightforward questions.'
            }
        }

        recommendation = recommendations.get(category.category, recommendations['factual'])

        return {
            'strategy': recommendation['strategy'],
            'explanation': recommendation['explanation'],
            'query_category': category.category,
            'confidence': category.confidence,
            'indicators': category.indicators
        }
