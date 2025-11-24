"""Token streaming logic for LLM responses."""

import asyncio
import json
import logging
from typing import AsyncIterator, Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)


async def stream_tokens_from_response(
    response: httpx.Response
) -> AsyncIterator[str]:
    """
    Stream tokens from an SSE (Server-Sent Events) response.

    OpenRouter uses SSE format for streaming responses.

    Args:
        response: The HTTP response object with streaming content

    Yields:
        Individual tokens as they arrive
    """
    buffer = ""

    async for chunk in response.aiter_bytes():
        try:
            # Decode the chunk
            text = chunk.decode('utf-8')
            buffer += text

            # Process complete lines
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                line = line.strip()

                # Skip empty lines
                if not line:
                    continue

                # SSE format: "data: {json}"
                if line.startswith('data: '):
                    data_str = line[6:]  # Remove "data: " prefix

                    # Check for stream end signal
                    if data_str == '[DONE]':
                        logger.debug("Stream completed")
                        return

                    try:
                        data = json.loads(data_str)

                        # Extract token from OpenRouter response format
                        # OpenRouter follows OpenAI's streaming format
                        if 'choices' in data and len(data['choices']) > 0:
                            choice = data['choices'][0]
                            if 'delta' in choice:
                                delta = choice['delta']
                                if 'content' in delta:
                                    token = delta['content']
                                    if token:
                                        yield token

                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse SSE data: {data_str[:100]}... Error: {e}")
                        continue

        except Exception as e:
            logger.error(f"Error in stream processing: {e}")
            break


async def stream_model_response(
    client: httpx.AsyncClient,
    url: str,
    headers: Dict[str, str],
    payload: Dict[str, Any],
    timeout: float = 300.0
) -> AsyncIterator[str]:
    """
    Stream a model's response token by token.

    Args:
        client: Async HTTP client
        url: API endpoint URL
        headers: Request headers
        payload: Request payload
        timeout: Request timeout in seconds

    Yields:
        Individual tokens as they arrive

    Raises:
        httpx.HTTPError: If the request fails
    """
    try:
        # Enable streaming in the payload
        payload['stream'] = True

        async with client.stream(
            'POST',
            url,
            headers=headers,
            json=payload,
            timeout=timeout
        ) as response:
            response.raise_for_status()

            async for token in stream_tokens_from_response(response):
                yield token

    except httpx.HTTPError as e:
        logger.error(f"HTTP error during streaming: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during streaming: {e}")
        raise


class StreamAccumulator:
    """Helper class to accumulate tokens from a stream."""

    def __init__(self):
        """Initialize the accumulator."""
        self.tokens: list[str] = []
        self.full_text: str = ""

    def add_token(self, token: str):
        """
        Add a token to the accumulator.

        Args:
            token: Token to add
        """
        self.tokens.append(token)
        self.full_text += token

    def get_text(self) -> str:
        """
        Get the accumulated text.

        Returns:
            Complete accumulated text
        """
        return self.full_text

    def get_tokens(self) -> list[str]:
        """
        Get the list of tokens.

        Returns:
            List of all tokens
        """
        return self.tokens

    def clear(self):
        """Clear the accumulator."""
        self.tokens = []
        self.full_text = ""


async def collect_stream(stream: AsyncIterator[str]) -> str:
    """
    Collect all tokens from a stream into a single string.

    Useful for cases where we want to stream to clients but also
    need the complete response for processing.

    Args:
        stream: Async iterator of tokens

    Returns:
        Complete response text
    """
    accumulator = StreamAccumulator()

    async for token in stream:
        accumulator.add_token(token)

    return accumulator.get_text()


async def stream_with_callback(
    stream: AsyncIterator[str],
    callback: callable
) -> str:
    """
    Stream tokens while calling a callback for each token.

    Args:
        stream: Async iterator of tokens
        callback: Async function to call with each token

    Returns:
        Complete response text
    """
    accumulator = StreamAccumulator()

    async for token in stream:
        accumulator.add_token(token)
        try:
            await callback(token)
        except Exception as e:
            logger.error(f"Error in stream callback: {e}")

    return accumulator.get_text()


class TokenRateLimiter:
    """Rate limiter for token streaming to prevent overwhelming clients."""

    def __init__(self, tokens_per_second: int = 50):
        """
        Initialize the rate limiter.

        Args:
            tokens_per_second: Maximum tokens to send per second
        """
        self.tokens_per_second = tokens_per_second
        self.last_send_time = asyncio.get_event_loop().time()

    async def wait_if_needed(self):
        """Wait if we're sending tokens too fast."""
        now = asyncio.get_event_loop().time()
        elapsed = now - self.last_send_time
        min_interval = 1.0 / self.tokens_per_second

        if elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)

        self.last_send_time = asyncio.get_event_loop().time()


async def stream_with_rate_limit(
    stream: AsyncIterator[str],
    tokens_per_second: int = 50
) -> AsyncIterator[str]:
    """
    Stream tokens with rate limiting.

    Args:
        stream: Async iterator of tokens
        tokens_per_second: Maximum tokens to send per second

    Yields:
        Tokens at a controlled rate
    """
    limiter = TokenRateLimiter(tokens_per_second)

    async for token in stream:
        await limiter.wait_if_needed()
        yield token
