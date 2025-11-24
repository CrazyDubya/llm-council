# Phase 1, Week 1-2: Implementation Task Breakdown

## Week 1: Day-by-Day Tasks

### Day 1: Streaming Backend Foundation
**Goal**: Set up WebSocket infrastructure and streaming foundation

**Tasks**:
- [ ] Create `backend/websocket.py` - WebSocket connection manager
  - ConnectionManager class
  - Active connections tracking
  - Broadcast functionality
  - Connection lifecycle management
- [ ] Create `backend/streaming.py` - Token streaming logic
  - Stream tokens from OpenRouter API
  - Handle SSE (Server-Sent Events) format
  - Error handling for stream interruptions
- [ ] Update `backend/openrouter.py` - Add streaming support
  - Add `stream=True` parameter to query functions
  - Handle streaming responses
  - Token-by-token yield
- [ ] Create basic WebSocket endpoint in `backend/main.py`
  - `/ws/{conversation_id}` endpoint
  - Test connection establishment
  - Basic echo test

**Acceptance Criteria**:
- WebSocket connections establish successfully
- Can stream dummy tokens to frontend
- No connection leaks (proper cleanup)

---

### Day 2: Streaming Backend Integration
**Goal**: Integrate streaming with council strategies

**Tasks**:
- [ ] Modify `backend/strategies/simple_ranking.py` for streaming
  - Yield tokens during Stage 1 responses
  - Send stage markers (STAGE1_START, STAGE1_MODEL_X, etc.)
  - Stream rankings in Stage 2
- [ ] Create streaming event types
  - `backend/streaming_events.py` - Event type definitions
  - JSON schema for each event type
  - Event serialization/deserialization
- [ ] Test streaming with real OpenRouter models
  - End-to-end test with GPT-4
  - Handle rate limiting
  - Measure latency improvements

**Acceptance Criteria**:
- Stage 1 responses stream token-by-token
- Frontend receives structured events
- Latency to first token < 500ms

---

### Day 3: Frontend Streaming UI
**Goal**: Build React components to display streaming responses

**Tasks**:
- [ ] Create `frontend/src/hooks/useWebSocket.js`
  - WebSocket connection hook
  - Auto-reconnect logic
  - Message queue for offline buffering
- [ ] Update `frontend/src/components/ChatInterface.jsx`
  - Integrate WebSocket hook
  - Display streaming indicator
  - "Stop generation" button
- [ ] Create `frontend/src/components/StreamingMessage.jsx`
  - Component for streaming text display
  - Cursor animation
  - Token accumulation logic
- [ ] Update Stage1 component for streaming
  - Real-time tab updates
  - Loading states per model
  - Token count display

**Acceptance Criteria**:
- Tokens appear in real-time in UI
- Smooth rendering (no jank)
- Stop button works correctly

---

### Day 4: Caching Layer
**Goal**: Implement response caching to reduce costs and latency

**Tasks**:
- [ ] Create `backend/cache.py`
  - LRU cache implementation (or use functools.lru_cache)
  - Redis-ready interface (async)
  - Cache key generation (hash query + models + strategy)
  - TTL support (24 hours default)
- [ ] Cache invalidation strategies
  - Time-based (TTL)
  - Manual invalidation API
  - Cache warming for common queries
- [ ] Integrate caching into strategies
  - Check cache before querying models
  - Store results after successful completion
  - Cache hit/miss logging
- [ ] Create cache analytics endpoint
  - `GET /api/cache/stats` - hit rate, size, etc.
  - Cache management UI preparation

**Acceptance Criteria**:
- Cache hit rate > 30% after initial usage
- Cache stores full conversation context
- No stale data issues

---

### Day 5: Meta-Strategy Foundation
**Goal**: Build the meta-strategy layer for composition

**Tasks**:
- [ ] Create `backend/strategies/meta.py`
  - MetaStrategy abstract base class
  - Execute method with sub-strategy support
  - Result passing between strategies
- [ ] Create `backend/strategies/composition.py`
  - SequentialStrategy (run strategies in order)
  - ParallelStrategy (run simultaneously, aggregate)
  - Strategy DAG executor (directed acyclic graph)
- [ ] Define strategy pipeline DSL
  - JSON schema for strategy compositions
  - `compositions/` directory for saved compositions
  - Example: multi_round_then_weighted.json
- [ ] Create composition validator
  - Detect cycles in DAG
  - Validate strategy compatibility
  - Cost estimation for compositions

**Acceptance Criteria**:
- Can run 2+ strategies sequentially
- Results properly passed between stages
- DAG validation catches cycles

---

### Day 6: Meta-Strategy Implementation
**Goal**: Implement specific composition patterns

**Tasks**:
- [ ] Implement SequentialStrategy
  - Pass stage1 results to next strategy
  - Aggregate final outputs
  - Handle failures in pipeline
- [ ] Implement ParallelStrategy
  - Run multiple strategies concurrently
  - Aggregate rankings
  - Compare outputs side-by-side
- [ ] Conditional branching logic
  - Quality gates: check confidence/agreement
  - Branch to different strategy based on intermediate results
  - Fallback strategies on failure
- [ ] Create 3 example compositions
  - simple_then_weighted.json
  - multi_round_parallel_compare.json
  - adaptive_fallback.json

**Acceptance Criteria**:
- 3 compositions working end-to-end
- Conditional branching functional
- Proper error handling in pipelines

---

### Day 7: Agent Identity System
**Goal**: Create persistent agent identities

**Tasks**:
- [ ] Create `backend/agents/identity.py`
  - Agent class (id, model, metadata)
  - Agent persistence (JSON files in data/agents/)
  - Agent CRUD operations
- [ ] Create `backend/agents/reputation.py`
  - Win tracking per agent
  - Average ranking calculation
  - Per-topic performance tracking
- [ ] Integrate agents with strategies
  - Replace model strings with Agent objects
  - Track which agent gave which response
  - Agent-aware caching
- [ ] Create agent profile API
  - `GET /api/agents` - list all agents
  - `GET /api/agents/{id}` - agent details
  - `GET /api/agents/{id}/stats` - performance stats

**Acceptance Criteria**:
- Agents persist across restarts
- Win rates calculated correctly
- API returns agent data

---

### Day 8: Adversarial Review Strategy
**Goal**: Implement adversarial review deliberation

**Tasks**:
- [ ] Create `backend/strategies/adversarial_review.py`
  - Split council into proposers and critics
  - Proposer stage: generate initial responses
  - Critic stage: find flaws in proposals
  - Defense stage: proposers defend their answers
  - Chairman synthesis weighs attack/defense
- [ ] Create adversarial prompts
  - Critic prompt: "Find flaws in this response..."
  - Defense prompt: "Defend your answer against..."
  - Balance prompt engineering
- [ ] Test adversarial strategy
  - Compare vs simple ranking on benchmark
  - Measure improvement in quality
  - Track debate dynamics

**Acceptance Criteria**:
- Adversarial strategy executes successfully
- Critics find meaningful flaws
- Defense improves answer quality

---

### Day 9: Agent UI & Polish
**Goal**: Build UI for agents and polish Week 1 work

**Tasks**:
- [ ] Create `frontend/src/components/AgentProfile.jsx`
  - Display agent avatar/icon
  - Show expertise tags
  - Performance stats visualization
  - "About this agent" tooltip
- [ ] Update Stage1 tabs with agent info
  - Agent name/icon in tab header
  - Win rate badge
  - Click for full profile
- [ ] Create `frontend/src/components/StrategySelector.jsx`
  - Dropdown for strategy selection
  - Include composed strategies
  - Strategy description tooltip
  - Performance indicators
- [ ] UI polish
  - Loading states for streaming
  - Error messages
  - Accessibility (ARIA labels)
  - Mobile responsiveness check

**Acceptance Criteria**:
- Agent profiles display correctly
- Strategy selector intuitive
- No UI bugs or glitches

---

### Day 10: Evolution Bootstrap & Testing
**Goal**: Set up experimentation framework and comprehensive testing

**Tasks**:
- [ ] Create `backend/evolution/experiments.py`
  - A/B test runner
  - Experiment configuration (JSON schema)
  - Statistical significance testing (t-test)
  - Track experiment results in data/experiments/
- [ ] Performance logging infrastructure
  - `backend/monitoring/performance.py`
  - Detailed timing for each stage
  - Success/failure rates
  - Cost tracking per query
- [ ] Create comprehensive tests
  - `tests/test_streaming.py`
  - `tests/test_cache.py`
  - `tests/test_meta_strategy.py`
  - `tests/test_agents.py`
  - `tests/test_adversarial.py`
- [ ] Baseline metrics collection
  - Run benchmark queries
  - Capture current performance
  - Establish improvement targets
  - Document in BASELINE_METRICS.md

**Acceptance Criteria**:
- A/B tests can be configured and run
- All tests passing (>80% coverage)
- Baseline metrics documented

---

## Week 2: Days 11-14 (Code Review Prep + Polish)

### Day 11-12: Integration & Bug Fixes
- [ ] End-to-end integration testing
- [ ] Fix bugs discovered in Week 1
- [ ] Performance optimization
- [ ] Documentation updates

### Day 13-14: Code Review Preparation
- [ ] Code cleanup and refactoring
- [ ] Add comprehensive docstrings
- [ ] Update API documentation
- [ ] Create architecture diagrams
- [ ] Prepare for Week 3 code review

---

## GitHub Project Structure

### Columns
1. **Backlog** - All planned tasks
2. **Ready** - Tasks ready to start
3. **In Progress** - Currently working on
4. **In Review** - Code review needed
5. **Testing** - QA and testing
6. **Done** - Completed

### Labels
- `phase-1` - Phase 1 tasks
- `path-1` - Path 1 (Polish & Performance)
- `path-2` - Path 2 (Extended Capabilities)
- `path-3` - Path 3 (Cognitive Architecture)
- `path-4` - Path 4 (Multi-Dimensional)
- `path-5` - Path 5 (Emergent Intelligence)
- `backend` - Backend work
- `frontend` - Frontend work
- `testing` - Testing tasks
- `documentation` - Docs
- `priority-high` - High priority
- `priority-medium` - Medium priority
- `priority-low` - Low priority

---

## Quick Start Commands

```bash
# Start backend with streaming
cd /home/user/llm-council
uv run python -m backend.main

# Start frontend
cd frontend
npm run dev

# Run tests
uv run pytest tests/ -v

# Check cache stats
curl http://localhost:8001/api/cache/stats
```

---

**Document Version**: 1.0
**Created**: 2025-11-24
**Status**: Ready for Implementation
