"""JSON-based storage for conversations."""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from .config import DATA_DIR


def ensure_data_dir():
    """Ensure the data directory exists."""
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)


def get_conversation_path(conversation_id: str) -> str:
    """Get the file path for a conversation."""
    return os.path.join(DATA_DIR, f"{conversation_id}.json")


def create_conversation(conversation_id: str) -> Dict[str, Any]:
    """
    Create a new conversation.

    Args:
        conversation_id: Unique identifier for the conversation

    Returns:
        New conversation dict
    """
    ensure_data_dir()

    conversation = {
        "id": conversation_id,
        "created_at": datetime.utcnow().isoformat(),
        "title": "New Conversation",
        "messages": [],
        "tags": [],
        "archived": False
    }

    # Save to file
    path = get_conversation_path(conversation_id)
    with open(path, 'w') as f:
        json.dump(conversation, f, indent=2)

    return conversation


def get_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    """
    Load a conversation from storage.

    Args:
        conversation_id: Unique identifier for the conversation

    Returns:
        Conversation dict or None if not found
    """
    path = get_conversation_path(conversation_id)

    if not os.path.exists(path):
        return None

    with open(path, 'r') as f:
        return json.load(f)


def save_conversation(conversation: Dict[str, Any]):
    """
    Save a conversation to storage.

    Args:
        conversation: Conversation dict to save
    """
    ensure_data_dir()

    path = get_conversation_path(conversation['id'])
    with open(path, 'w') as f:
        json.dump(conversation, f, indent=2)


def list_conversations(include_archived: bool = False) -> List[Dict[str, Any]]:
    """
    List all conversations (metadata only).

    Args:
        include_archived: If True, include archived conversations. Default False.

    Returns:
        List of conversation metadata dicts
    """
    ensure_data_dir()

    conversations = []
    for filename in os.listdir(DATA_DIR):
        if filename.endswith('.json'):
            path = os.path.join(DATA_DIR, filename)
            with open(path, 'r') as f:
                data = json.load(f)

                # Skip archived if not requested
                is_archived = data.get("archived", False)
                if is_archived and not include_archived:
                    continue

                # Return metadata only
                conversations.append({
                    "id": data["id"],
                    "created_at": data["created_at"],
                    "title": data.get("title", "New Conversation"),
                    "message_count": len(data["messages"]),
                    "tags": data.get("tags", []),
                    "archived": is_archived
                })

    # Sort by creation time, newest first
    conversations.sort(key=lambda x: x["created_at"], reverse=True)

    return conversations


def add_user_message(conversation_id: str, content: str):
    """
    Add a user message to a conversation.

    Args:
        conversation_id: Conversation identifier
        content: User message content
    """
    conversation = get_conversation(conversation_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    conversation["messages"].append({
        "role": "user",
        "content": content
    })

    save_conversation(conversation)


def add_assistant_message(
    conversation_id: str,
    stage1: List[Dict[str, Any]],
    stage2: List[Dict[str, Any]],
    stage3: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Add an assistant message with all 3 stages to a conversation.

    Args:
        conversation_id: Conversation identifier
        stage1: List of individual model responses or rounds
        stage2: List of model rankings
        stage3: Final synthesized response
        metadata: Optional metadata (strategy, rankings, execution time, etc.)
    """
    conversation = get_conversation(conversation_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    message = {
        "role": "assistant",
        "stage1": stage1,
        "stage2": stage2,
        "stage3": stage3,
        "timestamp": datetime.utcnow().isoformat(),
        "user_feedback": None  # -1 (dislike), 0 (neutral), 1 (like), None (no feedback yet)
    }

    # Add metadata if provided
    if metadata:
        message["metadata"] = metadata

    conversation["messages"].append(message)

    save_conversation(conversation)


def update_conversation_title(conversation_id: str, title: str):
    """
    Update the title of a conversation.

    Args:
        conversation_id: Conversation identifier
        title: New title for the conversation
    """
    conversation = get_conversation(conversation_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    conversation["title"] = title
    save_conversation(conversation)


def update_message_feedback(
    conversation_id: str,
    message_index: int,
    feedback: int
):
    """
    Update user feedback for a specific message.

    Args:
        conversation_id: Conversation identifier
        message_index: Index of the message in the conversation
        feedback: Feedback value (-1: dislike, 0: neutral, 1: like)
    """
    if feedback not in [-1, 0, 1]:
        raise ValueError("Feedback must be -1, 0, or 1")

    conversation = get_conversation(conversation_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    if message_index < 0 or message_index >= len(conversation["messages"]):
        raise ValueError(f"Invalid message index: {message_index}")

    message = conversation["messages"][message_index]
    if message["role"] != "assistant":
        raise ValueError("Can only add feedback to assistant messages")

    message["user_feedback"] = feedback
    message["feedback_timestamp"] = datetime.utcnow().isoformat()

    save_conversation(conversation)


def add_conversation_tag(conversation_id: str, tag: str):
    """
    Add a tag to a conversation.

    Args:
        conversation_id: Conversation identifier
        tag: Tag to add
    """
    conversation = get_conversation(conversation_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    tags = conversation.get("tags", [])
    if tag not in tags:
        tags.append(tag)
        conversation["tags"] = tags
        save_conversation(conversation)


def remove_conversation_tag(conversation_id: str, tag: str):
    """
    Remove a tag from a conversation.

    Args:
        conversation_id: Conversation identifier
        tag: Tag to remove
    """
    conversation = get_conversation(conversation_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    tags = conversation.get("tags", [])
    if tag in tags:
        tags.remove(tag)
        conversation["tags"] = tags
        save_conversation(conversation)


def set_conversation_tags(conversation_id: str, tags: List[str]):
    """
    Set all tags for a conversation (replaces existing tags).

    Args:
        conversation_id: Conversation identifier
        tags: List of tags
    """
    conversation = get_conversation(conversation_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    conversation["tags"] = tags
    save_conversation(conversation)


def archive_conversation(conversation_id: str):
    """
    Archive a conversation.

    Args:
        conversation_id: Conversation identifier
    """
    conversation = get_conversation(conversation_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    conversation["archived"] = True
    save_conversation(conversation)


def unarchive_conversation(conversation_id: str):
    """
    Unarchive a conversation.

    Args:
        conversation_id: Conversation identifier
    """
    conversation = get_conversation(conversation_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    conversation["archived"] = False
    save_conversation(conversation)


def search_conversations(
    query: str = None,
    tags: List[str] = None,
    include_archived: bool = False
) -> List[Dict[str, Any]]:
    """
    Search conversations by text query and/or tags.

    Args:
        query: Text to search for in title and messages (case-insensitive)
        tags: List of tags - returns conversations that have ANY of these tags
        include_archived: If True, include archived conversations

    Returns:
        List of matching conversation metadata dicts
    """
    all_conversations = list_conversations(include_archived=include_archived)

    # Filter by tags if specified
    if tags:
        all_conversations = [
            conv for conv in all_conversations
            if any(tag in conv.get("tags", []) for tag in tags)
        ]

    # Filter by text query if specified
    if query and query.strip():
        query_lower = query.lower()
        filtered = []

        for conv_meta in all_conversations:
            # Load full conversation to search messages
            conv = get_conversation(conv_meta["id"])
            if conv is None:
                continue

            # Search in title
            if query_lower in conv.get("title", "").lower():
                filtered.append(conv_meta)
                continue

            # Search in messages
            found = False
            for message in conv.get("messages", []):
                if message.get("role") == "user":
                    # Search user message content
                    if query_lower in message.get("content", "").lower():
                        found = True
                        break
                elif message.get("role") == "assistant":
                    # Search assistant responses
                    stage1 = message.get("stage1", [])
                    for response in stage1:
                        if query_lower in response.get("response", "").lower():
                            found = True
                            break
                    if found:
                        break

                    stage3 = message.get("stage3", {})
                    if query_lower in stage3.get("response", "").lower():
                        found = True
                        break

                if found:
                    break

            if found:
                filtered.append(conv_meta)

        all_conversations = filtered

    return all_conversations
