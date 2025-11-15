# PyBrosLab
Buddy-lab to explore Python fundamentals alongside modern web stacks through a steady stream of hands-on projects.

## How We Use This Repo
- Capture every project spark in the Idea Backlog before the details fade.
- Discuss and score each idea with the Evaluation Matrix to decide what to build next.
- Promote the highest scoring idea into an active project and clone it into its own folder when ready.

## Active Project
We’re currently focused on the **AI Day Planner**: a FastAPI + SQLite backend (with spaCy + Google Places/Distance Matrix) and a static UI that lets us log tasks, infer locations, and generate daily schedules.

Key capabilities:
- `/` serves the planner UI for adding tasks, managing home location, and viewing time estimates.
- `/tasks` provides CRUD operations; new tasks auto-infer locations from title text.
- `/locations/home` stores the home base used for travel calculations.
- `/plan/*` endpoints generate or fetch daily plans with reminders.

## Idea Backlog (paused until planner MVP stabilizes)
| # | Idea | Python Angle | Web / Other Tech | Why It Matters | Status |
|---|------|--------------|------------------|----------------|--------|
| 1 | AI day-planner secretary | Parse TODO lists with spaCy + LLM, cluster tasks, and auto-generate day plans. | Mobile-friendly Next.js UI with push notifications; tie into Google Calendar + geofencing for location-aware reminders. | Forces us to mix NLP, scheduling logic, and contextual notifications like a true digital assistant. | In Progress |
| 2 | Paper-trade signal lab | Use `pandas` + `backtrader` to simulate technical indicators on historical OHLCV data. | Astro/React dashboard with live charts; deploy on Hugging Face Spaces for quick sharing. | Blends data engineering, finance APIs, and real-time dashboards without risking capital. | Backlog |
| 3 | API-powered practice journal | Build FastAPI endpoints that log coding sessions. | Vue or Svelte dashboard for charts; Supabase auth. | Keeps us accountable while touching CRUD, auth, and charting. | Backlog |
| 4 | Playlist sentiment explorer | Use `textblob` or `nltk` to score lyrics and audio features from Spotify API. | Next.js UI with server actions for searches. | Fun data science intro plus OAuth/API work. | Backlog |
| 5 | Micro SaaS uptime monitor | Async Python workers that ping URLs, store metrics, alert on Discord. | Remix front end for reports; Tailwind for quick styling. | Covers background jobs, persistence, and user-facing dashboards. | Backlog |

_Add new ideas at the bottom. Keep descriptions punchy so we can scan them fast._

## Evaluation Matrix
Score each criterion 1‑5 (low to high). Multiply or sum scores depending on how fine-grained we need the comparison to be that week.

| Criterion | Guiding Questions | Score | Notes |
|-----------|-------------------|-------|-------|
| Learning Impact | Does it stretch our Python + web skills or just repeat what we already know? |  |  |
| Scope Fit | Can two people ship a meaningful slice in 2‑3 weekends? |  |  |
| Tool Diversity | Does it introduce a new framework/library/datastore? |  |  |
| Collaboration | Are there natural parallel tracks (backend/frontend, infra/data)? |  |  |
| Portfolio Value | Would a recruiter care about the story/demo? |  |  |

> Tip: After scoring, jot the total in the Idea Backlog’s notes column so we can sort quickly.

## Local Setup
1. **Clone + venv**
   ```bash
   git clone git@github.com:jingteng25742/PyBrosLab.git
   cd PyBrosLab
   /opt/homebrew/bin/python3.11 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   python -m spacy download en_core_web_trf
   ```
2. **Configuration**
   - Create a `.env` (or export env vars) with:
     ```
     GOOGLE_MAPS_API_KEY=your-key
     ```
   - The app will create `data/planner.db` automatically.
3. **Run**
   ```bash
   uvicorn app.main:app --reload
   ```
   Visit [http://127.0.0.1:8000](http://127.0.0.1:8000) for the client UI.
4. **Seed sample tasks (optional)**
   ```bash
   python scripts/seed.py
   ```
