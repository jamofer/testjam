#!/bin/sh
set -e

if [ -d /testjam-client ] && ! python -c "import testjam_client, click_repl, platformdirs" 2>/dev/null; then
  pip install --quiet -e "/testjam-client[cli]"
fi

alembic upgrade head

workers=${API_WORKERS:-1}
if [ "$workers" -gt 1 ]; then
  exec uvicorn testjam.main:app --host 0.0.0.0 --port 8000 --workers "$workers"
else
  exec uvicorn testjam.main:app --host 0.0.0.0 --port 8000 --reload
fi
