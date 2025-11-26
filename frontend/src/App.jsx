import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import StrategySelector from './components/StrategySelector';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import StrategyWorkbench from './components/StrategyWorkbench';
import { api } from './api';
import './App.css';

function App() {
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedStrategy, setSelectedStrategy] = useState('simple');
  const [showAnalytics, setShowAnalytics] = useState(false);
  const [strategyOptions, setStrategyOptions] = useState([]);
  const [showWorkbench, setShowWorkbench] = useState(false);
  const [councilOptions, setCouncilOptions] = useState([]);
  const [selectedCouncil, setSelectedCouncil] = useState('full');
  const [strategyConfigs, setStrategyConfigs] = useState({ multi_round: { rounds: 2 } });
  const [shouldAutoLoad, setShouldAutoLoad] = useState(true);

  const fallbackCouncilOptions = [
    {
      id: 'full',
      name: 'Full Council',
      chairman: 'google/gemini-3-pro-preview',
      models: [
        'openai/gpt-5.1',
        'google/gemini-3-pro-preview',
        'anthropic/claude-sonnet-4.5',
        'x-ai/grok-4',
      ],
    },
    {
      id: 'low_cost',
      name: 'Budget Council',
      chairman: 'anthropic/claude-haiku-4.5',
      models: [
        'anthropic/claude-haiku-4.5',
        'google/gemini-2.5-flash-lite',
        'openai/gpt-5-mini',
        'openai/gpt-5-nano',
      ],
    },
    {
      id: 'hybrid',
      name: 'Hybrid Council',
      chairman: 'google/gemini-3-pro-preview',
      models: [
        'google/gemini-3-pro-preview',
        'anthropic/claude-haiku-4.5',
        'google/gemini-2.5-flash-lite',
        'openai/gpt-5-mini',
      ],
    },
  ];

  useEffect(() => {
    loadConversations();
    loadStrategies();
    loadCouncils();
  }, []);

  useEffect(() => {
    if (currentConversationId && shouldAutoLoad) {
      loadConversation(currentConversationId);
    }
  }, [currentConversationId, shouldAutoLoad]);

  const loadConversations = async () => {
    try {
      const convs = await api.listConversations();
      setConversations(convs);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  };

  const loadConversation = async (id) => {
    try {
      const conv = await api.getConversation(id);
      setCurrentConversation(conv);
    } catch (error) {
      console.error('Failed to load conversation:', error);
    }
  };

  const loadStrategies = async () => {
    try {
      const response = await api.listStrategies();
      const entries = Object.entries(response).map(([id, meta]) => ({
        id,
        name: meta.name || id,
        description: meta.description || '',
      }));
      setStrategyOptions(entries);
    } catch (error) {
      console.error('Failed to load strategies:', error);
    }
  };

  const loadCouncils = async () => {
    try {
      const response = await api.listCouncils();
      const entries = Object.entries(response).map(([id, meta]) => ({
        id,
        name: meta.name || id,
        description: meta.description || '',
        models: meta.models || [],
        chairman: meta.chairman,
      }));
      setCouncilOptions(entries);
      if (!entries.find((c) => c.id === selectedCouncil) && entries.length) {
        setSelectedCouncil(entries[0].id);
      }
    } catch (error) {
      console.error('Failed to load councils:', error);
    }
  };

  const handleNewConversation = async () => {
    try {
      const newConv = await api.createConversation();
      setConversations([
        { id: newConv.id, created_at: newConv.created_at, message_count: 0 },
        ...conversations,
      ]);
      setCurrentConversationId(newConv.id);
      setCurrentConversation(null);
    } catch (error) {
      console.error('Failed to create conversation:', error);
    }
  };

  const handleSelectConversation = (id) => {
    setShouldAutoLoad(true);
    setCurrentConversationId(id);
  };

  const ensureConversationContext = async () => {
    if (currentConversationId) {
      return currentConversationId;
    }

    const newConv = await api.createConversation();
    setConversations((prev) => [
      { id: newConv.id, created_at: newConv.created_at, message_count: 0 },
      ...prev,
    ]);
    setCurrentConversationId(newConv.id);
    setCurrentConversation(newConv);
    return newConv.id;
  };

  const availableCouncils = councilOptions.length ? councilOptions : fallbackCouncilOptions;
  const activeCouncil = availableCouncils.find((c) => c.id === selectedCouncil) || availableCouncils[0];
  const multiRoundRounds = strategyConfigs.multi_round?.rounds ?? 2;

  const handleRoundsChange = (value) => {
    const sanitized = Math.min(5, Math.max(2, Number(value) || 2));
    setStrategyConfigs((prev) => ({
      ...prev,
      multi_round: { rounds: sanitized },
    }));
  };

  const handleSendMessage = async (content, strategyOverride) => {
    const conversationId = await ensureConversationContext();
    setShouldAutoLoad(false);

    if (!conversationId) return;

    const strategyToUse = strategyOverride || selectedStrategy || 'simple';
    if (strategyOverride && strategyOverride !== selectedStrategy) {
      setSelectedStrategy(strategyOverride);
    }

    setIsLoading(true);
    try {
      const userMessage = { role: 'user', content };
      setCurrentConversation((prev) => {
        const base = prev && prev.id === conversationId ? prev : { id: conversationId, messages: [] };
        return {
          ...base,
          messages: [...(base.messages || []), userMessage],
        };
      });

      const configToUse = strategyConfigs[strategyToUse] || {};
      const supportsStreaming = strategyToUse === 'simple';
      const assistantMessage = {
        role: 'assistant',
        stage1: null,
        stage2: null,
        stage3: null,
        metadata: null,
        loading: {
          stage1: !supportsStreaming,
          stage2: !supportsStreaming,
          stage3: !supportsStreaming,
        },
      };

      setCurrentConversation((prev) => {
        const base = prev && prev.id === conversationId ? prev : { id: conversationId, messages: [userMessage] };
        return {
          ...base,
          messages: [...(base.messages || []), assistantMessage],
        };
      });

      if (supportsStreaming) {
        await api.sendMessageStream(conversationId, content, (eventType, event) => {
          switch (eventType) {
            case 'stage1_start':
              setCurrentConversation((prev) => {
                if (!prev || prev.id !== conversationId || !prev.messages?.length) {
                  return prev;
                }
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                lastMsg.loading.stage1 = true;
                return { ...prev, messages };
              });
              break;

            case 'stage1_complete':
              setCurrentConversation((prev) => {
                if (!prev || prev.id !== conversationId || !prev.messages?.length) {
                  return prev;
                }
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                lastMsg.stage1 = event.data;
                lastMsg.loading.stage1 = false;
                return { ...prev, messages };
              });
              break;

            case 'stage2_start':
              setCurrentConversation((prev) => {
                if (!prev || prev.id !== conversationId || !prev.messages?.length) {
                  return prev;
                }
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                lastMsg.loading.stage2 = true;
                return { ...prev, messages };
              });
              break;

            case 'stage2_complete':
              setCurrentConversation((prev) => {
                if (!prev || prev.id !== conversationId || !prev.messages?.length) {
                  return prev;
                }
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                lastMsg.stage2 = event.data;
                lastMsg.metadata = event.metadata;
                lastMsg.loading.stage2 = false;
                return { ...prev, messages };
              });
              break;

            case 'stage3_start':
              setCurrentConversation((prev) => {
                if (!prev || prev.id !== conversationId || !prev.messages?.length) {
                  return prev;
                }
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                lastMsg.loading.stage3 = true;
                return { ...prev, messages };
              });
              break;

            case 'stage3_complete':
              setCurrentConversation((prev) => {
                if (!prev || prev.id !== conversationId || !prev.messages?.length) {
                  return prev;
                }
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                lastMsg.stage3 = event.data;
                lastMsg.loading.stage3 = false;
                return { ...prev, messages };
              });
              break;

            case 'title_complete':
              loadConversations();
              break;

            case 'complete':
              loadConversations();
              setIsLoading(false);
              setShouldAutoLoad(true);
              break;

            case 'error':
              console.error('Stream error:', event.message);
              setIsLoading(false);
              setShouldAutoLoad(true);
              break;

            default:
              console.log('Unknown event type:', eventType);
          }
        }, strategyToUse, configToUse, selectedCouncil);
      } else {
        const result = await api.sendMessage(
          conversationId,
          content,
          strategyToUse,
          configToUse,
          selectedCouncil,
        );

        setCurrentConversation((prev) => {
          if (!prev || prev.id !== conversationId || !prev.messages?.length) {
            return prev;
          }
          const messages = [...prev.messages];
          const lastMsg = messages[messages.length - 1];
          lastMsg.stage1 = result.stage1;
          lastMsg.stage2 = result.stage2;
          lastMsg.stage3 = result.stage3;
          lastMsg.metadata = result.metadata;
          lastMsg.loading = {
            stage1: false,
            stage2: false,
            stage3: false,
          };
          return { ...prev, messages };
        });

        loadConversations();
        setIsLoading(false);
        setShouldAutoLoad(true);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      setCurrentConversation((prev) => {
        if (!prev || prev.id !== conversationId || !prev.messages?.length) {
          return prev;
        }
        return {
          ...prev,
          messages: prev.messages.slice(0, -2),
        };
      });
      setIsLoading(false);
      setShouldAutoLoad(true);
    }
  };

  return (
    <div className="app">
      <Sidebar
        conversations={conversations}
        currentConversationId={currentConversationId}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
        onShowAnalytics={() => setShowAnalytics(true)}
      />
      <div className="main-content">
        <div className="control-bar">
          <StrategySelector
            selectedStrategy={selectedStrategy}
            onStrategyChange={setSelectedStrategy}
            strategies={strategyOptions}
          />
          <div className="council-selector">
            <label htmlFor="council-select">Model preset</label>
            <select
              id="council-select"
              value={selectedCouncil}
              onChange={(e) => setSelectedCouncil(e.target.value)}
            >
              {availableCouncils.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.name}
                </option>
              ))}
            </select>
            {activeCouncil && activeCouncil.models && activeCouncil.models.length > 0 && (
              <div className="council-preview">
                <span>Chairman: {activeCouncil.chairman}</span>
                <span>Models: {activeCouncil.models.join(', ')}</span>
              </div>
            )}
          </div>
          {selectedStrategy === 'multi_round' && (
            <div className="round-selector">
              <label htmlFor="round-input">Rounds</label>
              <input
                id="round-input"
                type="number"
                min={2}
                max={5}
                value={multiRoundRounds}
                onChange={(e) => handleRoundsChange(e.target.value)}
              />
            </div>
          )}
          <button
            className="workbench-toggle"
            onClick={() => setShowWorkbench(true)}
          >
            Strategy Workbench
          </button>
        </div>
        <ChatInterface
          conversation={currentConversation}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          selectedStrategy={selectedStrategy}
          onStrategyChange={setSelectedStrategy}
          strategyOptions={strategyOptions}
          selectedCouncil={selectedCouncil}
          onCouncilChange={setSelectedCouncil}
          councilOptions={councilOptions}
        />
      </div>

      {showAnalytics && (
        <AnalyticsDashboard onClose={() => setShowAnalytics(false)} />
      )}
      {showWorkbench && (
        <StrategyWorkbench
          isOpen={showWorkbench}
          onClose={() => setShowWorkbench(false)}
          strategies={strategyOptions}
          selectedCouncil={selectedCouncil}
        />
      )}
    </div>
  );
}

export default App;
