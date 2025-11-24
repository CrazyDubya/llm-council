/**
 * WebSocket hook for real-time streaming of council deliberations.
 *
 * Manages WebSocket connection lifecycle, auto-reconnect, and message handling.
 */

import { useEffect, useRef, useState, useCallback } from 'react';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8001';

export const useWebSocket = (conversationId, enabled = true) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const [error, setError] = useState(null);

  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const messageHandlersRef = useRef(new Set());
  const messageQueueRef = useRef([]);

  const MAX_RECONNECT_ATTEMPTS = 5;
  const RECONNECT_DELAY = 2000; // 2 seconds

  /**
   * Register a message handler callback.
   */
  const onMessage = useCallback((handler) => {
    messageHandlersRef.current.add(handler);

    // Return unsubscribe function
    return () => {
      messageHandlersRef.current.delete(handler);
    };
  }, []);

  /**
   * Notify all registered message handlers.
   */
  const notifyHandlers = useCallback((message) => {
    messageHandlersRef.current.forEach(handler => {
      try {
        handler(message);
      } catch (err) {
        console.error('Error in message handler:', err);
      }
    });
  }, []);

  /**
   * Send a message through the WebSocket.
   */
  const sendMessage = useCallback((message) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      // Queue message for when connection is established
      messageQueueRef.current.push(message);
      console.warn('WebSocket not connected, message queued:', message);
    }
  }, []);

  /**
   * Send queued messages.
   */
  const flushMessageQueue = useCallback(() => {
    while (messageQueueRef.current.length > 0) {
      const message = messageQueueRef.current.shift();
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify(message));
      }
    }
  }, []);

  /**
   * Connect to WebSocket server.
   */
  const connect = useCallback(() => {
    if (!enabled || !conversationId) return;

    // Don't reconnect if already connected or connecting
    if (wsRef.current &&
        (wsRef.current.readyState === WebSocket.OPEN ||
         wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    try {
      const wsUrl = `${WS_URL}/ws/${conversationId}`;
      console.log('Connecting to WebSocket:', wsUrl);

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;

        // Flush any queued messages
        flushMessageQueue();

        // Send ping to keep connection alive
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          } else {
            clearInterval(pingInterval);
          }
        }, 30000); // Ping every 30 seconds
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          setLastMessage(message);
          notifyHandlers(message);
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('WebSocket connection error');
      };

      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        setIsConnected(false);
        wsRef.current = null;

        // Attempt to reconnect if not a normal closure
        if (enabled && event.code !== 1000 && reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
          reconnectAttemptsRef.current += 1;
          console.log(`Reconnecting... Attempt ${reconnectAttemptsRef.current}`);

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, RECONNECT_DELAY * reconnectAttemptsRef.current);
        } else if (reconnectAttemptsRef.current >= MAX_RECONNECT_ATTEMPTS) {
          setError('Failed to reconnect after maximum attempts');
        }
      };

    } catch (err) {
      console.error('Error creating WebSocket:', err);
      setError(err.message);
    }
  }, [conversationId, enabled, flushMessageQueue, notifyHandlers]);

  /**
   * Disconnect from WebSocket server.
   */
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect');
      wsRef.current = null;
    }

    setIsConnected(false);
  }, []);

  /**
   * Send a message to the council.
   */
  const sendCouncilMessage = useCallback((content, strategy = 'simple', strategyConfig = {}) => {
    sendMessage({
      type: 'send_message',
      content,
      strategy,
      strategy_config: strategyConfig
    });
  }, [sendMessage]);

  /**
   * Request to stop generation.
   */
  const stopGeneration = useCallback(() => {
    sendMessage({
      type: 'stop_generation'
    });
  }, [sendMessage]);

  // Connect on mount or when conversationId changes
  useEffect(() => {
    if (enabled && conversationId) {
      connect();
    }

    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, [conversationId, enabled]); // Only reconnect when these change

  return {
    isConnected,
    error,
    lastMessage,
    sendMessage,
    sendCouncilMessage,
    stopGeneration,
    onMessage,
    connect,
    disconnect
  };
};

export default useWebSocket;
