# LandSearch Backend

LandSearch is a FastAPI-based backend service for processing, storing, and retrieving land survey documents and site plans. It provides endpoints for document upload, processing (including coordinate transformation), search, and retrieval, leveraging AI models and Supabase for storage.

## Features
- Upload and process land/site plan documents (PDF, image)
- AI-powered document extraction and coordinate transformation (Ghana National Grid to WGS84)
- Store, update, and retrieve processed and unapproved documents
- Search site plans by coordinates and metadata
- Prometheus metrics and health endpoints
- Sentry integration for error monitoring
- Supabase integration for persistent storage

## Installation

### Prerequisites
- Python 3.10+
- [Poetry](https://python-poetry.org/) (recommended) or pip

### Clone the repository
```powershell
git clone <repo-url>
cd landsearch-backend
```

### Install dependencies
#### Using Poetry
```powershell
poetry install
```
#### Using pip
```powershell
pip install -r requirements.txt
```

## Environment Variables
Create a `.env` file in the project root with the following variables:

| Variable                  | Description                                 |
|--------------------------|---------------------------------------------|
| SECRET_KEY                | JWT secret key                              |
| GEMINI_API_KEY            | Google Gemini API key                       |
| GEMINI_MODEL              | Gemini model version (default: gemini-1.5-pro-latest) |
| OPENAI_API_KEY            | OpenAI API key                              |
| ANON_PUBLIC               | Public key for authentication               |
| SECRET                    | Secret for authentication                   |
| SUPABASE_URL              | Supabase project URL                        |
| SUPABASE_KEY              | Supabase service key                        |
| SUPABASE_TABLE            | Supabase table name (default: LandSearch)   |
| SENTRY_DSN                | (Optional) Sentry DSN for error tracking    |
| LOG_LEVEL                 | (Optional) Logging level (default: INFO)    |
| ENVIRONMENT               | (Optional) Environment (default: production)|

Other settings (with defaults) can be found in `app/config/settings.py`.

## Running the Application

### Using Poetry
```powershell
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
### Using pip
```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- The API docs will be available at: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health check: [http://localhost:8000/health](http://localhost:8000/health)
- Prometheus metrics: [http://localhost:8000/metrics](http://localhost:8000/metrics)

## API Overview

### Main Endpoints
- `POST /api/document-processing/upload` — Upload and process site plan documents
- `PUT /api/document-processing/update-coordinates/{id}` — Update coordinates for a document
- `POST /api/document-processing/store-unapproved-siteplan/{user_id}` — Store unapproved document
- `PUT /api/document-processing/update-siteplan-unapproved/{id}` — Update unapproved document
- `PUT /api/document-processing/update-siteplan/{id}` — Update approved document
- `DELETE /api/document-processing/delete-document/{doc_id}` — Delete approved document
- `GET /api/site-plans/all/` — Retrieve all documents
- `GET /api/site-plans/unapproved` — Retrieve unapproved documents
- `POST /api/site-plans/document-search` — Search documents by coordinates/filters

See the FastAPI docs (`/docs`) for full request/response schemas.

## Project Structure
- `app/main.py` — FastAPI app entrypoint
- `app/api/` — API route definitions
- `app/core/` — Core logic for document upload, retrieval, and search
- `app/services/` — Services for document processing, storage, and coordinate computation
- `app/schemas/` — Pydantic models and schemas
- `app/config/` — Configuration and dependency injection
- `app/utils/` — Utilities (logging, monitoring, etc.)

## License
MIT License
