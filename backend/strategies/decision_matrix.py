"""Decision Matrix strategy - multi-criteria decision analysis framework."""

import re
from typing import List, Dict, Any, Tuple
from collections import defaultdict

from .base import EnsembleStrategy
from ..openrouter import query_models_parallel, query_model


class DecisionMatrixStrategy(EnsembleStrategy):
    """
    Decision Matrix framework strategy:
    1. Each model creates a weighted decision matrix across multiple criteria
    2. Models evaluate each other's matrices for completeness and rigor
    3. Chairman synthesizes the most balanced multi-criteria assessment
    """

    def get_name(self) -> str:
        return "Decision Matrix"

    def get_description(self) -> str:
        return "Multi-criteria analysis: models score options across weighted criteria"

    async def execute(
        self,
        query: str,
        models: List[str],
        chairman: str
    ) -> Dict[str, Any]:
        """Execute the decision matrix strategy."""

        # Stage 1: Collect decision matrices
        stage1_results = await self._stage1_collect_matrices(query, models)

        if not stage1_results:
            return {
                'stage1': [],
                'stage2': [],
                'stage3': {
                    "model": "error",
                    "response": "All models failed to respond. Please try again."
                },
                'metadata': {'framework': 'decision_matrix'}
            }

        # Stage 2: Evaluate matrices
        stage2_results, label_to_model = await self._stage2_evaluate_matrices(
            query, stage1_results, models
        )

        # Calculate aggregate rankings
        aggregate_rankings = self._calculate_aggregate_rankings(
            stage2_results, label_to_model
        )

        # Stage 3: Synthesize final matrix
        stage3_result = await self._stage3_synthesize_matrix(
            query,
            stage1_results,
            stage2_results,
            chairman
        )

        # Prepare metadata
        metadata = {
            "label_to_model": label_to_model,
            "aggregate_rankings": aggregate_rankings,
            "strategy": "decision_matrix",
            "framework": "decision_matrix"
        }

        return {
            'stage1': stage1_results,
            'stage2': stage2_results,
            'stage3': stage3_result,
            'metadata': metadata
        }

    async def _stage1_collect_matrices(
        self,
        user_query: str,
        models: List[str]
    ) -> List[Dict[str, Any]]:
        """Stage 1: Collect decision matrices from all models."""

        matrix_prompt = f"""Please create a comprehensive decision matrix for the following topic or decision:

{user_query}

Provide a structured multi-criteria analysis:

**STEP 1: IDENTIFY OPTIONS**
- List the main options/alternatives being considered (if not explicitly stated, infer reasonable options)

**STEP 2: DEFINE CRITERIA**
- List 4-6 key criteria for evaluation
- For each criterion, assign a weight (1-10) indicating its importance
- Explain why each criterion matters

**STEP 3: SCORE EACH OPTION**
- Create a matrix scoring each option against each criterion (1-10 scale)
- For each score, briefly justify the rating

**STEP 4: CALCULATE WEIGHTED SCORES**
- For each option, calculate: Criterion Weight × Score
- Sum the weighted scores for each option
- Show total weighted score for each option

**STEP 5: RECOMMENDATION**
- Based on the weighted scores, recommend the best option
- Highlight any close calls or important trade-offs

Be thorough and show all calculations clearly."""

        messages = [{"role": "user", "content": matrix_prompt}]

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

    async def _stage2_evaluate_matrices(
        self,
        user_query: str,
        stage1_results: List[Dict[str, Any]],
        models: List[str]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """Stage 2: Each model evaluates the decision matrices."""

        labels = [chr(65 + i) for i in range(len(stage1_results))]

        label_to_model = {
            f"Response {label}": result['model']
            for label, result in zip(labels, stage1_results)
        }

        responses_text = "\n\n".join([
            f"Response {label}:\n{result['response']}"
            for label, result in zip(labels, stage1_results)
        ])

        evaluation_prompt = f"""You are evaluating different decision matrices for the following topic:

Topic: {user_query}

Here are the matrices from different models (anonymized):

{responses_text}

Your task:
1. Evaluate each matrix based on:
   - **Criteria Selection**: Are the criteria comprehensive and relevant?
   - **Weighting Justification**: Are weights reasonable and explained?
   - **Scoring Rigor**: Are scores well-justified and consistent?
   - **Calculation Accuracy**: Are weighted scores calculated correctly?
   - **Option Coverage**: Are all reasonable options considered?
   - **Trade-off Analysis**: Does it acknowledge difficult trade-offs?

2. Then, at the very end of your response, provide a final ranking.

IMPORTANT: Your final ranking MUST be formatted EXACTLY as follows:
- Start with the line "FINAL RANKING:" (all caps, with colon)
- Then list the responses from best to worst as a numbered list
- Each line should be: number, period, space, then ONLY the response label (e.g., "1. Response A")

Example format:

Response A has good criteria but questionable weights...
Response B shows excellent rigor and calculation...

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

    async def _stage3_synthesize_matrix(
        self,
        user_query: str,
        stage1_results: List[Dict[str, Any]],
        stage2_results: List[Dict[str, Any]],
        chairman: str
    ) -> Dict[str, Any]:
        """Stage 3: Chairman synthesizes the best decision matrix."""

        stage1_text = "\n\n".join([
            f"Model: {result['model']}\nMatrix: {result['response']}"
            for result in stage1_results
        ])

        stage2_text = "\n\n".join([
            f"Model: {result['model']}\nEvaluation: {result['ranking']}"
            for result in stage2_results
        ])

        chairman_prompt = f"""You are the Chairman of an LLM Council. Multiple AI models have created decision matrices, and then evaluated each other's work.

Original Topic: {user_query}

STAGE 1 - Individual Decision Matrices:
{stage1_text}

STAGE 2 - Peer Evaluations:
{stage2_text}

Your task is to synthesize the best elements into a final, comprehensive decision matrix.

Instructions:
1. Review all matrices and evaluations
2. Determine the most comprehensive set of options and criteria
3. Assign reasonable weights to criteria (considering all input)
4. Score each option against each criterion
5. Calculate weighted totals correctly
6. Provide a clear recommendation with trade-off analysis

Present the final decision matrix in a clear, structured format with all calculations shown."""

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
