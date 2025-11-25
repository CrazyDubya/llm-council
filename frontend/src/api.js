/**
 * API client for the LLM Council backend.
 */

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001';

export const api = {
  /**
   * List all conversations.
   */
  async listConversations() {
    const response = await fetch(`${API_BASE}/api/conversations`);
    if (!response.ok) {
      throw new Error('Failed to list conversations');
    }
    return response.json();
  },

  /**
   * Create a new conversation.
   */
  async createConversation() {
    const response = await fetch(`${API_BASE}/api/conversations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({}),
    });
    if (!response.ok) {
      throw new Error('Failed to create conversation');
    }
    return response.json();
  },

  /**
   * Get a specific conversation.
   */
  async getConversation(conversationId) {
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}`
    );
    if (!response.ok) {
      throw new Error('Failed to get conversation');
    }
    return response.json();
  },

  /**
   * Send a message in a conversation.
   */
  async sendMessage(conversationId, content, strategy = 'simple', strategyConfig = {}) {
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}/message`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content,
          strategy,
          strategy_config: strategyConfig
        }),
      }
    );
    if (!response.ok) {
      throw new Error('Failed to send message');
    }
    return response.json();
  },

  /**
   * Send a message and receive streaming updates.
   * @param {string} conversationId - The conversation ID
   * @param {string} content - The message content
   * @param {function} onEvent - Callback function for each event: (eventType, data) => void
   * @param {string} strategy - Strategy to use (default: 'simple')
   * @param {object} strategyConfig - Strategy configuration (default: {})
   * @param {AbortSignal} signal - Optional AbortSignal for cancellation
   * @returns {Promise<void>}
   */
  async sendMessageStream(conversationId, content, onEvent, strategy = 'simple', strategyConfig = {}, signal = null) {
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}/message/stream`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content,
          strategy,
          strategy_config: strategyConfig
        }),
        signal,
      }
    );

    if (!response.ok) {
      throw new Error('Failed to send message');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            try {
              const event = JSON.parse(data);
              onEvent(event.type, event);
            } catch (e) {
              console.error('Failed to parse SSE event:', e);
            }
          }
        }
      }
    } catch (e) {
      if (e.name === 'AbortError') {
        console.log('Request was cancelled');
        return;
      }
      throw e;
    }
  },

  /**
   * Get strategy recommendation for a query.
   * @param {string} query - The query to analyze
   * @param {AbortSignal} signal - Optional AbortSignal for cancellation
   * @returns {Promise<object>} Recommendation object
   */
  async getStrategyRecommendation(query, signal = null) {
    const response = await fetch(
      `${API_BASE}/api/strategies/recommend`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
        signal,
      }
    );

    if (!response.ok) {
      throw new Error('Failed to get recommendation');
    }
    return response.json();
  },

  /**
   * Get analytics summary.
   * @returns {Promise<object>} Analytics summary
   */
  async getAnalyticsSummary() {
    const response = await fetch(`${API_BASE}/api/analytics/summary`);
    if (!response.ok) {
      throw new Error('Failed to get analytics');
    }
    return response.json();
  },

  /**
   * Get model leaderboard.
   * @param {number} limit - Maximum number of models to return
   * @returns {Promise<object>} Leaderboard data
   */
  async getLeaderboard(limit = 10) {
    const response = await fetch(`${API_BASE}/api/analytics/leaderboard?limit=${limit}`);
    if (!response.ok) {
      throw new Error('Failed to get leaderboard');
    }
    return response.json();
  },

  /**
   * Submit feedback for a message.
   * @param {string} conversationId - The conversation ID
   * @param {number} messageIndex - The message index
   * @param {number} feedback - Feedback value (-1, 0, or 1)
   * @returns {Promise<object>} Result
   */
  async submitFeedback(conversationId, messageIndex, feedback) {
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}/messages/${messageIndex}/feedback`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ feedback }),
      }
    );
    if (!response.ok) {
      throw new Error('Failed to submit feedback');
    }
    return response.json();
  },
};
