"""Model management utilities for dynamic council configuration."""

import httpx
from typing import List, Dict, Any, Optional
from .config import OPENROUTER_API_KEY


# Cache for model data to avoid excessive API calls
_model_cache = None
_cache_timestamp = None


async def fetch_available_models() -> List[Dict[str, Any]]:
    """
    Fetch available models from OpenRouter API.

    Returns:
        List of model dictionaries with metadata
    """
    global _model_cache, _cache_timestamp

    # Return cached data if recent (within 1 hour)
    import time
    if _model_cache and _cache_timestamp:
        if time.time() - _cache_timestamp < 3600:
            return _model_cache

    # Fetch from OpenRouter API
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://openrouter.ai/api/v1/models",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}"
                },
                timeout=10.0
            )

            if response.status_code == 200:
                data = response.json()
                models = data.get('data', [])

                # Process and enhance model data
                processed_models = []
                for model in models:
                    processed_models.append({
                        'id': model.get('id'),
                        'name': model.get('name', model.get('id')),
                        'description': model.get('description', ''),
                        'context_length': model.get('context_length', 0),
                        'pricing': model.get('pricing', {}),
                        'top_provider': model.get('top_provider', {}),
                        'architecture': model.get('architecture', {}),
                        'created': model.get('created'),
                        'per_request_limits': model.get('per_request_limits')
                    })

                # Cache the results
                _model_cache = processed_models
                _cache_timestamp = time.time()

                return processed_models

            else:
                # Fallback to default models if API fails
                return get_default_models()

        except Exception as e:
            print(f"Failed to fetch models from OpenRouter: {e}")
            return get_default_models()


def get_default_models() -> List[Dict[str, Any]]:
    """
    Get default model list as fallback.

    Returns:
        List of default model configurations
    """
    return [
        {
            'id': 'openai/gpt-4-turbo',
            'name': 'GPT-4 Turbo',
            'description': 'Most capable GPT-4 model',
            'context_length': 128000,
            'pricing': {'prompt': '0.00001', 'completion': '0.00003'},
            'category': 'flagship'
        },
        {
            'id': 'openai/gpt-3.5-turbo',
            'name': 'GPT-3.5 Turbo',
            'description': 'Fast and economical model',
            'context_length': 16385,
            'pricing': {'prompt': '0.0000005', 'completion': '0.0000015'},
            'category': 'budget'
        },
        {
            'id': 'anthropic/claude-3.5-sonnet',
            'name': 'Claude 3.5 Sonnet',
            'description': 'Balanced intelligence and speed',
            'context_length': 200000,
            'pricing': {'prompt': '0.000003', 'completion': '0.000015'},
            'category': 'flagship'
        },
        {
            'id': 'google/gemini-pro-1.5',
            'name': 'Gemini 1.5 Pro',
            'description': 'Long context, multimodal',
            'context_length': 1000000,
            'pricing': {'prompt': '0.0000035', 'completion': '0.0000105'},
            'category': 'flagship'
        },
        {
            'id': 'meta-llama/llama-3.1-70b-instruct',
            'name': 'Llama 3.1 70B',
            'description': 'Open source, high performance',
            'context_length': 131072,
            'pricing': {'prompt': '0.00000052', 'completion': '0.00000075'},
            'category': 'open_source'
        },
        {
            'id': 'mistralai/mixtral-8x7b-instruct',
            'name': 'Mixtral 8x7B',
            'description': 'Mixture of experts, efficient',
            'context_length': 32768,
            'pricing': {'prompt': '0.00000027', 'completion': '0.00000027'},
            'category': 'open_source'
        }
    ]


def filter_models(
    models: List[Dict[str, Any]],
    category: Optional[str] = None,
    min_context: Optional[int] = None,
    max_cost: Optional[float] = None,
    search: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Filter models based on criteria.

    Args:
        models: List of models to filter
        category: Filter by category (e.g., 'flagship', 'budget', 'open_source')
        min_context: Minimum context length required
        max_cost: Maximum cost per 1M tokens (prompt)
        search: Search term for name/description

    Returns:
        Filtered list of models
    """
    filtered = models

    if category:
        filtered = [m for m in filtered if m.get('category') == category]

    if min_context:
        filtered = [m for m in filtered if m.get('context_length', 0) >= min_context]

    if max_cost and max_cost > 0:
        filtered = [
            m for m in filtered
            if float(m.get('pricing', {}).get('prompt', 0)) <= max_cost
        ]

    if search:
        search_lower = search.lower()
        filtered = [
            m for m in filtered
            if search_lower in m.get('name', '').lower() or
               search_lower in m.get('description', '').lower() or
               search_lower in m.get('id', '').lower()
        ]

    return filtered


def estimate_cost(
    model_ids: List[str],
    avg_prompt_tokens: int = 1000,
    avg_completion_tokens: int = 500,
    num_calls: int = 1
) -> Dict[str, Any]:
    """
    Estimate cost for using specific models.

    Args:
        model_ids: List of model IDs
        avg_prompt_tokens: Average prompt length in tokens
        avg_completion_tokens: Average completion length in tokens
        num_calls: Number of API calls

    Returns:
        Cost estimate breakdown
    """
    models = get_default_models()
    model_map = {m['id']: m for m in models}

    total_cost = 0.0
    breakdown = []

    for model_id in model_ids:
        model = model_map.get(model_id)
        if not model:
            continue

        pricing = model.get('pricing', {})
        prompt_cost_per_token = float(pricing.get('prompt', 0))
        completion_cost_per_token = float(pricing.get('completion', 0))

        model_prompt_cost = prompt_cost_per_token * avg_prompt_tokens * num_calls
        model_completion_cost = completion_cost_per_token * avg_completion_tokens * num_calls
        model_total = model_prompt_cost + model_completion_cost

        total_cost += model_total

        breakdown.append({
            'model_id': model_id,
            'model_name': model['name'],
            'prompt_cost': model_prompt_cost,
            'completion_cost': model_completion_cost,
            'total_cost': model_total
        })

    return {
        'total_cost': total_cost,
        'breakdown': breakdown,
        'assumptions': {
            'avg_prompt_tokens': avg_prompt_tokens,
            'avg_completion_tokens': avg_completion_tokens,
            'num_calls': num_calls
        }
    }


def recommend_council(
    budget: Optional[float] = None,
    diversity: bool = True,
    include_reasoning: bool = False
) -> List[str]:
    """
    Recommend a balanced council composition.

    Args:
        budget: Optional budget constraint (cost per query)
        diversity: Whether to prioritize model diversity
        include_reasoning: Whether to include reasoning models (o1, DeepSeek-R1)

    Returns:
        List of recommended model IDs
    """
    models = get_default_models()

    if budget:
        # Filter by budget
        affordable_models = []
        for model in models:
            pricing = model.get('pricing', {})
            prompt_cost = float(pricing.get('prompt', 0))
            # Rough estimate: assume 1000 prompt + 500 completion tokens
            est_cost = (prompt_cost * 1000) + (float(pricing.get('completion', 0)) * 500)
            if est_cost <= budget:
                affordable_models.append(model)
        models = affordable_models

    if not models:
        return []

    # If diversity is prioritized, pick models from different providers
    if diversity:
        council = []
        providers_used = set()

        for model in models:
            provider = model['id'].split('/')[0]

            if provider not in providers_used or len(council) < 3:
                council.append(model['id'])
                providers_used.add(provider)

                if len(council) >= 4:  # Default council size
                    break

        return council

    # Otherwise, just pick top performers
    # Prioritize flagship models
    flagship = [m for m in models if m.get('category') == 'flagship']
    if len(flagship) >= 4:
        return [m['id'] for m in flagship[:4]]

    # Mix flagship and others
    council_models = flagship[:2] + models[:2]
    return [m['id'] for m in council_models]


def get_model_info(model_id: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a specific model.

    Args:
        model_id: The model ID

    Returns:
        Model info dictionary or None if not found
    """
    models = get_default_models()
    for model in models:
        if model['id'] == model_id:
            return model
    return None
