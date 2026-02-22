# Web App Template: Python (Flask) Backend & React Frontend

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