"""Utility for looking up OpenRouter model pricing."""

from typing import Dict, Optional
import logging

import httpx

from .config import OPENROUTER_API_KEY

MODELS_ENDPOINT = "https://openrouter.ai/api/v1/models"


class PricingManager:
    """Caches prompt/completion prices for OpenRouter models."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self._prices: Dict[str, Dict[str, float]] = {}
        self.refresh_prices()

    def refresh_prices(self) -> None:
        """Fetch price metadata from OpenRouter (best-effort)."""
        headers = {}
        if OPENROUTER_API_KEY:
            headers["Authorization"] = f"Bearer {OPENROUTER_API_KEY}"

        try:
            resp = httpx.get(MODELS_ENDPOINT, headers=headers, timeout=30.0)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            self.logger.warning("Unable to refresh pricing info: %s", exc)
            return

        prices: Dict[str, Dict[str, float]] = {}
        for entry in data.get('data', []):
            pricing = entry.get('pricing') or {}
            try:
                prompt_price = float(pricing.get('prompt', 0) or 0)
                completion_price = float(pricing.get('completion', 0) or 0)
            except (TypeError, ValueError):
                continue
            prices[entry['id']] = {
                'prompt': prompt_price,
                'completion': completion_price,
            }

        if prices:
            self._prices = prices

    def estimate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> Optional[float]:
        """Return estimated USD cost for a call, if pricing is known."""
        pricing = self._prices.get(model)
        if not pricing:
            return None
        return (
            prompt_tokens * pricing['prompt']
            + completion_tokens * pricing['completion']
        )

    def get_price_table(self) -> Dict[str, Dict[str, float]]:
        return dict(self._prices)
