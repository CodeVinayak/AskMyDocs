# AskMyDocs

A secure, scalable, full-stack application for document management and intelligent querying using RAG (Retrieval-Augmented Generation) technology.

## 🚀 Quick Start

1. **Start the Backend**
   ```bash
   cd backend
   uvicorn main:app --reload
   ```
   The backend will be available at http://localhost:8000

2. **Start the Frontend**
   Open a new terminal window/tab:
   ```bash
   cd frontend
   npm start
   ```
   The frontend will be available at http://localhost:3000

---

## Project Structure

```
.
├── backend/           # FastAPI backend
│   ├── main.py
│   ├── requirements.txt
├── frontend/         # React frontend
│   ├── src/
│   ├── package.json
└── CHANGELOG.md      # Project changelog and TODOs
```

## Low Level Design (LLD) Diagram

![LLD Diagram](LLD.png)

## Local Setup (No Docker, No Cloud)

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL (local instance)
- Redis (local instance)
- Elasticsearch (local instance)

### Environment Variables
Create a `.env` file in the `backend/` directory with the following:
```
DATABASE_URL=postgresql://user:password@localhost:5432/askmydocs_db
REDIS_URL=redis://localhost:6379/0
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
GEMINI_API_KEY=your-gemini-api-key
```

### Backend Setup
1. (Recommended) Create and activate a Python virtual environment:
   ```bash
   cd backend
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run database migrations (if using Alembic) or ensure tables are created.
4. Start the FastAPI backend:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend Setup
1. Install Node dependencies:
   ```bash
   cd frontend
   npm install
   ```
2. Start the React frontend:
   ```bash
   npm start
   ```

### Access the Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Features
- Document upload and management (local file storage)
- Advanced NLP features with RAG agents (Gemini API)
- User authentication (JWT)
- Document parsing with unstructured.io
- Elasticsearch integration (local)

## Tech Stack
- Backend: FastAPI
- Frontend: React.js
- Database: PostgreSQL, Redis
- Document Parsing: unstructured.io
- Search Engine: Elasticsearch
- RAG LLM: Gemini API (google-generativeai)

## Notes
- All files are stored locally in the backend's `storage/` directory.
- No Docker, Kubernetes, or AWS is required or used.
- See `CHANGELOG.md` for pending work and project progress. 