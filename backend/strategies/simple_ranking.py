"""Simple ranking strategy - the original v0.1 approach."""

import re
import asyncio
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict

from .base import EnsembleStrategy
from ..openrouter import query_models_parallel, query_model, query_model_streaming
from ..streaming_events import (
    Stage1StartEvent, Stage1ModelStartEvent, Stage1ModelTokenEvent,
    Stage1ModelCompleteEvent, Stage1CompleteEvent,
    Stage2StartEvent, Stage2ModelStartEvent, Stage2ModelTokenEvent,
    Stage2ModelCompleteEvent, Stage2CompleteEvent,
    Stage3StartEvent, Stage3TokenEvent, Stage3CompleteEvent
)
from ..cache import get_cache
import logging

logger = logging.getLogger(__name__)


class SimpleRankingStrategy(EnsembleStrategy):
    """
    Simple 3-stage ranking strategy:
    1. Collect individual responses from all models
    2. Each model ranks anonymized responses from peers
    3. Chairman synthesizes final answer with full context
    """

    def get_name(self) -> str:
        return "Simple Ranking"

    def get_description(self) -> str:
        return "3-stage process: individual responses → anonymous peer ranking → chairman synthesis"

    async def execute(
        self,
        query: str,
        models: List[str],
        chairman: str,
        connection_manager=None,
        conversation_id: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Execute the simple ranking strategy.

        Args:
            query: User's question
            models: List of model identifiers
            chairman: Chairman model identifier
            connection_manager: Optional WebSocket connection manager for streaming
            conversation_id: Optional conversation ID for WebSocket streaming
            use_cache: Whether to use caching (default: True)
        """

        cache = get_cache()

        # Check cache first (skip if streaming, as we want real-time tokens)
        if use_cache and not (connection_manager and conversation_id):
            cached_response = await cache.get_response(
                query=query,
                models=models,
                strategy='simple',
                strategy_config={}
            )

            if cached_response is not None:
                logger.info(f"Cache HIT for query: {query[:50]}...")
                return cached_response

            logger.info(f"Cache MISS for query: {query[:50]}...")

        # Stage 1: Collect individual responses
        stage1_results = await self._stage1_collect_responses(
            query, models, connection_manager, conversation_id
        )

        # If no models responded successfully, return error
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
            query, stage1_results, models, connection_manager, conversation_id
        )

        # Calculate aggregate rankings
        aggregate_rankings = self._calculate_aggregate_rankings(
            stage2_results, label_to_model
        )

        # Stage 3: Synthesize final answer
        stage3_result = await self._stage3_synthesize_final(
            query,
            stage1_results,
            stage2_results,
            chairman,
            connection_manager,
            conversation_id
        )

        # Prepare metadata
        metadata = {
            "label_to_model": label_to_model,
            "aggregate_rankings": aggregate_rankings,
            "strategy": "simple"
        }

        result = {
            'stage1': stage1_results,
            'stage2': stage2_results,
            'stage3': stage3_result,
            'metadata': metadata
        }

        # Store in cache (skip if streaming, as streaming responses shouldn't be cached)
        if use_cache and not (connection_manager and conversation_id):
            await cache.set_response(
                query=query,
                models=models,
                strategy='simple',
                response=result,
                strategy_config={}
            )
            logger.info(f"Cached response for query: {query[:50]}...")

        return result

    async def _stage1_collect_responses(
        self,
        user_query: str,
        models: List[str],
        connection_manager=None,
        conversation_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Stage 1: Collect individual responses from all council models.

        Args:
            user_query: The user's question
            models: List of model identifiers
            connection_manager: Optional WebSocket connection manager for streaming
            conversation_id: Optional conversation ID for WebSocket streaming

        Returns:
            List of dicts with 'model' and 'response' keys
        """
        messages = [{"role": "user", "content": user_query}]

        # Send stage 1 start event
        if connection_manager and conversation_id:
            await connection_manager.send_event(
                'stage1_start',
                Stage1StartEvent.create(models)['data'],
                conversation_id
            )

        stage1_results = []

        # If streaming is enabled, stream each model's response
        if connection_manager and conversation_id:
            # Stream responses sequentially for better UX (show progress per model)
            for idx, model in enumerate(models):
                # Send model start event
                await connection_manager.send_event(
                    'stage1_model_start',
                    Stage1ModelStartEvent.create(model, idx, len(models))['data'],
                    conversation_id
                )

                try:
                    # Stream the model's response
                    tokens = []
                    async for token in query_model_streaming(model, messages):
                        tokens.append(token)
                        # Send each token
                        await connection_manager.send_event(
                            'stage1_model_token',
                            Stage1ModelTokenEvent.create(model, token, idx)['data'],
                            conversation_id
                        )

                    # Collect full response
                    full_response = ''.join(tokens)

                    if full_response:
                        stage1_results.append({
                            "model": model,
                            "response": full_response
                        })

                        # Send model complete event
                        await connection_manager.send_event(
                            'stage1_model_complete',
                            Stage1ModelCompleteEvent.create(model, full_response, idx)['data'],
                            conversation_id
                        )

                except Exception as e:
                    print(f"Error streaming from model {model}: {e}")
                    # Continue with other models

            # Send stage 1 complete event
            await connection_manager.send_event(
                'stage1_complete',
                Stage1CompleteEvent.create(stage1_results)['data'],
                conversation_id
            )

        else:
            # Non-streaming mode (backward compatibility)
            responses = await query_models_parallel(models, messages)

            # Format results
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
        models: List[str],
        connection_manager=None,
        conversation_id: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """
        Stage 2: Each model ranks the anonymized responses.

        Args:
            user_query: The original user query
            stage1_results: Results from Stage 1
            models: List of model identifiers
            connection_manager: Optional WebSocket connection manager for streaming
            conversation_id: Optional conversation ID for WebSocket streaming

        Returns:
            Tuple of (rankings list, label_to_model mapping)
        """
        # Create anonymized labels for responses (Response A, Response B, etc.)
        labels = [chr(65 + i) for i in range(len(stage1_results))]  # A, B, C, ...

        # Create mapping from label to model name
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

Example of the correct format for your ENTIRE response:

Response A provides good detail on X but misses Y...
Response B is accurate but lacks depth on Z...
Response C offers the most comprehensive answer...

FINAL RANKING:
1. Response C
2. Response A
3. Response B

Now provide your evaluation and ranking:"""

        messages = [{"role": "user", "content": ranking_prompt}]

        # Send stage 2 start event
        if connection_manager and conversation_id:
            await connection_manager.send_event(
                'stage2_start',
                Stage2StartEvent.create(models, len(stage1_results))['data'],
                conversation_id
            )

        stage2_results = []

        # If streaming is enabled, stream rankings
        if connection_manager and conversation_id:
            # Stream rankings sequentially
            for idx, model in enumerate(models):
                # Send model start event
                await connection_manager.send_event(
                    'stage2_model_start',
                    Stage2ModelStartEvent.create(model, idx, len(models))['data'],
                    conversation_id
                )

                try:
                    # Stream the ranking
                    tokens = []
                    async for token in query_model_streaming(model, messages):
                        tokens.append(token)
                        # Send each token
                        await connection_manager.send_event(
                            'stage2_model_token',
                            Stage2ModelTokenEvent.create(model, token, idx)['data'],
                            conversation_id
                        )

                    # Collect full ranking
                    full_text = ''.join(tokens)
                    parsed = self._parse_ranking_from_text(full_text)

                    if full_text:
                        stage2_results.append({
                            "model": model,
                            "ranking": full_text,
                            "parsed_ranking": parsed
                        })

                        # Send model complete event
                        await connection_manager.send_event(
                            'stage2_model_complete',
                            Stage2ModelCompleteEvent.create(model, full_text, parsed, idx)['data'],
                            conversation_id
                        )

                except Exception as e:
                    print(f"Error streaming ranking from model {model}: {e}")
                    # Continue with other models

            # Send stage 2 complete event
            # Calculate aggregate rankings for the event
            aggregate = self._calculate_aggregate_rankings(stage2_results, label_to_model)
            await connection_manager.send_event(
                'stage2_complete',
                Stage2CompleteEvent.create(
                    stage2_results,
                    {"label_to_model": label_to_model, "aggregate_rankings": aggregate}
                )['data'],
                conversation_id
            )

        else:
            # Non-streaming mode (backward compatibility)
            responses = await query_models_parallel(models, messages)

            # Format results
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
        chairman: str,
        connection_manager=None,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Stage 3: Chairman synthesizes final response.

        Args:
            user_query: The original user query
            stage1_results: Individual model responses from Stage 1
            stage2_results: Rankings from Stage 2
            chairman: Chairman model identifier
            connection_manager: Optional WebSocket connection manager for streaming
            conversation_id: Optional conversation ID for WebSocket streaming

        Returns:
            Dict with 'model' and 'response' keys
        """
        # Build comprehensive context for chairman
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

STAGE 2 - Peer Rankings:
{stage2_text}

Your task as Chairman is to synthesize all of this information into a single, comprehensive, accurate answer to the user's original question. Consider:
- The individual responses and their insights
- The peer rankings and what they reveal about response quality
- Any patterns of agreement or disagreement

Provide a clear, well-reasoned final answer that represents the council's collective wisdom:"""

        messages = [{"role": "user", "content": chairman_prompt}]

        # Send stage 3 start event
        if connection_manager and conversation_id:
            await connection_manager.send_event(
                'stage3_start',
                Stage3StartEvent.create(chairman)['data'],
                conversation_id
            )

        # If streaming is enabled, stream the chairman's synthesis
        if connection_manager and conversation_id:
            try:
                # Stream the chairman's response
                tokens = []
                async for token in query_model_streaming(chairman, messages):
                    tokens.append(token)
                    # Send each token
                    await connection_manager.send_event(
                        'stage3_token',
                        Stage3TokenEvent.create(token)['data'],
                        conversation_id
                    )

                # Collect full response
                full_response = ''.join(tokens)

                result = {
                    "model": chairman,
                    "response": full_response if full_response else "Error: Unable to generate final synthesis."
                }

                # Send stage 3 complete event
                await connection_manager.send_event(
                    'stage3_complete',
                    Stage3CompleteEvent.create(result)['data'],
                    conversation_id
                )

                return result

            except Exception as e:
                print(f"Error streaming from chairman {chairman}: {e}")
                return {
                    "model": chairman,
                    "response": "Error: Unable to generate final synthesis."
                }

        else:
            # Non-streaming mode (backward compatibility)
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
                # This pattern looks for: number, period, optional space, "Response X"
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
        Calculate aggregate rankings across all models.

        Args:
            stage2_results: Rankings from each model
            label_to_model: Mapping from anonymous labels to model names

        Returns:
            List of dicts with model name and average rank, sorted best to worst
        """
        # Track positions for each model
        model_positions = defaultdict(list)

        for ranking in stage2_results:
            ranking_text = ranking['ranking']

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
