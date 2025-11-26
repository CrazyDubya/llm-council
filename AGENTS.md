# Repository Guidelines

## Project Structure & Module Organization
- `backend/` houses the FastAPI service (`main.py`), strategy engines (`backend/strategies/`), analytics, and OpenRouter integration. Runtime JSON lives under `data/` and `experiment_outputs/`.
- `frontend/` is a Vite/React app; `src/components/` contains chat, analytics, and workbench UIs, while `src/api.js` centralizes HTTP calls.
- Entry scripts: `start.sh` spins up both tiers, `LaunchCouncil.command` does the same via macOS double-click, and `run_experiments.py` batches council runs for benchmarking.

## Build, Test, and Development Commands
- `uv sync` then `uv run python -m backend.main` starts the API on `:8001`.
- `cd frontend && npm install` installs UI deps; `npm run dev -- --host 127.0.0.1 --port 5173` launches the web client.
- `uv run python run_experiments.py --question "Prompt" --strategies simple weighted_voting` executes scripted trials and logs under `experiment_outputs/`.
- No automated tests exist; rely on end-to-end manual flows (new chat, switching strategies/councils, running the workbench) plus targeted `curl` hits for backend endpoints.

## Coding Style & Naming Conventions
- Python: 4-space indent, snake_case, and prefer dependency-injected helpers over globals. Keep council configs in `backend/config.py`; new strategies subclass `EnsembleStrategy` and expose `get_name`/`get_description`.
- React: functional components with hooks, camelCase props/state, and colocated CSS modules. Fetch logic stays inside `src/api.js`; components receive callbacks instead of touching global state.
- Naming: conversations use UUIDs, strategy ids stay lowercase with underscores (`multi_round`). Keep files descriptive (`StrategyWorkbench.jsx`, `Stage3.css`).

## Testing Guidelines
- Exercise `/api/conversations`, `/api/councils`, and `/api/strategies/compare` locally before pushing. Confirm streaming (`/message/stream`) with the `simple` strategy and fall back to `/message` for others.
- In PRs, list manual test cases (e.g., "multi-round, 3 rounds, hybrid council"), plus any experiment scripts executed.

## Commit & Pull Request Guidelines
- Follow the short, descriptive commit style in history (`🚀 UI: council presets picker`). Group backend and frontend work into separate commits when practical.
- PRs need: summary of changes, repro + validation steps, screenshots/GIFs for UI tweaks, updated experiment logs when behavior shifts, and callouts for config/env additions (e.g., new OpenRouter models or pricing tables).
