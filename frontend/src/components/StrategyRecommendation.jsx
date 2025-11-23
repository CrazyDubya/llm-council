import { useState, useEffect } from 'react';
import './StrategyRecommendation.css';

export default function StrategyRecommendation({ query, onAccept, onDismiss }) {
  const [recommendation, setRecommendation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    // Only fetch recommendation if query is substantial
    if (query && query.trim().length > 20 && !dismissed) {
      fetchRecommendation(query);
    } else {
      setRecommendation(null);
    }
  }, [query, dismissed]);

  const fetchRecommendation = async (queryText) => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8001/api/strategies/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: queryText })
      });

      if (response.ok) {
        const data = await response.json();
        setRecommendation(data);
      }
    } catch (error) {
      console.error('Failed to get strategy recommendation:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAccept = () => {
    if (recommendation && onAccept) {
      onAccept(recommendation.strategy);
    }
    setDismissed(true);
  };

  const handleDismiss = () => {
    setDismissed(true);
    if (onDismiss) {
      onDismiss();
    }
  };

  if (dismissed || !recommendation || loading) {
    return null;
  }

  return (
    <div className="strategy-recommendation">
      <div className="recommendation-header">
        <span className="recommendation-icon">💡</span>
        <span className="recommendation-title">Suggested Strategy</span>
        <button className="dismiss-btn" onClick={handleDismiss}>×</button>
      </div>

      <div className="recommendation-body">
        <div className="recommendation-strategy">
          <strong>{recommendation.strategy.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</strong>
          <span className="confidence-badge">
            {Math.round(recommendation.confidence * 100)}% confidence
          </span>
        </div>

        <div className="recommendation-explanation">
          {recommendation.explanation}
        </div>

        <div className="recommendation-details">
          <span className="category-tag">
            {recommendation.query_category}
          </span>
          {recommendation.fallback_options && recommendation.fallback_options.length > 0 && (
            <span className="fallback-hint">
              Alternatives: {recommendation.fallback_options.slice(0, 2).join(', ')}
            </span>
          )}
        </div>
      </div>

      <div className="recommendation-actions">
        <button className="accept-btn" onClick={handleAccept}>
          Use This Strategy
        </button>
        <button className="dismiss-text-btn" onClick={handleDismiss}>
          Keep Current
        </button>
      </div>
    </div>
  );
}
