FROM python:3.12-slim

WORKDIR /app

COPY . .
RUN pip install --no-cache-dir ".[dev]"

RUN mkdir -p /app/uploads/cases /app/uploads/results

CMD ["uvicorn", "testjam.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
