#!/bin/sh
set -e

if [ -d /client ] && ! python -c "import testjam_client" 2>/dev/null; then
  pip install --quiet -e /client
fi

alembic upgrade head

workers=${API_WORKERS:-1}
if [ "$workers" -gt 1 ]; then
  exec uvicorn testjam.main:app --host 0.0.0.0 --port 8000 --workers "$workers"
else
  exec uvicorn testjam.main:app --host 0.0.0.0 --port 8000 --reload
fi
