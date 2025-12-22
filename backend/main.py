"""FastAPI backend for LLM Council."""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
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
from .config import COUNCIL_MODELS, CHAIRMAN_MODEL, CORS_ORIGINS, SERVER_PORT
from .analytics import AnalyticsEngine
from .query_classifier import QueryClassifier
from .websocket import connection_manager
from .openrouter import query_model_with_streaming
from .cache import get_cache, start_cleanup_task

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

# Start cache cleanup task on startup
@app.on_event("startup")
async def startup_event():
    """Start background tasks on application startup."""
    logger.info("Starting cache cleanup task...")
    asyncio.create_task(start_cleanup_task(interval=3600))  # Clean up every hour

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
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


@app.get("/api/cache/stats")
async def get_cache_stats():
    """
    Get cache statistics including hit rate, size, and performance metrics.

    Returns comprehensive cache statistics for monitoring and optimization.
    """
    cache = get_cache()
    stats = await cache.get_stats()
    return stats


@app.post("/api/cache/clear")
async def clear_cache():
    """
    Clear all cached responses.

    Use with caution - this will remove all cached data and require
    fresh queries to all models.
    """
    cache = get_cache()
    await cache.clear()
    return {"status": "success", "message": "Cache cleared successfully"}


@app.post("/api/cache/cleanup")
async def cleanup_cache():
    """
    Manually trigger cleanup of expired cache entries.

    Returns the number of entries removed.
    """
    cache = get_cache()
    removed = await cache.cleanup_expired()
    return {
        "status": "success",
        "message": f"Removed {removed} expired entries",
        "removed_count": removed
    }


@app.websocket("/ws/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    """
    WebSocket endpoint for real-time streaming of council deliberations.

    Clients connect to this endpoint to receive token-by-token streaming
    of model responses as they're generated.

    Args:
        websocket: The WebSocket connection
        conversation_id: ID of the conversation
    """
    await connection_manager.connect(websocket, conversation_id)
    logger.info(f"WebSocket connection established for conversation {conversation_id}")

    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_json()

            message_type = data.get('type')

            if message_type == 'ping':
                # Respond to ping with pong
                await websocket.send_json({'type': 'pong'})

            elif message_type == 'send_message':
                # Handle message send request
                query = data.get('content')
                strategy_name = data.get('strategy', 'simple')
                strategy_config = data.get('strategy_config', {})

                # Verify conversation exists
                conversation = storage.get_conversation(conversation_id)
                if conversation is None:
                    await connection_manager.send_error(
                        f"Conversation {conversation_id} not found",
                        conversation_id
                    )
                    continue

                # Check if first message
                is_first_message = len(conversation["messages"]) == 0

                # Add user message
                storage.add_user_message(conversation_id, query)

                try:
                    # Send start event
                    await connection_manager.send_event(
                        'council_start',
                        {'query': query, 'strategy': strategy_name},
                        conversation_id
                    )

                    # Generate title in background if first message
                    title_task = None
                    if is_first_message:
                        title_task = asyncio.create_task(generate_conversation_title(query))

                    # Get and execute strategy
                    # For now, we'll execute without true streaming (Day 2 task)
                    # This is just the WebSocket infrastructure setup
                    if strategy_name == 'weighted_voting':
                        strategy_config['analytics_engine'] = analytics

                    strategy = get_strategy(strategy_name, config=strategy_config)

                    # Execute strategy with streaming support
                    result = await strategy.execute(
                        query=query,
                        models=COUNCIL_MODELS,
                        chairman=CHAIRMAN_MODEL,
                        connection_manager=connection_manager,
                        conversation_id=conversation_id
                    )

                    # Wait for title if generating
                    if title_task:
                        title = await title_task
                        storage.update_conversation_title(conversation_id, title)
                        await connection_manager.send_event(
                            'title_complete',
                            {'title': title},
                            conversation_id
                        )

                    # Save assistant message
                    storage.add_assistant_message(
                        conversation_id,
                        result['stage1'],
                        result['stage2'],
                        result['stage3'],
                        metadata=result['metadata']
                    )

                    # Send completion
                    await connection_manager.send_completion(conversation_id)

                except Exception as e:
                    logger.error(f"Error in WebSocket message handling: {e}", exc_info=True)
                    await connection_manager.send_error(str(e), conversation_id)

            elif message_type == 'stop_generation':
                # Handle stop generation request (future: implement cancellation)
                await websocket.send_json({
                    'type': 'generation_stopped',
                    'message': 'Generation stop not yet implemented'
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for conversation {conversation_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    finally:
        await connection_manager.disconnect(websocket, conversation_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT)
