# CLAUDE.md - Technical Notes for LLM Council v0.2

This file contains technical details, architectural decisions, and important implementation notes for future development sessions.

## Project Overview

LLM Council v0.2 is an **ensemble strategy playground** where multiple LLMs collaboratively answer user questions through various deliberation strategies. The key innovations include:

1. **Pluggable Strategy Pattern**: Multiple ensemble approaches (simple, multi-round, reasoning-aware, weighted)
2. **Analytics-Driven Optimization**: Performance tracking with historical data analysis
3. **Intelligent Strategy Recommendation**: AI-powered strategy selection based on query classification
4. **Reasoning Model Support**: Special handling for o1, DeepSeek-R1, and other models with explicit reasoning traces

## Architecture Overview

### Core Concept: Strategy Pattern

All ensemble strategies extend the abstract `EnsembleStrategy` base class:

```python
class EnsembleStrategy(ABC):
    async def execute(query, models, chairman) -> Dict[str, Any]
    def get_name() -> str
    def get_description() -> str
    def get_config_schema() -> Dict[str, Any]
```

This allows easy experimentation with different deliberation approaches while maintaining a consistent API.

### Available Strategies

1. **SimpleRankingStrategy** (`simple`): Original v0.1 approach
   - Stage 1: Collect responses
   - Stage 2: Anonymous peer ranking
   - Stage 3: Chairman synthesis

2. **MultiRoundStrategy** (`multi_round`): Iterative refinement
   - Round 1: Initial responses + rankings
   - Round 2+: Models see top responses, critique, and revise
   - Tracks evolution metrics (rank changes, improvements)
   - Configurable rounds (default: 2) and top_n (default: 2)

3. **ReasoningAwareStrategy** (`reasoning_aware`): For o1/DeepSeek models
   - Dual ranking: reasoning quality (40%) + answer quality (60%)
   - Extracts `reasoning_details` from OpenRouter API
   - Falls back to answer-only ranking if no reasoning available
   - Evaluates logical coherence, analysis depth, argumentation rigor

4. **WeightedVotingStrategy** (`weighted_voting`): Analytics-driven
   - Applies performance-based weights to model votes
   - Higher win rate = more influence on final ranking
   - Uses historical data from AnalyticsEngine
   - Configurable min_weight and weighting method

## Backend Structure (`backend/`)

### Core Modules

**`config.py`**
- `COUNCIL_MODELS`: List of OpenRouter model identifiers
- `CHAIRMAN_MODEL`: Model for final synthesis
- `OPENROUTER_API_KEY` from `.env`
- Backend runs on **port 8001**

**`openrouter.py`**
- `query_model()`: Single async model query
- `query_models_parallel()`: Parallel queries via `asyncio.gather()`
- Returns `{'content': str, 'reasoning_details': Optional[str]}`
- Graceful degradation on failure

**`council.py`** - Legacy v0.1 functions (kept for compatibility)
- `generate_conversation_title()`: Uses LLM to create conversation titles

### Strategy System

**`strategies/base.py`**
- Abstract base class defining strategy interface
- All strategies must implement `execute()`, `get_name()`, `get_description()`

**`strategies/__init__.py`**
- Strategy registry: `_STRATEGIES` dict mapping names to classes
- `get_strategy(name, config)`: Factory function
- `list_strategies()`: Returns all available strategies with descriptions
- `register_strategy(name, cls)`: Allows dynamic registration

**`strategies/simple_ranking.py`**
- Refactored v0.1 logic into strategy pattern
- 3-stage process: responses → anonymous ranking → synthesis
- Helper methods: `_stage1_collect_responses()`, `_stage2_collect_rankings()`, `_stage3_synthesize_final()`

**`strategies/multi_round.py`**
- Implements iterative deliberation
- Configuration: `rounds` (default 2), `show_top_n` (default 2)
- Evolution tracking: rank changes, improvements/declines
- Metadata includes round-by-round data and evolution metrics

**`strategies/reasoning_aware.py`**
- Specialized for models with reasoning traces
- Configuration: `reasoning_weight` (default 0.4), `answer_weight` (default 0.6)
- Two parallel ranking stages: reasoning quality + answer quality
- Combined weighted scoring for final ranking

**`strategies/weighted_voting.py`**
- Uses AnalyticsEngine for performance-based weighting
- Configuration: `min_weight` (default 0.1), `use_win_rate` (default true)
- Calculates weighted average ranks
- Metadata includes model_weights for transparency

**`strategies/recommender.py`**
- Combines QueryClassifier + AnalyticsEngine
- Category-based preference ordering
- Performance-weighted scoring (70% performance, 30% category preference)
- Returns recommendation with confidence, explanation, and fallback options

### Analytics System

**`analytics.py`**
- `AnalyticsEngine` class for performance tracking
- Scans all conversations to compute:
  - Model performance: win_rate, avg_rank, top_3_rate
  - Strategy performance: usage count, average feedback
  - Per-strategy model breakdowns
- Methods:
  - `compute_all_analytics()`: Full recomputation
  - `get_model_performance(model)`: Specific model metrics
  - `get_strategy_performance(strategy)`: Strategy metrics
  - `get_model_leaderboard(limit)`: Top models by win rate
- Saves to `data/analytics/summary.json`

**`query_classifier.py`**
- Keyword-based query categorization
- Categories: technical, reasoning, analytical, creative, factual
- Regex pattern matching with weighted scoring
- Returns category, confidence, and matching indicators
- `get_recommended_strategy(query)`: Basic recommendation logic

### Storage & API

**`storage.py`**
- JSON-based conversation storage in `data/conversations/`
- Extended schema:
  - Conversations: `{id, created_at, title, messages[]}`
  - Messages: `{role, content/stage1/stage2/stage3, timestamp, user_feedback, metadata}`
  - Metadata: strategy name, label_to_model, aggregate_rankings, evolution metrics
- `update_message_feedback(conv_id, msg_idx, feedback)`: User thumbs up/down
- Feedback values: -1 (dislike), 0 (neutral), 1 (like), None

**`main.py`**
- FastAPI app with CORS for localhost:5173, localhost:3000
- Endpoints:
  - `GET /api/strategies`: List all strategies
  - `POST /api/strategies/recommend`: Get strategy recommendation for query
  - `POST /api/strategies/compare`: A/B test multiple strategies
  - `POST /api/conversations/{id}/message`: Send message (non-streaming)
  - `POST /api/conversations/{id}/message/stream`: Send message (streaming, simple strategy only)
  - `POST /api/conversations/{id}/messages/{idx}/feedback`: Submit feedback
  - `GET /api/analytics/*`: Various analytics endpoints
- Analytics engine and recommender initialized globally

## Frontend Structure (`frontend/src/`)

### Core Components

**`App.jsx`**
- Main orchestration: conversations, current conversation, strategy selection
- State: `selectedStrategy`, `showAnalytics`, `currentConversationId`, etc.
- Passes strategy state to ChatInterface
- Renders AnalyticsDashboard modal

**`components/ChatInterface.jsx`**
- Multi-message conversation support (input always visible)
- Detects strategy type from message metadata
- Conditionally renders MultiRoundView vs Stage1/Stage2 components
- Integrates StrategyRecommendation component
- Passes conversationId and messageIndex to Stage3 for feedback

**`components/StrategySelector.jsx`**
- Dropdown for strategy selection
- Options: Simple, Multi-Round, Reasoning-Aware, Weighted Voting
- Can be extended to fetch from `/api/strategies` dynamically

**`components/StrategyRecommendation.jsx`** ⭐ NEW
- AI-powered strategy suggestion card
- Appears when user types 20+ character query
- Calls `/api/strategies/recommend` API
- Shows: strategy, confidence, explanation, category, fallback options
- Beautiful gradient UI with accept/dismiss actions
- Auto-dismissable

### Stage Display Components

**`components/Stage1.jsx`**
- Tab view of individual model responses
- ReactMarkdown rendering with markdown-content wrapper

**`components/Stage2.jsx`**
- Tab view showing RAW evaluation text from each model
- De-anonymization on client side (models see anonymous labels)
- Shows "Extracted Ranking" for validation
- Aggregate rankings table with average positions

**`components/Stage3.jsx`**
- Final synthesized answer from chairman
- Green-tinted background (#f0fff0)
- Thumbs up/down feedback buttons ⭐ NEW
- Calls `/api/conversations/{id}/messages/{idx}/feedback`

**`components/MultiRoundView.jsx`** ⭐ NEW
- Round-by-round tabs for multi-round strategy
- Evolution metrics with ⬆️⬇️ indicators
- Shows top responses presented to models
- Per-round model responses and rankings

**`components/AnalyticsDashboard.jsx`** ⭐ NEW
- Modal overlay with comprehensive analytics
- Summary cards: conversations, queries, strategies, models
- Model leaderboard with 🥇🥈🥉 medals
- Strategy performance cards
- Refresh button to recompute analytics

### Styling

- Light mode theme
- Primary color: #4a90e2 (blue)
- Global markdown styling: `.markdown-content` class
- Strategy recommendation: Purple gradient (#667eea to #764ba2)
- Smooth animations and transitions

## Key Design Decisions

### Strategy Pattern Benefits
- Easy to add new ensemble approaches
- Consistent API for all strategies
- Configuration schema per strategy
- Independent testing and optimization

### Analytics Integration
- Performance tracking enables data-driven decisions
- Weighted voting uses historical win rates
- Strategy recommendations improve over time
- User feedback creates reinforcement learning loop

### Query Classification
- Simple keyword-based approach (no ML model needed)
- 5 categories with distinct strategy preferences
- Confidence scoring based on match strength
- Graceful degradation when confidence is low

### Multi-Round Deliberation
- Prevents stagnation in simple ranking
- Allows models to learn from peers
- Evolution tracking shows improvement/decline
- Configurable rounds prevent excessive API costs

### Reasoning-Aware Evaluation
- Recognizes that reasoning quality ≠ answer quality
- Dual ranking captures both dimensions
- Weighted combination (40/60 default) is tunable
- Falls back gracefully for non-reasoning models

## Important Implementation Details

### Strategy Registration
Strategies are registered in `backend/strategies/__init__.py`:
```python
_STRATEGIES = {
    'simple': SimpleRankingStrategy,
    'multi_round': MultiRoundStrategy,
    'reasoning_aware': ReasoningAwareStrategy,
    'weighted_voting': WeightedVotingStrategy,
}
```

### Analytics Injection
WeightedVotingStrategy needs AnalyticsEngine:
```python
if request.strategy == 'weighted_voting':
    config['analytics_engine'] = analytics
strategy = get_strategy(request.strategy, config=config)
```

### Relative Imports
All backend modules use relative imports:
```python
from .config import COUNCIL_MODELS
from ..openrouter import query_model
```

### Port Configuration
- Backend: 8001
- Frontend: 5173 (Vite default)

### Metadata Persistence
- Metadata IS NOW persisted to storage (v0.2 change)
- Includes strategy name, rankings, evolution metrics
- Enables analytics computation across sessions

## Common Gotchas

1. **Module Import Errors**: Run as `python -m backend.main` from project root
2. **CORS Issues**: Frontend must match allowed origins in `main.py`
3. **Ranking Parse Failures**: Fallback regex extracts "Response X" patterns
4. **Missing Analytics**: First few queries won't have enough data for weighted voting
5. **Streaming Limitation**: Only 'simple' strategy supports streaming currently
6. **Strategy Config**: Some strategies require specific config (e.g., analytics_engine for weighted_voting)

## Data Flow Summary

### Simple Strategy
```
User Query → Strategy Selection
    ↓
Stage 1: Parallel queries → [individual responses]
    ↓
Stage 2: Anonymize → Parallel ranking queries → [evaluations + parsed rankings]
    ↓
Aggregate Rankings → [sorted by avg position]
    ↓
Stage 3: Chairman synthesis with full context
    ↓
Return: {stage1, stage2, stage3, metadata} → Save to storage
    ↓
Frontend: Display with tabs + validation UI
    ↓
User Feedback → Analytics Engine → Weighted Voting / Recommendations
```

### Multi-Round Strategy
```
User Query → Multi-Round Strategy
    ↓
Round 1: Responses → Rankings → Identify top N
    ↓
Round 2: Show top N + critiques → Models revise → Rankings
    ↓
Evolution Tracking: Calculate rank changes
    ↓
Stage 3: Chairman synthesis
    ↓
Return with round-by-round data → Frontend renders MultiRoundView
```

### Reasoning-Aware Strategy
```
User Query → Reasoning-Aware Strategy
    ↓
Stage 1: Responses + Extract reasoning_details
    ↓
Stage 2a: Rank reasoning quality (logic, depth, rigor)
Stage 2b: Rank answer quality (accuracy, completeness)
    ↓
Combine: 40% reasoning + 60% answer (configurable)
    ↓
Stage 3: Chairman synthesis with reasoning context
```

## API Reference

### Strategy Endpoints

**GET /api/strategies**
- Returns: Dict of strategy names to {name, description}

**POST /api/strategies/recommend**
- Body: `{query: str}`
- Returns: `{strategy, confidence, explanation, fallback_options, query_category, performance_data}`

**POST /api/strategies/compare**
- Body: `{query: str, strategies: List[str], strategy_configs: Dict}`
- Returns: `{query, comparisons: [{strategy, success, result/error}], timestamp}`

### Analytics Endpoints

**GET /api/analytics/summary**
- Returns full analytics summary
- Includes total_conversations, total_queries, strategy_stats, model_stats

**GET /api/analytics/leaderboard**
- Returns top models by win rate
- Includes win_rate, wins, total_evaluations, avg_rank, top_3_rate

**GET /api/analytics/models/{model}**
- Returns specific model performance metrics

**GET /api/analytics/strategies/{strategy}**
- Returns specific strategy metrics

### Feedback Endpoint

**POST /api/conversations/{id}/messages/{index}/feedback**
- Body: `{feedback: int}` (-1, 0, 1)
- Updates message feedback and recomputes analytics

## Testing Notes

### Manual Testing Checklist
1. Test each strategy independently
2. Verify strategy recommendation with different query types
3. Check analytics dashboard updates after feedback
4. Test multi-round evolution tracking
5. Verify reasoning extraction for o1/DeepSeek models
6. Test weighted voting with/without analytics data
7. Verify A/B comparison endpoint

### API Testing
Use `test_openrouter.py` for OpenRouter connectivity.

For strategy testing:
```python
from backend.strategies import get_strategy
strategy = get_strategy('multi_round', config={'rounds': 3})
result = await strategy.execute(query, models, chairman)
```

## Future Enhancements

### Completed in v0.2 ✅
- ~~Configurable strategies~~ ✅
- ~~Model performance analytics~~ ✅
- ~~Support for reasoning models~~ ✅
- ~~Strategy recommendation system~~ ✅

### Potential v0.3 Features
- Streaming support for all strategies
- Custom model selection per conversation
- Export conversations to markdown/PDF
- Advanced analytics visualizations (charts, trends)
- Strategy A/B testing UI component
- Fine-tuned query classifier (ML-based)
- Caching layer for repeated queries
- Rate limiting and cost tracking
- Multi-tenant support
- API authentication

## Architecture Comparison

### v0.1 (Simple Council)
- Single hardcoded 3-stage approach
- No analytics or tracking
- Basic UI with tabs
- Metadata not persisted

### v0.2 (Ensemble Strategy Playground)
- 4 pluggable strategies
- Full analytics pipeline
- AI-powered strategy recommendations
- Rich UI with multi-round view, feedback, analytics dashboard
- Metadata persisted for historical analysis
- Query classification and performance tracking
- A/B testing framework

The v0.2 architecture transforms LLM Council from a proof-of-concept into a research platform for exploring ensemble deliberation strategies.
