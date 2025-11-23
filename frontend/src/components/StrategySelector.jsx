import { useState, useEffect } from 'react';
import './StrategySelector.css';

function StrategySelector({ selectedStrategy, onStrategyChange }) {
  const [strategies, setStrategies] = useState({
    simple: { name: 'Simple Ranking', description: 'Default 3-stage ranking' },
    multi_round: { name: 'Multi-Round', description: 'Iterative deliberation with 2 rounds' },
    reasoning_aware: { name: 'Reasoning-Aware', description: 'Optimized for o1/DeepSeek models' },
    weighted_voting: { name: 'Weighted Voting', description: 'Performance-weighted model influence' }
  });

  // Strategy options (can be fetched from /api/strategies in the future)
  const strategyOptions = [
    { id: 'simple', name: 'Simple Ranking' },
    { id: 'multi_round', name: 'Multi-Round (2 rounds)' },
    { id: 'reasoning_aware', name: 'Reasoning-Aware (o1/DeepSeek)' },
    { id: 'weighted_voting', name: 'Weighted Voting (Analytics)' }
  ];

  return (
    <div className="strategy-selector">
      <label htmlFor="strategy-select" className="strategy-label">
        Strategy:
      </label>
      <select
        id="strategy-select"
        value={selectedStrategy}
        onChange={(e) => onStrategyChange(e.target.value)}
        className="strategy-dropdown"
      >
        {strategyOptions.map(strategy => (
          <option key={strategy.id} value={strategy.id}>
            {strategy.name}
          </option>
        ))}
      </select>
    </div>
  );
}

export default StrategySelector;
