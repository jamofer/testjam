# syntax=docker/dockerfile:1.7
FROM python:3.14-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -e ".[dev]"

RUN mkdir -p /app/uploads/cases /app/uploads/results

CMD ["uvicorn", "testjam.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
