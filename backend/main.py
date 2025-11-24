"""FastAPI backend for LLM Council."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import uuid
import json
import asyncio
import logging

from . import storage
from .council import generate_conversation_title
from .strategies import get_strategy, list_strategies
from .strategies.recommender import StrategyRecommender
from .config import COUNCIL_MODELS, CHAIRMAN_MODEL
from .analytics import AnalyticsEngine
from .query_classifier import QueryClassifier
from . import time_travel, fact_checking, model_management

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize analytics engine, query classifier, and strategy recommender
logger.info("Initializing analytics engine and recommender system...")
analytics = AnalyticsEngine()
classifier = QueryClassifier()
recommender = StrategyRecommender(classifier, analytics)
logger.info("System initialization complete")

app = FastAPI(title="LLM Council API")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""
    pass


class SendMessageRequest(BaseModel):
    """Request to send a message in a conversation."""
    content: str
    strategy: str = "simple"  # Default to simple strategy
    strategy_config: Dict[str, Any] = {}


class RecommendStrategyRequest(BaseModel):
    """Request to get strategy recommendation for a query."""
    query: str


class CompareStrategiesRequest(BaseModel):
    """Request to compare multiple strategies on the same query."""
    query: str
    strategies: List[str]
    strategy_configs: Dict[str, Dict[str, Any]] = {}


class ConversationMetadata(BaseModel):
    """Conversation metadata for list view."""
    id: str
    created_at: str
    title: str
    message_count: int
    tags: List[str] = []
    archived: bool = False


class Conversation(BaseModel):
    """Full conversation with all messages."""
    id: str
    created_at: str
    title: str
    messages: List[Dict[str, Any]]


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "LLM Council API"}


@app.get("/api/strategies")
async def get_strategies():
    """List all available ensemble strategies."""
    return list_strategies()


@app.post("/api/strategies/recommend")
async def recommend_strategy(request: RecommendStrategyRequest):
    """
    Recommend the best ensemble strategy based on query classification
    and historical performance data.

    Analyzes the query content to determine its type (technical, analytical, etc.)
    and combines this with historical performance data to suggest the optimal strategy.
    """
    recommendation = recommender.recommend(request.query)

    return {
        'strategy': recommendation.strategy,
        'confidence': recommendation.confidence,
        'explanation': recommendation.explanation,
        'fallback_options': recommendation.fallback_options,
        'query_category': recommendation.query_category,
        'performance_data': recommendation.performance_data
    }


@app.post("/api/strategies/compare")
async def compare_strategies(request: CompareStrategiesRequest):
    """
    A/B test multiple strategies on the same query.

    Runs the query through multiple strategies in parallel and returns
    all results for side-by-side comparison. Useful for evaluating
    which strategy works best for a particular type of query.

    Note: This endpoint does not save results to any conversation.
    It's purely for experimental comparison purposes.
    """
    # Validate strategies
    available_strategies = list_strategies()
    for strategy_name in request.strategies:
        if strategy_name not in available_strategies:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown strategy '{strategy_name}'. Available: {', '.join(available_strategies.keys())}"
            )

    # Run all strategies in parallel
    async def run_strategy(strategy_name: str):
        try:
            # Get config for this strategy
            config = request.strategy_configs.get(strategy_name, {})

            # Inject analytics for weighted_voting
            if strategy_name == 'weighted_voting':
                config = dict(config)
                config['analytics_engine'] = analytics

            # Get and execute strategy
            strategy = get_strategy(strategy_name, config=config)
            result = await strategy.execute(
                query=request.query,
                models=COUNCIL_MODELS,
                chairman=CHAIRMAN_MODEL
            )

            return {
                'strategy': strategy_name,
                'success': True,
                'result': result
            }
        except Exception as e:
            return {
                'strategy': strategy_name,
                'success': False,
                'error': str(e)
            }

    # Execute all strategies in parallel
    tasks = [run_strategy(s) for s in request.strategies]
    results = await asyncio.gather(*tasks)

    return {
        'query': request.query,
        'comparisons': results,
        'timestamp': asyncio.get_event_loop().time()
    }


@app.get("/api/conversations", response_model=List[ConversationMetadata])
async def list_conversations():
    """List all conversations (metadata only)."""
    return storage.list_conversations()


@app.post("/api/conversations", response_model=Conversation)
async def create_conversation(request: CreateConversationRequest):
    """Create a new conversation."""
    conversation_id = str(uuid.uuid4())
    conversation = storage.create_conversation(conversation_id)
    return conversation


@app.get("/api/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    """Get a specific conversation with all its messages."""
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@app.post("/api/conversations/{conversation_id}/message")
async def send_message(conversation_id: str, request: SendMessageRequest):
    """
    Send a message and run the 3-stage council process.
    Returns the complete response with all stages.
    """
    # Check if conversation exists
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Check if this is the first message
    is_first_message = len(conversation["messages"]) == 0

    # Add user message
    storage.add_user_message(conversation_id, request.content)

    # If this is the first message, generate a title
    if is_first_message:
        title = await generate_conversation_title(request.content)
        storage.update_conversation_title(conversation_id, title)

    # Get the requested strategy
    try:
        # Inject analytics engine for strategies that need it
        config = dict(request.strategy_config)  # Copy to avoid mutation
        if request.strategy == 'weighted_voting':
            config['analytics_engine'] = analytics

        strategy = get_strategy(request.strategy, config=config)
        logger.info(f"Executing strategy: {request.strategy} for conversation: {conversation_id}")
    except ValueError as e:
        logger.error(f"Invalid strategy: {request.strategy}")
        raise HTTPException(status_code=400, detail=str(e))

    # Execute the strategy
    try:
        result = await strategy.execute(
            query=request.content,
            models=COUNCIL_MODELS,
            chairman=CHAIRMAN_MODEL
        )
        logger.info(f"Strategy execution complete: {request.strategy}")
    except Exception as e:
        logger.error(f"Strategy execution failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Strategy execution failed")

    # Add assistant message with all stages and metadata
    storage.add_assistant_message(
        conversation_id,
        result['stage1'],
        result['stage2'],
        result['stage3'],
        metadata=result['metadata']
    )

    # Return the complete response with metadata
    return {
        "stage1": result['stage1'],
        "stage2": result['stage2'],
        "stage3": result['stage3'],
        "metadata": result['metadata']
    }


@app.post("/api/conversations/{conversation_id}/message/stream")
async def send_message_stream(conversation_id: str, request: SendMessageRequest):
    """
    Send a message and stream the 3-stage council process.
    Returns Server-Sent Events as each stage completes.

    Note: Currently only supports 'simple' strategy in streaming mode.
    For other strategies, use the non-streaming endpoint.
    """
    # Check if conversation exists
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Check if this is the first message
    is_first_message = len(conversation["messages"]) == 0

    # For now, streaming only supports simple strategy
    if request.strategy != "simple":
        raise HTTPException(
            status_code=400,
            detail="Streaming mode currently only supports 'simple' strategy. Use non-streaming endpoint for other strategies."
        )

    async def event_generator():
        try:
            # Add user message
            storage.add_user_message(conversation_id, request.content)

            # Start title generation in parallel (don't await yet)
            title_task = None
            if is_first_message:
                title_task = asyncio.create_task(generate_conversation_title(request.content))

            # Get strategy and execute with streaming
            # Inject analytics engine for strategies that need it
            config = dict(request.strategy_config)  # Copy to avoid mutation
            if request.strategy == 'weighted_voting':
                config['analytics_engine'] = analytics

            strategy = get_strategy(request.strategy, config=config)

            # Execute strategy (non-streaming for now - future: support streaming in strategy interface)
            yield f"data: {json.dumps({'type': 'stage1_start'})}\n\n"
            result = await strategy.execute(
                query=request.content,
                models=COUNCIL_MODELS,
                chairman=CHAIRMAN_MODEL
            )

            yield f"data: {json.dumps({'type': 'stage1_complete', 'data': result['stage1']})}\n\n"

            yield f"data: {json.dumps({'type': 'stage2_start'})}\n\n"
            yield f"data: {json.dumps({'type': 'stage2_complete', 'data': result['stage2'], 'metadata': result['metadata']})}\n\n"

            yield f"data: {json.dumps({'type': 'stage3_start'})}\n\n"
            yield f"data: {json.dumps({'type': 'stage3_complete', 'data': result['stage3']})}\n\n"

            # Wait for title generation if it was started
            if title_task:
                title = await title_task
                storage.update_conversation_title(conversation_id, title)
                yield f"data: {json.dumps({'type': 'title_complete', 'data': {'title': title}})}\n\n"

            # Save complete assistant message with metadata
            storage.add_assistant_message(
                conversation_id,
                result['stage1'],
                result['stage2'],
                result['stage3'],
                metadata=result['metadata']
            )

            # Send completion event
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"

        except Exception as e:
            # Send error event
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.get("/api/analytics/summary")
async def get_analytics_summary():
    """Get comprehensive analytics summary."""
    summary = analytics.compute_all_analytics()
    return summary


@app.get("/api/analytics/leaderboard")
async def get_leaderboard(limit: int = 10):
    """
    Get model leaderboard ranked by win rate.

    Args:
        limit: Maximum number of models to return (default: 10)
    """
    leaderboard = analytics.get_model_leaderboard(limit=limit)
    return {"leaderboard": leaderboard}


@app.get("/api/analytics/models/{model}")
async def get_model_analytics(model: str):
    """
    Get performance metrics for a specific model.

    Args:
        model: Model identifier (URL-encoded)
    """
    performance = analytics.get_model_performance(model)
    if performance is None:
        raise HTTPException(status_code=404, detail=f"Model {model} not found in analytics")
    return {"model": model, "performance": performance}


@app.get("/api/analytics/strategies/{strategy}")
async def get_strategy_analytics(strategy: str):
    """
    Get performance metrics for a specific strategy.

    Args:
        strategy: Strategy identifier
    """
    performance = analytics.get_strategy_performance(strategy)
    if performance is None:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy} not found in analytics")
    return {"strategy": strategy, "performance": performance}


class FeedbackRequest(BaseModel):
    """Request to update message feedback."""
    feedback: int  # -1, 0, or 1


@app.post("/api/conversations/{conversation_id}/messages/{message_index}/feedback")
async def update_feedback(
    conversation_id: str,
    message_index: int,
    request: FeedbackRequest
):
    """
    Update user feedback for a specific message.

    Args:
        conversation_id: The conversation ID
        message_index: Index of the message (0-based)
        request: Feedback request with feedback value (-1, 0, 1)
    """
    try:
        storage.update_message_feedback(
            conversation_id,
            message_index,
            request.feedback
        )
        # Invalidate analytics cache since feedback affects recommendations
        analytics.invalidate_cache()
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class TagRequest(BaseModel):
    """Request to add/remove a tag."""
    tag: str


class TagsRequest(BaseModel):
    """Request to set all tags."""
    tags: List[str]


@app.get("/api/conversations/search")
async def search_conversations_endpoint(
    query: str = None,
    tags: str = None,
    include_archived: bool = False
):
    """
    Search conversations by text query and/or tags.

    Args:
        query: Text to search for in title and messages
        tags: Comma-separated list of tags
        include_archived: Include archived conversations in results
    """
    # Parse tags if provided
    tag_list = None
    if tags:
        tag_list = [t.strip() for t in tags.split(',') if t.strip()]

    results = storage.search_conversations(
        query=query,
        tags=tag_list,
        include_archived=include_archived
    )

    return {"results": results, "count": len(results)}


@app.post("/api/conversations/{conversation_id}/tags")
async def add_tag(conversation_id: str, request: TagRequest):
    """Add a tag to a conversation."""
    try:
        storage.add_conversation_tag(conversation_id, request.tag)
        return {"status": "success", "tag": request.tag}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/api/conversations/{conversation_id}/tags")
async def remove_tag(conversation_id: str, request: TagRequest):
    """Remove a tag from a conversation."""
    try:
        storage.remove_conversation_tag(conversation_id, request.tag)
        return {"status": "success", "tag": request.tag}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.put("/api/conversations/{conversation_id}/tags")
async def set_tags(conversation_id: str, request: TagsRequest):
    """Set all tags for a conversation (replaces existing tags)."""
    try:
        storage.set_conversation_tags(conversation_id, request.tags)
        return {"status": "success", "tags": request.tags}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/conversations/{conversation_id}/archive")
async def archive_conversation_endpoint(conversation_id: str):
    """Archive a conversation."""
    try:
        storage.archive_conversation(conversation_id)
        return {"status": "success", "archived": True}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/conversations/{conversation_id}/unarchive")
async def unarchive_conversation_endpoint(conversation_id: str):
    """Unarchive a conversation."""
    try:
        storage.unarchive_conversation(conversation_id)
        return {"status": "success", "archived": False}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ===== TIME-TRAVEL BENCHMARKING ENDPOINTS =====

class CreateBenchmarkRequest(BaseModel):
    """Request to create a benchmark snapshot."""
    conversation_id: str
    message_index: int


class RerunBenchmarkRequest(BaseModel):
    """Request to rerun a benchmark."""
    models: List[str]
    chairman: str
    strategy: str = "simple"


@app.post("/api/benchmarks")
async def create_benchmark(request: CreateBenchmarkRequest):
    """Create a benchmark snapshot from a conversation response."""
    try:
        conv = storage.get_conversation(request.conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

        if request.message_index >= len(conv['messages']):
            raise HTTPException(status_code=400, detail="Invalid message index")

        message = conv['messages'][request.message_index]
        if message['role'] != 'assistant':
            raise HTTPException(status_code=400, detail="Can only benchmark assistant messages")

        snapshot_id = time_travel.create_benchmark_snapshot(
            request.conversation_id,
            request.message_index,
            {
                'stage1': message.get('stage1'),
                'stage2': message.get('stage2'),
                'stage3': message.get('stage3'),
                'metadata': message.get('metadata')
            }
        )

        return {"status": "success", "snapshot_id": snapshot_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/benchmarks")
async def list_benchmarks():
    """List all benchmark snapshots."""
    benchmarks = time_travel.list_benchmarks()
    return {"benchmarks": benchmarks}


@app.get("/api/benchmarks/{snapshot_id}")
async def get_benchmark(snapshot_id: str):
    """Get a specific benchmark snapshot."""
    benchmark = time_travel.get_benchmark(snapshot_id)
    if not benchmark:
        raise HTTPException(status_code=404, detail="Benchmark not found")
    return benchmark


@app.post("/api/benchmarks/{snapshot_id}/rerun")
async def rerun_benchmark(snapshot_id: str, request: RerunBenchmarkRequest):
    """Re-run a benchmark with current models."""
    try:
        result = await time_travel.rerun_benchmark(
            snapshot_id,
            request.models,
            request.chairman,
            request.strategy
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ===== FACT-CHECKING ENDPOINTS =====

class AnalyzeResponseRequest(BaseModel):
    """Request to analyze a response for fact-checking."""
    text: str


@app.post("/api/fact-check/citations")
async def extract_citations_endpoint(request: AnalyzeResponseRequest):
    """Extract citations from text."""
    citations = fact_checking.extract_citations(request.text)
    return {"citations": citations, "count": len(citations)}


@app.post("/api/fact-check/claims")
async def extract_claims_endpoint(request: AnalyzeResponseRequest):
    """Extract factual claims from text."""
    claims = fact_checking.extract_claims(request.text)
    numerical_claims = fact_checking.extract_numerical_claims(request.text)

    return {
        "claims": claims,
        "numerical_claims": numerical_claims,
        "total_claims": len(claims) + len(numerical_claims)
    }


class CrossReferenceRequest(BaseModel):
    """Request for cross-reference validation."""
    responses: List[Dict[str, str]]


@app.post("/api/fact-check/cross-reference")
async def cross_reference_endpoint(request: CrossReferenceRequest):
    """Validate consistency across multiple responses."""
    result = fact_checking.cross_reference_validate(request.responses)
    return result


# ===== MODEL MANAGEMENT ENDPOINTS =====

@app.get("/api/models")
async def list_models(
    category: str = None,
    min_context: int = None,
    max_cost: float = None,
    search: str = None
):
    """
    List available models with optional filtering.

    Query parameters:
        category: Filter by category (flagship, budget, open_source)
        min_context: Minimum context length
        max_cost: Maximum cost per 1M tokens
        search: Search term for name/description
    """
    models = await model_management.fetch_available_models()

    if any([category, min_context, max_cost, search]):
        models = model_management.filter_models(
            models,
            category=category,
            min_context=min_context,
            max_cost=max_cost,
            search=search
        )

    return {"models": models, "count": len(models)}


@app.get("/api/models/{model_id:path}")
async def get_model_info_endpoint(model_id: str):
    """Get detailed information about a specific model."""
    model_info = model_management.get_model_info(model_id)
    if not model_info:
        raise HTTPException(status_code=404, detail="Model not found")
    return model_info


class EstimateCostRequest(BaseModel):
    """Request to estimate cost."""
    model_ids: List[str]
    avg_prompt_tokens: int = 1000
    avg_completion_tokens: int = 500
    num_calls: int = 1


@app.post("/api/models/estimate-cost")
async def estimate_cost_endpoint(request: EstimateCostRequest):
    """Estimate cost for using specific models."""
    estimate = model_management.estimate_cost(
        request.model_ids,
        request.avg_prompt_tokens,
        request.avg_completion_tokens,
        request.num_calls
    )
    return estimate


class RecommendCouncilRequest(BaseModel):
    """Request for council recommendation."""
    budget: float = None
    diversity: bool = True
    include_reasoning: bool = False


@app.post("/api/models/recommend-council")
async def recommend_council_endpoint(request: RecommendCouncilRequest):
    """Get recommended council composition."""
    recommendations = model_management.recommend_council(
        budget=request.budget,
        diversity=request.diversity,
        include_reasoning=request.include_reasoning
    )
    return {"recommended_models": recommendations}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
