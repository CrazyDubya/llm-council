"""Abstract base class for ensemble strategies."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class EnsembleStrategy(ABC):
    """
    Abstract base class for LLM Council ensemble strategies.

    Each strategy implements a different approach to collecting, evaluating,
    and synthesizing responses from multiple models.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the strategy.

        Args:
            config: Optional configuration dictionary specific to this strategy
        """
        self.config = config or {}

    @abstractmethod
    async def execute(
        self,
        query: str,
        models: List[str],
        chairman: str
    ) -> Dict[str, Any]:
        """
        Execute the strategy and return structured results.

        Args:
            query: The user's question/prompt
            models: List of model identifiers to query
            chairman: Model identifier for final synthesis

        Returns:
            Dictionary containing:
            {
                'stage1': List or Dict containing initial responses,
                'stage2': List or Dict containing evaluations/rankings,
                'stage3': str or Dict containing final synthesis,
                'metadata': Dict with strategy-specific metadata
            }
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        Return the human-readable name of this strategy.

        Returns:
            Strategy name (e.g., "Simple Ranking", "Multi-Round Deliberation")
        """
        pass

    def get_description(self) -> str:
        """
        Return a description of what this strategy does.

        Returns:
            Strategy description for UI display
        """
        return ""

    def get_config_schema(self) -> Dict[str, Any]:
        """
        Return JSON schema for configuration options.

        This allows UIs to dynamically generate configuration forms.

        Returns:
            Dictionary describing configuration parameters
        """
        return {}
