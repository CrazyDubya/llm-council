"""SWOT Analysis strategy - structured decision framework."""

import re
from typing import List, Dict, Any, Tuple
from collections import defaultdict

from .base import EnsembleStrategy
from ..openrouter import query_models_parallel, query_model


class SwotAnalysisStrategy(EnsembleStrategy):
    """
    SWOT Analysis framework strategy:
    1. Each model performs SWOT analysis (Strengths, Weaknesses, Opportunities, Threats)
    2. Models evaluate each other's analyses for comprehensiveness and insight
    3. Chairman synthesizes the best insights from all SWOTs
    """

    def get_name(self) -> str:
        return "SWOT Analysis"

    def get_description(self) -> str:
        return "Structured framework: models analyze Strengths, Weaknesses, Opportunities, and Threats"

    async def execute(
        self,
        query: str,
        models: List[str],
        chairman: str
    ) -> Dict[str, Any]:
        """Execute the SWOT analysis strategy."""

        # Stage 1: Collect SWOT analyses
        stage1_results = await self._stage1_collect_swot(query, models)

        # If no models responded successfully, return error
        if not stage1_results:
            return {
                'stage1': [],
                'stage2': [],
                'stage3': {
                    "model": "error",
                    "response": "All models failed to respond. Please try again."
                },
                'metadata': {'framework': 'swot'}
            }

        # Stage 2: Evaluate SWOT analyses
        stage2_results, label_to_model = await self._stage2_evaluate_swots(
            query, stage1_results, models
        )

        # Calculate aggregate rankings
        aggregate_rankings = self._calculate_aggregate_rankings(
            stage2_results, label_to_model
        )

        # Stage 3: Synthesize final SWOT
        stage3_result = await self._stage3_synthesize_swot(
            query,
            stage1_results,
            stage2_results,
            chairman
        )

        # Prepare metadata
        metadata = {
            "label_to_model": label_to_model,
            "aggregate_rankings": aggregate_rankings,
            "strategy": "swot",
            "framework": "swot"
        }

        return {
            'stage1': stage1_results,
            'stage2': stage2_results,
            'stage3': stage3_result,
            'metadata': metadata
        }

    async def _stage1_collect_swot(
        self,
        user_query: str,
        models: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Stage 1: Collect SWOT analyses from all council models.

        Args:
            user_query: The user's question/topic
            models: List of model identifiers

        Returns:
            List of dicts with 'model' and 'response' keys
        """
        swot_prompt = f"""Please perform a comprehensive SWOT analysis for the following topic or question:

{user_query}

Provide a structured SWOT analysis covering:

**STRENGTHS:**
- List the key strengths, advantages, or positive aspects
- What works well? What are the strong points?

**WEAKNESSES:**
- List the limitations, disadvantages, or negative aspects
- What could be improved? What are the weak points?

**OPPORTUNITIES:**
- List potential opportunities or positive future possibilities
- What could be leveraged? What trends favor this?

**THREATS:**
- List potential threats, risks, or challenges
- What could go wrong? What external factors pose risks?

Be specific and insightful in each category. Aim for 3-5 points per category when possible."""

        messages = [{"role": "user", "content": swot_prompt}]

        # Query all models in parallel
        responses = await query_models_parallel(models, messages)

        # Format results
        stage1_results = []
        for model, response in responses.items():
            if response is not None:  # Only include successful responses
                stage1_results.append({
                    "model": model,
                    "response": response.get('content', '')
                })

        return stage1_results

    async def _stage2_evaluate_swots(
        self,
        user_query: str,
        stage1_results: List[Dict[str, Any]],
        models: List[str]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """
        Stage 2: Each model evaluates the SWOT analyses.

        Args:
            user_query: The original user query
            stage1_results: SWOT analyses from Stage 1
            models: List of model identifiers

        Returns:
            Tuple of (evaluations list, label_to_model mapping)
        """
        # Create anonymized labels for responses (Response A, Response B, etc.)
        labels = [chr(65 + i) for i in range(len(stage1_results))]  # A, B, C, ...

        # Create mapping from label to model name
        label_to_model = {
            f"Response {label}": result['model']
            for label, result in zip(labels, stage1_results)
        }

        # Build the evaluation prompt
        responses_text = "\n\n".join([
            f"Response {label}:\n{result['response']}"
            for label, result in zip(labels, stage1_results)
        ])

        evaluation_prompt = f"""You are evaluating different SWOT analyses for the following topic:

Topic: {user_query}

Here are the SWOT analyses from different models (anonymized):

{responses_text}

Your task:
1. Evaluate each SWOT analysis based on:
   - **Comprehensiveness**: Does it cover all four categories thoroughly?
   - **Insight**: Are the points specific, actionable, and insightful?
   - **Balance**: Is there good balance across categories?
   - **Relevance**: Do all points directly relate to the topic?

2. Then, at the very end of your response, provide a final ranking.

IMPORTANT: Your final ranking MUST be formatted EXACTLY as follows:
- Start with the line "FINAL RANKING:" (all caps, with colon)
- Then list the responses from best to worst as a numbered list
- Each line should be: number, period, space, then ONLY the response label (e.g., "1. Response A")
- Do not add any other text or explanations in the ranking section

Example format:

Response A has strong opportunities section but weak on threats...
Response B provides good balance across all categories...
Response C offers the most specific and actionable points...

FINAL RANKING:
1. Response C
2. Response B
3. Response A

Now provide your evaluation and ranking:"""

        messages = [{"role": "user", "content": evaluation_prompt}]

        # Get evaluations from all council models in parallel
        responses = await query_models_parallel(models, messages)

        # Format results
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

    async def _stage3_synthesize_swot(
        self,
        user_query: str,
        stage1_results: List[Dict[str, Any]],
        stage2_results: List[Dict[str, Any]],
        chairman: str
    ) -> Dict[str, Any]:
        """
        Stage 3: Chairman synthesizes the best SWOT insights.

        Args:
            user_query: The original user query
            stage1_results: Individual SWOT analyses from Stage 1
            stage2_results: Evaluations from Stage 2
            chairman: Chairman model identifier

        Returns:
            Dict with 'model' and 'response' keys
        """
        # Build comprehensive context for chairman
        stage1_text = "\n\n".join([
            f"Model: {result['model']}\nSWOT Analysis: {result['response']}"
            for result in stage1_results
        ])

        stage2_text = "\n\n".join([
            f"Model: {result['model']}\nEvaluation: {result['ranking']}"
            for result in stage2_results
        ])

        chairman_prompt = f"""You are the Chairman of an LLM Council. Multiple AI models have performed SWOT analyses on a topic, and then evaluated each other's analyses.

Original Topic: {user_query}

STAGE 1 - Individual SWOT Analyses:
{stage1_text}

STAGE 2 - Peer Evaluations:
{stage2_text}

Your task as Chairman is to synthesize the best insights from all analyses into a comprehensive, final SWOT analysis.

Instructions:
1. Review all the SWOT analyses and their evaluations
2. Identify the most insightful, specific, and relevant points from each category
3. Produce a final SWOT analysis that represents the council's collective wisdom
4. Ensure good balance across all four categories
5. Remove redundancies and combine similar points where appropriate

Provide the final SWOT analysis in a clear, structured format with STRENGTHS, WEAKNESSES, OPPORTUNITIES, and THREATS sections:"""

        messages = [{"role": "user", "content": chairman_prompt}]

        # Query the chairman model
        response = await query_model(chairman, messages)

        if response is None:
            # Fallback if chairman fails
            return {
                "model": chairman,
                "response": "Error: Unable to generate final synthesis."
            }

        return {
            "model": chairman,
            "response": response.get('content', '')
        }

    def _parse_ranking_from_text(self, ranking_text: str) -> List[str]:
        """
        Parse the FINAL RANKING section from the model's response.

        Args:
            ranking_text: The full text response from the model

        Returns:
            List of response labels in ranked order
        """
        # Look for "FINAL RANKING:" section
        if "FINAL RANKING:" in ranking_text:
            # Extract everything after "FINAL RANKING:"
            parts = ranking_text.split("FINAL RANKING:")
            if len(parts) >= 2:
                ranking_section = parts[1]
                # Try to extract numbered list format (e.g., "1. Response A")
                numbered_matches = re.findall(r'\d+\.\s*Response [A-Z]', ranking_section)
                if numbered_matches:
                    # Extract just the "Response X" part
                    return [re.search(r'Response [A-Z]', m).group() for m in numbered_matches]

                # Fallback: Extract all "Response X" patterns in order
                matches = re.findall(r'Response [A-Z]', ranking_section)
                return matches

        # Fallback: try to find any "Response X" patterns in order
        matches = re.findall(r'Response [A-Z]', ranking_text)
        return matches

    def _calculate_aggregate_rankings(
        self,
        stage2_results: List[Dict[str, Any]],
        label_to_model: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Calculate aggregate rankings across all evaluations.

        Args:
            stage2_results: Evaluations from each model
            label_to_model: Mapping from anonymous labels to model names

        Returns:
            List of dicts with model name and average rank, sorted best to worst
        """
        # Track positions for each model
        model_positions = defaultdict(list)

        for evaluation in stage2_results:
            ranking_text = evaluation['ranking']

            # Parse the ranking from the structured format
            parsed_ranking = self._parse_ranking_from_text(ranking_text)

            for position, label in enumerate(parsed_ranking, start=1):
                if label in label_to_model:
                    model_name = label_to_model[label]
                    model_positions[model_name].append(position)

        # Calculate average position for each model
        aggregate = []
        for model, positions in model_positions.items():
            if positions:
                avg_rank = sum(positions) / len(positions)
                aggregate.append({
                    "model": model,
                    "average_rank": round(avg_rank, 2),
                    "rankings_count": len(positions)
                })

        # Sort by average rank (lower is better)
        aggregate.sort(key=lambda x: x['average_rank'])

        return aggregate
