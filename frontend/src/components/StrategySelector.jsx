import './StrategySelector.css';

function StrategySelector({ selectedStrategy, onStrategyChange, strategies = [] }) {
  const fallbackOptions = [
    { id: 'simple', name: 'Simple Ranking' },
    { id: 'multi_round', name: 'Multi-Round (2 rounds)' },
    { id: 'reasoning_aware', name: 'Reasoning-Aware (o1/DeepSeek)' },
    { id: 'weighted_voting', name: 'Weighted Voting (Analytics)' }
  ];

  const strategyOptions = strategies.length ? strategies : fallbackOptions;

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
        {strategyOptions.map((strategy) => (
          <option key={strategy.id} value={strategy.id}>
            {strategy.name}
          </option>
        ))}
      </select>
    </div>
  );
}

export default StrategySelector;
