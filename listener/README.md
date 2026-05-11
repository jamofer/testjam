# testjam-listener

Robot Framework listener that streams results into a
[Testjam](../README.md) server in real time. Creates a fresh execution per
run, discovers and synchronises suites / cases / steps from the Robot tree,
and reports pass/fail + per-step duration + per-line logs as tests run.

## Install

```bash
pip install testjam-listener
```

## Run

```bash
TESTJAM_API_URL=http://localhost:8000/api/v1 \
TESTJAM_USER=admin \
TESTJAM_PASS=secret \
TESTJAM_PROJECT="Robot Framework" \
robot --listener testjam_listener.TestjamListener tests/
```

Auth: either `TESTJAM_USER` + `TESTJAM_PASS` (admin login) **or**
`TESTJAM_API_KEY`. `TESTJAM_PROJECT` is the destination project (created
if missing).

## Streaming behaviour

While a keyword runs:

1. `start_keyword` → `POST /results/{id}/step-results` (status `running`).
2. `log_message` → `POST /results/{id}/step-results/{step_result_id}/log`
   per line.
3. `end_keyword` → `PUT /results/{id}/step-results/{step_result_id}` with
   final status + duration + accumulated log output.

If the server rejects any of these endpoints with a 4xx the listener
disables streaming for the rest of the run and falls back to a single
batched `POST /executions/{id}/results` at `end_test` (legacy mode).
