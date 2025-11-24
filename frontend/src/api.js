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

  // ===== TIME-TRAVEL BENCHMARKING =====

  /**
   * Create a benchmark snapshot.
   */
  async createBenchmark(conversationId, messageIndex) {
    const response = await fetch(`${API_BASE}/api/benchmarks`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        conversation_id: conversationId,
        message_index: messageIndex,
      }),
    });
    if (!response.ok) {
      throw new Error('Failed to create benchmark');
    }
    return response.json();
  },

  /**
   * List all benchmarks.
   */
  async listBenchmarks() {
    const response = await fetch(`${API_BASE}/api/benchmarks`);
    if (!response.ok) {
      throw new Error('Failed to list benchmarks');
    }
    const data = await response.json();
    return data.benchmarks;
  },

  /**
   * Get a specific benchmark.
   */
  async getBenchmark(snapshotId) {
    const response = await fetch(`${API_BASE}/api/benchmarks/${snapshotId}`);
    if (!response.ok) {
      throw new Error('Failed to get benchmark');
    }
    return response.json();
  },

  /**
   * Re-run a benchmark.
   */
  async rerunBenchmark(snapshotId, models, chairman, strategy = 'simple') {
    const response = await fetch(
      `${API_BASE}/api/benchmarks/${snapshotId}/rerun`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ models, chairman, strategy }),
      }
    );
    if (!response.ok) {
      throw new Error('Failed to rerun benchmark');
    }
    return response.json();
  },

  // ===== FACT-CHECKING =====

  /**
   * Extract citations from text.
   */
  async extractCitations(text) {
    const response = await fetch(`${API_BASE}/api/fact-check/citations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text }),
    });
    if (!response.ok) {
      throw new Error('Failed to extract citations');
    }
    return response.json();
  },

  /**
   * Extract claims from text.
   */
  async extractClaims(text) {
    const response = await fetch(`${API_BASE}/api/fact-check/claims`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text }),
    });
    if (!response.ok) {
      throw new Error('Failed to extract claims');
    }
    return response.json();
  },

  /**
   * Cross-reference validate responses.
   */
  async crossReferenceValidate(responses) {
    const response = await fetch(`${API_BASE}/api/fact-check/cross-reference`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ responses }),
    });
    if (!response.ok) {
      throw new Error('Failed to cross-reference validate');
    }
    return response.json();
  },

  // ===== MODEL MANAGEMENT =====

  /**
   * List available models.
   */
  async listModels(filters = {}) {
    const params = new URLSearchParams();
    if (filters.category) params.append('category', filters.category);
    if (filters.min_context) params.append('min_context', filters.min_context);
    if (filters.max_cost) params.append('max_cost', filters.max_cost);
    if (filters.search) params.append('search', filters.search);

    const response = await fetch(
      `${API_BASE}/api/models?${params.toString()}`
    );
    if (!response.ok) {
      throw new Error('Failed to list models');
    }
    const data = await response.json();
    return data.models;
  },

  /**
   * Get model info.
   */
  async getModelInfo(modelId) {
    const response = await fetch(
      `${API_BASE}/api/models/${encodeURIComponent(modelId)}`
    );
    if (!response.ok) {
      throw new Error('Failed to get model info');
    }
    return response.json();
  },

  /**
   * Estimate cost for models.
   */
  async estimateCost(modelIds, avgPromptTokens = 1000, avgCompletionTokens = 500, numCalls = 1) {
    const response = await fetch(`${API_BASE}/api/models/estimate-cost`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model_ids: modelIds,
        avg_prompt_tokens: avgPromptTokens,
        avg_completion_tokens: avgCompletionTokens,
        num_calls: numCalls,
      }),
    });
    if (!response.ok) {
      throw new Error('Failed to estimate cost');
    }
    return response.json();
  },

  /**
   * Get council recommendations.
   */
  async recommendCouncil(budget = null, diversity = true, includeReasoning = false) {
    const response = await fetch(`${API_BASE}/api/models/recommend-council`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        budget,
        diversity,
        include_reasoning: includeReasoning,
      }),
    });
    if (!response.ok) {
      throw new Error('Failed to get recommendations');
    }
    const data = await response.json();
    return data.recommended_models;
  },
};
