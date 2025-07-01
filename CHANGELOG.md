# AskMyDocs - Changelog & TODO

## [v1.0.0] - Initial Local-Only Release

### Major Changes
- Removed all AWS, Docker, and Kubernetes dependencies. Project runs fully locally.
- Switched from S3 to local file storage for document uploads.
- Replaced OpenAI with Gemini API for RAG agent (google-generativeai).
- Integrated unstructured.io for advanced document parsing.
- JWT-based authentication for secure API access.
- Elasticsearch, PostgreSQL, and Redis used as local services.
- Modern React frontend with Material-UI, JWT auth, and local API usage.
- All API requests routed through a custom Axios instance for auth.
- LLD diagram (class diagram) added and shown in README.
- .gitignore updated to exclude venv and all files in backend/storage.
- README simplified and updated for local setup and Gemini API usage.
- Assignment status and LLD diagram tracked in Assignment_Status.md.

### Completed
- [x] Frontend and backend refactored for local-only operation.
- [x] All cloud/container code and instructions removed.
- [x] Gemini API integrated for RAG queries.
- [x] Local file storage for uploads.
- [x] JWT authentication enforced.
- [x] LLD diagram and status file added.
- [x] .gitignore and README updated.
- [x] Full local workflow tested: register, login, upload, query, list, delete documents.

### Pending / Optional
- [ ] Add monitoring/logging (Prometheus, Grafana, ELK) if needed.
- [ ] Add demo screencast or live demo link.
- [ ] Add LangChain/LlamaIndex or agent frameworks if strict assignment compliance is required.
- [ ] Add more diagrams (sequence, deployment) if needed.

---

## Notes
- All major features are complete and work locally.
- See README for setup instructions and Assignment_Status.md for requirement tracking. 