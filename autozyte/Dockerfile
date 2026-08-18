FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

COPY shop ./shop
COPY ferdai ./ferdai
COPY server ./server

CMD uvicorn server.main:app --host 0.0.0.0 --port ${PORT:-8000}
