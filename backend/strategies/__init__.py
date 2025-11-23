"""Ensemble strategy registry and factory."""

from typing import Dict
from .base import EnsembleStrategy
from .simple_ranking import SimpleRankingStrategy
from .multi_round import MultiRoundStrategy
from .reasoning_aware import ReasoningAwareStrategy
from .weighted_voting import WeightedVotingStrategy


# Registry of available strategies
_STRATEGIES: Dict[str, type] = {
    'simple': SimpleRankingStrategy,
    'multi_round': MultiRoundStrategy,
    'reasoning_aware': ReasoningAwareStrategy,
    'weighted_voting': WeightedVotingStrategy,
}


def get_strategy(name: str, config: Dict = None) -> EnsembleStrategy:
    """
    Get a strategy instance by name.

    Args:
        name: Strategy identifier (e.g., 'simple', 'multi_round')
        config: Optional configuration dictionary for the strategy

    Returns:
        Instance of the requested strategy

    Raises:
        ValueError: If strategy name is not recognized
    """
    if name not in _STRATEGIES:
        available = ', '.join(_STRATEGIES.keys())
        raise ValueError(f"Unknown strategy '{name}'. Available: {available}")

    strategy_class = _STRATEGIES[name]
    return strategy_class(config=config)


def list_strategies() -> Dict[str, str]:
    """
    List all available strategies.

    Returns:
        Dictionary mapping strategy names to descriptions
    """
    strategies = {}
    for name, strategy_class in _STRATEGIES.items():
        # Instantiate temporarily to get description
        instance = strategy_class()
        strategies[name] = {
            'name': instance.get_name(),
            'description': instance.get_description()
        }
    return strategies


def register_strategy(name: str, strategy_class: type):
    """
    Register a new strategy.

    Args:
        name: Strategy identifier
        strategy_class: Class that extends EnsembleStrategy
    """
    if not issubclass(strategy_class, EnsembleStrategy):
        raise TypeError(f"{strategy_class} must extend EnsembleStrategy")

    _STRATEGIES[name] = strategy_class


__all__ = [
    'EnsembleStrategy',
    'SimpleRankingStrategy',
    'MultiRoundStrategy',
    'ReasoningAwareStrategy',
    'WeightedVotingStrategy',
    'get_strategy',
    'list_strategies',
    'register_strategy'
]
