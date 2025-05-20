# AskMyDocs

A secure, scalable, full-stack application for document management and intelligent querying using RAG (Retrieval-Augmented Generation) technology.

## Project Structure

```
.
├── backend/           # FastAPI backend
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/         # React frontend
│   ├── src/
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml
```

## Local Setup with Docker Compose

### Prerequisites

- Docker
- Docker Compose

### Running the Application

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd askmydocs
   ```

2. Start the application using Docker Compose:
   ```bash
   docker compose up --build
   ```

3. Access the applications:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Development

- The backend and frontend services are configured with hot-reloading for development.
- Backend code changes will automatically reload the FastAPI server.
- Frontend code changes will automatically reload the React development server.

## Features (Coming Soon)

- Document upload and management
- Advanced NLP features with RAG agents
- User authentication
- Document parsing with unstructured.io
- Elasticsearch integration
- AWS S3 storage integration

## Tech Stack

- Backend: FastAPI
- Frontend: React.js
- Database: PostgreSQL, Redis
- Document Parsing: unstructured.io
- Search Engine: Elasticsearch
- Containerization: Docker, Kubernetes 