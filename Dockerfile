FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python deps — copied first to maximize layer cache hits
COPY requirements.txt .
RUN pip install -r requirements.txt

# Drop privileges
RUN useradd --create-home --shell /bin/bash app
USER app

# App code
COPY --chown=app:app . .

# Persist indexes across restarts
VOLUME ["/app/faiss_indexes"]

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
