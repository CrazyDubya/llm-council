"""Configuration for the LLM Council."""

import os
import json
from dotenv import load_dotenv

load_dotenv()

# OpenRouter API key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Council members - list of OpenRouter model identifiers
# Can be overridden via COUNCIL_MODELS env var as JSON array
_DEFAULT_COUNCIL_MODELS = [
    "openai/gpt-4o",
    "google/gemini-2.0-flash-exp",
    "anthropic/claude-3.5-sonnet",
    "x-ai/grok-2-1212",
]

def _parse_models_env(env_var: str, default: list) -> list:
    """Parse models from environment variable (JSON array) or use default."""
    env_value = os.getenv(env_var)
    if env_value:
        try:
            models = json.loads(env_value)
            if isinstance(models, list) and all(isinstance(m, str) for m in models):
                return models
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON in {env_var}, using defaults")
    return default

COUNCIL_MODELS = _parse_models_env("COUNCIL_MODELS", _DEFAULT_COUNCIL_MODELS)

# Chairman model - synthesizes final response
CHAIRMAN_MODEL = os.getenv("CHAIRMAN_MODEL", "google/gemini-2.0-flash-exp")

# OpenRouter API endpoint
OPENROUTER_API_URL = os.getenv(
    "OPENROUTER_API_URL",
    "https://openrouter.ai/api/v1/chat/completions"
)

# Data directory for conversation storage
DATA_DIR = os.getenv("DATA_DIR", "data/conversations")

# API settings
API_TIMEOUT = float(os.getenv("API_TIMEOUT", "120"))
API_MAX_RETRIES = int(os.getenv("API_MAX_RETRIES", "3"))

# Server settings
SERVER_PORT = int(os.getenv("SERVER_PORT", "8001"))
CORS_ORIGINS = json.loads(os.getenv(
    "CORS_ORIGINS",
    '["http://localhost:5173", "http://localhost:3000"]'
))
