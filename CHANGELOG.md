# Changelog

All notable changes to LLM Council will be documented in this file.

## [0.2.0] - 2025-11-23

### 🎯 Major Features

#### Strategy Pattern Architecture
- **Pluggable Ensemble Strategies**: Abstract base class allows easy experimentation with different deliberation approaches
- **4 Built-in Strategies**:
  - `simple`: Original 3-stage ranking (v0.1 logic)
  - `multi_round`: Iterative deliberation with model revision
  - `reasoning_aware`: Dual evaluation for o1/DeepSeek reasoning models
  - `weighted_voting`: Analytics-driven performance weighting
- **Strategy Registry**: Dynamic registration and factory pattern
- **Configuration Schema**: Per-strategy customization options

#### Analytics & Performance Tracking
- **AnalyticsEngine**: Comprehensive performance metrics across all conversations
- **Model Leaderboard**: Win rates, average rankings, top-3 rates
- **Strategy Effectiveness**: Usage counts and average feedback scores
- **Historical Data**: Per-strategy model breakdowns
- **Persistence**: Analytics cached to `data/analytics/summary.json`

#### Intelligent Strategy Recommendation
- **QueryClassifier**: Keyword-based query categorization (technical, reasoning, analytical, creative, factual)
- **StrategyRecommender**: Combines classification + analytics for smart suggestions
- **Confidence Scoring**: Recommendation quality metrics
- **Fallback Options**: Alternative strategy suggestions
- **API Endpoint**: `POST /api/strategies/recommend`

#### Multi-Round Deliberation
- **Iterative Refinement**: Models revise based on top peer responses
- **Evolution Tracking**: Rank changes, improvements/declines between rounds
- **Configurable**: Adjustable round count and top-N display
- **Rich Metadata**: Round-by-round data and evolution metrics

#### Reasoning-Aware Strategy
- **Dual Ranking**: Separate evaluation of reasoning quality and answer quality
- **Weighted Combination**: Configurable weights (default 40% reasoning, 60% answer)
- **OpenRouter Integration**: Extracts `reasoning_details` from API responses
- **Graceful Fallback**: Works with non-reasoning models

#### Weighted Voting Strategy
- **Performance-Based Weighting**: Higher win rates = more influence
- **Analytics Integration**: Uses historical data from AnalyticsEngine
- **Configurable**: Min weight and weighting method options
- **Transparency**: Metadata includes model weights

### 🎨 Frontend Enhancements

#### New Components
- **StrategyRecommendation**: Beautiful gradient card with AI-powered suggestions
- **MultiRoundView**: Round-by-round tabs with evolution metrics
- **AnalyticsDashboard**: Comprehensive modal with leaderboards and stats
- **Stage3 Feedback**: Thumbs up/down rating buttons

#### UI Improvements
- **Multi-Message Support**: Input form now always visible for follow-up questions
- **Strategy Dropdown**: 4 strategies selectable from dropdown
- **Real-Time Recommendations**: Appear as user types substantial queries
- **Smooth Animations**: Slide-down effects and transitions
- **Professional Design**: Purple gradients, medals, confidence badges

### 🔧 Backend Enhancements

#### New Modules
- `backend/analytics.py`: AnalyticsEngine class
- `backend/query_classifier.py`: QueryClassifier with regex patterns
- `backend/strategies/base.py`: Abstract strategy interface
- `backend/strategies/simple_ranking.py`: Refactored v0.1 logic
- `backend/strategies/multi_round.py`: Iterative deliberation
- `backend/strategies/reasoning_aware.py`: Dual evaluation
- `backend/strategies/weighted_voting.py`: Performance weighting
- `backend/strategies/recommender.py`: Strategy recommendation system
- `backend/strategies/__init__.py`: Strategy registry and factory

#### New API Endpoints
- `GET /api/strategies`: List all strategies
- `POST /api/strategies/recommend`: Get strategy suggestion
- `POST /api/strategies/compare`: A/B test multiple strategies
- `GET /api/analytics/summary`: Full analytics data
- `GET /api/analytics/leaderboard`: Model rankings
- `GET /api/analytics/models/{model}`: Specific model metrics
- `GET /api/analytics/strategies/{strategy}`: Strategy metrics
- `POST /api/conversations/{id}/messages/{index}/feedback`: User feedback

#### Storage Schema Updates
- **Extended Metadata**: Strategy name, label_to_model, aggregate_rankings, evolution metrics
- **User Feedback**: -1 (dislike), 0 (neutral), 1 (like), None
- **Timestamps**: Created and feedback timestamps
- **Persistence**: Metadata now saved to storage (v0.1 was ephemeral)

### 📚 Documentation

#### New Files
- **CLAUDE_v02.md**: Complete technical reference (architecture, strategies, API, data flows)
- **CHANGELOG.md**: This file - version history

#### Updated Files
- **README.md**: Added v0.2 features, strategy explanations, API reference
- **CLAUDE.md**: Preserved as v0.1 reference

### 🧪 Developer Experience

#### Testing
- Strategy-specific testing guidelines
- Manual testing checklist
- API testing examples

#### Architecture
- Clean separation of concerns (strategies, analytics, classification)
- Dependency injection for analytics engine
- Consistent error handling and graceful degradation
- Async/parallel execution throughout

### 🔄 Migration from v0.1

#### Breaking Changes
- None! v0.1 functionality preserved as `simple` strategy
- Old conversations still work
- Default strategy is `simple` for backward compatibility

#### New Defaults
- Strategy: `simple` (same as v0.1)
- Metadata persistence: Now enabled by default
- Multi-message conversations: Now supported

### 🚀 Performance

- Parallel strategy execution for A/B testing
- Analytics caching for faster subsequent queries
- Efficient JSON storage with minimal overhead
- Async/await throughout for low latency

### 🐛 Bug Fixes

- Fixed input form visibility (now always shown, not just on first message)
- Added proper metadata persistence to storage
- Fixed strategy configuration injection for weighted voting

## [0.1.0] - Initial Release

### Features
- 3-stage deliberation system
- Anonymous peer ranking
- Chairman synthesis
- Tab-based UI for stage inspection
- OpenRouter integration
- JSON-based conversation storage
- React + Vite frontend
- FastAPI backend
