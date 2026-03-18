FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY backend/requirements.deploy.txt /tmp/requirements.deploy.txt

RUN pip install --upgrade pip && \
    pip install -r /tmp/requirements.deploy.txt

COPY backend /app/backend
COPY Lottery_data /app/Lottery_data

WORKDIR /app/backend

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-8080} Flask_app_simplified:app"]
