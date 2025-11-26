"""Configuration for the LLM Council."""

import os
from dotenv import load_dotenv

load_dotenv()

# OpenRouter API key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Council members - list of OpenRouter model identifiers
COUNCIL_MODELS = [
    "openai/gpt-5.1",
    "google/gemini-3-pro-preview",
    "anthropic/claude-sonnet-4.5",
    "x-ai/grok-4",
]

# Chairman model - synthesizes final response
CHAIRMAN_MODEL = "google/gemini-3-pro-preview"

COUNCIL_PRESETS = {
    "full": {
        "name": "Full Council",
        "description": "GPT/Gemini/Claude/Grok ensemble with Gemini chair",
        "models": COUNCIL_MODELS,
        "chairman": CHAIRMAN_MODEL,
    },
    "low_cost": {
        "name": "Budget Council",
        "description": "Haiku chair with Flash Lite and GPT-5 mini/nano",
        "models": [
            "anthropic/claude-haiku-4.5",
            "google/gemini-2.5-flash-lite",
            "openai/gpt-5-mini",
            "openai/gpt-5-nano",
        ],
        "chairman": "anthropic/claude-haiku-4.5",
    },
    "hybrid": {
        "name": "Hybrid Council",
        "description": "Gemini chair paired with smaller specialist models",
        "models": [
            "google/gemini-3-pro-preview",
            "anthropic/claude-haiku-4.5",
            "google/gemini-2.5-flash-lite",
            "openai/gpt-5-mini",
        ],
        "chairman": "google/gemini-3-pro-preview",
    },
}

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Data directory for conversation storage
DATA_DIR = "data/conversations"
