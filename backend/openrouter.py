"""OpenRouter API client for making LLM requests."""

import httpx
from typing import List, Dict, Any, Optional, AsyncIterator
from .config import OPENROUTER_API_KEY, OPENROUTER_API_URL
from .streaming import stream_model_response, collect_stream


async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0
) -> Optional[Dict[str, Any]]:
    """
    Query a single model via OpenRouter API.

    Args:
        model: OpenRouter model identifier (e.g., "openai/gpt-4o")
        messages: List of message dicts with 'role' and 'content'
        timeout: Request timeout in seconds

    Returns:
        Response dict with 'content' and optional 'reasoning_details', or None if failed
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            message = data['choices'][0]['message']

            return {
                'content': message.get('content'),
                'reasoning_details': message.get('reasoning_details')
            }

    except Exception as e:
        print(f"Error querying model {model}: {e}")
        return None


async def query_models_parallel(
    models: List[str],
    messages: List[Dict[str, str]]
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Query multiple models in parallel.

    Args:
        models: List of OpenRouter model identifiers
        messages: List of message dicts to send to each model

    Returns:
        Dict mapping model identifier to response dict (or None if failed)
    """
    import asyncio

    # Create tasks for all models
    tasks = [query_model(model, messages) for model in models]

    # Wait for all to complete
    responses = await asyncio.gather(*tasks)

    # Map models to their responses
    return {model: response for model, response in zip(models, responses)}


async def query_model_streaming(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 300.0
) -> AsyncIterator[str]:
    """
    Query a single model via OpenRouter API with streaming.

    Args:
        model: OpenRouter model identifier (e.g., "openai/gpt-4o")
        messages: List of message dicts with 'role' and 'content'
        timeout: Request timeout in seconds

    Yields:
        Individual tokens as they arrive

    Raises:
        httpx.HTTPError: If the request fails
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        async for token in stream_model_response(client, OPENROUTER_API_URL, headers, payload, timeout):
            yield token


async def query_model_with_streaming(
    model: str,
    messages: List[Dict[str, str]],
    stream_callback: Optional[callable] = None,
    timeout: float = 300.0
) -> Optional[Dict[str, Any]]:
    """
    Query a model with optional streaming callback, returns complete response.

    This function allows streaming tokens via callback while still returning
    the complete response at the end (for backward compatibility).

    Args:
        model: OpenRouter model identifier
        messages: List of message dicts with 'role' and 'content'
        stream_callback: Optional async function to call with each token
        timeout: Request timeout in seconds

    Returns:
        Response dict with 'content' and optional 'reasoning_details', or None if failed
    """
    try:
        stream = query_model_streaming(model, messages, timeout)

        # Collect tokens
        tokens = []
        async for token in stream:
            tokens.append(token)
            if stream_callback:
                try:
                    await stream_callback(token, model)
                except Exception as e:
                    print(f"Error in stream callback: {e}")

        content = ''.join(tokens)

        return {
            'content': content,
            'reasoning_details': None  # Streaming responses don't include reasoning_details
        }

    except Exception as e:
        print(f"Error querying model {model} with streaming: {e}")
        return None
