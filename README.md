# RAG Assistant

A small, end-to-end retrieval-augmented generation (RAG) app for asking questions about uploaded text documents. It combines a React interface, a FastAPI service, local text embeddings, PostgreSQL/pgvector retrieval, and Gemini answer generation.

I built this project to explore the engineering behind a document-grounded assistant: how to ingest source material, retrieve relevant passages, and constrain an LLM's answer to those passages. The interface is intentionally minimal so the retrieval pipeline and its tradeoffs are easy to inspect.

## Demo

![RAG Demo_Valid Question](demos\RAG_demo_valid.png)

After uploading [`tests/test.txt`](tests/test.txt), the RAG Assistant answers **“How close can a person get before the robots stop?”** with **1.5 metres** which corresponds to the correct answer in the package.

![RAG Demo_Invalid Question](demos\RAG_demo_invalid.png)

Upon asking something the handbook does not cover, such as its stock price, the RAG Assistant answers with the default `NOT_FOUND` behavior.

## What it does

- Accepts UTF-8 `.txt` uploads and rejects other extensions or invalid encoding.
- Splits each document into overlapping chunks and creates 1,024-dimensional embeddings locally.
- Stores the original document, ordered chunks, and embeddings in PostgreSQL with pgvector.
- Retrieves the three closest chunks by cosine distance for each question.
- Sends those retrieved passages and the question to Gemini, with an instruction to return `NOT_FOUND` when the context lacks the answer.
- Returns both the generated answer and retrieved chunks through the API. The current UI displays the answer; API clients can inspect the context.
- Supports document deletion through the API; database foreign-key cascading removes its chunks.

## Architecture

```mermaid
flowchart LR
    UI[React + Vite UI] -->|/api requests| API[FastAPI]
    API -->|upload .txt| Split[Chunk text<br/>600 characters, 80 overlap]
    Split --> Embed[Local BGE embeddings<br/>1,024 dimensions]
    Embed --> DB[(PostgreSQL + pgvector<br/>documents and chunks)]
    API -->|question| Query[Embed question<br/>with same model]
    Query --> Search[Cosine similarity<br/>top 3 chunks]
    DB --> Search
    Search --> LLM[Gemini<br/>answer from context]
    LLM --> API
    API -->|answer + retrieved context| UI
```

**Ingestion:** `POST /api/upload` validates and decodes a text file, splits it with `RecursiveCharacterTextSplitter`, embeds the chunks with `BAAI/bge-large-en-v1.5`, and saves the document and chunks. Each chunk records its document ID and position.

**Question answering:** `POST /api/ask` embeds the question with the same model, orders stored chunks by pgvector cosine distance, and supplies the closest three as context to Gemini. The API response includes the answer plus each retrieved chunk's ID, content, and document ID.

**Deletion:** `DELETE /api/delete/{document_id}` deletes a document and its associated chunks via `ON DELETE CASCADE`.

### Engineering decisions

| Decision | Why |
| --- | --- |
| Local `BAAI/bge-large-en-v1.5` embeddings | Keeps embedding generation in the application and makes document and query representations consistent. The model is loaded once per process with an LRU cache. |
| Normalized, 1,024-dimensional vectors | Matches the `vector(1024)` database column and supports cosine-based retrieval. |
| 600-character chunks with 80-character overlap | Keeps passages small enough to retrieve selectively while retaining some context across chunk boundaries. These are initial values, values could be further tuned after some testing. |
| PostgreSQL + pgvector | Stores documents and vectors in one database, with a foreign key for document ownership and an HNSW cosine index defined in the SQL schema for faster similar chunk retrieval. |
| Top-three retrieval | Caps the amount of source text sent to the generator and keeps the first version of the retrieval path straightforward. |
| Grounded prompt and `NOT_FOUND` instruction | Gives the model an explicit way to abstain when retrieved context does not contain an answer. This is a prompt-level safeguard, not a guarantee. |
| Vite proxy for `/api` | Lets the local React app call FastAPI without a separate browser-side API URL or local CORS configuration. |

## Tech stack

| Layer | Tools |
| --- | --- |
| Frontend | React, TypeScript, Vite, Bootstrap |
| API | Python, FastAPI, Pydantic |
| Text processing and embeddings | LangChain text splitters, Sentence Transformers, `BAAI/bge-large-en-v1.5` |
| Retrieval and persistence | PostgreSQL, pgvector, SQLAlchemy, psycopg |
| Generation | Google Gen AI SDK, Gemini (model configured in `backend/rag.py`) |
| Tests | pytest, FastAPI `TestClient` |

## Run locally

### Prerequisites

- Python 3.11, Node.js and npm, and Docker.
- A Gemini API key with access to the model configured in [`backend/rag.py`](backend/rag.py).
- Enough disk space to download the Sentence Transformers embedding model on first use.

Commands below are for PowerShell and run from the repository root unless a step says otherwise.

### 1. Start PostgreSQL and create the vector schema

```powershell
docker run --name rag-postgres -e POSTGRES_USER=raguser -e POSTGRES_PASSWORD=localdevpassword -e POSTGRES_DB=ragdb -p 5432:5432 -v rag_postgres_data:/var/lib/postgresql/data -d pgvector/pgvector:pg17
Get-Content backend/database_commands/create_tables.sql | docker exec -i rag-postgres psql -U raguser -d ragdb
```

The SQL creates the pgvector extension, the `documents` and `chunks` tables, and an HNSW index for cosine search. Run it **before starting the API**. The API also calls SQLAlchemy `create_all` at import time, which creates missing tables but does not create the HNSW index. The SQL script is intended for a fresh database and is not an idempotent migration.

On later runs, start the existing container with `docker start rag-postgres`; the named Docker volume preserves its data.

### 2. Configure the backend

Create a `.env` file in the repository root (it is gitignored):

```dotenv
DATABASE_URL=postgresql+psycopg://raguser:localdevpassword@localhost:5432/ragdb
GEMINI_API_KEY=your_api_key_here
```

Install Python dependencies:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

The backend reads `DATABASE_URL` through `python-dotenv`; the Google Gen AI client reads the API key from the environment. Keep real credentials out of version control. The first embedding request downloads the model, so first use can take longer.

### 3. Start the backend and frontend

In one terminal at the **repository root**:

```powershell
.venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload --port 8000
```

In another terminal at the repository root:

```powershell
npm ci
cd frontend
npm ci
npm run dev
```

Bootstrap is currently declared in the root `package.json`, while the React/Vite dependencies are in `frontend/package.json`; both installs are needed. Open the URL printed by Vite (typically `http://localhost:5173`). FastAPI's interactive API docs are at `http://localhost:8000/docs`. The Vite dev server proxies `/api` requests to port 8000.

## API at a glance

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/upload` | Multipart form field `file` containing a UTF-8 `.txt` file; returns document ID, filename, and chunk count. |
| `POST` | `/api/ask` | JSON body `{"question":"..."}` (1–500 characters); returns `response` and the retrieved `context` chunks. |
| `DELETE` | `/api/delete/{document_id}` | Deletes a document by UUID; returns the deleted ID. Available through the API, not yet the UI. |

## Project structure

```text
.
├── main.py                         # FastAPI routes and request validation
├── backend/
│   ├── rag.py                      # Chunking, embeddings, and Gemini call
│   ├── database.py                 # SQLAlchemy models and pgvector retrieval
│   └── database_commands/
│       └── create_tables.sql       # Initial schema, extension, and HNSW index
├── frontend/
│   ├── api.ts                      # Frontend API requests
│   └── src/
│       ├── App.tsx                 # Upload and question UI
│       └── main.tsx                # React entry point and Bootstrap import
├── tests/                          # API and database checks; sample text file
├── requirements.txt               # Python dependencies
└── README.md
```

## Tests

With PostgreSQL running and the backend environment configured, run:

```powershell
python -m pytest tests/test_upload.py tests/test_ask.py
```

The upload tests cover accepted and rejected file types; one test substitutes dummy embeddings. The question tests exercise real retrieval and generation against the sample document, so they require the database, embedding model, and Gemini access and can incur API usage. The current tests delete uploaded documents in the database after the tests have concluded. `tests/test_db.py` is a direct connection check (`python tests/test_db.py`), rather than a pytest test.

## Limitations

- Retrieval always returns the three closest chunks, even when none is relevant. There is no similarity threshold or reranking step.
- Questions search across all uploaded documents; users cannot select a document or filter the search.
- The API returns the retrieved chunks, but the UI does not show source passages alongside the answer.
- `NOT_FOUND` depends on the model following its prompt. Answer grounding and retrieval quality have not been systematically evaluated.

## Future improvements

- Add a relevance threshold and reranking, then measure retrieval performance on a representative question set.
- Add a document list with selection and deletion in the UI, and add the ability to scope retrieval to selected documents.
- Show cited passages and document names beside each answer so users can verify the source.
- Build an evaluation set with answerable and unanswerable questions to track retrieval accuracy, answer correctness, and appropriate abstention.
- Add upload limits and user-specific document access before making the app available to multiple users.
