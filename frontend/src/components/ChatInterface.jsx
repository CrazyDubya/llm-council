import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import Stage1 from './Stage1';
import Stage2 from './Stage2';
import Stage3 from './Stage3';
import MultiRoundView from './MultiRoundView';
import StrategyRecommendation from './StrategyRecommendation';
import './ChatInterface.css';

export default function ChatInterface({
  conversation,
  onSendMessage,
  isLoading,
  selectedStrategy,
  onStrategyChange,
  strategyOptions = [],
  selectedCouncil,
  onCouncilChange,
  councilOptions = [],
}) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  const strategies = strategyOptions.length
    ? strategyOptions
    : [
        { id: 'simple', name: 'Simple Ranking' },
        { id: 'weighted_voting', name: 'Weighted Voting' },
        { id: 'multi_round', name: 'Multi-Round' },
        { id: 'reasoning_aware', name: 'Reasoning-Aware' },
      ];

  const councils = councilOptions.length
    ? councilOptions
    : [
        { id: 'full', name: 'Full Council' },
        { id: 'low_cost', name: 'Budget Council' },
        { id: 'hybrid', name: 'Hybrid Council' },
      ];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversation]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSendMessage(input, selectedStrategy);
    setInput('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const messages = conversation?.messages || [];
  const currentStrategy = strategies.find((s) => s.id === selectedStrategy) || strategies[0];
  const currentCouncil = councils.find((c) => c.id === selectedCouncil) || councils[0];

  return (
    <div className="chat-interface">
      <div className="messages-container">
        {!conversation && (
          <div className="empty-state">
            <h2>Welcome to LLM Council</h2>
            <p>Ask your first question to spin up the council.</p>
          </div>
        )}

        {!messages.length && conversation && (
          <div className="empty-state">
            <h2>Start a conversation</h2>
            <p>Ask a question to consult the LLM Council</p>
          </div>
        )}

        {conversation && (
          <div className="session-summary">
            <span>Strategy: {currentStrategy?.name || currentStrategy?.id}</span>
            {currentCouncil && (
              <span>Council: {currentCouncil.name || currentCouncil.id}</span>
            )}
          </div>
        )}

        {messages.map((msg, index) => (
          <div key={index} className="message-group">
            {msg.role === 'user' ? (
              <div className="user-message">
                <div className="message-label">You</div>
                <div className="message-content">
                  <div className="markdown-content">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                </div>
              </div>
            ) : (
              <div className="assistant-message">
                <div className="message-label">LLM Council</div>

                {msg.stage1 && Array.isArray(msg.stage1) && msg.stage1[0]?.round_number ? (
                  <div className="multi-round-container">
                    {msg.loading?.stage1 && (
                      <div className="stage-loading">
                        <div className="spinner"></div>
                        <span>Running multi-round deliberation...</span>
                      </div>
                    )}
                    {!msg.loading?.stage1 && (
                      <MultiRoundView rounds={msg.stage1} metadata={msg.metadata} />
                    )}
                  </div>
                ) : (
                  <>
                    {msg.loading?.stage1 && (
                      <div className="stage-loading">
                        <div className="spinner"></div>
                        <span>Running Stage 1: Collecting individual responses...</span>
                      </div>
                    )}
                    {msg.stage1 && <Stage1 responses={msg.stage1} />}

                    {msg.loading?.stage2 && (
                      <div className="stage-loading">
                        <div className="spinner"></div>
                        <span>Running Stage 2: Peer rankings...</span>
                      </div>
                    )}
                    {msg.stage2 && (
                      <Stage2
                        rankings={msg.stage2}
                        labelToModel={msg.metadata?.label_to_model}
                        aggregateRankings={msg.metadata?.aggregate_rankings}
                      />
                    )}
                  </>
                )}

                {msg.loading?.stage3 && (
                  <div className="stage-loading">
                    <div className="spinner"></div>
                    <span>Running Stage 3: Final synthesis...</span>
                  </div>
                )}
                {msg.stage3 && (
                  <Stage3
                    finalResponse={msg.stage3}
                    conversationId={conversation?.id}
                    messageIndex={index}
                    currentFeedback={msg.user_feedback}
                    apiUsage={msg.metadata?.api_usage}
                    councilInfo={msg.metadata?.council}
                  />
                )}
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="loading-indicator">
            <div className="spinner"></div>
            <span>Consulting the council...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <StrategyRecommendation
        query={input}
        onAccept={(strategy) => onStrategyChange(strategy)}
        onDismiss={() => {}}
      />

      <form className="input-form" onSubmit={handleSubmit}>
        <textarea
          className="message-input"
          placeholder="Ask your question... (Shift+Enter for new line, Enter to send)"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          rows={3}
        />
        <button
          type="submit"
          className="send-button"
          disabled={!input.trim() || isLoading}
        >
          Send
        </button>
      </form>
    </div>
  );
}
