FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV POETRY_VERSION=1.8.2
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

WORKDIR /app

COPY pyproject.toml poetry.lock* ./

ENV POETRY_VIRTUALENVS_CREATE=false
RUN poetry install --no-root --only main

COPY src ./src

ENV PYTHONPATH=/app

EXPOSE 8080
# Cloud Run에서 제공하는 PORT 환경 변수를 사용하도록 수정하는 것이 좋습니다.
CMD ["gunicorn", "src.main:app", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8080", "--workers=2"]