FROM python:3.12-slim

WORKDIR /tests/e2e

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates gnupg \
 && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
 && apt-get install -y --no-install-recommends nodejs \
 && rm -rf /var/lib/apt/lists/*

COPY . .
RUN pip install --no-cache-dir .
RUN rfbrowser init chromium \
 && npx --yes playwright install-deps chromium
