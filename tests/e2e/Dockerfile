# syntax=docker/dockerfile:1.7
#
# Thin per-PR layer on top of the pre-built e2e base image (chromium + node +
# python deps + rfbrowser/playwright). Source is copied last and re-installed
# with `--no-deps` so dependency resolution is skipped.
ARG E2E_BASE=ghcr.io/jamofer/testjam-e2e-base:latest
FROM ${E2E_BASE}

COPY testjam-client /testjam-client
COPY tests/e2e /tests/e2e

# Drop any editable install records left over from the base image stub so the
# real source layout takes over. Safe no-op when the base image is fresh.
RUN pip uninstall -y testjam-client testjam-listener testjam-e2e 2>/dev/null || true \
 && pip install --no-cache-dir --no-deps -e "/testjam-client[robot-listener]" -e /tests/e2e

WORKDIR /tests/e2e
