"""FastAPI backend for LLM Council."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import uuid
import json
import asyncio

from . import storage
from .council import generate_conversation_title
from .strategies import get_strategy, list_strategies
from .strategies.recommender import StrategyRecommender
from .config import COUNCIL_MODELS, CHAIRMAN_MODEL
from .analytics import AnalyticsEngine
from .query_classifier import QueryClassifier

# Initialize analytics engine, query classifier, and strategy recommender
analytics = AnalyticsEngine()
classifier = QueryClassifier()
recommender = StrategyRecommender(classifier, analytics)

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
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Execute the strategy
    result = await strategy.execute(
        query=request.content,
        models=COUNCIL_MODELS,
        chairman=CHAIRMAN_MODEL
    )

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
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
