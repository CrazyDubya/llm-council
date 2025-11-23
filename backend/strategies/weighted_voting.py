"""Weighted voting strategy - uses analytics to weight model votes."""

import re
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict

from .base import EnsembleStrategy
from ..openrouter import query_models_parallel, query_model


class WeightedVotingStrategy(EnsembleStrategy):
    """
    Weighted voting strategy that applies historical performance-based
    weights to model votes during ranking aggregation.

    Models with higher win rates have more influence on the final ranking.
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        # Analytics engine will be injected via config
        self.analytics = config.get('analytics_engine') if config else None
        self.min_weight = config.get('min_weight', 0.1) if config else 0.1
        self.use_win_rate = config.get('use_win_rate', True) if config else True

    def get_name(self) -> str:
        return "Weighted Voting"

    def get_description(self) -> str:
        return "Rankings weighted by model performance (higher-performing models have more influence)"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            'min_weight': {
                'type': 'number',
                'min': 0.0,
                'max': 1.0,
                'default': 0.1,
                'description': 'Minimum weight for any model (prevents zero influence)'
            },
            'use_win_rate': {
                'type': 'boolean',
                'default': True,
                'description': 'Use win rate for weighting (otherwise use inverse average rank)'
            }
        }

    async def execute(
        self,
        query: str,
        models: List[str],
        chairman: str
    ) -> Dict[str, Any]:
        """Execute the weighted voting strategy."""

        # Stage 1: Collect individual responses
        stage1_results = await self._stage1_collect_responses(query, models)

        if not stage1_results:
            return {
                'stage1': [],
                'stage2': [],
                'stage3': {
                    "model": "error",
                    "response": "All models failed to respond. Please try again."
                },
                'metadata': {}
            }

        # Stage 2: Collect rankings
        stage2_results, label_to_model = await self._stage2_collect_rankings(
            query, stage1_results, models
        )

        # Get model weights from analytics
        model_weights = self._get_model_weights(models)

        # Calculate weighted aggregate rankings
        aggregate_rankings = self._calculate_weighted_aggregate_rankings(
            stage2_results, label_to_model, model_weights
        )

        # Stage 3: Synthesize final answer
        stage3_result = await self._stage3_synthesize_final(
            query,
            stage1_results,
            stage2_results,
            chairman
        )

        # Prepare metadata
        metadata = {
            "label_to_model": label_to_model,
            "aggregate_rankings": aggregate_rankings,
            "strategy": "weighted_voting",
            "model_weights": model_weights
        }

        return {
            'stage1': stage1_results,
            'stage2': stage2_results,
            'stage3': stage3_result,
            'metadata': metadata
        }

    def _get_model_weights(self, models: List[str]) -> Dict[str, float]:
        """
        Get performance-based weights for each model.

        Args:
            models: List of model identifiers

        Returns:
            Dict mapping model to weight (0.0-1.0)
        """
        weights = {}

        if not self.analytics:
            # If no analytics available, use equal weights
            return {model: 1.0 for model in models}

        for model in models:
            perf = self.analytics.get_model_performance(model)

            if perf and perf['total_evaluations'] >= 3:
                # Sufficient data - use historical performance
                if self.use_win_rate:
                    # Use win rate as weight
                    weight = max(perf['win_rate'], self.min_weight)
                else:
                    # Use inverse of average rank
                    # Lower avg_rank is better, so invert it
                    avg_rank = perf.get('avg_rank', 3.0)
                    # Normalize: rank 1 -> 1.0, rank 5 -> 0.2
                    weight = max(1.0 / avg_rank, self.min_weight)
            else:
                # Insufficient data - use neutral weight
                weight = 0.5

            weights[model] = weight

        return weights

    async def _stage1_collect_responses(
        self,
        user_query: str,
        models: List[str]
    ) -> List[Dict[str, Any]]:
        """Stage 1: Collect individual responses from all council models."""
        messages = [{"role": "user", "content": user_query}]
        responses = await query_models_parallel(models, messages)

        stage1_results = []
        for model, response in responses.items():
            if response is not None:
                stage1_results.append({
                    "model": model,
                    "response": response.get('content', '')
                })

        return stage1_results

    async def _stage2_collect_rankings(
        self,
        user_query: str,
        stage1_results: List[Dict[str, Any]],
        models: List[str]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """Stage 2: Each model ranks the anonymized responses."""

        # Create anonymized labels
        labels = [chr(65 + i) for i in range(len(stage1_results))]
        label_to_model = {
            f"Response {label}": result['model']
            for label, result in zip(labels, stage1_results)
        }

        # Build the ranking prompt
        responses_text = "\n\n".join([
            f"Response {label}:\n{result['response']}"
            for label, result in zip(labels, stage1_results)
        ])

        ranking_prompt = f"""You are evaluating different responses to the following question:

Question: {user_query}

Here are the responses from different models (anonymized):

{responses_text}

Your task:
1. First, evaluate each response individually. For each response, explain what it does well and what it does poorly.
2. Then, at the very end of your response, provide a final ranking.

IMPORTANT: Your final ranking MUST be formatted EXACTLY as follows:
- Start with the line "FINAL RANKING:" (all caps, with colon)
- Then list the responses from best to worst as a numbered list
- Each line should be: number, period, space, then ONLY the response label (e.g., "1. Response A")
- Do not add any other text or explanations in the ranking section

Now provide your evaluation and ranking:"""

        messages = [{"role": "user", "content": ranking_prompt}]
        responses = await query_models_parallel(models, messages)

        stage2_results = []
        for model, response in responses.items():
            if response is not None:
                full_text = response.get('content', '')
                parsed = self._parse_ranking_from_text(full_text)
                stage2_results.append({
                    "model": model,
                    "ranking": full_text,
                    "parsed_ranking": parsed
                })

        return stage2_results, label_to_model

    async def _stage3_synthesize_final(
        self,
        user_query: str,
        stage1_results: List[Dict[str, Any]],
        stage2_results: List[Dict[str, Any]],
        chairman: str
    ) -> Dict[str, Any]:
        """Stage 3: Chairman synthesizes final response."""

        stage1_text = "\n\n".join([
            f"Model: {result['model']}\nResponse: {result['response']}"
            for result in stage1_results
        ])

        stage2_text = "\n\n".join([
            f"Model: {result['model']}\nRanking: {result['ranking']}"
            for result in stage2_results
        ])

        chairman_prompt = f"""You are the Chairman of an LLM Council. Multiple AI models have provided responses to a user's question, and then ranked each other's responses.

Original Question: {user_query}

STAGE 1 - Individual Responses:
{stage1_text}

STAGE 2 - Peer Rankings (weighted by model performance):
{stage2_text}

Your task as Chairman is to synthesize all of this information into a single, comprehensive, accurate answer to the user's original question. Consider:
- The individual responses and their insights
- The peer rankings and what they reveal about response quality
- Any patterns of agreement or disagreement

Provide a clear, well-reasoned final answer that represents the council's collective wisdom:"""

        messages = [{"role": "user", "content": chairman_prompt}]
        response = await query_model(chairman, messages)

        if response is None:
            return {
                "model": chairman,
                "response": "Error: Unable to generate final synthesis."
            }

        return {
            "model": chairman,
            "response": response.get('content', '')
        }

    def _parse_ranking_from_text(self, ranking_text: str) -> List[str]:
        """Parse the FINAL RANKING section from the model's response."""
        if "FINAL RANKING:" in ranking_text:
            parts = ranking_text.split("FINAL RANKING:")
            if len(parts) >= 2:
                ranking_section = parts[1]
                numbered_matches = re.findall(r'\d+\.\s*Response [A-Z]', ranking_section)
                if numbered_matches:
                    return [re.search(r'Response [A-Z]', m).group() for m in numbered_matches]
                matches = re.findall(r'Response [A-Z]', ranking_section)
                return matches

        matches = re.findall(r'Response [A-Z]', ranking_text)
        return matches

    def _calculate_weighted_aggregate_rankings(
        self,
        stage2_results: List[Dict[str, Any]],
        label_to_model: Dict[str, str],
        model_weights: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        Calculate aggregate rankings with performance-based weighting.

        Each model's vote is weighted by their historical performance.
        Higher-performing models have more influence on the final ranking.

        Args:
            stage2_results: Rankings from each model
            label_to_model: Mapping from anonymous labels to model names
            model_weights: Performance-based weights for each model

        Returns:
            List of dicts with model name and weighted average rank
        """
        # Track weighted positions for each response model
        model_weighted_scores = defaultdict(lambda: {'total_score': 0.0, 'total_weight': 0.0})

        for ranking in stage2_results:
            ranking_model = ranking['model']
            parsed_ranking = ranking.get('parsed_ranking', [])

            # Get weight for this ranking model
            weight = model_weights.get(ranking_model, 0.5)

            # Process each position in this ranking
            for position, label in enumerate(parsed_ranking, start=1):
                if label in label_to_model:
                    response_model = label_to_model[label]

                    # Add weighted score (lower position = better)
                    # We use position directly, weighted by the ranker's performance
                    model_weighted_scores[response_model]['total_score'] += position * weight
                    model_weighted_scores[response_model]['total_weight'] += weight

        # Calculate weighted average rank for each model
        aggregate = []
        for model, scores in model_weighted_scores.items():
            if scores['total_weight'] > 0:
                weighted_avg_rank = scores['total_score'] / scores['total_weight']
                aggregate.append({
                    "model": model,
                    "average_rank": round(weighted_avg_rank, 2),
                    "total_weight": round(scores['total_weight'], 2),
                    "rankings_count": len([r for r in stage2_results
                                         if model in [label_to_model.get(l)
                                                     for l in r.get('parsed_ranking', [])]])
                })

        # Sort by weighted average rank (lower is better)
        aggregate.sort(key=lambda x: x['average_rank'])

        return aggregate
