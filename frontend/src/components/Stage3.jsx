import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import './Stage3.css';

const API_BASE = 'http://localhost:8001';

export default function Stage3({
  finalResponse,
  conversationId,
  messageIndex,
  currentFeedback,
  apiUsage,
  councilInfo
}) {
  const [feedback, setFeedback] = useState(currentFeedback);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!finalResponse) {
    return null;
  }

  const formatCost = (value) => {
    if (value === null || value === undefined) {
      return 'n/a';
    }
    if (value < 0.001) {
      return `$${value.toExponential(2)}`;
    }
    return `$${value.toFixed(3)}`;
  };

  const handleFeedback = async (value) => {
    if (!conversationId || messageIndex === undefined) {
      return; // Can't submit feedback without conversation context
    }

    setIsSubmitting(true);
    try {
      const response = await fetch(
        `${API_BASE}/api/conversations/${conversationId}/messages/${messageIndex}/feedback`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ feedback: value }),
        }
      );

      if (response.ok) {
        setFeedback(value);
      } else {
        console.error('Failed to submit feedback');
      }
    } catch (error) {
      console.error('Error submitting feedback:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="stage stage3">
      <h3 className="stage-title">Stage 3: Final Council Answer</h3>
      <div className="final-response">
        <div className="chairman-label">
          Chairman: {finalResponse.model.split('/')[1] || finalResponse.model}
        </div>
        <div className="final-text markdown-content">
          <ReactMarkdown>{finalResponse.response}</ReactMarkdown>
        </div>

        {councilInfo && (
          <div className="council-info">
            <div className="usage-heading">Council Configuration</div>
            <div className="council-details">
              <div>
                <span className="usage-label">Chairman</span>
                <strong>{councilInfo.chairman}</strong>
              </div>
              <div>
                <span className="usage-label">Models</span>
                <span className="council-models">{(councilInfo.models || []).join(', ')}</span>
              </div>
            </div>
          </div>
        )}

        {apiUsage?.calls?.length ? (
          <div className="api-usage">
            <div className="usage-heading">API Usage & Estimated Cost</div>
            <div className="usage-totals">
              <div>
                <span className="usage-label">Total Prompt Tokens</span>
                <strong>{apiUsage.total_prompt_tokens?.toLocaleString?.() ?? 'n/a'}</strong>
              </div>
              <div>
                <span className="usage-label">Total Completion Tokens</span>
                <strong>{apiUsage.total_completion_tokens?.toLocaleString?.() ?? 'n/a'}</strong>
              </div>
              <div>
                <span className="usage-label">Estimated Cost</span>
                <strong>{formatCost(apiUsage.total_cost)}</strong>
              </div>
            </div>
            <div className="usage-call-list">
              {apiUsage.calls.slice(0, 5).map((call, idx) => (
                <div key={idx} className="usage-row">
                  <div className="usage-model">
                    <div className="usage-model-name">{call.model}</div>
                    <div className="usage-stage">
                      {call.context?.stage || 'unknown stage'}
                      {call.context?.round ? ` · round ${call.context.round}` : ''}
                    </div>
                  </div>
                  <div className="usage-metrics">
                    <span>{call.usage?.prompt_tokens ?? 0} prompt</span>
                    <span>{call.usage?.completion_tokens ?? 0} completion</span>
                  </div>
                  <div className="usage-cost">{formatCost(call.cost)}</div>
                </div>
              ))}
              {apiUsage.calls.length > 5 && (
                <div className="usage-note">
                  Showing first 5 of {apiUsage.calls.length} calls. View analytics for the full trace.
                </div>
              )}
            </div>
          </div>
        ) : null}

        {/* Feedback buttons */}
        {conversationId && messageIndex !== undefined && (
          <div className="feedback-section">
            <span className="feedback-label">Was this helpful?</span>
            <div className="feedback-buttons">
              <button
                className={`feedback-btn ${feedback === 1 ? 'active like' : ''}`}
                onClick={() => handleFeedback(1)}
                disabled={isSubmitting}
                title="Helpful"
              >
                👍
              </button>
              <button
                className={`feedback-btn ${feedback === -1 ? 'active dislike' : ''}`}
                onClick={() => handleFeedback(-1)}
                disabled={isSubmitting}
                title="Not helpful"
              >
                👎
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
