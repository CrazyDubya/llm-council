/**
 * API client for the LLM Council backend.
 */

const API_BASE = 'http://localhost:8001';

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
   * @returns {Promise<void>}
   */
  async sendMessageStream(conversationId, content, onEvent, strategy = 'simple', strategyConfig = {}) {
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
      }
    );

    if (!response.ok) {
      throw new Error('Failed to send message');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

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
  },

  /**
   * Search conversations.
   */
  async searchConversations(query = null, tags = null, includeArchived = false) {
    const params = new URLSearchParams();
    if (query) params.append('query', query);
    if (tags && tags.length > 0) params.append('tags', tags.join(','));
    if (includeArchived) params.append('include_archived', 'true');

    const response = await fetch(
      `${API_BASE}/api/conversations/search?${params.toString()}`
    );
    if (!response.ok) {
      throw new Error('Failed to search conversations');
    }
    const data = await response.json();
    return data.results;
  },

  /**
   * Add a tag to a conversation.
   */
  async addTag(conversationId, tag) {
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}/tags`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ tag }),
      }
    );
    if (!response.ok) {
      throw new Error('Failed to add tag');
    }
    return response.json();
  },

  /**
   * Remove a tag from a conversation.
   */
  async removeTag(conversationId, tag) {
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}/tags`,
      {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ tag }),
      }
    );
    if (!response.ok) {
      throw new Error('Failed to remove tag');
    }
    return response.json();
  },

  /**
   * Archive a conversation.
   */
  async archiveConversation(conversationId) {
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}/archive`,
      {
        method: 'POST',
      }
    );
    if (!response.ok) {
      throw new Error('Failed to archive conversation');
    }
    return response.json();
  },

  /**
   * Unarchive a conversation.
   */
  async unarchiveConversation(conversationId) {
    const response = await fetch(
      `${API_BASE}/api/conversations/${conversationId}/unarchive`,
      {
        method: 'POST',
      }
    );
    if (!response.ok) {
      throw new Error('Failed to unarchive conversation');
    }
    return response.json();
  },
};
