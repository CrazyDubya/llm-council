# LLM Council v0.2 Implementation Plan

## Vision
Transform LLM Council into a strategy playground that combines multi-round deliberation, reasoning-aware evaluation, and performance analytics into a flexible, data-driven ensemble system.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    User Query                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Strategy Selector (manual or analytics-suggested)      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              EnsembleStrategy (abstract)                │
│  ┌──────────────────────────────────────────────────┐   │
│  │ - execute(query, models) → result                │   │
│  │ - get_metadata() → dict                          │   │
│  └──────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┬────────────────┐
        │            │            │                │
        ▼            ▼            ▼                ▼
┌─────────────┐ ┌─────────┐ ┌──────────┐ ┌─────────────┐
│   Simple    │ │  Multi  │ │Reasoning │ │  Weighted   │
│  Ranking    │ │  Round  │ │  Aware   │ │   Voting    │
└─────────────┘ └─────────┘ └──────────┘ └─────────────┘
        │            │            │                │
        └────────────┼────────────┴────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Analytics Layer (cross-cutting)            │
│  - Track: strategy, models, rankings, user feedback     │
│  - Compute: win rates, consistency, domain performance  │
│  - Suggest: optimal strategy for query type             │
└─────────────────────────────────────────────────────────┘
```

---

## Phase 1: Strategy Infrastructure

### Goals
- Create pluggable strategy system
- Refactor existing code without breaking functionality
- Establish foundation for all future strategies

### Deliverables

#### 1.1 EnsembleStrategy Base Class
**File:** `backend/strategies/base.py`

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class EnsembleStrategy(ABC):
    """Abstract base class for council ensemble strategies."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    @abstractmethod
    async def execute(self, query: str, models: List[str], chairman: str) -> Dict[str, Any]:
        """
        Execute the strategy and return structured result.

        Returns:
            {
                'stage1': [...],  # Individual responses
                'stage2': [...],  # Rankings/evaluations
                'stage3': str,    # Final synthesis
                'metadata': {...} # Strategy-specific metadata
            }
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return human-readable strategy name."""
        pass

    def get_description(self) -> str:
        """Return strategy description for UI."""
        return ""
```

#### 1.2 SimpleRankingStrategy (Refactor)
**File:** `backend/strategies/simple_ranking.py`

Move existing `council.py` logic into this class:
- `stage1_collect_responses()` → internal method
- `stage2_collect_rankings()` → internal method
- `stage3_synthesize_final()` → internal method
- `execute()` → orchestrates all three stages

**No functional changes**, just restructuring.

#### 1.3 API Updates
**File:** `backend/main.py`

```python
from .strategies import get_strategy

@app.post("/api/conversations/{conversation_id}/message")
async def send_message(
    conversation_id: str,
    message: MessageRequest,
    strategy_name: str = "simple"  # New parameter
):
    strategy = get_strategy(strategy_name)
    result = await strategy.execute(
        query=message.content,
        models=COUNCIL_MODELS,
        chairman=CHAIRMAN_MODEL
    )
    # ... save and return
```

#### 1.4 UI Strategy Selector
**File:** `frontend/src/components/StrategySelector.jsx`

Simple dropdown (will be enhanced in Phase 6):
```jsx
<select value={strategy} onChange={e => setStrategy(e.target.value)}>
  <option value="simple">Simple Ranking</option>
  {/* More strategies added in later phases */}
</select>
```

### Testing
- Run existing test queries through SimpleRankingStrategy
- Verify identical behavior to v0.1
- Test strategy parameter in API

### Success Criteria
- ✅ All v0.1 functionality works unchanged
- ✅ Strategy pattern in place for future additions
- ✅ Clean separation of concerns

---

## Phase 2: Multi-Round Strategy

### Goals
- Implement iterative deliberation
- Test if models improve when given peer feedback
- Reveal convergence vs divergence patterns

### Deliverables

#### 2.1 MultiRoundStrategy Class
**File:** `backend/strategies/multi_round.py`

```python
class MultiRoundStrategy(EnsembleStrategy):
    def __init__(self, rounds: int = 2, show_critiques: bool = True):
        super().__init__({'rounds': rounds, 'show_critiques': show_critiques})
        self.rounds = rounds
        self.show_critiques = show_critiques

    async def execute(self, query: str, models: List[str], chairman: str):
        all_rounds = []

        for round_num in range(self.rounds):
            if round_num == 0:
                # Initial responses
                round_result = await self._round_initial(query, models)
            else:
                # Show previous top responses + critiques, ask for revisions
                round_result = await self._round_refinement(
                    query, models, all_rounds[-1]
                )

            all_rounds.append(round_result)

        # Final synthesis sees all rounds
        stage3 = await self._synthesize_with_rounds(query, all_rounds, chairman)

        return {
            'stage1': all_rounds,  # List of rounds, each with responses
            'stage2': all_rounds[-1]['rankings'],  # Final round rankings
            'stage3': stage3,
            'metadata': {
                'rounds': self.rounds,
                'evolution': self._compute_evolution_metrics(all_rounds)
            }
        }
```

#### 2.2 Revision Prompt Engineering

**Round 1 Prompt:** (same as current)
```
{query}
```

**Round 2+ Prompt:**
```
Original query: {query}

In the previous round, the top-ranked responses were:

{top_2_responses_with_critiques}

Please provide a revised response, incorporating insights from the peer evaluations above.
You may strengthen your original answer or adopt a different approach if convinced by the critiques.
```

#### 2.3 Round Evolution UI
**File:** `frontend/src/components/MultiRoundView.jsx`

```jsx
<div className="multi-round-view">
  <div className="round-selector">
    {rounds.map((r, i) => (
      <button key={i} onClick={() => setRound(i)}>
        Round {i + 1}
      </button>
    ))}
  </div>

  <div className="round-content">
    <Stage1 responses={rounds[currentRound].responses} />
    <Stage2 rankings={rounds[currentRound].rankings} />

    {currentRound > 0 && (
      <div className="evolution-metrics">
        <h4>Response Evolution</h4>
        <p>Models that revised: {metrics.revised_count}</p>
        <p>Rank changes: {metrics.rank_changes}</p>
      </div>
    )}
  </div>
</div>
```

#### 2.4 Evolution Metrics

Track:
- Which models changed their response (text similarity)
- Rank stability across rounds (did top stay top?)
- Convergence measure (are responses becoming more similar?)

### Testing
- Test 2-round and 3-round configurations
- Compare quality: single pass vs multi-round
- Observe: Do models genuinely improve or just converge?

### Success Criteria
- ✅ Multi-round strategy executes without errors
- ✅ UI clearly shows evolution across rounds
- ✅ Can observe interesting patterns (agreement, stubbornness, revision quality)

---

## Phase 3: Analytics Layer Foundation

### Goals
- Track strategy and model performance over time
- Build data foundation for weighted strategies
- Enable evidence-based strategy selection

### Deliverables

#### 3.1 Extended Storage Schema
**File:** `backend/storage.py`

Extend conversation schema:
```python
{
    'id': str,
    'created_at': str,
    'messages': [
        {
            'role': 'user',
            'content': str
        },
        {
            'role': 'assistant',
            'content': str,
            'stage1': [...],
            'stage2': [...],
            'stage3': str,
            'metadata': {
                'strategy_used': str,
                'strategy_config': dict,
                'label_to_model': dict,
                'aggregate_rankings': [...],
                'execution_time_ms': int,
                'user_feedback': Optional[int]  # -1, 0, 1 (dislike, neutral, like)
            }
        }
    ]
}
```

New file: `data/analytics/summary.json`
```python
{
    'total_conversations': int,
    'total_queries': int,
    'strategy_stats': {
        'simple': {'count': int, 'avg_feedback': float},
        'multi_round': {'count': int, 'avg_feedback': float},
        ...
    },
    'model_stats': {
        'openai/gpt-4': {
            'total_evaluations': int,
            'wins': int,  # Times ranked #1
            'avg_rank': float,
            'win_rate': float,
            'by_strategy': {...}
        },
        ...
    },
    'last_updated': str
}
```

#### 3.2 Analytics Engine
**File:** `backend/analytics.py`

```python
class AnalyticsEngine:
    def __init__(self, storage: ConversationStorage):
        self.storage = storage
        self.summary_path = 'data/analytics/summary.json'

    def recompute_all(self):
        """Scan all conversations and rebuild analytics."""
        all_convos = self.storage.list_all()
        # ... compute stats
        self._save_summary(summary)

    def get_model_performance(self, model: str) -> Dict:
        """Get performance metrics for a specific model."""
        pass

    def get_best_strategy_for_query_type(self, query_type: str) -> str:
        """Recommend strategy based on historical performance."""
        pass

    def record_user_feedback(self, conversation_id: str, message_index: int, feedback: int):
        """Record thumbs up/down feedback."""
        pass
```

#### 3.3 User Feedback UI
**File:** `frontend/src/components/Stage3.jsx`

Add feedback buttons:
```jsx
<div className="stage3-container">
  <div className="final-answer">
    <ReactMarkdown>{content}</ReactMarkdown>
  </div>

  <div className="feedback-buttons">
    <button onClick={() => handleFeedback(1)}>👍</button>
    <button onClick={() => handleFeedback(-1)}>👎</button>
  </div>
</div>
```

#### 3.4 Analytics Dashboard
**File:** `frontend/src/components/AnalyticsDashboard.jsx`

Initial version shows:
- Total conversations and queries
- Strategy usage breakdown (pie chart)
- Model win rates (bar chart)
- Recent feedback trends

### Testing
- Generate 20+ test conversations across strategies
- Verify analytics computations are accurate
- Test feedback recording and retrieval

### Success Criteria
- ✅ All conversations tracked with full metadata
- ✅ Analytics recomputation produces accurate metrics
- ✅ Dashboard displays meaningful insights

---

## Phase 4: Reasoning-Aware Strategy

### Goals
- Support o1, DeepSeek-R1, and other reasoning models
- Evaluate both reasoning quality and final answers
- Surface hidden reasoning to users

### Deliverables

#### 4.1 Reasoning Extraction
**File:** `backend/openrouter.py`

Update `query_model()` to extract reasoning:
```python
async def query_model(model: str, prompt: str, system: str = None):
    # ... existing code ...

    result = {
        'content': content,
        'model': model
    }

    # Extract reasoning if present (o1 models, DeepSeek, etc.)
    if 'reasoning_content' in response_data:
        result['reasoning'] = response_data['reasoning_content']

    return result
```

#### 4.2 ReasoningAwareStrategy
**File:** `backend/strategies/reasoning_aware.py`

```python
class ReasoningAwareStrategy(EnsembleStrategy):
    def __init__(self, reasoning_weight: float = 0.4, answer_weight: float = 0.6):
        super().__init__({
            'reasoning_weight': reasoning_weight,
            'answer_weight': answer_weight
        })

    async def execute(self, query: str, models: List[str], chairman: str):
        # Stage 1: Collect responses with reasoning traces
        responses = await self._collect_with_reasoning(query, models)

        # Stage 2: Dual ranking
        # First: Rank reasoning quality
        reasoning_rankings = await self._rank_reasoning(responses, models)

        # Second: Rank final answers
        answer_rankings = await self._rank_answers(responses, models)

        # Combine with weights
        combined_rankings = self._combine_rankings(
            reasoning_rankings,
            answer_rankings,
            self.config['reasoning_weight'],
            self.config['answer_weight']
        )

        # Stage 3: Chairman sees reasoning + answers
        stage3 = await self._synthesize_with_reasoning(
            query, responses, combined_rankings, chairman
        )

        return {
            'stage1': responses,
            'stage2': {
                'reasoning_rankings': reasoning_rankings,
                'answer_rankings': answer_rankings,
                'combined': combined_rankings
            },
            'stage3': stage3,
            'metadata': {
                'has_reasoning': True,
                'reasoning_weight': self.config['reasoning_weight']
            }
        }
```

#### 4.3 Reasoning Ranking Prompt

```
You are evaluating the REASONING QUALITY of the following responses to: {query}

For each response, the reasoning trace shows the model's chain of thought.

Evaluate based on:
1. Logical coherence and structure
2. Depth of analysis
3. Identification of key considerations
4. Rigor of argumentation

{anonymized_responses_with_reasoning}

FINAL RANKING: (list from best to worst reasoning)
1. Response X
2. Response Y
...
```

#### 4.4 Reasoning Trace UI
**File:** `frontend/src/components/ReasoningTrace.jsx`

```jsx
<div className="reasoning-trace">
  <button onClick={() => setExpanded(!expanded)}>
    {expanded ? '▼' : '▶'} View Reasoning ({reasoningLength} tokens)
  </button>

  {expanded && (
    <div className="reasoning-content">
      <ReactMarkdown>{reasoning}</ReactMarkdown>
    </div>
  )}
</div>
```

Update `Stage1.jsx` to show reasoning traces when available.

### Testing
- Test with o1-preview, o1-mini, DeepSeek-R1
- Verify reasoning extraction works correctly
- Compare reasoning-aware vs simple ranking on same queries

### Success Criteria
- ✅ Reasoning traces extracted and displayed
- ✅ Dual ranking (reasoning + answer) works correctly
- ✅ UI clearly shows reasoning quality evaluations

---

## Phase 5: Weighted Strategies & Auto-Suggestion

### Goals
- Use analytics to weight model votes
- Auto-suggest optimal strategy based on query
- Enable A/B testing across strategies

### Deliverables

#### 5.1 WeightedVotingStrategy
**File:** `backend/strategies/weighted_voting.py`

```python
class WeightedVotingStrategy(EnsembleStrategy):
    def __init__(self, analytics_engine: AnalyticsEngine):
        super().__init__()
        self.analytics = analytics_engine

    async def execute(self, query: str, models: List[str], chairman: str):
        # Get model weights from analytics
        weights = {
            model: self.analytics.get_model_performance(model)['win_rate']
            for model in models
        }

        # Stage 1: Standard response collection
        responses = await self._collect_responses(query, models)

        # Stage 2: Weighted ranking aggregation
        rankings = await self._collect_rankings(responses, models)

        # Apply weights when computing aggregate rankings
        aggregate = self._weighted_aggregate(rankings, weights)

        # Stage 3: Synthesis with weight-aware context
        stage3 = await self._synthesize(
            query, responses, aggregate, weights, chairman
        )

        return {
            'stage1': responses,
            'stage2': rankings,
            'stage3': stage3,
            'metadata': {
                'weights': weights,
                'aggregate_rankings': aggregate
            }
        }
```

#### 5.2 Query Classification
**File:** `backend/query_classifier.py`

```python
class QueryClassifier:
    """Classify queries to suggest optimal strategy."""

    CATEGORIES = {
        'technical': ['code', 'algorithm', 'debug', 'implement', 'function'],
        'analytical': ['analyze', 'compare', 'evaluate', 'why', 'explain'],
        'creative': ['write', 'story', 'creative', 'imagine', 'design'],
        'factual': ['what is', 'who is', 'when', 'where', 'define']
    }

    def classify(self, query: str) -> str:
        """Simple keyword-based classification (can be enhanced with ML later)."""
        query_lower = query.lower()

        scores = {cat: 0 for cat in self.CATEGORIES}
        for cat, keywords in self.CATEGORIES.items():
            for keyword in keywords:
                if keyword in query_lower:
                    scores[cat] += 1

        return max(scores, key=scores.get) if max(scores.values()) > 0 else 'general'
```

#### 5.3 Strategy Recommendation System
**File:** `backend/strategies/recommender.py`

```python
class StrategyRecommender:
    def __init__(self, analytics: AnalyticsEngine, classifier: QueryClassifier):
        self.analytics = analytics
        self.classifier = classifier

    def suggest_strategy(self, query: str) -> Dict[str, Any]:
        """Suggest optimal strategy based on query and historical performance."""

        query_type = self.classifier.classify(query)

        # Get strategy performance for this query type
        strategy_perf = self.analytics.get_strategy_performance_by_type(query_type)

        # Check if reasoning models are in council
        has_reasoning = self._check_reasoning_models()

        recommendation = {
            'strategy': self._pick_best(strategy_perf, has_reasoning),
            'query_type': query_type,
            'confidence': strategy_perf.get('confidence', 0.5),
            'rationale': self._generate_rationale(query_type, strategy_perf)
        }

        return recommendation
```

#### 5.4 A/B Testing Framework
**File:** `backend/api_experimental.py`

```python
@app.post("/api/experiments/compare-strategies")
async def compare_strategies(request: CompareRequest):
    """Run same query through multiple strategies and return all results."""

    results = {}

    for strategy_name in request.strategies:
        strategy = get_strategy(strategy_name)
        result = await strategy.execute(
            query=request.query,
            models=COUNCIL_MODELS,
            chairman=CHAIRMAN_MODEL
        )
        results[strategy_name] = result

    return {
        'query': request.query,
        'results': results,
        'comparison_id': generate_id()
    }
```

**UI Component:** `frontend/src/components/StrategyComparison.jsx`
- Side-by-side view of multiple strategies
- Ability to vote on which result is better
- Feeds back into analytics

### Testing
- Test weighted voting with different model compositions
- Verify query classification accuracy
- Run A/B tests on 10+ queries across strategies

### Success Criteria
- ✅ Weighted voting produces different results than simple ranking
- ✅ Strategy recommendations are sensible and evidence-based
- ✅ A/B testing UI allows direct comparison

---

## Phase 6: UI Integration & Polish

### Goals
- Unified, intuitive interface for all features
- Professional documentation
- Production-ready v0.2 release

### Deliverables

#### 6.1 Strategy Configuration Panel
**File:** `frontend/src/components/StrategyConfig.jsx`

```jsx
<div className="strategy-config">
  <h3>Ensemble Strategy</h3>

  <div className="strategy-selector">
    <label>Strategy:</label>
    <select value={strategy} onChange={handleStrategyChange}>
      <option value="simple">Simple Ranking</option>
      <option value="multi_round">Multi-Round Deliberation</option>
      <option value="reasoning">Reasoning-Aware</option>
      <option value="weighted">Weighted Voting</option>
    </select>
  </div>

  {strategy === 'multi_round' && (
    <div className="strategy-options">
      <label>Rounds: <input type="number" min="2" max="5" value={rounds} /></label>
      <label><input type="checkbox" checked={showCritiques} /> Show critiques</label>
    </div>
  )}

  {strategy === 'reasoning' && (
    <div className="strategy-options">
      <label>Reasoning weight: <input type="range" min="0" max="1" step="0.1" /></label>
    </div>
  )}

  {recommendation && (
    <div className="strategy-recommendation">
      ℹ️ Recommended: <strong>{recommendation.strategy}</strong>
      <br />
      {recommendation.rationale}
    </div>
  )}
</div>
```

#### 6.2 Analytics Sidebar
**File:** `frontend/src/components/AnalyticsSidebar.jsx`

Collapsible sidebar showing:
- Model performance leaderboard
- Your query history (by category)
- Strategy usage stats
- Recent feedback trends

#### 6.3 Export Functionality

**Conversation Export:**
- Markdown format (readable)
- JSON format (programmatic)
- Includes all stages, rankings, and metadata

**Analytics Export:**
- CSV of model performance
- PDF report with charts

#### 6.4 Documentation Updates

**README.md:**
- Update with v0.2 features
- Strategy comparison table
- Quick start guide for each strategy
- Screenshots of new UI

**CLAUDE.md:**
- Document strategy architecture
- Explain analytics schema
- Notes on extending with new strategies
- Migration notes from v0.1

**New File:** `STRATEGIES.md`
- Detailed explanation of each strategy
- When to use which strategy
- Configuration options
- Performance characteristics

#### 6.5 Final Testing & Polish

- Cross-browser testing (Chrome, Firefox, Safari)
- Mobile responsive design
- Error handling edge cases
- Performance optimization (lazy load analytics)
- Accessibility (keyboard navigation, screen readers)

### Success Criteria
- ✅ All features accessible through intuitive UI
- ✅ Documentation is comprehensive and accurate
- ✅ No critical bugs in core functionality
- ✅ Ready for public release

---

## Implementation Timeline & Dependencies

```
Phase 1 (Foundation) ─────────────────┐
  │                                    │
  ├─> Phase 2 (Multi-Round)           │
  │     │                              │
  ├─> Phase 3 (Analytics) ─────────────┤
  │     │                              │
  │     ├─> Phase 5 (Weighted/Auto)   │
  │                                    │
  └─> Phase 4 (Reasoning)              │
        │                              │
        └──────────────────────────────┤
                                       │
                       Phase 6 (Integration & Polish)
```

**Estimated Effort:**
- Phase 1: 4-6 hours (careful refactoring)
- Phase 2: 3-4 hours (new strategy + UI)
- Phase 3: 4-5 hours (data schema + analytics)
- Phase 4: 3-4 hours (reasoning extraction + dual ranking)
- Phase 5: 4-5 hours (weighting + recommendation system)
- Phase 6: 3-4 hours (polish + documentation)

**Total: ~20-28 hours** (can be done in phases over multiple sessions)

---

## Key Design Principles

1. **Graceful Degradation**: Every strategy works even with partial failures
2. **Transparency**: All intermediate results visible to users
3. **Extensibility**: Adding new strategies should be straightforward
4. **Data-Driven**: Analytics inform strategy selection, not hunches
5. **Backward Compatible**: v0.1 conversations still viewable
6. **Performance**: Maintain parallel execution, minimize latency

---

## Success Metrics for v0.2

- **Functional**: All 4+ strategies working correctly
- **Performance**: Average latency per strategy < 30s
- **Quality**: User feedback shows improvement over v0.1
- **Adoption**: Documentation enables others to extend system
- **Research**: Produces interesting insights about model behavior

---

## Future Enhancements (v0.3+)

Ideas to consider after v0.2:
- Streaming responses (reduce perceived latency)
- Custom council composition per query
- Domain-specific councils with routing
- Adversarial/debate strategies
- Integration with local models (Ollama)
- Export to academic paper format
- Model cost tracking and optimization

---

**Ready to implement. Start with Phase 1!**
