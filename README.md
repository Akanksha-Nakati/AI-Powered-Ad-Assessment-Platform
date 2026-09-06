# AI-Powered Ad Assessment Platform

Upload an ad creative and get a scored, cited critique: six criteria out of ten, written
feedback, concrete recommendations, and the marketing guidance each judgement rests on.
Add your own brand guidelines and they are cited alongside general best practice. Upload
several variants and get them ranked.

Gemini reads the image, a Chroma vector store retrieves relevant guidance, and Claude
scores the ad against it.

## How it works

```
                   ┌─────────────────────────────────────────────┐
  ad image  ──────►│ 1. Gemini vision    structured description  │
                   │ 2. Chroma retrieval  brand + global guidance│
                   │ 3. Claude scoring    schema-enforced JSON   │
                   └─────────────────────────────────────────────┘
                                    │
                                    ▼
                     scores · feedback · recommendations · citations
```

The pipeline is ports-and-adapters: `app/services` orchestrates against Protocols in
`app/domain/ports.py`, and `app/container.py` is the only module that picks a concrete
provider. That is what lets the whole flow run in tests with no network and no API keys.

## Quick start

### Docker (recommended)

```bash
cp .env.example .env   # add GOOGLE_API_KEY and ANTHROPIC_API_KEY
```

```bash
docker compose up --build
```

The UI is on <http://localhost:8080> and the API on <http://localhost:8000>
(interactive docs at `/docs`).

### Local

Python 3.13 — `pydantic-core` and `Pillow` have no 3.14 wheels yet and would try to
compile from source.

```bash
cp .env.example .env && bash start.sh
```

```bash
cd frontend && npm install && npm run dev
```

The frontend calls relative `/api` paths, which Vite proxies to the backend, so there is
no host to configure.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `GOOGLE_API_KEY` | — | Gemini vision and embeddings. Always required. |
| `ANTHROPIC_API_KEY` | — | Claude scoring. Required unless `SCORING_PROVIDER=gemini`. |
| `SCORING_PROVIDER` | `claude` | `claude` or `gemini`. |
| `VISION_PROVIDER` | `gemini` | Vision analysis provider. |
| `DATABASE_URL` | SQLite in `backend/storage/` | Point at `postgresql+asyncpg://…` for Postgres. |
| `FRONTEND_ORIGIN` | localhost dev origins | Locks CORS to one origin. |

Missing credentials fail at startup with the full list, not on the first request.

## API

All routes are under `/api/v1`.

| Method | Path | |
|---|---|---|
| `POST` | `/assessments` | Score one ad. Multipart: `ad_image`, `platform`, `industry`, `ad_type`, optional `brand_id`. |
| `GET` | `/assessments` | History, newest first (`limit`, `offset`). |
| `GET` | `/assessments/{id}` | One assessment. |
| `POST` | `/comparisons` | Rank 2–5 variants. Multipart: repeated `ad_images` plus the same fields. |
| `POST` | `/brands` · `GET` `/brands` | Create and list brands. |
| `GET` `DELETE` | `/brands/{id}` | Fetch or remove a brand and its vectors. |
| `GET` `POST` | `/brands/{id}/documents` | List and upload brand guidelines (`.md`/`.txt`). |
| `GET` | `/health` | Readiness and active providers. |

## Design notes

**Structured output, not prompt-and-parse.** Both providers are given the `AdScorecard`
schema — Claude via `messages.parse`, Gemini via `response_schema` — so a malformed reply
is impossible rather than silently caught. A scorecard missing any criterion is rejected,
and `overall_score` is derived from the per-criterion scores so the headline figure cannot
disagree with the bars.

**One contract, generated downstream.** The Pydantic models are the API's response models,
the providers' output schema, and the source of the frontend's TypeScript types (via
`openapi-typescript`). CI regenerates both and fails if the committed versions drift, so
a backend rename breaks the frontend build instead of blanking a panel at runtime.

**Retrieval splits its budget.** Brand documents and global best practice are queried
separately and merged, rather than taking a single top-k across both. A brand with many
documents would otherwise crowd out the general guidance entirely, and citing both is the
point.

**The vector store knows what embedded it.** The persisted index records its embedding
model and a corpus fingerprint. Changing either forces a rebuild, because similarity
against a differently-embedded index is meaningless rather than merely stale.

**Assessments are cached** on the image digest, the placement, the prompt version and the
model — so re-running the same ad is free, while a prompt edit correctly invalidates.

## Development

```bash
pytest -q && ruff check . && mypy
```

Tests use the fakes in `backend/tests/fakes.py`, which satisfy the same Protocols as the
real adapters. The suite makes no network calls and needs no credentials — if it ever
asks for a key, something has started calling a provider.

After changing the API, regenerate the contract:

```bash
python -m backend.app.cli openapi && npm --prefix frontend run gen:api
```

Schema changes are Alembic migrations:

```bash
alembic revision --autogenerate -m "describe the change" && alembic upgrade head
```

## Layout

```
backend/
  app/
    api/          routers, dependencies, one error-mapping module
    domain/       models, criteria and rubrics, errors, Protocol ports
    services/     assessment, comparison, knowledge orchestration
    infra/        llm/ rag/ db/ storage/ adapters
    container.py  composition root
  alembic/        migrations
  tests/          fakes and the suite that uses them
frontend/src/
  app/            layout and routes
  features/       assess · compare · history · brands
  components/ui/  shared presentational pieces
  lib/api/        generated schema, typed client
```
