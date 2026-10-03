import { useState, useEffect } from 'react';
import { api } from '../api';
import ReactMarkdown from 'react-markdown';
import './TimeTravelComparison.css';

export default function TimeTravelComparison({ onClose }) {
  const [benchmarks, setBenchmarks] = useState([]);
  const [selectedBenchmark, setSelectedBenchmark] = useState(null);
  const [selectedRerun, setSelectedRerun] = useState(null);
  const [loading, setLoading] = useState(true);
  const [rerunning, setRerunning] = useState(false);

  useEffect(() => {
    loadBenchmarks();
  }, []);

  const loadBenchmarks = async () => {
    try {
      const data = await api.listBenchmarks();
      setBenchmarks(data);
    } catch (error) {
      console.error('Failed to load benchmarks:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadBenchmarkDetails = async (snapshotId) => {
    try {
      const data = await api.getBenchmark(snapshotId);
      setSelectedBenchmark(data);
      setSelectedRerun(null);
    } catch (error) {
      console.error('Failed to load benchmark details:', error);
    }
  };

  const handleRerun = async () => {
    if (!selectedBenchmark) return;

    setRerunning(true);
    try {
      // Use the same models/chairman from original
      const originalModels = selectedBenchmark.original_response.stage1.map(r => r.model);
      const originalChairman = selectedBenchmark.original_response.stage3.model;

      const result = await api.rerunBenchmark(
        selectedBenchmark.snapshot_id,
        originalModels,
        originalChairman,
        'simple'
      );

      // Reload benchmark to get updated reruns
      await loadBenchmarkDetails(selectedBenchmark.snapshot_id);
    } catch (error) {
      console.error('Failed to rerun benchmark:', error);
    } finally {
      setRerunning(false);
    }
  };

  const formatDate = (isoDate) => {
    return new Date(isoDate).toLocaleString();
  };

  const renderDriftMetrics = (metrics) => {
    if (!metrics) return null;

    return (
      <div className="drift-metrics">
        <h4>Drift Analysis</h4>

        {metrics.final_answer_similarity !== undefined && (
          <div className="metric-item">
            <span className="metric-label">Final Answer Similarity:</span>
            <div className="similarity-bar">
              <div
                className="similarity-fill"
                style={{
                  width: `${metrics.final_answer_similarity * 100}%`,
                  backgroundColor: getSimilarityColor(metrics.final_answer_similarity)
                }}
              />
              <span className="similarity-value">
                {(metrics.final_answer_similarity * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        )}

        {metrics.average_model_similarity !== undefined && (
          <div className="metric-item">
            <span className="metric-label">Avg Model Similarity:</span>
            <div className="similarity-bar">
              <div
                className="similarity-fill"
                style={{
                  width: `${metrics.average_model_similarity * 100}%`,
                  backgroundColor: getSimilarityColor(metrics.average_model_similarity)
                }}
              />
              <span className="similarity-value">
                {(metrics.average_model_similarity * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        )}

        {metrics.average_rank_change !== undefined && (
          <div className="metric-item">
            <span className="metric-label">Avg Rank Change:</span>
            <span className="metric-value">±{metrics.average_rank_change.toFixed(2)} positions</span>
          </div>
        )}

        {metrics.response_count_change !== undefined && metrics.response_count_change !== 0 && (
          <div className="metric-item">
            <span className="metric-label">Response Count Change:</span>
            <span className="metric-value">
              {metrics.response_count_change > 0 ? '+' : ''}{metrics.response_count_change}
            </span>
          </div>
        )}

        {metrics.model_similarities && metrics.model_similarities.length > 0 && (
          <div className="model-similarities">
            <h5>Per-Model Drift</h5>
            {metrics.model_similarities.map((ms, idx) => (
              <div key={idx} className="model-similarity-item">
                <span className="model-name-small">{ms.model.split('/')[1] || ms.model}</span>
                <div className="similarity-bar small">
                  <div
                    className="similarity-fill"
                    style={{
                      width: `${ms.similarity * 100}%`,
                      backgroundColor: getSimilarityColor(ms.similarity)
                    }}
                  />
                  <span className="similarity-value">{(ms.similarity * 100).toFixed(0)}%</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const getSimilarityColor = (similarity) => {
    if (similarity >= 0.8) return '#4caf50'; // Green - high similarity
    if (similarity >= 0.6) return '#ffc107'; // Yellow - moderate
    if (similarity >= 0.4) return '#ff9800'; // Orange - low
    return '#f44336'; // Red - very different
  };

  if (loading) {
    return (
      <div className="time-travel-overlay">
        <div className="time-travel-modal">
          <div className="loading">Loading benchmarks...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="time-travel-overlay" onClick={onClose}>
      <div className="time-travel-modal" onClick={(e) => e.stopPropagation()}>
        <div className="time-travel-header">
          <h2>⏱️ Time-Travel Benchmarks</h2>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        <div className="time-travel-content">
          {/* Benchmarks List */}
          <div className="benchmarks-list">
            <h3>Snapshots</h3>
            {benchmarks.length === 0 ? (
              <div className="no-benchmarks">No benchmarks yet</div>
            ) : (
              <div className="benchmark-items">
                {benchmarks.map((bm) => (
                  <div
                    key={bm.snapshot_id}
                    className={`benchmark-item ${
                      selectedBenchmark?.snapshot_id === bm.snapshot_id ? 'active' : ''
                    }`}
                    onClick={() => loadBenchmarkDetails(bm.snapshot_id)}
                  >
                    <div className="benchmark-query">{bm.query}</div>
                    <div className="benchmark-meta">
                      <span className="benchmark-date">{formatDate(bm.created_at)}</span>
                      <span className="benchmark-reruns">{bm.rerun_count} reruns</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Benchmark Details */}
          <div className="benchmark-details">
            {!selectedBenchmark ? (
              <div className="no-selection">Select a benchmark to view details</div>
            ) : (
              <>
                <div className="details-header">
                  <h3>Benchmark Details</h3>
                  <button
                    className="rerun-btn"
                    onClick={handleRerun}
                    disabled={rerunning}
                  >
                    {rerunning ? '⏳ Re-running...' : '🔄 Re-run Now'}
                  </button>
                </div>

                <div className="original-query">
                  <h4>Original Query</h4>
                  <p>{selectedBenchmark.query}</p>
                  <span className="query-date">Created: {formatDate(selectedBenchmark.created_at)}</span>
                </div>

                {selectedBenchmark.reruns && selectedBenchmark.reruns.length > 0 && (
                  <div className="reruns-section">
                    <h4>Reruns ({selectedBenchmark.reruns.length})</h4>
                    <div className="reruns-list">
                      {selectedBenchmark.reruns.map((rerun, idx) => (
                        <div
                          key={idx}
                          className={`rerun-item ${selectedRerun === idx ? 'active' : ''}`}
                          onClick={() => setSelectedRerun(selectedRerun === idx ? null : idx)}
                        >
                          <div className="rerun-header-line">
                            <span className="rerun-date">{formatDate(rerun.rerun_at)}</span>
                            {rerun.drift_metrics?.final_answer_similarity !== undefined && (
                              <span
                                className="drift-indicator"
                                style={{
                                  color: getSimilarityColor(rerun.drift_metrics.final_answer_similarity)
                                }}
                              >
                                {(rerun.drift_metrics.final_answer_similarity * 100).toFixed(0)}% similar
                              </span>
                            )}
                          </div>

                          {selectedRerun === idx && (
                            <div className="rerun-details">
                              {renderDriftMetrics(rerun.drift_metrics)}

                              <div className="comparison-view">
                                <div className="comparison-column">
                                  <h5>Original Response</h5>
                                  <div className="response-preview markdown-content">
                                    <ReactMarkdown>
                                      {selectedBenchmark.original_response.stage3?.response || 'No response'}
                                    </ReactMarkdown>
                                  </div>
                                </div>

                                <div className="comparison-column">
                                  <h5>New Response</h5>
                                  <div className="response-preview markdown-content">
                                    <ReactMarkdown>
                                      {rerun.result.stage3?.response || 'No response'}
                                    </ReactMarkdown>
                                  </div>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {(!selectedBenchmark.reruns || selectedBenchmark.reruns.length === 0) && (
                  <div className="no-reruns">
                    No reruns yet. Click "Re-run Now" to compare with current model behavior.
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
