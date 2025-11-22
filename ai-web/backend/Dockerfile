FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN echo "Installing backend requirements:" \
    && cat requirements.txt \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir alembic

COPY app ./app
COPY alembic.ini ./alembic.ini
COPY alembic ./alembic

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
