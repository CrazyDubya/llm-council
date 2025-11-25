import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import CopyButton from './CopyButton';
import { api } from '../api';
import './Stage3.css';

export default function Stage3({
  finalResponse,
  conversationId,
  messageIndex,
  currentFeedback
}) {
  const [feedback, setFeedback] = useState(currentFeedback);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!finalResponse) {
    return null;
  }

  const handleFeedback = async (value) => {
    if (!conversationId || messageIndex === undefined) {
      return; // Can't submit feedback without conversation context
    }

    setIsSubmitting(true);
    try {
      await api.submitFeedback(conversationId, messageIndex, value);
      setFeedback(value);
    } catch (error) {
      console.error('Error submitting feedback:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="stage stage3">
      <div className="stage-header">
        <h3 className="stage-title">Stage 3: Final Council Answer</h3>
        <CopyButton text={finalResponse.response} />
      </div>
      <div className="final-response">
        <div className="chairman-label">
          Chairman: {finalResponse.model.split('/')[1] || finalResponse.model}
        </div>
        <div className="final-text markdown-content">
          <ReactMarkdown>{finalResponse.response}</ReactMarkdown>
        </div>

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
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
                </svg>
              </button>
              <button
                className={`feedback-btn ${feedback === -1 ? 'active dislike' : ''}`}
                onClick={() => handleFeedback(-1)}
                disabled={isSubmitting}
                title="Not helpful"
              >
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17" />
                </svg>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
