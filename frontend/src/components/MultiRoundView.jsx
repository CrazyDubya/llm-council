import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import './MultiRoundView.css';

function MultiRoundView({ rounds, metadata }) {
  const [selectedRound, setSelectedRound] = useState(rounds.length - 1); // Default to last round
  const [selectedModel, setSelectedModel] = useState(null);

  const currentRound = rounds[selectedRound];
  const evolution = metadata?.evolution || {};

  return (
    <div className="multi-round-view">
      {/* Round selector */}
      <div className="round-selector">
        <h3>Round Evolution</h3>
        <div className="round-tabs">
          {rounds.map((round, index) => (
            <button
              key={index}
              className={`round-tab ${selectedRound === index ? 'active' : ''}`}
              onClick={() => setSelectedRound(index)}
            >
              Round {round.round_number}
              {index === rounds.length - 1 && <span className="final-badge">Final</span>}
            </button>
          ))}
        </div>
      </div>

      {/* Evolution metrics */}
      {evolution.evolution_detected && selectedRound > 0 && (
        <div className="evolution-metrics">
          <h4>🔄 Changes from Previous Round</h4>
          {evolution.rank_changes && evolution.rank_changes[selectedRound - 1] && (
            <div className="rank-changes">
              {evolution.rank_changes[selectedRound - 1].map((change, idx) => (
                <div key={idx} className={`rank-change ${change.improved ? 'improved' : 'declined'}`}>
                  <strong>{change.model}</strong>:
                  {change.improved ? ' ⬆️ ' : ' ⬇️ '}
                  {Math.abs(change.change)} positions
                </div>
              ))}
              {evolution.rank_changes[selectedRound - 1].length === 0 && (
                <p className="no-changes">No significant rank changes</p>
              )}
            </div>
          )}
        </div>
      )}

      {/* Round content */}
      <div className="round-content">
        <h3>Round {currentRound.round_number} Responses</h3>

        {/* Show top responses from previous round if this is a revision round */}
        {currentRound.top_from_previous && (
          <div className="previous-top-responses">
            <h4>📊 Top Responses Shown to Models (from previous round):</h4>
            {currentRound.top_from_previous.map((resp, idx) => (
              <div key={idx} className="top-response-preview">
                <strong>{resp.model}</strong> (Avg Rank: {resp.average_rank})
                <p className="response-snippet">
                  {resp.response.substring(0, 150)}...
                </p>
              </div>
            ))}
          </div>
        )}

        {/* Model response tabs */}
        <div className="model-tabs">
          {currentRound.responses.map((resp, idx) => (
            <button
              key={idx}
              className={`model-tab ${selectedModel === resp.model ? 'active' : ''}`}
              onClick={() => setSelectedModel(resp.model)}
            >
              {resp.model.split('/').pop()}
            </button>
          ))}
        </div>

        {/* Selected model response */}
        {selectedModel && (
          <div className="model-response">
            <div className="markdown-content">
              <ReactMarkdown>
                {currentRound.responses.find(r => r.model === selectedModel)?.response || ''}
              </ReactMarkdown>
            </div>
          </div>
        )}

        {/* Aggregate rankings for this round */}
        <div className="round-rankings">
          <h4>Aggregate Rankings (Round {currentRound.round_number})</h4>
          <table className="rankings-table">
            <thead>
              <tr>
                <th>Rank</th>
                <th>Model</th>
                <th>Average Position</th>
                <th>Votes</th>
              </tr>
            </thead>
            <tbody>
              {currentRound.aggregate_rankings.map((rank, idx) => (
                <tr key={idx} className={idx === 0 ? 'top-ranked' : ''}>
                  <td>{idx + 1}</td>
                  <td>{rank.model}</td>
                  <td>{rank.average_rank}</td>
                  <td>{rank.rankings_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default MultiRoundView;
