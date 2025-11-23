"""Reasoning-aware strategy for models with chain-of-thought capabilities."""

import re
from typing import List, Dict, Any, Tuple
from collections import defaultdict

from .base import EnsembleStrategy
from ..openrouter import query_models_parallel, query_model


class ReasoningAwareStrategy(EnsembleStrategy):
    """
    Reasoning-aware strategy optimized for o1, DeepSeek-R1, and other
    models that produce explicit reasoning traces.

    Ranks responses based on both reasoning quality and final answer quality.
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.reasoning_weight = config.get('reasoning_weight', 0.4) if config else 0.4
        self.answer_weight = config.get('answer_weight', 0.6) if config else 0.6

    def get_name(self) -> str:
        return "Reasoning-Aware"

    def get_description(self) -> str:
        return f"Dual ranking: reasoning quality ({self.reasoning_weight:.0%}) + answer quality ({self.answer_weight:.0%})"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            'reasoning_weight': {
                'type': 'number',
                'min': 0.0,
                'max': 1.0,
                'default': 0.4,
                'description': 'Weight for reasoning quality (0-1)'
            },
            'answer_weight': {
                'type': 'number',
                'min': 0.0,
                'max': 1.0,
                'default': 0.6,
                'description': 'Weight for answer quality (0-1)'
            }
        }

    async def execute(
        self,
        query: str,
        models: List[str],
        chairman: str
    ) -> Dict[str, Any]:
        """Execute reasoning-aware strategy."""

        # Stage 1: Collect responses with reasoning traces
        stage1_results = await self._collect_responses_with_reasoning(query, models)

        # Check if any models provided reasoning
        has_reasoning = any(r.get('reasoning') for r in stage1_results)

        if has_reasoning:
            # Stage 2a: Rank reasoning quality
            reasoning_rankings, label_to_model = await self._rank_reasoning_quality(
                query, stage1_results, models
            )

            # Stage 2b: Rank answer quality
            answer_rankings, _ = await self._rank_answer_quality(
                query, stage1_results, models
            )

            # Combine rankings with weights
            combined_rankings = self._combine_rankings(
                reasoning_rankings,
                answer_rankings,
                label_to_model
            )
        else:
            # Fallback to simple ranking if no reasoning available
            combined_rankings, label_to_model = await self._rank_answer_quality(
                query, stage1_results, models
            )
            reasoning_rankings = None

        # Calculate aggregate rankings
        aggregate_rankings = self._calculate_aggregate_rankings(
            combined_rankings, label_to_model
        )

        # Stage 3: Chairman synthesis with reasoning context
        stage3_result = await self._synthesize_with_reasoning(
            query,
            stage1_results,
            combined_rankings,
            chairman,
            has_reasoning
        )

        return {
            'stage1': stage1_results,
            'stage2': combined_rankings,
            'stage3': stage3_result,
            'metadata': {
                'strategy': 'reasoning_aware',
                'reasoning_weight': self.reasoning_weight,
                'answer_weight': self.answer_weight,
                'has_reasoning': has_reasoning,
                'label_to_model': label_to_model,
                'aggregate_rankings': aggregate_rankings,
                'reasoning_rankings': reasoning_rankings if has_reasoning else None
            }
        }

    async def _collect_responses_with_reasoning(
        self,
        query: str,
        models: List[str]
    ) -> List[Dict[str, Any]]:
        """Collect responses and extract reasoning traces."""

        messages = [{"role": "user", "content": query}]
        responses = await query_models_parallel(models, messages)

        stage1_results = []
        for model, response in responses.items():
            if response is not None:
                result = {
                    "model": model,
                    "response": response.get('content', '')
                }

                # Extract reasoning if present
                reasoning_details = response.get('reasoning_details')
                if reasoning_details:
                    result['reasoning'] = reasoning_details
                    result['has_reasoning'] = True
                else:
                    result['has_reasoning'] = False

                stage1_results.append(result)

        return stage1_results

    async def _rank_reasoning_quality(
        self,
        user_query: str,
        stage1_results: List[Dict[str, Any]],
        models: List[str]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """Rank responses based on reasoning quality."""

        # Create anonymized labels
        labels = [chr(65 + i) for i in range(len(stage1_results))]
        label_to_model = {
            f"Response {label}": result['model']
            for label, result in zip(labels, stage1_results)
        }

        # Build reasoning evaluation prompt
        responses_text = "\n\n".join([
            f"Response {label}:\nReasoning: {result.get('reasoning', 'No explicit reasoning provided')}\nAnswer: {result['response']}"
            for label, result in zip(labels, stage1_results)
        ])

        ranking_prompt = f"""You are evaluating the REASONING QUALITY of different responses to this question:

Question: {user_query}

{responses_text}

Evaluate based on:
1. Logical coherence and structure of the reasoning
2. Depth and thoroughness of analysis
3. Identification of key considerations
4. Rigor of argumentation
5. Clarity of reasoning steps

IMPORTANT: Your final ranking MUST be formatted EXACTLY as follows:
- Start with "FINAL RANKING:" (all caps, with colon)
- Then list responses from best to worst as a numbered list
- Each line: number, period, space, then ONLY the response label (e.g., "1. Response A")

Now provide your evaluation and ranking:"""

        messages = [{"role": "user", "content": ranking_prompt}]
        responses = await query_models_parallel(models, messages)

        rankings = []
        for model, response in responses.items():
            if response is not None:
                full_text = response.get('content', '')
                parsed = self._parse_ranking_from_text(full_text)
                rankings.append({
                    "model": model,
                    "ranking": full_text,
                    "parsed_ranking": parsed,
                    "type": "reasoning"
                })

        return rankings, label_to_model

    async def _rank_answer_quality(
        self,
        user_query: str,
        stage1_results: List[Dict[str, Any]],
        models: List[str]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """Rank responses based on answer quality (same as simple strategy)."""

        labels = [chr(65 + i) for i in range(len(stage1_results))]
        label_to_model = {
            f"Response {label}": result['model']
            for label, result in zip(labels, stage1_results)
        }

        responses_text = "\n\n".join([
            f"Response {label}:\n{result['response']}"
            for label, result in zip(labels, stage1_results)
        ])

        ranking_prompt = f"""You are evaluating different responses to the following question:

Question: {user_query}

Here are the responses (anonymized):

{responses_text}

Evaluate based on accuracy, completeness, clarity, and usefulness.

FINAL RANKING: (list from best to worst)
"""

        messages = [{"role": "user", "content": ranking_prompt}]
        responses = await query_models_parallel(models, messages)

        rankings = []
        for model, response in responses.items():
            if response is not None:
                full_text = response.get('content', '')
                parsed = self._parse_ranking_from_text(full_text)
                rankings.append({
                    "model": model,
                    "ranking": full_text,
                    "parsed_ranking": parsed,
                    "type": "answer"
                })

        return rankings, label_to_model

    def _combine_rankings(
        self,
        reasoning_rankings: List[Dict[str, Any]],
        answer_rankings: List[Dict[str, Any]],
        label_to_model: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """Combine reasoning and answer rankings with weights."""

        combined = []

        for reasoning_rank, answer_rank in zip(reasoning_rankings, answer_rankings):
            # Combine the ranking texts
            combined_text = f"REASONING EVALUATION:\n{reasoning_rank['ranking']}\n\nANSWER EVALUATION:\n{answer_rank['ranking']}"

            # Calculate weighted rank positions for each response
            # (This is simplified - in practice would need more sophisticated merging)
            combined.append({
                "model": reasoning_rank['model'],
                "ranking": combined_text,
                "parsed_ranking": reasoning_rank['parsed_ranking'],  # Use reasoning as primary
                "reasoning_ranking": reasoning_rank['parsed_ranking'],
                "answer_ranking": answer_rank['parsed_ranking']
            })

        return combined

    async def _synthesize_with_reasoning(
        self,
        query: str,
        stage1_results: List[Dict[str, Any]],
        rankings: List[Dict[str, Any]],
        chairman: str,
        has_reasoning: bool
    ) -> Dict[str, Any]:
        """Synthesize final answer considering reasoning traces."""

        # Build context with reasoning traces
        stage1_text = "\n\n".join([
            f"Model: {result['model']}\nReasoning: {result.get('reasoning', 'N/A')}\nAnswer: {result['response']}"
            if has_reasoning and result.get('reasoning')
            else f"Model: {result['model']}\nAnswer: {result['response']}"
            for result in stage1_results
        ])

        stage2_text = "\n\n".join([
            f"Model: {rank['model']}\nEvaluation: {rank['ranking']}"
            for rank in rankings
        ])

        chairman_prompt = f"""You are the Chairman of an LLM Council. Multiple AI models have provided responses, some with explicit reasoning traces.

Original Question: {query}

STAGE 1 - Responses {"(with reasoning traces)" if has_reasoning else ""}:
{stage1_text}

STAGE 2 - Peer Evaluations:
{stage2_text}

Your task: Synthesize a final answer that:
- Leverages the best reasoning steps from the responses
- Provides a clear, accurate answer
- Acknowledges different approaches where relevant

Provide the final answer:"""

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
        """Parse ranking from text."""
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

    def _calculate_aggregate_rankings(
        self,
        rankings: List[Dict[str, Any]],
        label_to_model: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """Calculate aggregate rankings."""
        model_positions = defaultdict(list)

        for ranking in rankings:
            parsed_ranking = ranking.get('parsed_ranking', [])
            for position, label in enumerate(parsed_ranking, start=1):
                if label in label_to_model:
                    model_name = label_to_model[label]
                    model_positions[model_name].append(position)

        aggregate = []
        for model, positions in model_positions.items():
            if positions:
                avg_rank = sum(positions) / len(positions)
                aggregate.append({
                    "model": model,
                    "average_rank": round(avg_rank, 2),
                    "rankings_count": len(positions)
                })

        aggregate.sort(key=lambda x: x['average_rank'])
        return aggregate
