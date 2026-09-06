# Pinned to 3.13: pydantic-core and Pillow have no 3.14 wheels yet and would
# fall back to compiling from source.
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Requirements first so the dependency layer is cached across source changes.
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --upgrade pip && pip install -r backend/requirements.txt

COPY backend/ backend/
COPY alembic.ini alembic.ini

# Writable location for SQLite, Chroma and uploaded blobs.
RUN mkdir -p backend/storage

EXPOSE 8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
