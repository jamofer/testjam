FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .
RUN pip install --no-cache-dir -e ".[dev]"

RUN mkdir -p /app/uploads/cases /app/uploads/results

CMD ["uvicorn", "testjam.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
