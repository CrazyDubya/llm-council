import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import './Stage3.css';

const API_BASE = 'http://localhost:8001';

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
