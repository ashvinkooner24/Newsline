## Inspiration
We were frustrated by how hard it is to answer a simple question: “what actually happened?” without wading through clickbait, partisan spin, and conflicting headlines. We wanted a way to check out the story and the sources at the same time - not just “left vs right”, but how strongly each claim is supported, and who’s shaping the narrative.

## What it does
The system scrapes a set of major outlets, clusters articles about the same topic, and uses an LLM to synthesize a single, modular, neutrally-worded article (our Newsblends). Each section of the Newsblend carries live metrics: how many sources back it, how aligned they are, political bias and credibility scores, and emotional tone. On hover, you see a dropdown of outlets and quotes that support that specific passage, turning the article into an interactive, explorable explanation of all the accounts. __**Your opinions are your own.**__

## Structure

- backend/
  - app.py (Flask API)
  - requirements.txt
- frontend/
  - package.json
  - App.js
  - index.js
  - index.html

## Setup

### Backend
1. Navigate to `backend`.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run Flask server:
   ```bash
   python app.py
   ```

### Frontend
1. Navigate to `frontend`.
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start React app:
   ```bash
   npm start
   ```

## Usage
- React frontend fetches data from Flask backend at `/api/data`.
- Make sure Flask runs on port 5000 and React on 3000 (default).

## Customization
- Add more API endpoints in `app.py`.
- Expand React components in `App.js`.

# Backend API for News Aggregation Platform

## Setup
 pray 
1. Create and activate your Python virtual environment:
   
   python -m venv .venv
   .venv\Scripts\Activate.ps1

2. Install dependencies:
   
   pip install -r Backend/requirements.txt

3. Run the FastAPI server:
   
   uvicorn Backend.main:app --reload

## API Endpoints

- GET /stories — Returns all stories (mock data)
- GET /stories/{story_id} — Returns a single story by index

## Structure

- Backend/models.py — Data models
- Backend/main.py — FastAPI app and mock data
- Backend/requirements.txt — Python dependencies

## Notes
- Embedding and chunking logic is stubbed for later LLM integration.
- No authentication included (MVP).
- Storage is in-memory/mock for now; MongoDB can be integrated later.


## To run article ingestion pipeline 
python backend.scoring.pipeline.run_pipeline(directory: string)
