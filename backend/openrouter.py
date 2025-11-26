"""OpenRouter API client for making LLM requests with usage logging."""

from contextvars import ContextVar
from typing import List, Dict, Any, Optional, Callable

import httpx

from .config import OPENROUTER_API_KEY, OPENROUTER_API_URL

# Context-local store of API call metadata so concurrent requests do not conflict
_call_log: ContextVar[Optional[List[Dict[str, Any]]]] = ContextVar(
    "openrouter_call_log",
    default=None,
)


def _get_log() -> List[Dict[str, Any]]:
    log = _call_log.get()
    if log is None:
        log = []
        _call_log.set(log)
    return log


def reset_call_log() -> None:
    """Clear the current API call log (one per request context)."""
    _call_log.set([])


def get_call_log() -> List[Dict[str, Any]]:
    """Return a shallow copy of the current API call log."""
    log = _call_log.get()
    if log is None:
        return []
    return list(log)


def summarize_call_log(
    price_lookup: Optional[Callable[[str, int, int], Optional[float]]] = None
) -> Dict[str, Any]:
    """Summarize tokens (and optional cost) for the latest log."""
    log = get_call_log()
    summary = []
    total_prompt = 0
    total_completion = 0
    total_cost = 0.0

    for entry in log:
        usage = entry.get('usage') or {}
        prompt_tokens = usage.get('prompt_tokens') or 0
        completion_tokens = usage.get('completion_tokens') or 0
        total_prompt += prompt_tokens
        total_completion += completion_tokens

        estimated_cost = None
        if price_lookup is not None:
            estimated_cost = price_lookup(entry['model'], prompt_tokens, completion_tokens)
            if estimated_cost is not None:
                total_cost += estimated_cost

        summary.append({
            'model': entry['model'],
            'context': entry.get('context') or {},
            'response_id': entry.get('response_id'),
            'usage': {
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
            },
            'cost': estimated_cost,
        })

    return {
        'calls': summary,
        'total_prompt_tokens': total_prompt,
        'total_completion_tokens': total_completion,
        'total_cost': total_cost if price_lookup is not None else None,
    }


async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0,
    call_context: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Query a single model via OpenRouter API.

    Args:
        model: OpenRouter model identifier (e.g., "openai/gpt-4o")
        messages: List of message dicts with 'role' and 'content'
        timeout: Request timeout in seconds
        call_context: Optional metadata describing why the call was made

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
            usage = data.get('usage')

            log_entry = {
                'model': model,
                'messages': messages,
                'response_id': data.get('id'),
                'created': data.get('created'),
                'usage': usage,
            }
            if call_context:
                log_entry['context'] = dict(call_context)

            _get_log().append(log_entry)

            return {
                'content': message.get('content'),
                'reasoning_details': message.get('reasoning_details'),
                'usage': usage,
            }

    except Exception as e:
        print(f"Error querying model {model}: {e}")
        return None


async def query_models_parallel(
    models: List[str],
    messages: List[Dict[str, str]],
    call_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Query multiple models in parallel.

    Args:
        models: List of OpenRouter model identifiers
        messages: List of message dicts to send to each model
        call_context: Optional metadata describing why the call was made

    Returns:
        Dict mapping model identifier to response dict (or None if failed)
    """
    import asyncio

    ctx = dict(call_context) if call_context else None

    async def _run(model_name: str):
        return await query_model(
            model_name,
            messages,
            call_context=ctx
        )

    tasks = [_run(model) for model in models]
    responses = await asyncio.gather(*tasks)
    return {model: response for model, response in zip(models, responses)}
