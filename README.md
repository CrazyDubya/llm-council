# LLM Council v0.2 - Ensemble Strategy Playground

![llmcouncil](header.jpg)

The idea of this repo is that instead of asking a question to your favorite LLM provider (e.g. OpenAI GPT 5.1, Google Gemini 3.0 Pro, Anthropic Claude Sonnet 4.5, xAI Grok 4, etc.), you can group them into your "LLM Council" and let them collaborate through various deliberation strategies. This is a local web app that uses OpenRouter to orchestrate multi-model deliberation.

## What's New in v0.2

**Version 0.2** transforms LLM Council from a single-strategy prototype into an ensemble strategy playground:

- 🎯 **4 Deliberation Strategies**: Simple ranking, multi-round deliberation, reasoning-aware (for o1/DeepSeek), and weighted voting
- 🤖 **AI-Powered Strategy Selection**: Intelligent recommendations based on query type and historical performance
- 📊 **Analytics Dashboard**: Track model performance, win rates, and strategy effectiveness
- 👍 **User Feedback System**: Rate responses to improve future recommendations
- 🔄 **Multi-Round Deliberation**: Models iteratively refine their answers based on peer feedback
- 🧠 **Reasoning-Aware Evaluation**: Special handling for models that show their work (o1, DeepSeek-R1)
- ⚖️ **Performance-Weighted Voting**: Better models get more influence in the final ranking

## How It Works

### Basic Flow (Simple Strategy)

1. **Stage 1: First opinions**. The query is sent to all council models in parallel, responses are collected and displayed in tabs.
2. **Stage 2: Peer Review**. Each model ranks the responses (anonymized to prevent bias) based on accuracy and insight.
3. **Stage 3: Chairman Synthesis**. The designated Chairman model synthesizes all responses and rankings into a final answer.

### Advanced Strategies

- **Multi-Round**: After initial ranking, top-performing models' responses are shared with everyone. Models can then revise their answers based on peer work.
- **Reasoning-Aware**: Evaluates both the quality of reasoning (logic, rigor) and final answers separately, then combines scores.
- **Weighted Voting**: Uses historical performance data to give high-performing models more influence in rankings.

## Vibe Code Alert

This project was 99% vibe coded as a fun Saturday hack because I wanted to explore and evaluate a number of LLMs side by side in the process of [reading books together with LLMs](https://x.com/karpathy/status/1990577951671509438). It's nice and useful to see multiple responses side by side, and also the cross-opinions of all LLMs on each other's outputs. I'm not going to support it in any way, it's provided here as is for other people's inspiration and I don't intend to improve it. Code is ephemeral now and libraries are over, ask your LLM to change it in whatever way you like.

## Setup

### 1. Install Dependencies

The project uses [uv](https://docs.astral.sh/uv/) for project management.

**Backend:**
```bash
uv sync
```

**Frontend:**
```bash
cd frontend
npm install
cd ..
```

### 2. Configure API Key

Create a `.env` file in the project root:

```bash
OPENROUTER_API_KEY=sk-or-v1-...
```

Get your API key at [openrouter.ai](https://openrouter.ai/). Make sure to purchase the credits you need, or sign up for automatic top up.

### 3. Configure Models (Optional)

Edit `backend/config.py` to customize the council:

```python
COUNCIL_MODELS = [
    "openai/gpt-5.1",
    "google/gemini-3-pro-preview",
    "anthropic/claude-sonnet-4.5",
    "x-ai/grok-4",
]

CHAIRMAN_MODEL = "google/gemini-3-pro-preview"
```

## Running the Application

**Option 1: Use the start script**
```bash
./start.sh
```

**Option 2: Run manually**

Terminal 1 (Backend):
```bash
uv run python -m backend.main
```

Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
```

Then open http://localhost:5173 in your browser.

## Features

### Strategy Selection
Choose from 4 deliberation strategies via dropdown:
- **Simple Ranking**: Classic 3-stage approach (fastest)
- **Multi-Round**: 2-round iterative deliberation (thorough)
- **Reasoning-Aware**: For o1/DeepSeek models (explicit reasoning evaluation)
- **Weighted Voting**: Analytics-driven (experts get more weight)

### Smart Recommendations
As you type a query, the system analyzes it and suggests the best strategy:
- Technical questions → Multi-Round
- Logic/math problems → Reasoning-Aware
- Analytical comparisons → Weighted Voting
- Creative/factual queries → Simple Ranking

### Analytics Dashboard
Click the 📊 icon to view:
- Model leaderboard (win rates, average rankings)
- Strategy effectiveness metrics
- Usage statistics and feedback trends

### User Feedback
Rate any final answer with 👍/👎 to help improve recommendations.

## API Endpoints

The backend exposes a REST API (see `CLAUDE_v02.md` for details):

- `POST /api/strategies/recommend` - Get strategy suggestion for a query
- `POST /api/strategies/compare` - A/B test multiple strategies on same query
- `GET /api/analytics/*` - Various analytics endpoints
- `POST /api/conversations/{id}/messages/{index}/feedback` - Submit feedback

## Tech Stack

- **Backend:** FastAPI (Python 3.10+), async httpx, OpenRouter API
- **Frontend:** React + Vite, react-markdown for rendering
- **Storage:** JSON files in `data/conversations/` and `data/analytics/`
- **Package Management:** uv for Python, npm for JavaScript
- **Architecture:** Strategy pattern, analytics engine, query classifier

## Documentation

- **README.md** (this file): User guide and setup
- **CLAUDE_v02.md**: Complete technical documentation for v0.2 architecture
- **V02_IMPLEMENTATION_PLAN.md**: Original implementation roadmap
