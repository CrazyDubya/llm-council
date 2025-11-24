"""Streaming event types and schemas for WebSocket communication."""

from typing import Dict, Any, Optional, List
from enum import Enum
from pydantic import BaseModel


class EventType(str, Enum):
    """Enumeration of all possible streaming event types."""

    # Connection events
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    PING = "ping"
    PONG = "pong"

    # Council execution events
    COUNCIL_START = "council_start"
    COUNCIL_COMPLETE = "council_complete"

    # Stage 1 events
    STAGE1_START = "stage1_start"
    STAGE1_MODEL_START = "stage1_model_start"
    STAGE1_MODEL_TOKEN = "stage1_model_token"
    STAGE1_MODEL_COMPLETE = "stage1_model_complete"
    STAGE1_COMPLETE = "stage1_complete"

    # Stage 2 events
    STAGE2_START = "stage2_start"
    STAGE2_MODEL_START = "stage2_model_start"
    STAGE2_MODEL_TOKEN = "stage2_model_token"
    STAGE2_MODEL_COMPLETE = "stage2_model_complete"
    STAGE2_COMPLETE = "stage2_complete"

    # Stage 3 events
    STAGE3_START = "stage3_start"
    STAGE3_TOKEN = "stage3_token"
    STAGE3_COMPLETE = "stage3_complete"

    # Metadata events
    TITLE_COMPLETE = "title_complete"
    METADATA_UPDATE = "metadata_update"

    # Error and control events
    ERROR = "error"
    WARNING = "warning"
    GENERATION_STOPPED = "generation_stopped"
    PROGRESS = "progress"


class StreamingEvent(BaseModel):
    """Base class for all streaming events."""
    type: EventType
    data: Dict[str, Any] = {}
    timestamp: Optional[float] = None


class ConnectionEvent(StreamingEvent):
    """Connection-related events."""
    pass


class CouncilStartEvent(StreamingEvent):
    """Event sent when council deliberation starts."""
    type: EventType = EventType.COUNCIL_START

    @staticmethod
    def create(query: str, strategy: str, models: List[str]) -> Dict[str, Any]:
        return {
            "type": EventType.COUNCIL_START.value,
            "data": {
                "query": query,
                "strategy": strategy,
                "models": models,
                "total_models": len(models)
            }
        }


class Stage1StartEvent(StreamingEvent):
    """Event sent when Stage 1 (initial responses) starts."""
    type: EventType = EventType.STAGE1_START

    @staticmethod
    def create(models: List[str]) -> Dict[str, Any]:
        return {
            "type": EventType.STAGE1_START.value,
            "data": {
                "models": models,
                "total_models": len(models),
                "description": "Collecting initial responses from all council models"
            }
        }


class Stage1ModelStartEvent(StreamingEvent):
    """Event sent when a specific model starts responding in Stage 1."""
    type: EventType = EventType.STAGE1_MODEL_START

    @staticmethod
    def create(model: str, model_index: int, total_models: int) -> Dict[str, Any]:
        return {
            "type": EventType.STAGE1_MODEL_START.value,
            "data": {
                "model": model,
                "model_index": model_index,
                "total_models": total_models
            }
        }


class Stage1ModelTokenEvent(StreamingEvent):
    """Event sent for each token from a model in Stage 1."""
    type: EventType = EventType.STAGE1_MODEL_TOKEN

    @staticmethod
    def create(model: str, token: str, model_index: int) -> Dict[str, Any]:
        return {
            "type": EventType.STAGE1_MODEL_TOKEN.value,
            "data": {
                "model": model,
                "token": token,
                "model_index": model_index
            }
        }


class Stage1ModelCompleteEvent(StreamingEvent):
    """Event sent when a model completes its response in Stage 1."""
    type: EventType = EventType.STAGE1_MODEL_COMPLETE

    @staticmethod
    def create(model: str, response: str, model_index: int) -> Dict[str, Any]:
        return {
            "type": EventType.STAGE1_MODEL_COMPLETE.value,
            "data": {
                "model": model,
                "response": response,
                "model_index": model_index,
                "response_length": len(response)
            }
        }


class Stage1CompleteEvent(StreamingEvent):
    """Event sent when all Stage 1 responses are complete."""
    type: EventType = EventType.STAGE1_COMPLETE

    @staticmethod
    def create(responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "type": EventType.STAGE1_COMPLETE.value,
            "data": {
                "responses": responses,
                "total_responses": len(responses)
            }
        }


class Stage2StartEvent(StreamingEvent):
    """Event sent when Stage 2 (peer review) starts."""
    type: EventType = EventType.STAGE2_START

    @staticmethod
    def create(models: List[str], responses_count: int) -> Dict[str, Any]:
        return {
            "type": EventType.STAGE2_START.value,
            "data": {
                "models": models,
                "total_models": len(models),
                "responses_to_rank": responses_count,
                "description": "Models ranking each other's responses anonymously"
            }
        }


class Stage2ModelStartEvent(StreamingEvent):
    """Event sent when a model starts ranking in Stage 2."""
    type: EventType = EventType.STAGE2_MODEL_START

    @staticmethod
    def create(model: str, model_index: int, total_models: int) -> Dict[str, Any]:
        return {
            "type": EventType.STAGE2_MODEL_START.value,
            "data": {
                "model": model,
                "model_index": model_index,
                "total_models": total_models
            }
        }


class Stage2ModelTokenEvent(StreamingEvent):
    """Event sent for each token from a model's ranking in Stage 2."""
    type: EventType = EventType.STAGE2_MODEL_TOKEN

    @staticmethod
    def create(model: str, token: str, model_index: int) -> Dict[str, Any]:
        return {
            "type": EventType.STAGE2_MODEL_TOKEN.value,
            "data": {
                "model": model,
                "token": token,
                "model_index": model_index
            }
        }


class Stage2ModelCompleteEvent(StreamingEvent):
    """Event sent when a model completes its ranking in Stage 2."""
    type: EventType = EventType.STAGE2_MODEL_COMPLETE

    @staticmethod
    def create(model: str, ranking: str, parsed_ranking: List[str], model_index: int) -> Dict[str, Any]:
        return {
            "type": EventType.STAGE2_MODEL_COMPLETE.value,
            "data": {
                "model": model,
                "ranking": ranking,
                "parsed_ranking": parsed_ranking,
                "model_index": model_index
            }
        }


class Stage2CompleteEvent(StreamingEvent):
    """Event sent when all Stage 2 rankings are complete."""
    type: EventType = EventType.STAGE2_COMPLETE

    @staticmethod
    def create(rankings: List[Dict[str, Any]], metadata: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": EventType.STAGE2_COMPLETE.value,
            "data": {
                "rankings": rankings,
                "metadata": metadata,
                "total_rankings": len(rankings)
            }
        }


class Stage3StartEvent(StreamingEvent):
    """Event sent when Stage 3 (chairman synthesis) starts."""
    type: EventType = EventType.STAGE3_START

    @staticmethod
    def create(chairman: str) -> Dict[str, Any]:
        return {
            "type": EventType.STAGE3_START.value,
            "data": {
                "chairman": chairman,
                "description": "Chairman synthesizing final answer from all responses and rankings"
            }
        }


class Stage3TokenEvent(StreamingEvent):
    """Event sent for each token from the chairman's synthesis."""
    type: EventType = EventType.STAGE3_TOKEN

    @staticmethod
    def create(token: str) -> Dict[str, Any]:
        return {
            "type": EventType.STAGE3_TOKEN.value,
            "data": {
                "token": token
            }
        }


class Stage3CompleteEvent(StreamingEvent):
    """Event sent when Stage 3 synthesis is complete."""
    type: EventType = EventType.STAGE3_COMPLETE

    @staticmethod
    def create(synthesis: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": EventType.STAGE3_COMPLETE.value,
            "data": {
                "synthesis": synthesis,
                "response_length": len(synthesis.get("response", ""))
            }
        }


class TitleCompleteEvent(StreamingEvent):
    """Event sent when conversation title generation is complete."""
    type: EventType = EventType.TITLE_COMPLETE

    @staticmethod
    def create(title: str) -> Dict[str, Any]:
        return {
            "type": EventType.TITLE_COMPLETE.value,
            "data": {
                "title": title
            }
        }


class MetadataUpdateEvent(StreamingEvent):
    """Event sent when metadata is updated."""
    type: EventType = EventType.METADATA_UPDATE

    @staticmethod
    def create(metadata: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": EventType.METADATA_UPDATE.value,
            "data": metadata
        }


class ProgressEvent(StreamingEvent):
    """Event sent to update progress during long operations."""
    type: EventType = EventType.PROGRESS

    @staticmethod
    def create(stage: str, progress: float, message: str) -> Dict[str, Any]:
        return {
            "type": EventType.PROGRESS.value,
            "data": {
                "stage": stage,
                "progress": progress,  # 0.0 to 1.0
                "message": message
            }
        }


class ErrorEvent(StreamingEvent):
    """Event sent when an error occurs."""
    type: EventType = EventType.ERROR

    @staticmethod
    def create(error: str, stage: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {
            "type": EventType.ERROR.value,
            "data": {
                "error": error,
                "stage": stage,
                "details": details or {}
            }
        }


class WarningEvent(StreamingEvent):
    """Event sent when a warning occurs."""
    type: EventType = EventType.WARNING

    @staticmethod
    def create(warning: str, stage: Optional[str] = None) -> Dict[str, Any]:
        return {
            "type": EventType.WARNING.value,
            "data": {
                "warning": warning,
                "stage": stage
            }
        }


class CouncilCompleteEvent(StreamingEvent):
    """Event sent when the entire council deliberation is complete."""
    type: EventType = EventType.COUNCIL_COMPLETE

    @staticmethod
    def create(conversation_id: str, message_index: int) -> Dict[str, Any]:
        return {
            "type": EventType.COUNCIL_COMPLETE.value,
            "data": {
                "conversation_id": conversation_id,
                "message_index": message_index,
                "status": "success"
            }
        }


# Helper function to serialize events
def serialize_event(event: Dict[str, Any]) -> str:
    """
    Serialize an event to JSON string for transmission.

    Args:
        event: Event dictionary

    Returns:
        JSON string
    """
    import json
    return json.dumps(event)


def deserialize_event(data: str) -> Dict[str, Any]:
    """
    Deserialize an event from JSON string.

    Args:
        data: JSON string

    Returns:
        Event dictionary
    """
    import json
    return json.loads(data)
