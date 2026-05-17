FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates gnupg \
 && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
 && apt-get install -y --no-install-recommends nodejs \
 && rm -rf /var/lib/apt/lists/*

COPY client /client
COPY listener /listener
COPY tests/e2e /tests/e2e

RUN pip install --no-cache-dir -e /client -e /listener -e /tests/e2e
RUN rfbrowser init chromium \
 && npx --yes playwright install-deps chromium

WORKDIR /tests/e2e
