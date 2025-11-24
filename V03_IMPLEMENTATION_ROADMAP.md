# LLM Council v0.3 - Multi-Phasic Implementation Roadmap

**Version:** 0.3 Implementation Plan
**Date:** 2025-11-24
**Approach:** Incremental delivery across 5 phases with cross-pollination

This roadmap combines features from Paths 2 (Experimental), 3 (Formulaic), 4 (Esoteric), and 5 (Dealer's Choice), plus selected UI/UX enhancements from Path 1 (excluding authentication).

---

## Overview: The 5 Phases

| Phase | Theme | Duration | Key Deliverable |
|-------|-------|----------|-----------------|
| **Phase 1** | Visual Foundation & Frameworks | 2 weeks | Visual consensus maps + SWOT analysis |
| **Phase 2** | Time & Knowledge | 2 weeks | Time-travel benchmarking + fact-checking |
| **Phase 3** | Intelligence & Adaptation | 2.5 weeks | Dynamic councils + adaptive weighting |
| **Phase 4** | Depth & Philosophy | 2 weeks | Socratic mode + epistemic scoring |
| **Phase 5** | Multi-Modal & Polish | 2.5 weeks | Code execution + dark mode + dashboards |

**Total Timeline:** ~11 weeks with built-in buffer

---

## Phase 1: Visual Foundation & Frameworks
**Duration:** 2 weeks | **Theme:** "See the patterns, structure the thinking"

### Core Features

#### 1.1 Visual Consensus Mapping (Path 5.1)
**Week 1:**
- Interactive graph visualization of model agreement/disagreement
- D3.js or React Flow for node-edge rendering
- Nodes = model responses, edges = similarity scores (cosine similarity on embeddings)
- Color coding: consensus (green), split opinion (yellow), outliers (red)
- Click nodes to see full response text

**Week 2:**
- Animated evolution across deliberation rounds (for multi-round strategy)
- Cluster detection algorithm (DBSCAN or hierarchical clustering)
- Export as interactive HTML and static PNG
- Integration with existing Stage 2 display

#### 1.2 Framework-Based Evaluation (Path 3.1)
**Week 1:**
- SWOT analysis template (models evaluate Strengths, Weaknesses, Opportunities, Threats)
- New strategy: `SwotAnalysisStrategy` extending base `Strategy` class
- Stage 1: Models respond with structured SWOT breakdown
- Stage 2: Models rank based on comprehensiveness and insight

**Week 2:**
- Cost-Benefit analysis template with quantitative scoring
- Decision Matrix mode (user defines weighted criteria)
- Risk Assessment framework (probability × impact matrix)
- UI: Framework selector dropdown alongside strategy selector

#### 1.3 Conversation Manager (Path 1, cherry-picked)
**Week 1-2:**
- Search conversations by keyword (full-text search on JSON)
- Filter by date range, strategy type, model composition
- Tag system: user-defined labels for conversations
- Archive/unarchive (soft delete with restore)
- Bulk operations (archive multiple, export batch)

### Review & Testing (End of Week 2)
- [ ] Visual regression tests for consensus maps
- [ ] Validate SWOT output parsing from multiple models
- [ ] User testing: can users understand the visual mappings?
- [ ] Performance check: rendering large graphs (10+ models)

### Fun Enhancement: "Council Constellations"
Create beautiful constellation-style visualizations where models are stars, connections are light trails, and consensus forms patterns like actual star constellations. Name clusters after constellations (Orion Cluster = tight agreement, Big Dipper = linear chain of reasoning).

### Cross-Pollination Opportunities
- **→ Phase 2:** Use visual maps to show how model performance changes over time
- **→ Phase 3:** Visualize adaptive weights as node sizes (bigger = more influence)
- **→ Phase 4:** Map philosophical consistency across conversations
- **→ Phase 5:** Add multi-modal nodes (code, images) to consensus graphs

---

## Phase 2: Time & Knowledge
**Duration:** 2 weeks | **Theme:** "Learn from the past, verify the present"

### Core Features

#### 2.1 Time-Travel Benchmarking (Path 5.3)
**Week 1:**
- Database schema: store model version, timestamp, performance metrics
- Re-run engine: execute historical conversations with current models
- Comparison view: side-by-side old vs new responses
- Performance drift detection: statistical tests (t-test, effect size)

**Week 2:**
- Longitudinal study export (CSV with columns: timestamp, model, version, score, strategy)
- Trend visualization: line charts showing model improvement over time
- Regression alerts: notify if models are degrading
- "What's Changed" report generator (automatic changelog)

#### 2.2 Validation & Fact-Checking (Path 3.5)
**Week 1:**
- Citation extraction: parse URLs and references from responses
- External fact-checking API integration (Google Fact Check Tools API)
- Claim extraction: identify factual assertions using NLP
- Verification status badges (verified ✓, disputed ⚠, unknown ?)

**Week 2:**
- Cross-reference validation: check consistency across model responses
- Confidence intervals on numerical claims (extract ranges, flag outliers)
- Source quality scoring (academic > news > blog)
- Fact-check results displayed in Stage 1 tabs

#### 2.3 Model Management UI (Path 1, cherry-picked)
**Week 1-2:**
- Dynamic model selector: browse OpenRouter catalog in-app
- Add/remove council members without editing config.py
- Model info cards: display cost, context window, capabilities
- Preset councils: save configurations (e.g., "Budget Council", "Reasoning Experts")
- Cost estimation: preview expense before running deliberation

### Review & Testing (End of Week 2)
- [ ] Validate time-travel accuracy: do re-runs match original outputs?
- [ ] Test fact-checking with known true/false claims
- [ ] Load testing: 100+ historical conversations
- [ ] API rate limit handling for fact-check services

### Fun Enhancement: "Model Time Machine"
Animated timeline where you "travel" through model evolution. Watch GPT-4 → GPT-4.5 → GPT-5.1 answer the same question with visual transitions showing differences. Add retro UI styling (old terminal font, sepia tones) for historical runs.

### Cross-Pollination Opportunities
- **← Phase 1:** Show consensus map evolution in time-travel mode
- **→ Phase 3:** Use historical performance to initialize adaptive weights
- **→ Phase 4:** Track epistemic humility over time (are models learning to say "I don't know"?)
- **→ Phase 5:** Fact-check code execution results against known test cases

---

## Phase 3: Intelligence & Adaptation
**Duration:** 2.5 weeks | **Theme:** "Smart systems that learn and optimize"

### Core Features

#### 3.1 Dynamic Council Composition (Path 2.1)
**Week 1:**
- Query classifier: categorize questions (math, creative, factual, analytical, ethical)
- Model capability matrix: define strengths (e.g., Claude = writing, DeepSeek = math)
- Auto-selection algorithm: choose optimal 3-5 models based on query type
- Override UI: user can approve/modify suggestions

**Week 2:**
- Council size optimization: A/B test 3 vs 5 vs 7 models per query type
- Specialist routing: hard questions get reasoning models (o1, DeepSeek-R1)
- Cost-performance tradeoff slider: "fast & cheap" vs "slow & thorough"
- Model rotation: bench consistent underperformers, promote rising stars

#### 3.2 Adaptive Weighting 2.0 (Path 5.4)
**Week 1:**
- Bayesian updating: real-time competency scoring using user feedback
- Context-specific expertise: separate weights for math vs history vs code
- Uncertainty quantification: confidence intervals on model weights
- Prior initialization: bootstrap from Phase 2 historical data

**Week 2:**
- Transparent explanations: "Model X got 40% weight because..."
- Weight visualization: pie charts, bar graphs in Stage 2 display
- Manual override: user can adjust weights for individual conversations
- Weight decay: older performance data fades (recency bias)

#### 3.3 Multi-Round Recursive Deliberation (Path 2.2)
**Week 1-2:**
- Extend to N rounds (configurable, default max = 4)
- Convergence detection: stop when cosine similarity > 0.9 across responses
- Cross-examination mode: models pose questions to each other
- User intervention: allow clarification requests mid-deliberation
- UI: expandable rounds accordion (Round 1, Round 2, ...)

### Review & Testing (End of Week 2.5)
- [ ] Validate query classification accuracy (precision/recall)
- [ ] Test adaptive weights with synthetic feedback data
- [ ] Convergence testing: do models actually converge or diverge?
- [ ] Cost analysis: is dynamic composition cheaper than fixed councils?

### Fun Enhancement: "Council Evolution Simulator"
Gamify adaptive weights: show models as "leveling up" with XP bars, badges for expertise domains, leaderboards with silly titles ("Math Wizard", "Wordsmith Supreme"). Include sound effects and animations when weights update.

### Cross-Pollination Opportunities
- **← Phase 1:** Visualize dynamic composition choices on consensus maps
- **← Phase 2:** Use time-travel data to validate adaptive weight predictions
- **→ Phase 4:** Apply adaptive weighting to epistemic humility scores
- **→ Phase 5:** Adjust weights based on code execution success rates

---

## Phase 4: Depth & Philosophy
**Duration:** 2 weeks | **Theme:** "Think deeply, question everything"

### Core Features

#### 4.1 Socratic Dialogue Mode (Path 4.1)
**Week 1:**
- New strategy: `SocraticStrategy` (no direct answers, only questions)
- Stage 1: Models generate 3-5 probing questions instead of answers
- Stage 2: Models rank quality of questions (depth, relevance, progression)
- Stage 3: Chairman synthesizes question sequence (beginner → advanced)
- UI: "Socratic Session" with progressive revelation

**Week 2:**
- User response integration: user answers questions, models ask follow-ups
- Philosophical depth tracking: surface vs intermediate vs fundamental
- Question type classification: clarifying, challenging, connecting, hypothetical
- Exit condition: user says "I understand" or "give me the answer"

#### 4.2 Epistemic Humility Scoring (Path 4.3)
**Week 1:**
- Uncertainty phrase detection: "I'm not sure", "This is speculative", "Likely but not certain"
- Overconfidence penalty: flag absolute statements ("definitely", "always", "never")
- Calibration scoring: check if confidence matches accuracy (on fact-checkable claims)
- Unknown-unknowns identification: "This question assumes X, which may not be true"

**Week 2:**
- Humility leaderboard: rank models by epistemic honesty
- Metacognitive awareness: reward models that reflect on limitations
- Appropriate confidence: different thresholds for math (high confidence OK) vs predictions (low confidence appropriate)
- UI: display confidence badges (🟢 appropriately confident, 🔴 overconfident)

#### 4.3 Philosophical Consistency Checker (Path 4.4)
**Week 1-2:**
- Multi-conversation analysis: track model positions over time
- Contradiction detection: "In conversation A you said X, but in B you said ¬X"
- Principle extraction: identify implicit values (utilitarian, deontological, virtue ethics)
- Worldview mapping: visualize model philosophies as radar charts
- Consistency report: percentage agreement across similar questions

### Review & Testing (End of Week 2)
- [ ] User study: is Socratic mode engaging or frustrating?
- [ ] Validate epistemic scoring with known overconfident/humble examples
- [ ] Test philosophical checker with intentionally contradictory prompts
- [ ] Edge case: what if models refuse to answer vs admit uncertainty?

### Fun Enhancement: "Philosopher's Arena"
Models debate as historical philosophers (Socrates, Kant, Mill). UI styled like ancient Greek agora with marble columns. Models get avatars and speaking styles. Chairman is "Oracle of Delphi". Add dramatic music and ancient scroll-style exports.

### Cross-Pollination Opportunities
- **← Phase 1:** Map philosophical positions on consensus graphs (utilitarian cluster vs deontological cluster)
- **← Phase 2:** Track epistemic humility over model versions (are newer models more honest?)
- **← Phase 3:** Adaptive weights should reward humility, penalize overconfidence
- **→ Phase 5:** Epistemic scores for code predictions (confidence in bug-free code)

---

## Phase 5: Multi-Modal & Polish
**Duration:** 2.5 weeks | **Theme:** "Beyond text, beautiful experience"

### Core Features

#### 5.1 Multi-Modal Deliberation (Path 5.5)
**Week 1:**
- Image input support: upload images, models analyze and discuss
- Vision model integration: GPT-4V, Claude Sonnet 4.5, Gemini 2.0 Pro Vision
- Stage 1: Models describe and interpret image
- Stage 2: Models rank interpretations for accuracy and insight

**Week 2:**
- Code execution environment: sandboxed Python/JavaScript runner
- Models submit code, system executes and returns results
- Test-driven deliberation: models propose solutions, tests validate correctness
- Diagram generation: models produce Mermaid/DOT diagrams, rendered in UI

#### 5.2 Response DNA & Breeding (Path 5.2)
**Week 1:**
- Genetic algorithm: crossover best-ranked response sections
- Section extraction: parse responses into intro, analysis, conclusion
- Fitness function: user feedback (👍/👎) + peer rankings
- Mutation: chairman adds novel synthesis elements
- Lineage tracking: "This answer is 40% GPT-5.1, 30% Claude, 30% Gemini"

**Week 2:**
- Breeding UI: visual representation of genetic crossover
- Generational tracking: Response v1 → v2 → v3 across deliberation rounds
- User-guided breeding: "I like this part from A and that part from B"
- Export pedigree: family tree of answer evolution

#### 5.3 Dark Mode & Visual Polish (Path 1, cherry-picked)
**Week 1:**
- Dark/light mode toggle with system preference detection
- Custom color schemes: blue (default), green, purple, amber
- Smooth transitions between themes (CSS variables + transitions)
- Accessibility: WCAG 2.1 AA contrast ratios, focus indicators

**Week 2:**
- Dashboard redesign: modern card-based layout
- Responsive design: mobile-friendly (currently desktop-only)
- Loading states: skeleton screens, progress indicators
- Micro-interactions: button hover states, smooth scrolling, toast notifications

#### 5.4 Performance Dashboards (Path 1, cherry-picked)
**Week 1-2:**
- Analytics overview: total conversations, strategies used, models called
- Model leaderboard: win rates, avg rankings, cost per conversation
- Strategy effectiveness: which strategies perform best for which query types
- Cost analysis: spending over time, per-model costs, budget projections
- Charts: victory distributions, performance trends, strategy heatmaps

### Review & Testing (End of Week 2.5)
- [ ] Test image analysis with diverse images (photos, diagrams, memes)
- [ ] Code execution security audit: sandboxing, resource limits, timeout
- [ ] Visual regression tests for dark mode (all components)
- [ ] Performance testing: dashboard with 1000+ conversations
- [ ] Accessibility audit: keyboard navigation, screen reader compatibility

### Fun Enhancement: "Council Arcade"
Retro gaming aesthetic for dashboards. Models are characters with pixel art avatars. Leaderboards styled like high score tables. Achievement system ("🏆 First Perfect Score", "🎯 10-Win Streak"). Sound effects for wins/losses. Optional CRT screen effect toggle.

### Cross-Pollination Opportunities
- **← Phase 1:** Dark mode for consensus maps (neon colors on black background)
- **← Phase 2:** Dashboard shows time-travel benchmark results
- **← Phase 3:** Visualize dynamic council selection decisions in dashboards
- **← Phase 4:** Track Socratic sessions and epistemic humility in analytics

---

## Phase Integration: The Big Picture

### Data Model Evolution

```
v0.2: {stage1, stage2, stage3, metadata}
v0.3: {
  stage1: [...],
  stage2: [...],
  stage3: {...},
  metadata: {
    consensus_map: {nodes, edges, clusters},
    framework: "swot" | "cost_benefit" | "decision_matrix",
    time_travel: {original_date, rerun_date, drift_score},
    fact_checks: [{claim, status, sources}],
    dynamic_composition: {selected_models, reason},
    adaptive_weights: {model_id: {weight, confidence}},
    epistemic_scores: {model_id: humility_score},
    multi_modal: {images: [...], code_executions: [...]},
    breeding_lineage: {contributors: {model_id: percentage}}
  }
}
```

### UI Architecture Evolution

```
App.jsx
├── Sidebar (new)
│   ├── ConversationList (enhanced: search, filter, tags)
│   ├── ModelSelector (new: dynamic council builder)
│   └── ThemeToggle (new: dark mode)
├── ChatInterface
│   ├── QueryInput (enhanced: framework selector, image upload)
│   ├── StrategySelector (existing)
│   └── DynamicCouncilSuggestion (new)
├── ResponseDisplay
│   ├── Stage1Tabs (enhanced: fact-check badges, code execution results)
│   ├── Stage2Tabs (enhanced: epistemic scores, adaptive weights)
│   ├── Stage3Final (existing)
│   ├── ConsensusMap (new: D3.js visualization)
│   └── BreedingLineage (new: genetic algorithm view)
└── Dashboard (new)
    ├── AnalyticsOverview
    ├── ModelLeaderboard
    ├── StrategyEffectiveness
    └── TimeTravelBenchmarks
```

### Testing Strategy

Each phase includes:
1. **Unit tests:** New functions, algorithms, parsers
2. **Integration tests:** API endpoints, strategy execution
3. **Visual tests:** UI components, responsive design
4. **Performance tests:** Large datasets, complex visualizations
5. **User acceptance tests:** Real-world scenarios, usability

### Deployment Strategy

- **Branch strategy:** `phase-1-visual`, `phase-2-time`, etc., merge to `v0.3-dev`
- **Feature flags:** Enable/disable features in production for gradual rollout
- **Incremental releases:** v0.3.1 (Phase 1), v0.3.2 (Phase 2), ..., v0.3.5 (Phase 5)
- **Backward compatibility:** All v0.2 strategies continue to work

---

## Fun Enhancements Summary

| Phase | Enhancement | Why It's Fun |
|-------|-------------|--------------|
| 1 | Council Constellations | Beautiful space-themed visualizations |
| 2 | Model Time Machine | Retro UI, time-travel animations |
| 3 | Council Evolution Simulator | Gamification with XP, badges, leaderboards |
| 4 | Philosopher's Arena | Historical roleplay, dramatic Greek styling |
| 5 | Council Arcade | Pixel art, achievements, retro gaming aesthetic |

---

## Cross-Pollination Matrix

|  | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 |
|---|---------|---------|---------|---------|---------|
| **Phase 1** | — | Maps show time evolution | Maps show adaptive weights | Maps show philosophical positions | Dark mode for maps |
| **Phase 2** | Historical consensus | — | Historical data → weights | Humility tracking over time | Dashboard time-travel view |
| **Phase 3** | Dynamic composition viz | Time-travel validates weights | — | Weights reward humility | Code execution informs weights |
| **Phase 4** | Philosophical consistency maps | Epistemic drift over time | Adaptive epistemic weights | — | Humility scores for code |
| **Phase 5** | Multi-modal consensus nodes | Fact-check code outputs | Multi-modal adaptive weights | Visual philosophy debates | — |

---

## Risk Mitigation

### Technical Risks
- **Consensus map performance:** Use WebGL for large graphs, lazy rendering
- **Time-travel storage:** Compress historical data, use append-only log
- **Code execution security:** Docker containers, strict resource limits, 5s timeout
- **API costs:** Cache fact-checks, rate limiting, budget alerts

### Scope Risks
- **Feature creep:** Stick to roadmap, resist adding more mid-phase
- **Complexity:** Each phase builds incrementally, can skip optional enhancements
- **Timeline slippage:** 15% buffer built into each phase

### User Experience Risks
- **Overwhelming UI:** Progressive disclosure, advanced features hidden in menus
- **Learning curve:** Tooltips, tutorial mode, documentation updates
- **Performance degradation:** Lazy loading, pagination, virtual scrolling

---

## Success Metrics

### Phase 1
- [ ] 90% of users find consensus maps intuitive (survey)
- [ ] SWOT analysis used in 20%+ of conversations
- [ ] Search/filter reduces time-to-conversation by 50%

### Phase 2
- [ ] Time-travel shows measurable model improvement (>10% better scores)
- [ ] Fact-checking identifies 5+ false claims per 100 conversations
- [ ] Model selector reduces config.py edits to zero

### Phase 3
- [ ] Dynamic composition saves 20% on API costs (vs fixed councils)
- [ ] Adaptive weights improve user satisfaction by 15%
- [ ] Multi-round convergence in <3 rounds for 80% of queries

### Phase 4
- [ ] Socratic mode rated "engaging" by 70%+ of users
- [ ] Epistemic scoring catches overconfidence in 30%+ of responses
- [ ] Philosophical consistency >80% for individual models

### Phase 5
- [ ] Code execution adds value in 40%+ of technical queries
- [ ] Dark mode adopted by 60%+ of users
- [ ] Dashboard visited weekly by 80%+ of active users

---

## Resource Requirements

### Development
- **Backend:** Python, FastAPI, async programming, NLP libraries
- **Frontend:** React, D3.js/React Flow, state management (Zustand/Redux)
- **Infrastructure:** Sandboxed execution environment (Docker), embedding APIs

### External Services
- Google Fact Check Tools API (free tier: 10k requests/day)
- OpenRouter (existing, variable costs)
- Embedding API for consensus maps (OpenAI embeddings or local model)

### Team Skills Needed
- Data visualization (D3.js, graph algorithms)
- NLP (claim extraction, similarity scoring)
- DevOps (Docker, security hardening)
- UX design (dashboards, responsive layouts)

---

## Next Steps

1. **Finalize plan:** Review this roadmap, gather feedback
2. **Set up infrastructure:** Create phase branches, CI/CD for testing
3. **Begin Phase 1:** Start with consensus maps (high visual impact)
4. **Weekly check-ins:** Review progress, adjust timeline as needed
5. **Document as we go:** Update CLAUDE.md with architectural decisions

---

## Appendix: Quick Reference

### Phase Deliverables Checklist

**Phase 1:**
- [ ] Visual consensus mapping (interactive + static)
- [ ] SWOT, cost-benefit, decision matrix frameworks
- [ ] Conversation search, filter, tags, archive
- [ ] Council Constellations fun enhancement

**Phase 2:**
- [ ] Time-travel benchmarking with drift detection
- [ ] Fact-checking integration with verification badges
- [ ] Model management UI with cost estimation
- [ ] Model Time Machine fun enhancement

**Phase 3:**
- [ ] Dynamic council composition with query classification
- [ ] Adaptive weighting 2.0 with Bayesian updates
- [ ] Multi-round recursive deliberation (N rounds)
- [ ] Council Evolution Simulator fun enhancement

**Phase 4:**
- [ ] Socratic dialogue mode
- [ ] Epistemic humility scoring
- [ ] Philosophical consistency checker
- [ ] Philosopher's Arena fun enhancement

**Phase 5:**
- [ ] Image analysis and code execution
- [ ] Response breeding with genetic algorithm
- [ ] Dark mode and visual polish
- [ ] Performance dashboards with analytics
- [ ] Council Arcade fun enhancement

---

**Document Status:** Final roadmap for v0.3 implementation
**Estimated Completion:** ~11 weeks from start
**Next Milestone:** Begin Phase 1 development
