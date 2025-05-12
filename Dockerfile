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


EXPOSE 8080
CMD ["gunicorn", "--pythonpath", "/app", "src.main:app", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8080", "--workers=2"]
