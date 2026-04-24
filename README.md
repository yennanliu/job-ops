# job-ops

AI-powered resume tailoring app using a multi-agent LangGraph pipeline + FastAPI + OpenAI.

## Structure

```
job-ops/
├── agent/
│   ├── config.py       — Settings (OpenAI key, model names)
│   ├── designer.py     — Resume structure parser for PDF export
│   ├── graph.py        — LangGraph pipeline definition
│   ├── nodes.py        — All agent node functions
│   ├── prompts.py      — System prompts for each agent
│   └── state.py        — ResumeState TypedDict
├── static/
│   ├── app.js          — Shared JS utilities
│   ├── history.html    — History page
│   ├── index.html      — Main tailoring UI
│   └── style.css       — Shared styles
├── tests/
│   ├── test_api.py     — FastAPI route integration tests
│   ├── test_db.py      — SQLite layer unit tests
│   └── test_nodes.py   — Agent node unit tests
├── db.py               — SQLite persistence layer
├── main.py             — FastAPI app with all routes
├── run.py              — CLI test runner
└── pyproject.toml      — uv project config
```

## Setup

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
uv sync
```

## Run

```bash
uv run uvicorn main:app --reload
# Open http://localhost:8000
```

## Test

```bash
uv run pytest
```

## Agent Pipeline

```
START → Parse → ATS Scan → Rewrite → Cover Letter → Recruiter ─┐
                                                                 ├→ Score → END
                                                   Hiring Mgr ──┘
```

1. **Parse** — validates inputs, initializes state
2. **ATS Scan** — scores keyword match between resume and JD
3. **Rewrite** — tailors resume using ATS feedback
4. **Cover Letter** — generates a role-specific cover letter
5. **Recruiter** + **Hiring Manager** — run in parallel, evaluate fit
6. **Score** — aggregates ATS (40%) + hiring manager (60%) scores

Supports multiple iterations (×1–×5) where each round feeds the previous feedback back into the rewriter.
