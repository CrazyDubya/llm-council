/**
 * StreamingMessage component displays text as it streams in token-by-token.
 *
 * Features:
 * - Animated cursor while streaming
 * - Smooth text accumulation
 * - ReactMarkdown rendering when complete
 */

import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import './StreamingMessage.css';

export const StreamingMessage = ({
  isStreaming = false,
  content = '',
  showCursor = true,
  className = ''
}) => {
  const [displayedContent, setDisplayedContent] = useState(content);
  const contentRef = useRef(content);
  const scrollRef = useRef(null);

  // Update displayed content when content prop changes
  useEffect(() => {
    contentRef.current = content;
    setDisplayedContent(content);
  }, [content]);

  // Auto-scroll to bottom as content streams
  useEffect(() => {
    if (scrollRef.current && isStreaming) {
      scrollRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, [displayedContent, isStreaming]);

  return (
    <div className={`streaming-message ${className}`} ref={scrollRef}>
      {isStreaming ? (
        <div className="streaming-text">
          <span className="text-content">{displayedContent}</span>
          {showCursor && <span className="streaming-cursor">▋</span>}
        </div>
      ) : (
        <div className="markdown-content">
          <ReactMarkdown>{displayedContent || '*No response*'}</ReactMarkdown>
        </div>
      )}
    </div>
  );
};

/**
 * StreamingModelResponse component for displaying a single model's streaming response.
 */
export const StreamingModelResponse = ({
  model,
  isStreaming = false,
  content = '',
  isComplete = false
}) => {
  return (
    <div className={`streaming-model-response ${isComplete ? 'complete' : ''}`}>
      <div className="model-header">
        <span className="model-name">{model}</span>
        {isStreaming && <span className="streaming-indicator">●</span>}
        {isComplete && <span className="complete-indicator">✓</span>}
      </div>
      <StreamingMessage
        isStreaming={isStreaming}
        content={content}
        showCursor={isStreaming}
      />
    </div>
  );
};

/**
 * StreamingProgress component shows overall progress.
 */
export const StreamingProgress = ({
  stage,
  currentModel = null,
  totalModels = 0,
  completedModels = 0,
  message = ''
}) => {
  const progress = totalModels > 0 ? (completedModels / totalModels) * 100 : 0;

  const stageNames = {
    'stage1': 'Stage 1: Collecting Responses',
    'stage2': 'Stage 2: Peer Review',
    'stage3': 'Stage 3: Chairman Synthesis'
  };

  return (
    <div className="streaming-progress">
      <div className="progress-header">
        <span className="stage-name">{stageNames[stage] || stage}</span>
        {currentModel && (
          <span className="current-model">
            {currentModel} ({completedModels + 1}/{totalModels})
          </span>
        )}
      </div>

      {totalModels > 0 && (
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      {message && <div className="progress-message">{message}</div>}
    </div>
  );
};

export default StreamingMessage;
