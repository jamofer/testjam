# syntax=docker/dockerfile:1.7
#
# Thin per-PR layer on top of the pre-built e2e base image (chromium + node +
# python deps + rfbrowser/playwright). Source is copied last and re-installed
# with `--no-deps` so dependency resolution is skipped.
ARG E2E_BASE=ghcr.io/jamofer/testjam-e2e-base:latest
FROM ${E2E_BASE}

COPY client /client
COPY listener /listener
COPY tests/e2e /tests/e2e

RUN pip install --no-cache-dir --no-deps -e /client -e /listener -e /tests/e2e

WORKDIR /tests/e2e
