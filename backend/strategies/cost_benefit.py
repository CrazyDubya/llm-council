"""Cost-Benefit Analysis strategy - structured decision framework."""

import re
from typing import List, Dict, Any, Tuple
from collections import defaultdict

from .base import EnsembleStrategy
from ..openrouter import query_models_parallel, query_model


class CostBenefitStrategy(EnsembleStrategy):
    """
    Cost-Benefit Analysis framework strategy:
    1. Each model performs cost-benefit analysis with quantitative scoring
    2. Models evaluate each other's analyses for thoroughness and balance
    3. Chairman synthesizes the most comprehensive cost-benefit assessment
    """

    def get_name(self) -> str:
        return "Cost-Benefit Analysis"

    def get_description(self) -> str:
        return "Structured framework: models analyze costs vs benefits with scoring"

    async def execute(
        self,
        query: str,
        models: List[str],
        chairman: str
    ) -> Dict[str, Any]:
        """Execute the cost-benefit analysis strategy."""

        # Stage 1: Collect cost-benefit analyses
        stage1_results = await self._stage1_collect_analyses(query, models)

        if not stage1_results:
            return {
                'stage1': [],
                'stage2': [],
                'stage3': {
                    "model": "error",
                    "response": "All models failed to respond. Please try again."
                },
                'metadata': {'framework': 'cost_benefit'}
            }

        # Stage 2: Evaluate analyses
        stage2_results, label_to_model = await self._stage2_evaluate_analyses(
            query, stage1_results, models
        )

        # Calculate aggregate rankings
        aggregate_rankings = self._calculate_aggregate_rankings(
            stage2_results, label_to_model
        )

        # Stage 3: Synthesize final analysis
        stage3_result = await self._stage3_synthesize_analysis(
            query,
            stage1_results,
            stage2_results,
            chairman
        )

        # Prepare metadata
        metadata = {
            "label_to_model": label_to_model,
            "aggregate_rankings": aggregate_rankings,
            "strategy": "cost_benefit",
            "framework": "cost_benefit"
        }

        return {
            'stage1': stage1_results,
            'stage2': stage2_results,
            'stage3': stage3_result,
            'metadata': metadata
        }

    async def _stage1_collect_analyses(
        self,
        user_query: str,
        models: List[str]
    ) -> List[Dict[str, Any]]:
        """Stage 1: Collect cost-benefit analyses from all models."""

        analysis_prompt = f"""Please perform a comprehensive cost-benefit analysis for the following topic or decision:

{user_query}

Provide a structured analysis covering:

**BENEFITS (PROS):**
- List all potential benefits, advantages, and positive outcomes
- For each benefit, assign a score from 1-10 indicating its importance/magnitude
- Explain why each benefit matters

**COSTS (CONS):**
- List all potential costs, disadvantages, and negative outcomes
- For each cost, assign a score from 1-10 indicating its severity/impact
- Explain why each cost matters

**QUANTITATIVE SUMMARY:**
- Total benefit score (sum of all benefit scores)
- Total cost score (sum of all cost scores)
- Net score (benefits minus costs)
- Overall recommendation based on the analysis

Be specific, thorough, and balanced in your analysis. Consider both tangible and intangible factors."""

        messages = [{"role": "user", "content": analysis_prompt}]

        # Query all models in parallel
        responses = await query_models_parallel(models, messages)

        # Format results
        stage1_results = []
        for model, response in responses.items():
            if response is not None:
                stage1_results.append({
                    "model": model,
                    "response": response.get('content', '')
                })

        return stage1_results

    async def _stage2_evaluate_analyses(
        self,
        user_query: str,
        stage1_results: List[Dict[str, Any]],
        models: List[str]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """Stage 2: Each model evaluates the cost-benefit analyses."""

        labels = [chr(65 + i) for i in range(len(stage1_results))]

        label_to_model = {
            f"Response {label}": result['model']
            for label, result in zip(labels, stage1_results)
        }

        responses_text = "\n\n".join([
            f"Response {label}:\n{result['response']}"
            for label, result in zip(labels, stage1_results)
        ])

        evaluation_prompt = f"""You are evaluating different cost-benefit analyses for the following topic:

Topic: {user_query}

Here are the analyses from different models (anonymized):

{responses_text}

Your task:
1. Evaluate each analysis based on:
   - **Comprehensiveness**: Does it identify all major costs and benefits?
   - **Balance**: Are both costs and benefits fairly represented?
   - **Quantification**: Are scores reasonable and well-justified?
   - **Insight**: Does it uncover non-obvious factors?
   - **Recommendation quality**: Is the conclusion logical based on the analysis?

2. Then, at the very end of your response, provide a final ranking.

IMPORTANT: Your final ranking MUST be formatted EXACTLY as follows:
- Start with the line "FINAL RANKING:" (all caps, with colon)
- Then list the responses from best to worst as a numbered list
- Each line should be: number, period, space, then ONLY the response label (e.g., "1. Response A")

Example format:

Response A provides thorough cost analysis but misses some benefits...
Response B has excellent quantification and balance...

FINAL RANKING:
1. Response B
2. Response A

Now provide your evaluation and ranking:"""

        messages = [{"role": "user", "content": evaluation_prompt}]

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

    async def _stage3_synthesize_analysis(
        self,
        user_query: str,
        stage1_results: List[Dict[str, Any]],
        stage2_results: List[Dict[str, Any]],
        chairman: str
    ) -> Dict[str, Any]:
        """Stage 3: Chairman synthesizes the best cost-benefit analysis."""

        stage1_text = "\n\n".join([
            f"Model: {result['model']}\nAnalysis: {result['response']}"
            for result in stage1_results
        ])

        stage2_text = "\n\n".join([
            f"Model: {result['model']}\nEvaluation: {result['ranking']}"
            for result in stage2_results
        ])

        chairman_prompt = f"""You are the Chairman of an LLM Council. Multiple AI models have performed cost-benefit analyses, and then evaluated each other's work.

Original Topic: {user_query}

STAGE 1 - Individual Cost-Benefit Analyses:
{stage1_text}

STAGE 2 - Peer Evaluations:
{stage2_text}

Your task is to synthesize the best insights into a final, comprehensive cost-benefit analysis.

Instructions:
1. Review all analyses and evaluations
2. Identify the most important costs and benefits mentioned
3. Provide reasonable scores (1-10) for each factor
4. Calculate totals and net score
5. Give a clear recommendation based on the analysis

Format your response with clear BENEFITS and COSTS sections, scoring, and a final recommendation."""

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
        """Parse the FINAL RANKING section."""
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
        stage2_results: List[Dict[str, Any]],
        label_to_model: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """Calculate aggregate rankings across all evaluations."""
        model_positions = defaultdict(list)

        for evaluation in stage2_results:
            ranking_text = evaluation['ranking']
            parsed_ranking = self._parse_ranking_from_text(ranking_text)

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
