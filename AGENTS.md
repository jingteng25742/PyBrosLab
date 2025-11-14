# PyBrosLab Agent Playbook

This file documents the autonomous (or just highly focused) roles we expect to rotate through while hacking on PyBrosLab projects. Each "agent" owns a narrow slice of decisions so that work keeps flowing even when only one of us is online.

## 1. Product Strategist Agent
- **Inputs:** Idea backlog from `README.md`, evaluation matrix scores, community feedback.
- **Outputs:** A single top-priority idea with a clearly scoped experiment brief (user story, success metric, guardrails).
- **Cadence:** Revisit after every demo session or when a blocker stalls development.
- **Hand-off:** Create an issue or short brief in the repo before development starts.

## 2. Backend Builder Agent
- **Scope:** FastAPI app inside `app/`, including SQLAlchemy models, services, and planner logic.
- **Checklist:**
  1. Add/adjust schemas in `app/schemas.py` and corresponding routes in `app/main.py`.
  2. Update `app/planner.py` if scheduling heuristics change.
  3. Maintain migrations or lightweight seed scripts (currently `scripts/seed.py`).
- **Definition of done:** Endpoint documented, unit tests exist in `tests/`, and sample data still seeds correctly.

## 3. Frontend/Client Agent
- **Scope:** Anything that consumes the API, currently the static client at `app/static/index.html` but could evolve into React/Next.js.
- **Checklist:**
  1. Verify API contracts using the latest docs/tests before building UI flows.
  2. Keep assets self-contained (no build step unless agreed).
  3. Document manual QA steps in PR descriptions.

## 4. Data & AI Experimenter Agent
- **Scope:** Prototypes around NLP, clustering, or LLM-powered planning (hook points live near `planner.py`).
- **Responsibilities:**
  - Produce notebooks or scripts under `experiments/` (create if needed) describing datasets, prompts, and evaluation metrics.
  - Keep dependencies isolated; update `requirements.txt` only when a prototype graduates into the core stack.

## 5. QA Custodian Agent
- **Scope:** Automated test authoring/running and general quality gates.
- **Tools:** `pytest`, FastAPI TestClient, any linters we adopt later.
- **Checklist:**
  1. Run `python3 -m pytest` inside the active virtualenv before every push.
  2. Backfill tests for new bugs to lock regressions.
  3. Track flaky tests in an issue and assign owners.

## 6. Ops & DX Agent
- **Scope:** Tooling, local dev ergonomics, deployment scripts.
- **Checklist:**
  1. Maintain dependency lists (`requirements.txt`, future lockfiles).
  2. Provide quick-start docs (e.g., how to create a virtualenv, run `uvicorn app.main:app --reload`).
  3. Create/monitor deployment workflows once we pick a target (Railway, Fly.io, etc.).

## Working Agreements
- Rotate agents each sprint so everyone touches strategy, code, and polish.
- When acting as multiple agents, explicitly call out which hat you wore in the PR description.
- If a decision spans multiple agents (e.g., planner changes affecting UI), schedule a short async design note before implementing.

> Tip: This is a living doc. Append new agents or retire old ones whenever the project structure evolves.
