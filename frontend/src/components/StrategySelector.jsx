import { useState, useEffect } from 'react';
import './StrategySelector.css';

function StrategySelector({ selectedStrategy, onStrategyChange }) {
  const [strategies, setStrategies] = useState({
    simple: { name: 'Simple Ranking', description: 'Default 3-stage ranking' },
    multi_round: { name: 'Multi-Round', description: 'Iterative deliberation with 2 rounds' },
    reasoning_aware: { name: 'Reasoning-Aware', description: 'Optimized for o1/DeepSeek models' },
    weighted_voting: { name: 'Weighted Voting', description: 'Performance-weighted model influence' },
    swot: { name: 'SWOT Analysis', description: 'Strengths, Weaknesses, Opportunities, Threats framework' },
    cost_benefit: { name: 'Cost-Benefit Analysis', description: 'Quantitative cost vs benefit scoring' },
    decision_matrix: { name: 'Decision Matrix', description: 'Multi-criteria weighted decision analysis' }
  });

  // Strategy options grouped by type
  const strategyOptions = [
    { id: 'simple', name: 'Simple Ranking', group: 'Deliberation' },
    { id: 'multi_round', name: 'Multi-Round', group: 'Deliberation' },
    { id: 'reasoning_aware', name: 'Reasoning-Aware', group: 'Deliberation' },
    { id: 'weighted_voting', name: 'Weighted Voting', group: 'Deliberation' },
    { id: 'swot', name: 'SWOT Analysis', group: 'Frameworks' },
    { id: 'cost_benefit', name: 'Cost-Benefit Analysis', group: 'Frameworks' },
    { id: 'decision_matrix', name: 'Decision Matrix', group: 'Frameworks' }
  ];

  // Group strategies by category
  const deliberationStrategies = strategyOptions.filter(s => s.group === 'Deliberation');
  const frameworkStrategies = strategyOptions.filter(s => s.group === 'Frameworks');

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
        <optgroup label="Deliberation Strategies">
          {deliberationStrategies.map(strategy => (
            <option key={strategy.id} value={strategy.id}>
              {strategy.name}
            </option>
          ))}
        </optgroup>
        <optgroup label="Decision Frameworks">
          {frameworkStrategies.map(strategy => (
            <option key={strategy.id} value={strategy.id}>
              {strategy.name}
            </option>
          ))}
        </optgroup>
      </select>
    </div>
  );
}

export default StrategySelector;
