# Day 3: WebSocket Integration Guide

This document explains how to integrate the WebSocket streaming components into the React frontend.

## Components Created

### 1. `useWebSocket` Hook (`frontend/src/hooks/useWebSocket.js`)
A comprehensive WebSocket hook with:
- Auto-reconnect logic (max 5 attempts)
- Message queue for offline buffering
- Event handler registration system
- Ping/pong keepalive
- Clean lifecycle management

### 2. StreamingMessage Components (`frontend/src/components/StreamingMessage.jsx`)
Three components for displaying streaming content:
- `StreamingMessage`: Base component with cursor animation
- `StreamingModelResponse`: Model-specific streaming display
- `StreamingProgress`: Progress indicator for stages

## Integration Steps

### Step 1: Add WebSocket to App.jsx

```jsx
import useWebSocket from './hooks/useWebSocket';

function App() {
  // ... existing state ...
  const [streamingResponses, setStreamingResponses] = useState({});

  // Initialize WebSocket
  const {
    isConnected,
    sendCouncilMessage,
    stopGeneration,
    onMessage
  } = useWebSocket(currentConversationId, !!currentConversationId);

  // Register message handler
  useEffect(() => {
    if (!currentConversationId) return;

    const unsubscribe = onMessage((message) => {
      handleWebSocketMessage(message);
    });

    return unsubscribe;
  }, [currentConversationId, onMessage]);

  const handleWebSocketMessage = (message) => {
    const { type, data } = message;

    switch (type) {
      case 'stage1_model_start':
        // Initialize streaming for this model
        setStreamingResponses(prev => ({
          ...prev,
          [data.model]: { content: '', isStreaming: true }
        }));
        break;

      case 'stage1_model_token':
        // Append token to model's response
        setStreamingResponses(prev => ({
          ...prev,
          [data.model]: {
            ...prev[data.model],
            content: prev[data.model].content + data.token
          }
        }));
        break;

      case 'stage1_model_complete':
        // Mark model as complete
        setStreamingResponses(prev => ({
          ...prev,
          [data.model]: {
            ...prev[data.model],
            isStreaming: false
          }
        }));
        break;

      case 'stage1_complete':
        // Update conversation with complete responses
        setCurrentConversation(prev => {
          const messages = [...prev.messages];
          const lastMsg = messages[messages.length - 1];
          lastMsg.stage1 = data.responses;
          lastMsg.loading.stage1 = false;
          return { ...prev, messages };
        });
        break;

      // Similar handlers for stage2 and stage3...

      case 'complete':
        setIsLoading(false);
        loadConversations();
        break;

      case 'error':
        console.error('WebSocket error:', data.error);
        setIsLoading(false);
        break;
    }
  };

  const handleSendMessage = async (content) => {
    if (!currentConversationId || !isConnected) return;

    setIsLoading(true);
    setStreamingResponses({});

    // Optimistically add user message
    const userMessage = { role: 'user', content };
    setCurrentConversation(prev => ({
      ...prev,
      messages: [...prev.messages, userMessage]
    }));

    // Add partial assistant message
    const assistantMessage = {
      role: 'assistant',
      stage1: null,
      stage2: null,
      stage3: null,
      metadata: null,
      loading: { stage1: true, stage2: false, stage3: false },
      streaming: streamingResponses
    };

    setCurrentConversation(prev => ({
      ...prev,
      messages: [...prev.messages, assistantMessage]
    }));

    // Send via WebSocket
    sendCouncilMessage(content, selectedStrategy, {});
  };
}
```

### Step 2: Update ChatInterface.jsx

Add streaming display to the Stage 1 section:

```jsx
import { StreamingModelResponse, StreamingProgress } from './StreamingMessage';

// In the render:
{msg.loading?.stage1 && (
  <>
    <StreamingProgress
      stage="stage1"
      currentModel={getCurrentStreamingModel(msg)}
      totalModels={COUNCIL_MODELS.length}
      completedModels={getCompletedModelsCount(msg)}
    />

    {msg.streaming && Object.entries(msg.streaming).map(([model, data]) => (
      <StreamingModelResponse
        key={model}
        model={model}
        isStreaming={data.isStreaming}
        content={data.content}
        isComplete={!data.isStreaming}
      />
    ))}
  </>
)}
```

### Step 3: Update Stage1.jsx

Modify to show streaming responses in tabs:

```jsx
import { StreamingMessage } from './StreamingMessage';

export default function Stage1({ responses, streaming }) {
  return (
    <div className="stage stage1">
      <div className="tabs">
        {responses.map((resp, idx) => {
          const streamingData = streaming?.[resp.model];
          const isStreaming = streamingData?.isStreaming;
          const content = isStreaming ? streamingData.content : resp.response;

          return (
            <div key={idx} className="tab-panel">
              <h3>{resp.model}</h3>
              <StreamingMessage
                isStreaming={isStreaming}
                content={content}
                showCursor={isStreaming}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}
```

### Step 4: Add Stop Button

```jsx
{isLoading && (
  <button
    onClick={stopGeneration}
    className="stop-button"
  >
    ⏹ Stop Generation
  </button>
)}
```

## Token-Level Streaming Flow

```
User sends message
    ↓
WebSocket: send_message event
    ↓
Backend starts Stage 1
    ↓
Frontend receives: stage1_start
    ↓
For each model:
    ├─ stage1_model_start → Initialize UI
    ├─ stage1_model_token → Append to display (many times)
    └─ stage1_model_complete → Mark done
    ↓
Frontend receives: stage1_complete → Save to state
    ↓
(Repeat for Stage 2 and Stage 3)
    ↓
Frontend receives: complete → Done
```

## Benefits of WebSocket vs SSE

1. **Bi-directional**: Can send stop_generation command
2. **More Efficient**: Single persistent connection
3. **Real-time**: True token-by-token streaming
4. **Better Error Handling**: Connection status tracking
5. **Offline Queue**: Messages queued when disconnected

## Testing

1. **Start Backend**:
   ```bash
   cd /home/user/llm-council
   uv run python -m backend.main
   ```

2. **Start Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

3. **Test WebSocket**:
   - Create new conversation
   - Send message
   - Watch tokens stream in real-time
   - Check browser console for WebSocket logs

## Fallback Strategy

Keep SSE support for now:
- Try WebSocket first
- Fall back to SSE if WebSocket unavailable
- Graceful degradation

```jsx
const useStreamingMethod = () => {
  const [method, setMethod] = useState('websocket');

  useEffect(() => {
    // Test WebSocket availability
    const testWs = new WebSocket(WS_URL + '/ws/test');
    testWs.onerror = () => setMethod('sse');
    testWs.onopen = () => testWs.close();
  }, []);

  return method;
};
```

## Next Steps

1. Complete App.jsx integration
2. Add streaming to Stage2 and Stage3 components
3. Implement stop button functionality
4. Add connection status indicator
5. Handle reconnection scenarios
6. Add E2E tests for streaming

## Notes

- WebSocket URL configured via `VITE_WS_URL` env var
- Default: `ws://localhost:8001`
- Auto-reconnect with exponential backoff
- Message queue for offline resilience
- Ping/pong keepalive every 30 seconds
