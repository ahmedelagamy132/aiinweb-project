FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN echo "Installing backend requirements from requirements.txt:" \
    && cat requirements.txt \
    && echo "\n--- pip install output ---" \
    && pip install --no-cache-dir --progress-bar off -r requirements.txt \
    && pip install --no-cache-dir --progress-bar off alembic \
    && echo "\n--- pinned packages after install ---" \
    && pip freeze

COPY app ./app
COPY alembic.ini ./alembic.ini
COPY alembic ./alembic
COPY ingest_documents.py ./ingest_documents.py
COPY data ./data

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
