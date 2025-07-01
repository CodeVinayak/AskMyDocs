# AskMyDocs

A full-stack app for document management and intelligent querying using RAG (Retrieval-Augmented Generation).

## Project Structure

```
.
├── backend/           # FastAPI backend
├── frontend/          # React frontend
└── CHANGELOG.md       # Project changelog and TODOs
```

## Low Level Design (LLD) Diagram

![LLD Diagram](LLD.png)

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL, Redis, Elasticsearch (local)

### Environment Variables
Create a `.env` file in `backend/`:
```
DATABASE_URL=postgresql://user:password@localhost:5432/askmydocs_db
REDIS_URL=redis://localhost:6379/0
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
GEMINI_API_KEY=your-gemini-api-key
```

### Backend
```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm start
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Features
- Document upload & management (local storage)
- RAG agent (Gemini API)
- User authentication (JWT)
- Document parsing (unstructured.io)
- Elasticsearch search

## Tech Stack
- FastAPI, React.js
- PostgreSQL, Redis
- unstructured.io, Elasticsearch
- Gemini API (google-generativeai)

## Notes
- All files are stored locally in `backend/storage/`.
- No Docker, Kubernetes, or AWS required.
- See `CHANGELOG.md` for progress. 