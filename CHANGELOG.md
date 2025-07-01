# AskMyDocs - Changelog & TODO

## [Unreleased]

### Frontend
- [x] Reviewed all React components and context for local API usage and JWT authentication.
- [x] Confirmed no AWS or cloud dependencies in frontend code.
- [ ] Ensure all API endpoints match backend changes (after backend refactor).

### Backend
- [x] Reviewed backend for AWS S3, OpenAI, and Docker/K8s dependencies.
- [x] Remove all AWS S3 code and replace with local file storage for document uploads.
- [x] Remove all OpenAI/ChatOpenAI code and integrate Gemini API for RAG agent.
- [x] Update requirements.txt to remove boto3, openai, and add google-generativeai (Gemini).
- [x] Refactor /upload/ endpoint to save files locally and update storage_path usage.
- [x] Refactor /query/ endpoint to use Gemini API for answer generation.
- [x] Update README for local-only setup and remove Docker/K8s/AWS instructions.

### General
- [x] Deleted all Docker, Docker Compose, and Kubernetes files.
- [x] Deleted all cloud-specific instructions from project root.
- [ ] Update README to reflect local setup and Gemini API usage.
- [ ] Test full local workflow: register, login, upload, query, list, delete documents.

---

## Pending
- [ ] Update frontend if backend API changes.
- [ ] Update documentation for local setup.
- [ ] Test full local workflow.

---

## Notes
- Always refer to this file for what is pending and what has changed.
- All changes should be tracked here for future reference. 