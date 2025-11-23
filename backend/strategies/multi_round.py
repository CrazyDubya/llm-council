"""Multi-round deliberation strategy with iterative refinement."""

import re
from typing import List, Dict, Any, Tuple
from collections import defaultdict

from .base import EnsembleStrategy
from ..openrouter import query_models_parallel, query_model


class MultiRoundStrategy(EnsembleStrategy):
    """
    Multi-round deliberation strategy:
    - Round 1: Initial responses
    - Round 2+: Models see top responses + critiques, can revise
    - Final: Chairman synthesizes with full evolution context
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.rounds = config.get('rounds', 2) if config else 2
        self.show_top_n = config.get('show_top_n', 2) if config else 2

    def get_name(self) -> str:
        return f"Multi-Round ({self.rounds} rounds)"

    def get_description(self) -> str:
        return f"Iterative deliberation with {self.rounds} rounds of refinement based on peer feedback"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            'rounds': {
                'type': 'integer',
                'min': 2,
                'max': 5,
                'default': 2,
                'description': 'Number of deliberation rounds'
            },
            'show_top_n': {
                'type': 'integer',
                'min': 1,
                'max': 5,
                'default': 2,
                'description': 'Number of top responses to show in revision prompts'
            }
        }

    async def execute(
        self,
        query: str,
        models: List[str],
        chairman: str
    ) -> Dict[str, Any]:
        """Execute multi-round deliberation strategy."""

        all_rounds = []

        for round_num in range(self.rounds):
            if round_num == 0:
                # Round 1: Initial responses
                round_data = await self._execute_initial_round(query, models)
            else:
                # Round 2+: Show top responses and allow revision
                round_data = await self._execute_revision_round(
                    query, models, all_rounds[-1], round_num + 1
                )

            all_rounds.append(round_data)

        # Calculate final aggregate rankings from last round
        final_rankings = all_rounds[-1]['aggregate_rankings']

        # Synthesize with full evolution context
        stage3_result = await self._synthesize_with_evolution(
            query, all_rounds, chairman
        )

        # Calculate evolution metrics
        evolution_metrics = self._calculate_evolution_metrics(all_rounds)

        return {
            'stage1': all_rounds,  # All rounds with responses
            'stage2': all_rounds[-1]['rankings'],  # Final round rankings
            'stage3': stage3_result,
            'metadata': {
                'strategy': 'multi_round',
                'rounds': self.rounds,
                'label_to_model': all_rounds[-1]['label_to_model'],
                'aggregate_rankings': final_rankings,
                'evolution': evolution_metrics
            }
        }

    async def _execute_initial_round(
        self,
        query: str,
        models: List[str]
    ) -> Dict[str, Any]:
        """Execute Round 1: Initial responses and rankings."""

        # Collect initial responses
        messages = [{"role": "user", "content": query}]
        responses = await query_models_parallel(models, messages)

        stage1_results = []
        for model, response in responses.items():
            if response is not None:
                stage1_results.append({
                    "model": model,
                    "response": response.get('content', '')
                })

        # Anonymize and rank
        rankings, label_to_model = await self._collect_rankings(
            query, stage1_results, models
        )

        # Calculate aggregate
        aggregate_rankings = self._calculate_aggregate_rankings(
            rankings, label_to_model
        )

        return {
            'round_number': 1,
            'responses': stage1_results,
            'rankings': rankings,
            'label_to_model': label_to_model,
            'aggregate_rankings': aggregate_rankings
        }

    async def _execute_revision_round(
        self,
        query: str,
        models: List[str],
        previous_round: Dict[str, Any],
        round_number: int
    ) -> Dict[str, Any]:
        """Execute revision round: Show top responses and collect revisions."""

        # Get top N responses from previous round
        top_responses = self._get_top_responses(
            previous_round['aggregate_rankings'],
            previous_round['responses'],
            previous_round['rankings'],
            n=self.show_top_n
        )

        # Build revision prompt for each model
        revision_prompts = {}
        for model in models:
            revision_prompts[model] = self._build_revision_prompt(
                query, top_responses, round_number
            )

        # Collect revised responses
        revised_responses = []
        for model in models:
            messages = [{"role": "user", "content": revision_prompts[model]}]
            response = await query_model(model, messages)

            if response is not None:
                revised_responses.append({
                    "model": model,
                    "response": response.get('content', '')
                })

        # Rank the revised responses
        rankings, label_to_model = await self._collect_rankings(
            query, revised_responses, models
        )

        # Calculate aggregate
        aggregate_rankings = self._calculate_aggregate_rankings(
            rankings, label_to_model
        )

        return {
            'round_number': round_number,
            'responses': revised_responses,
            'rankings': rankings,
            'label_to_model': label_to_model,
            'aggregate_rankings': aggregate_rankings,
            'top_from_previous': top_responses
        }

    def _get_top_responses(
        self,
        aggregate_rankings: List[Dict[str, Any]],
        responses: List[Dict[str, Any]],
        rankings: List[Dict[str, Any]],
        n: int
    ) -> List[Dict[str, Any]]:
        """Get top N responses based on aggregate rankings."""

        top_models = [rank['model'] for rank in aggregate_rankings[:n]]

        top_responses = []
        for model in top_models:
            # Find the response
            response_data = next(
                (r for r in responses if r['model'] == model),
                None
            )
            if response_data:
                # Find representative critique
                critique = self._get_representative_critique(model, rankings)

                top_responses.append({
                    'model': model,
                    'response': response_data['response'],
                    'average_rank': next(
                        r['average_rank'] for r in aggregate_rankings
                        if r['model'] == model
                    ),
                    'critique': critique
                })

        return top_responses

    def _get_representative_critique(
        self,
        target_model: str,
        rankings: List[Dict[str, Any]]
    ) -> str:
        """Get a representative critique of the target model's response."""

        critiques = []
        for ranking in rankings:
            # Extract the part of the ranking that discusses this model
            # This is a simplified approach - could be enhanced
            ranking_text = ranking.get('ranking', '')
            critiques.append(ranking_text[:200])  # First 200 chars as sample

        return critiques[0] if critiques else "No specific critique available."

    def _build_revision_prompt(
        self,
        original_query: str,
        top_responses: List[Dict[str, Any]],
        round_number: int
    ) -> str:
        """Build prompt for revision round."""

        top_text = "\n\n".join([
            f"Response from {resp['model']} (Avg Rank: {resp['average_rank']}):\n{resp['response']}"
            for resp in top_responses
        ])

        return f"""Original question: {original_query}

This is Round {round_number} of a multi-round deliberation. In the previous round, the top-ranked responses were:

{top_text}

Based on these top responses and their insights, please provide your revised response to the original question.

You may:
- Strengthen your original answer by incorporating valid points from the top responses
- Change your approach if you find their reasoning more compelling
- Maintain your original position if you believe it's still the best approach

Provide your revised answer:"""

    async def _collect_rankings(
        self,
        user_query: str,
        responses: List[Dict[str, Any]],
        models: List[str]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """Collect rankings (same as SimpleRankingStrategy)."""

        labels = [chr(65 + i) for i in range(len(responses))]
        label_to_model = {
            f"Response {label}": result['model']
            for label, result in zip(labels, responses)
        }

        responses_text = "\n\n".join([
            f"Response {label}:\n{result['response']}"
            for label, result in zip(labels, responses)
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
        responses_dict = await query_models_parallel(models, messages)

        stage2_results = []
        for model, response in responses_dict.items():
            if response is not None:
                full_text = response.get('content', '')
                parsed = self._parse_ranking_from_text(full_text)
                stage2_results.append({
                    "model": model,
                    "ranking": full_text,
                    "parsed_ranking": parsed
                })

        return stage2_results, label_to_model

    def _parse_ranking_from_text(self, ranking_text: str) -> List[str]:
        """Parse ranking from text (same as SimpleRankingStrategy)."""

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
        """Calculate aggregate rankings (same as SimpleRankingStrategy)."""

        model_positions = defaultdict(list)

        for ranking in rankings:
            parsed_ranking = self._parse_ranking_from_text(ranking['ranking'])
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

    async def _synthesize_with_evolution(
        self,
        query: str,
        all_rounds: List[Dict[str, Any]],
        chairman: str
    ) -> Dict[str, Any]:
        """Synthesize final answer considering evolution across rounds."""

        # Build context showing evolution
        evolution_text = ""
        for round_data in all_rounds:
            round_num = round_data['round_number']
            evolution_text += f"\n\n=== ROUND {round_num} ===\n"

            for resp in round_data['responses']:
                evolution_text += f"\nModel: {resp['model']}\nResponse: {resp['response']}\n"

            evolution_text += f"\nAggregate Rankings (Round {round_num}):\n"
            for rank in round_data['aggregate_rankings']:
                evolution_text += f"- {rank['model']}: Avg Rank {rank['average_rank']}\n"

        chairman_prompt = f"""You are the Chairman of an LLM Council conducting multi-round deliberation.

Original Question: {query}

The council has completed {len(all_rounds)} rounds of deliberation. Here is the evolution:

{evolution_text}

Your task as Chairman is to synthesize the final answer, considering:
- How responses evolved across rounds
- Which insights emerged or strengthened over time
- The final rankings after deliberation
- Any convergence or divergence in thinking

Provide a comprehensive final answer that represents the council's collective wisdom after deliberation:"""

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

    def _calculate_evolution_metrics(
        self,
        all_rounds: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate metrics about how responses evolved."""

        if len(all_rounds) < 2:
            return {'rounds': 1, 'evolution_detected': False}

        # Track rank changes
        rank_changes = []
        for i in range(1, len(all_rounds)):
            prev_rankings = {
                r['model']: r['average_rank']
                for r in all_rounds[i-1]['aggregate_rankings']
            }
            curr_rankings = {
                r['model']: r['average_rank']
                for r in all_rounds[i]['aggregate_rankings']
            }

            changes = []
            for model in curr_rankings:
                if model in prev_rankings:
                    change = prev_rankings[model] - curr_rankings[model]
                    if abs(change) > 0.1:  # Significant change
                        changes.append({
                            'model': model,
                            'change': round(change, 2),
                            'improved': change > 0
                        })

            rank_changes.append(changes)

        return {
            'rounds': len(all_rounds),
            'rank_changes': rank_changes,
            'evolution_detected': any(len(changes) > 0 for changes in rank_changes)
        }
