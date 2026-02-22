# Copilot Instructions — The Newsline

## Project Overview

A news aggregation platform that consolidates articles from multiple outlets, scores them for **bias**, **credibility**, and **source agreement**, then presents a unified, citation-backed summary. The app is called "The Newsline".

## Architecture

- **Backend** (`backend/`): Python 3.12, FastAPI + Pydantic. Run with `uvicorn backend.main:app --reload` from the project root (the package uses relative imports).
- **Frontend** (`frontend/`): React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui. Run with `bun dev` (port 8080). Uses `@/` path alias → `src/`.
- **Dev proxy**: Vite proxies `/api/*` → `http://127.0.0.1:8000/*` (strips the `/api` prefix), so frontend fetch calls use `/api/stories` while the backend route is `/stories`.

## Data Flow & Model Boundary

Backend Pydantic models (`backend/models.py`) use **snake_case** (`bias_score`, `trust_score`). Frontend types (`src/types/news.ts`) use **camelCase** (`biasLean`, `credibilityScore`). All transformation between the two lives in `src/api/newsApi.ts` — when adding a backend field, mirror it in the `Backend*` interfaces there, then map it in the `transform*` functions.

Stories are identified by **slug** (generated from the heading). Both `backend/utils/slugify.py` and `newsApi.ts` have a `slugify` function — these must produce identical output for routing to work.

The frontend **gracefully falls back to mock data** (`src/data/mockNews.ts`) when the backend is unreachable, so it can be developed independently.

## Scoring Pipeline (`backend/scoring/`)

These modules are standalone scripts (not yet wired into the API):
- `sentiment_scoring.py` — subjectivity via `GroNLP/mdebertav3-subjectivity-english` + NLTK sentence tokenization.
- `agreement_scoring.py` — cross-article claim comparison using `sentence-transformers/all-MiniLM-L6-v2` embeddings + `facebook/bart-large-mnli` NLI.
- `credibility_scoring.py` — composite score: 40% reputation, 30% objectivity, 30% agreement, with penalties for contradictions/missing context.
- `gemini_article_aggregator.py` — calls Gemini (`gemini-3-flash-preview`) to produce a consolidated article with structured citations. Requires `GEMINI_API_KEY` in a `.env` file at the project root.

## Web Scraping (`backend/scraping/`)

`crawler.py` supports sitemap-based, recursive link-following, and Selenium fallback for JS-heavy pages. Scraped articles are saved to `backend/scraping/rag-source/article/`. Max 100 pages per site.

## Frontend Conventions

- **shadcn/ui primitives** live in `src/components/ui/`. Domain-specific components (e.g., `BiasMeter`, `CredibilityGauge`, `TopicCard`) live in `src/components/`.
- **Pages** are in `src/pages/`. Routes follow the pattern: `/topic/:slug`, `/topic/:slug/article/:articleId`, `/user/:userId`, `/source/:sourceId`. Add custom routes **above** the `*` catch-all in `App.tsx`.
- Data fetching uses `async` functions from `src/api/newsApi.ts` called in `useEffect`; `@tanstack/react-query` is installed but not yet used in pages — prefer it for new data-fetching code.
- Tests: `vitest` + `jsdom` + `@testing-library/react`. Run `bun test` from `frontend/`.

## Key Commands

```bash
# Backend
cd /path/to/project && pip install -r backend/requirements.txt
uvicorn backend.main:app --reload          # serves on :8000

# Frontend
cd frontend && bun install && bun dev      # serves on :8080

# Frontend tests
cd frontend && bun test
```

## Environment Variables

| Variable | Location | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | `.env` (project root) | Gemini API for article aggregation |
