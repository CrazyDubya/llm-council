import { useState, useEffect } from 'react';
import './AnalyticsDashboard.css';

const API_BASE = 'http://localhost:8001';

export default function AnalyticsDashboard({ onClose }) {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/api/analytics/summary`);
      if (!response.ok) {
        throw new Error('Failed to fetch analytics');
      }
      const data = await response.json();
      setAnalytics(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="analytics-overlay">
        <div className="analytics-modal">
          <div className="loading">Loading analytics...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="analytics-overlay">
        <div className="analytics-modal">
          <div className="error">Error: {error}</div>
          <button onClick={onClose}>Close</button>
        </div>
      </div>
    );
  }

  if (!analytics) {
    return null;
  }

  // Calculate leaderboard from model_stats
  const leaderboard = Object.entries(analytics.model_stats || {})
    .map(([model, stats]) => ({
      model,
      ...stats
    }))
    .sort((a, b) => b.win_rate - a.win_rate)
    .slice(0, 10);

  return (
    <div className="analytics-overlay" onClick={onClose}>
      <div className="analytics-modal" onClick={(e) => e.stopPropagation()}>
        <div className="analytics-header">
          <h2>📊 Council Analytics</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="analytics-content">
          {/* Summary Stats */}
          <div className="analytics-summary">
            <div className="stat-card">
              <div className="stat-value">{analytics.total_conversations}</div>
              <div className="stat-label">Conversations</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{analytics.total_queries}</div>
              <div className="stat-label">Queries Processed</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">
                {Object.keys(analytics.strategy_stats || {}).length}
              </div>
              <div className="stat-label">Strategies</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">
                {Object.keys(analytics.model_stats || {}).length}
              </div>
              <div className="stat-label">Models</div>
            </div>
          </div>

          {/* Model Leaderboard */}
          <div className="analytics-section">
            <h3>🏆 Model Leaderboard (by Win Rate)</h3>
            <div className="leaderboard">
              <table>
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Model</th>
                    <th>Win Rate</th>
                    <th>Wins</th>
                    <th>Evaluations</th>
                    <th>Avg Rank</th>
                  </tr>
                </thead>
                <tbody>
                  {leaderboard.map((item, idx) => (
                    <tr key={item.model} className={idx === 0 ? 'top-model' : ''}>
                      <td className="rank-cell">
                        {idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : idx + 1}
                      </td>
                      <td className="model-cell">{item.model}</td>
                      <td>{(item.win_rate * 100).toFixed(1)}%</td>
                      <td>{item.wins}</td>
                      <td>{item.total_evaluations}</td>
                      <td>{item.avg_rank?.toFixed(2) || 'N/A'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Strategy Stats */}
          <div className="analytics-section">
            <h3>📈 Strategy Performance</h3>
            <div className="strategy-stats">
              {Object.entries(analytics.strategy_stats || {}).map(([strategy, stats]) => (
                <div key={strategy} className="strategy-card">
                  <div className="strategy-name">{strategy}</div>
                  <div className="strategy-metrics">
                    <div className="metric">
                      <span className="metric-label">Uses:</span>
                      <span className="metric-value">{stats.count}</span>
                    </div>
                    {stats.avg_feedback !== null && (
                      <div className="metric">
                        <span className="metric-label">Avg Feedback:</span>
                        <span className={`metric-value ${stats.avg_feedback > 0 ? 'positive' : stats.avg_feedback < 0 ? 'negative' : ''}`}>
                          {stats.avg_feedback > 0 ? '+' : ''}{stats.avg_feedback.toFixed(2)}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Last Updated */}
          <div className="analytics-footer">
            <span className="last-updated">
              Last updated: {new Date(analytics.last_updated).toLocaleString()}
            </span>
            <button className="refresh-btn" onClick={fetchAnalytics}>
              🔄 Refresh
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
