import { useState, useEffect, useRef } from 'react';
import { api } from '../api';
import './StrategyRecommendation.css';

export default function StrategyRecommendation({ query, onAccept, onDismiss }) {
  const [recommendation, setRecommendation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const abortControllerRef = useRef(null);

  useEffect(() => {
    // Debounce: only fetch after user stops typing for 500ms
    if (query && query.trim().length > 20 && !dismissed) {
      const timer = setTimeout(() => {
        fetchRecommendation(query);
      }, 500);

      return () => {
        clearTimeout(timer);
        // Cancel any in-flight request when query changes
        if (abortControllerRef.current) {
          abortControllerRef.current.abort();
        }
      };
    } else {
      setRecommendation(null);
    }
  }, [query, dismissed]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const fetchRecommendation = async (queryText) => {
    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    setLoading(true);
    try {
      const data = await api.getStrategyRecommendation(
        queryText,
        abortControllerRef.current.signal
      );

      // Only set if confidence is reasonable
      if (data.confidence >= 0.2) {
        setRecommendation(data);
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        // Request was cancelled, ignore
        return;
      }
      console.error('Failed to get strategy recommendation:', error);
      // Silently fail - recommendation is optional enhancement
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
