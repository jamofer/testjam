#!/bin/sh
set -e

alembic upgrade head

workers=${API_WORKERS:-1}
if [ "$workers" -gt 1 ]; then
  exec uvicorn testjam.main:app --host 0.0.0.0 --port 8000 --workers "$workers"
else
  exec uvicorn testjam.main:app --host 0.0.0.0 --port 8000 --reload
fi
