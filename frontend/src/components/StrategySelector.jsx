import { useState, useEffect } from 'react';
import './StrategySelector.css';

function StrategySelector({ selectedStrategy, onStrategyChange }) {
  const [strategies, setStrategies] = useState({
    simple: { name: 'Simple Ranking', description: 'Default 3-stage ranking' }
  });

  // For now, we'll use a hardcoded list since we only have one strategy
  // In the future, we can fetch from /api/strategies
  const strategyOptions = [
    { id: 'simple', name: 'Simple Ranking' }
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
