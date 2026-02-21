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