# The Newsline

A news aggregation platform that consolidates articles from multiple outlets, scores them for **bias**, **credibility**, and **source agreement**, then presents a unified, citation-backed summary.

---

## Stack

| Layer | Tech |
|---|---|
| Backend | Python 3.12, FastAPI, Pydantic |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui |
| AI Aggregator | Google Gemini (`gemini-3-flash-preview`) |
| Scoring | HuggingFace Transformers, sentence-transformers |

---

## Running Everything

Open **two terminal tabs** from the project root.

### 1 — Backend (FastAPI, port 8000)

```bash
# From the project root
python -m venv .venv          # only needed once
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt

uvicorn backend.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

### 2 — Frontend (Vite, port 8080)

```bash
cd frontend
bun install    # or: npm install
bun dev        # or: npm run dev
```

Open `http://localhost:8080` in your browser.

> The Vite dev server proxies `/api/*` → `http://127.0.0.1:8000` automatically, so no CORS configuration is needed.

---

## Environment Variables

Create a `.env` file in the **project root**:

```
GEMINI_API_KEY=your_key_here
```

This is required only for the Gemini article aggregator (`backend/scoring/gemini_article_aggregator.py`). The API and frontend work without it using mock/generated data.

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/stories` | All consolidated stories with scoring |
| GET | `/stories/{slug}` | Single story by URL slug |
| GET | `/users` | All user profiles |
| GET | `/user/{id}` | Single user by id or username |

Interactive docs: `http://127.0.0.1:8000/docs`

---

## Project Structure

```
backend/
  main.py                    # FastAPI app + CORS
  models.py                  # Pydantic models (TopicSummary, Article, etc.)
  api/stories.py             # Route handlers
  data/mockData.py           # Loads generatedTopics.json, fallback mock data
  scoring/
    sentiment_scoring.py     # Subjectivity scoring (GroNLP model)
    agreement_scoring.py     # Cross-article claim comparison (MiniLM + BART)
    credibility_scoring.py   # Composite credibility (reputation + objectivity + agreement)
    gemini_article_aggregator.py  # Calls Gemini to produce consolidated article
  scraping/
    crawler.py               # Sitemap + recursive scraper with Selenium fallback
  utils/slugify.py

frontend/src/
  api/newsApi.ts             # Fetch helpers + snake_case → camelCase transforms
  types/news.ts              # TypeScript types
  pages/                     # Index, TopicDetail, ArticleDetail, UserProfile, SourceProfile
  components/                # BiasMeter, CredibilityGauge, CitedContent, SourceList, …
  data/mockNews.ts           # Frontend fallback mock data

generatedTopics.json         # Real Gemini aggregator output (served by backend)
```

---

## Scoring Pipeline

Each story is built from N article sources scraped across outlets:

1. **`sentiment_scoring.py`** — scores each article for subjectivity/objectivity
2. **`agreement_scoring.py`** — embeds claims with MiniLM, runs NLI (BART) to detect entailment/contradiction across articles
3. **`credibility_scoring.py`** — composite per-article score: `0.4 × reputation + 0.3 × objectivity + 0.3 × agreement`, penalised for contradictions and missing context
4. **`gemini_article_aggregator.py`** — calls Gemini to produce a structured consolidated article with per-section citations and bias labels

Each `SummarySection` carries its own `credibility_score` and `agreement` derived from its cited sources.

---

## Notes

- The frontend **gracefully falls back to `mockNews.ts`** when the backend is unreachable.
- The backend **falls back to inline mock topics** when `generatedTopics.json` is absent.
- No authentication is included (MVP).
- Storage is file/in-memory; a database can be wired in later.