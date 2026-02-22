# The Newsline

Imagine if every breaking story came with x‑ray vision. We ingest coverage from across the media ecosystem, then reconstruct a clean, neutral narrative - making credibility & bias visible at a glance. 

# Inspiration
We were frustrated by how hard it is to answer a simple question: “what actually happened?” without wading through clickbait, partisan spin, and conflicting headlines. We wanted a way to check out the story and the sources at the same time - not just “left vs right”, but how strongly each claim is supported, and who’s shaping the narrative.

# What it does
The system scrapes a set of major outlets, clusters articles about the same topic, and uses an LLM to synthesize a single, modular, neutrally-worded article (our Newsblends). Each section of the Newsblend carries live metrics: how many sources back it, how aligned they are, political bias and credibility scores, and emotional tone. On hover, you see a dropdown of outlets and quotes that support that specific passage, turning the article into an interactive, explorable explanation of all the accounts. Your opinions are your own.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | Python 3.11 · FastAPI · Uvicorn |
| AI / ML | Google Gemini (`gemini-3-flash-preview`) · HuggingFace Transformers · sentence-transformers · PyTorch |
| Database | MongoDB (with in-memory/mock fallback) |
| Scraping | Selenium · newspaper3k · BeautifulSoup |
| Frontend | React 18 · TypeScript · Vite · shadcn/ui · Tailwind CSS |

---

## Project Structure

```
backend/
  main.py                  # FastAPI app, CORS config, router registration
  models.py                # Pydantic models (StoryWrapper, Story, Segment, ...)
  mongodb.py               # MongoDB connection helpers
  topic_assignment.py      # Assigns scraped articles to topics
  api/
    stories.py             # /stories, /pipeline/status, /stories/ingest endpoints
  data/
    mockData.py            # Seed data loaded from stories.json
    stories.json
  scoring/
    pipeline.py            # Orchestrates the full scoring pipeline + cache
    sentiment_scoring.py   # Objectivity / subjectivity per article
    agreement_scoring.py   # Entailment / contradiction / missing-context detection
    credibility_scoring.py # Composite credibility score per article
    gemini_article_aggregator.py  # Gemini structured-output aggregation
  scraping/
    crawler.py             # Main web crawler
  utils/
    slugify.py

frontend/
  src/
    pages/                 # Index, TopicDetail, ArticleDetail, SourceProfile, UserProfile
    components/            # BiasMeter, CredibilityGauge, ToneAnalysis, FactCheckDisplay, ...
    api/newsApi.ts         # Typed API client (fetches from FastAPI)
    types/news.ts          # Shared TypeScript types
```

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+ (or Bun)
- A `GEMINI_API_KEY` environment variable (or `.env` file in the repo root)

### Backend

```powershell
# 1. Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the FastAPI server (auto-reload)
uvicorn backend.main:app --reload
```

The API will be available at `http://localhost:8000`.

### Frontend

```bash
# From the repo root
cd frontend

# Install dependencies (npm or bun)
npm install   # or: bun install

# Start the dev server
npm run dev   # or: bun run dev
```

The app will be available at `http://localhost:5173`.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/stories` | Returns all scored stories |
| `GET` | `/stories/{slug}` | Returns a single story by slug |
| `POST` | `/stories/ingest` | Runs the full pipeline on a directory of `.txt` articles |
| `GET` | `/pipeline/status` | Current state of the background scoring pipeline |
| `GET` | `/users` | Returns all users |
| `GET` | `/user/{username}` | Returns a single user profile |

#### Ingest request body

```json
{ "articles_dir": "backend/scoring/test" }
```

---

## Scoring Pipeline

`POST /stories/ingest` (or calling `run_pipeline(articles_dir)` directly) executes:

1. **Sentiment scoring** — classifies each article as objective or subjective
2. **Agreement scoring** — detects entailment, contradiction, and missing context across sources
3. **Credibility scoring** — composite score combining sentiment + source reputation
4. **Gemini aggregation** — structured JSON summary with inline citations, bias labels, and body sections

Results are cached in memory and persisted to `backend/data/stories.json`.

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini API key |
| `MONGODB_URI` | MongoDB connection string (optional; falls back to mock data) |

---

## Notes

- No authentication is included (MVP).
- The frontend falls back to mock data (`mockNews.ts`) when the backend is unreachable.
- Source reputation scores are configured in `backend/scoring/pipeline.py` (`SOURCE_REPUTATION` dict).
