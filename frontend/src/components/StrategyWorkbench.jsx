import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { api } from '../api';
import './StrategyWorkbench.css';

export default function StrategyWorkbench({ isOpen, onClose, strategies, selectedCouncil }) {
  const [question, setQuestion] = useState('');
  const [selected, setSelected] = useState(() => new Set());
  const [results, setResults] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen) {
      setError('');
    }
  }, [isOpen]);

  if (!isOpen) {
    return null;
  }

  const toggleStrategy = (id) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleRun = async () => {
    if (!question.trim() || selected.size === 0) {
      setError('Provide a question and select at least one strategy.');
      return;
    }
    setIsRunning(true);
    setError('');
    try {
      const resp = await api.compareStrategies(question, Array.from(selected), {
        council: selectedCouncil,
      });
      setResults(resp.comparisons || []);
    } catch (err) {
      setError(err.message || 'Failed to run strategies');
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="workbench-overlay">
      <div className="workbench-panel">
        <div className="workbench-header">
          <h2>Strategy Workbench</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        <p className="workbench-subtitle">Run multiple strategies on the same prompt and compare their outputs and costs side-by-side.</p>
        <p className="workbench-council">Using council preset: <strong>{selectedCouncil || 'full'}</strong></p>
        <textarea
          className="workbench-input"
          placeholder="Enter your question for the council..."
          rows={5}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={isRunning}
        />
        <div className="workbench-strategies">
          <div className="strategy-label">Strategies</div>
          <div className="strategy-grid">
            {(strategies || []).map((strategy) => (
              <label key={strategy.id} className={`strategy-option ${selected.has(strategy.id) ? 'selected' : ''}`}>
                <input
                  type="checkbox"
                  value={strategy.id}
                  checked={selected.has(strategy.id)}
                  onChange={() => toggleStrategy(strategy.id)}
                  disabled={isRunning}
                />
                <div>
                  <div className="strategy-name">{strategy.name}</div>
                  <div className="strategy-description">{strategy.description}</div>
                </div>
              </label>
            ))}
          </div>
        </div>
        {error && <div className="workbench-error">{error}</div>}
        <button
          className="run-btn"
          onClick={handleRun}
          disabled={isRunning || !question.trim() || selected.size === 0}
        >
          {isRunning ? 'Running...' : 'Run Selected Strategies'}
        </button>

        <div className="workbench-results">
          {results.map((result) => (
            <div key={result.strategy} className="result-card">
              <div className="result-header">
                <div>
                  <div className="result-strategy">{result.strategy}</div>
                  {!result.success && <span className="result-error">Failed: {result.error}</span>}
                  {result.result?.metadata?.council && (
                    <div className="result-council">
                      Council: {result.result.metadata.council.name || result.result.metadata.council.id}
                    </div>
                  )}
                </div>
                {result.result?.metadata?.api_usage && (
                  <div className="result-cost">
                    Cost: ${result.result.metadata.api_usage.total_cost?.toFixed(3) ?? 'n/a'}
                  </div>
                )}
              </div>
              {result.success && (
                <div className="result-body">
                  <div className="result-stages">
                    <div className="result-stage">
                      <strong>Stage 1</strong>
                      <div className="result-scroll">
                        {result.result.stage1 && Array.isArray(result.result.stage1)
                          ? result.result.stage1.map((entry) => (
                              <div key={entry.model} className="result-entry">
                                <span className="entry-model">{entry.model}</span>
                                <ReactMarkdown>{entry.response}</ReactMarkdown>
                              </div>
                            ))
                          : <ReactMarkdown>{JSON.stringify(result.result.stage1, null, 2)}</ReactMarkdown>}
                      </div>
                    </div>
                    <div className="result-stage">
                      <strong>Stage 2</strong>
                      <div className="result-scroll">
                        <ReactMarkdown>{JSON.stringify(result.result.stage2, null, 2)}</ReactMarkdown>
                      </div>
                    </div>
                  </div>
                  <div className="result-stage">
                    <strong>Stage 3</strong>
                    <div className="result-scroll">
                      <ReactMarkdown>{result.result.stage3?.response || 'No final answer'}</ReactMarkdown>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
