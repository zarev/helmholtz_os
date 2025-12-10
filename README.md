# Helmholtz OS — PoC tools for open-access paper scraping and a small LLM-backed memory PoC

This repository contains a small collection of proof-of-concept tools used to:
- scrape lists of open-access scientific papers and download PDFs (`open_access_scraper.py`, `web_scraper.py`)
- convert PDFs into Markdown using a vision+LLM flow (`pdf_to_markdown.py`)
- run a tiny FastAPI backend that stores simple "memories" (vector embeddings + content) and serves a minimal frontend (`backend/`)

The project is intended as a lightweight experimentation playground — not a production system. It demonstrates scraping, simple storage of text+embeddings (via `pgvector`), and how to plug-in a local LLM or fall back to deterministic components.

---

## Repository layout

- `open_access_scraper.py` — simple downloader that reads `data/open_access_papers.csv` and saves PDFs to `papers/`.
- `web_scraper.py` — helper module with dataclasses and CSV loaders to build scrape jobs from `data/` files.
- `pdf_to_markdown.py` — convert a PDF to page images and call Google Gemini (vision) to extract Markdown per page.
- `frontend/` — minimal static UI (`index.html`, `main.js`) used by the backend for demo purposes.
- `backend/` — small FastAPI application with:
  - `main.py` — API endpoints and static file mounting
  - `embedder.py` — deterministic placeholder embedder used for PoC
  - `llama_client.py` — adapter to a local llama.cpp HTTP server (with graceful fallbacks)
  - `db.py` — tiny psycopg2 helpers + migrations
  - `requirements.txt` — backend dependencies
- `data/` — example CSVs (`open_access_papers.csv`, `sources.csv`). Tests expect the provided entries.
- `tests/` — pytest unit tests for scraper and PDF conversion logic.
- `docker-compose.yml` — helper to run a `pgvector`-enabled PostgreSQL for local testing.
- `.env.example` — example environment variables for Gemini keys (see notes below).

---

## Quickstart (development)

Prerequisites: Python 3.10+ (recommended), `pip`, and optionally Docker if you prefer to run the DB via `docker-compose`.

1) (optional) Start PostgreSQL with pgvector via Docker Compose

```bash
docker-compose up -d
```

2) Create a virtual environment and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r backend/requirements.txt
```

3) Environment variables

- The backend expects a PostgreSQL accessible via `DATABASE_URL` (defaults to `postgresql://postgres:postgres@localhost:5432/tomo`).
- To use the PDF -> Markdown script with Google Gemini, set `GEMINI_API_KEY` in your environment (the script reads `GEMINI_API_KEY`). The repository includes `.env.example` with some example keys; copy it to `.env` and adjust as needed.
- If you have a local LLM HTTP server (e.g. a small `llama.cpp`-based server), set `LLAMA_SERVER_URL` and/or `LLAMA_SERVER_CMD` to let the backend start/control it.

Example `.env` (local development):

```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/tomo"
export GEMINI_API_KEY="your_gemini_key_here"
# Optional: address of a running LLM HTTP server
export LLAMA_SERVER_URL="http://127.0.0.1:8080"
```

4) Run backend (serves API and the static frontend)

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Visit http://127.0.0.1:8000/ to use the minimal UI.

5) Download example papers

```bash
python open_access_scraper.py
```

This reads `data/open_access_papers.csv` and writes PDFs into a `papers/` directory.

6) Convert a PDF to Markdown (requires Gemini API key)

```bash
# edit `pdf_to_markdown.py` constants or set env GEMINI_API_KEY and run
python pdf_to_markdown.py
```

Outputs: `output_with_images.md` and page images under `pdf_images/` by default.

---

## API endpoints (backend)

Once the backend is running, the main endpoints are:

- `GET /health` — return basic liveness
- `POST /talk` — body `{ "text": "...", "pet_id": optional }` — stores a memory (text + embedding) and returns a reply. The endpoint will try to call a running LLM server for embeddings/completions; if unavailable it falls back to the deterministic embedder and an echo-style reply.
- `POST /memories/search` — body `{ "text": "...", "k": 5 }` — returns nearest memories using pgvector if available.
- `POST /model/start` and `POST /model/stop` — start/stop a local model process if needed (backend uses `LLAMA_SERVER_CMD` or a provided command).

The frontend at `frontend/` uses `/talk` and `/memories/search` for demonstration.

---

## Design notes & architecture

- Deterministic embedder: `backend/embedder.py` implements `text_to_embedding()` using iterative hashing. This is intentionally simple so tests and demos run without large models.
- LLM adapter: `backend/llama_client.py` tries multiple common HTTP endpoints for embeddings and completions. If the server isn't reachable or returns unexpected shapes, it gracefully falls back to the deterministic embedder and a short deterministic completion.
- Storage: `backend/db.py` uses `psycopg2` and a simple SQL migration (`backend/migrations/001_init.sql`) to create a `memories` table with a `vector` column (pgvector). The migration is run automatically on backend startup in this PoC.
- PDF -> Markdown: `pdf_to_markdown.py` uses `pdf2image` to render PDF pages to images, saves them and sends each image to Google Gemini (vision) to request Markdown extraction. It implements retries for transient errors.

---

## Running tests

From the repository root:

```bash
pytest -q
```

The tests are focused on the CSV loaders (`web_scraper.py`) and the PDF->Markdown extraction logic (the latter stubs out the Google modules so tests run offline).

---

## Common troubleshooting

- Database connection errors: ensure `DATABASE_URL` is correct and the DB is reachable. The provided `docker-compose.yml` runs a `pgvector`-enabled Postgres container exposing `5432`.
- Gemini/API keys: `pdf_to_markdown.py` looks for `GEMINI_API_KEY`. The repository `.env.example` uses `MH_GEMINI_API_KEY` as a sample — prefer exporting `GEMINI_API_KEY` for the script.
- LLM server: if you want richer replies or embeddings, run a local LLM HTTP server and set `LLAMA_SERVER_URL`/`LLAMA_SERVER_CMD`. The backend adapter will try to hit common endpoints.

---

## Contributing

This repository is a PoC collection. If you plan to extend it:
- add appropriate input validation and error handling
- move sensitive configuration to secret stores (do not commit API keys)
- consider async DB drivers and prepared statements for production
- replace the deterministic embedder with a proper embeddings provider for real semantic search

If you'd like, I can also open a small checklist of follow-up improvements (CI, formatting, packaging, tests for backend endpoints).

---

## License

This repository does not include a license file. Add an appropriate `LICENSE` if you intend to share the code publicly.
