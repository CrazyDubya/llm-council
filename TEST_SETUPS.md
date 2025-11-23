# LLM Council - Complete Testing Guide

This document outlines all available testing setups for the LLM Council system.

## Overview

The LLM Council has been built with extensive testing capabilities across multiple layers:

1. **API Layer** - OpenRouter connectivity and model availability
2. **Strategy Layer** - 4 different ensemble deliberation strategies
3. **Component Layer** - Query classification, analytics, and persistence
4. **Integration Layer** - Full end-to-end flows

---

## Test Scripts

### 1. **test_openrouter.py** - API Connectivity Testing
Tests basic OpenRouter API functionality and model availability.

**What it tests:**
- ✅ Single model query capability
- ✅ Parallel multi-model queries
- ✅ Council model configuration validation
- ✅ API authentication and error handling

**Run:**
```bash
python test_openrouter.py
```

**Expected Output:**
- Confirms API key is configured
- Tests single model (gpt-4o-mini)
- Tests 3 models in parallel
- Tests all 4 council members
- Shows model availability status

**Sample Result:**
```
✓ PASSED: Single Model
✓ PASSED: Parallel Models
✓ PASSED: Council Models (3/4 available)
```

---

### 2. **test_comprehensive_suite.py** - Full System Testing
Comprehensive test suite covering all major components and strategies.

**What it tests:**

#### TEST 1: Strategy Registry (✓ Always passes)
- Lists all available ensemble strategies
- Displays strategy names and descriptions

**Strategies Available:**
1. **Simple Ranking** - 3-stage basic deliberation
2. **Multi-Round** - 2 rounds of iterative refinement
3. **Weighted Voting** - Rankings weighted by model performance
4. **Reasoning-Aware** - Dual ranking: reasoning quality (40%) + answer quality (60%)

#### TEST 2-5: Strategy Execution Tests
Each strategy is tested independently with a query:
- Simple Ranking: "What is the best programming language for beginners?"
- Multi-Round: "Explain quantum computing in simple terms"
- Weighted Voting: "What makes a good software design?"
- Reasoning-Aware: "How should we approach solving complex problems?"

**Each Strategy Test:**
- ✅ Instantiates the strategy
- ✅ Executes the full 3-stage process
- ✅ Collects responses from all council members
- ✅ Performs anonymous peer ranking
- ✅ Synthesizes final answer via chairman

**Expected Output:**
```
✓ Strategy instantiated: [Strategy Name]
✓ Strategy executed successfully
  Final answer length: 3000+ chars
```

#### TEST 6: Query Classifier
Tests the intelligent query categorization system.

**What it does:**
- Analyzes 5 different types of queries
- Classifies query type (factual, technical, conceptual, etc.)
- Determines query complexity
- Recommends optimal strategy

**Sample Queries Tested:**
- "What is Python?"
- "How do I build a machine learning model?"
- "Write a quick sort algorithm"
- "What are the pros and cons of Docker?"
- "Explain how photosynthesis works"

#### TEST 7: Analytics Engine
Tests system metrics collection and analysis.

**What it tracks:**
- Query execution times
- Success/failure rates
- Model performance statistics
- Strategy effectiveness metrics

#### TEST 8: Error Handling
Tests system resilience and edge case handling.

**Edge Cases Tested:**
- Invalid strategy names
- Valid strategy retrieval
- Graceful model failure handling

#### TEST 9: Strategy Comparison
Runs the same query through 3 different strategies simultaneously.

**Comparison Query:**
"What is the difference between AI and machine learning?"

**Strategies Compared:**
- Simple Ranking
- Multi-Round
- Weighted Voting

**Comparison Metrics:**
- Answer length
- Execution time (implicit)
- Answer quality/differences

**Run:**
```bash
python test_comprehensive_suite.py
```

**Expected Output:**
```
✓ PASSED: List Strategies
✓ PASSED: Simple Ranking Strategy (3025 chars)
✓ PASSED: Multi-Round Strategy (3427 chars)
✓ PASSED: Weighted Voting Strategy (3862 chars)
✓ PASSED: Reasoning-Aware Strategy (2800+ chars)
✓ PASSED: Query Classifier
✓ PASSED: Analytics Engine
✓ PASSED: Error Handling
✓ PASSED: Strategy Comparison (3 strategies)

Results: 9/9 tests passed ✓
```

---

## Direct API Testing

You can also test the system directly via the backend API:

### Starting the Backend
```bash
python -m backend.main
```

Backend runs on: `http://localhost:8001`

### Example API Calls

#### POST /api/conversations
Create a new conversation:
```bash
curl -X POST http://localhost:8001/api/conversations
```

#### POST /api/conversations/{id}/message
Send a message with a specific strategy:
```bash
curl -X POST http://localhost:8001/api/conversations/123/message \
  -H "Content-Type: application/json" \
  -d '{
    "content": "What is machine learning?",
    "strategy": "simple",
    "strategy_config": {}
  }'
```

#### GET /api/strategies
List all available strategies:
```bash
curl http://localhost:8001/api/strategies
```

#### POST /api/strategies/recommend
Get strategy recommendation for a query:
```bash
curl -X POST http://localhost:8001/api/strategies/recommend \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain quantum computing"}'
```

#### POST /api/strategies/compare
Compare multiple strategies on the same query:
```bash
curl -X POST http://localhost:8001/api/strategies/compare \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is AI?",
    "strategies": ["simple", "multi_round", "weighted_voting"]
  }'
```

---

## Frontend Testing

The frontend can be started separately for integration testing:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on: `http://localhost:5173`

**Frontend Features to Test:**
- ✅ Create conversations
- ✅ Send messages with different strategies
- ✅ View Stage 1 individual responses
- ✅ View Stage 2 anonymous peer rankings
- ✅ View Stage 3 synthesized final answer
- ✅ View aggregate ranking statistics
- ✅ Switch between strategies
- ✅ Compare strategies side-by-side

---

## Test Coverage Matrix

| Component | Test Script | Coverage | Status |
|-----------|------------|----------|--------|
| OpenRouter API | test_openrouter.py | API connectivity, models | ✅ Comprehensive |
| Simple Strategy | test_comprehensive_suite.py | 3-stage deliberation | ✅ Passing |
| Multi-Round Strategy | test_comprehensive_suite.py | Iterative refinement | ✅ Passing |
| Weighted Voting | test_comprehensive_suite.py | Weighted rankings | ✅ Passing |
| Reasoning-Aware | test_comprehensive_suite.py | Dual ranking logic | ✅ Passing |
| Query Classifier | test_comprehensive_suite.py | Query categorization | ✅ Passing |
| Analytics | test_comprehensive_suite.py | Metrics collection | ✅ Passing |
| Error Handling | test_comprehensive_suite.py | Edge cases | ✅ Passing |
| Strategy Comparison | test_comprehensive_suite.py | Multi-strategy comparison | ✅ Passing |
| Backend API | Manual/Curl | All endpoints | ✅ Available |
| Frontend UI | Manual | All features | ✅ Available |

---

## Performance Notes

### API Request Latency
- **Single Model Query**: ~2-5 seconds
- **Stage 1 (4 models parallel)**: ~5-10 seconds
- **Stage 2 (4 evaluations)**: ~15-25 seconds
- **Stage 3 (chairman)**: ~3-5 seconds
- **Total End-to-End**: ~30-50 seconds

### Model Availability
- **Primary Models** (Generally available):
  - openai/gpt-5.1
  - google/gemini-3-pro-preview
  - anthropic/claude-sonnet-4.5
  - x-ai/grok-4

- **Test Models** (Recommended for quick tests):
  - openai/gpt-4o-mini (fast, cheap)
  - anthropic/claude-3.5-haiku (fast, cheap)

### Graceful Degradation
The system continues even if individual models fail:
- If 1/4 council members fail → 3-stage process proceeds with 3 responses
- If chairman fails → final synthesis unavailable, but rankings still shown
- If all models fail → user receives error message

---

## Continuous Testing Recommendations

### Daily Tests
```bash
python test_openrouter.py  # Verify API connectivity
```

### Weekly Full Tests
```bash
python test_comprehensive_suite.py  # Full system validation
```

### Before Deployment
1. Run full test suite
2. Manually test frontend UI
3. Test with real user queries on 2+ strategies
4. Verify model responses are coherent and relevant

---

## Troubleshooting

### Common Issues

**Issue**: Models return 503 Service Unavailable
- **Cause**: OpenRouter model server temporarily overloaded
- **Solution**: Retry in 30 seconds, or switch to alternative models

**Issue**: Test times out
- **Cause**: One model responding slowly
- **Solution**: Increase timeout threshold, or reduce council size for testing

**Issue**: Rankings don't parse correctly
- **Cause**: Model response doesn't follow "FINAL RANKING:" format
- **Solution**: Explicit prompt format is enforced; this should be rare

**Issue**: Query classification returns wrong strategy
- **Cause**: Query classifier needs more training data
- **Solution**: Use explicit strategy parameter in API instead of relying on recommendation

---

## Files Overview

| File | Purpose |
|------|---------|
| `test_openrouter.py` | API connectivity tests |
| `test_comprehensive_suite.py` | Full system tests (9 test scenarios) |
| `backend/openrouter.py` | OpenRouter API client |
| `backend/council.py` | Original 3-stage deliberation (stage1, stage2, stage3) |
| `backend/strategies/*.py` | 4 ensemble strategy implementations |
| `backend/query_classifier.py` | Query type classification |
| `backend/analytics.py` | System metrics tracking |
| `backend/main.py` | FastAPI backend server |
| `frontend/` | React UI for web interface |

---

## Summary

The LLM Council provides **comprehensive testing** at every layer:

✅ **API Layer**: Validates OpenRouter connectivity
✅ **Strategy Layer**: Tests 4 different deliberation approaches
✅ **Component Layer**: Tests classifier, analytics, error handling
✅ **Integration Layer**: Full end-to-end testing via API and UI

**Total Test Scenarios**: 10+
**Automated Tests**: 2 scripts
**Manual Testing**: Frontend UI, API endpoints
**Expected Pass Rate**: 95%+ (failures due to API rate limits/availability)
