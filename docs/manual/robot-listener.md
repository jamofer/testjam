# Robot Framework listener

> Traducción: [robot-listener.es.md](robot-listener.es.md).

The Robot listener ships inside the [`testjam-client`](../../testjam-client/) Python package as the optional `robot-listener` extra. It plugs into Robot Framework as a [listener interface v3](https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#listener-interface) and is the recommended way to make Testjam visible to a CI pipeline.

What the listener does on every `robot` run:

1. Authenticates against Testjam (Bearer token or `X-API-Key`).
2. Discovers and syncs **suites / cases / steps** from the Robot tree into the matching Testjam project.
3. Creates a fresh **automatic execution** for the run.
4. Streams per-step status, duration and logs to Testjam **live** as the run progresses — the run page updates in real time.

## Install

Install the `testjam-client` package with the `robot-listener` extra inside the same virtualenv that runs Robot:

```bash
pip install "./testjam-client[robot-listener]"
# or, when published:
pip install "testjam-client[robot-listener]"
```

## Run

```bash
TESTJAM_API_URL=http://your-host:8080/api/v1 \
TESTJAM_USER=admin TESTJAM_PASS=secret \
TESTJAM_PROJECT="My Project" \
robot --listener testjam_client.listener.TestjamListener tests/
```

Authentication is one of:

- `TESTJAM_USER` + `TESTJAM_PASS` (any user; admin recommended).
- `TESTJAM_API_KEY` (a project-scoped key issued from **Members → API tokens**).

When using `TESTJAM_API_KEY`, the project is fixed by the key — `TESTJAM_PROJECT` becomes a sanity check, not a router.

## Environment variables

| Variable              | Default          | Purpose                                                       |
|-----------------------|------------------|---------------------------------------------------------------|
| `TESTJAM_API_URL`     | required         | Base URL up to `/api/v1`.                                     |
| `TESTJAM_USER`        | —                | Login username when using Bearer auth.                        |
| `TESTJAM_PASS`        | —                | Login password.                                               |
| `TESTJAM_API_KEY`     | —                | Project-scoped API key (alternative to user/pass).            |
| `TESTJAM_PROJECT`     | required         | Project name. Created on the fly if missing and the user is allowed to. |
| `TESTJAM_VERSION`     | git tag / `dev`  | Version label attached to the execution.                      |
| `TESTJAM_ENVIRONMENT` | —                | Optional environment label.                                   |
| `TESTJAM_EXECUTION`   | auto             | Override the execution name; default is `<plan> <UTC>`.       |
| `TESTJAM_PLAN`        | —                | Plan name to attach. If unset, the listener uses an ad-hoc plan derived from the suite tree. |
| `TESTJAM_LOG_LEVEL`   | `INFO`           | Listener log verbosity.                                       |

## Mapping Robot → Testjam

The listener creates / updates entities in this order:

| Robot construct        | Testjam entity         | Notes                                                |
|------------------------|------------------------|------------------------------------------------------|
| Robot suite directory  | `TestSuite` (nested)   | Hierarchy mirrored 1:1.                              |
| `.robot` file          | `TestSuite` (leaf)     | Setup / teardown become suite-level step blocks.     |
| `Test Case`            | `TestCase`             | `[Tags]` map to Testjam tags.                        |
| Robot step             | `TestStep`             | Keyword name + args → step action.                   |
| Robot tag `id:<value>` | `TestCase.external_id` | Used by the importers and matchers.                  |

## Tag-driven custom fields

Robot tags of the form `cf:key=value` (or `cf:key=value1,value2` for multi-select fields) are parsed on every test, accumulated across the run and written onto `execution.custom_fields` when the run closes. Later tags overwrite earlier ones for the same key.

```robotframework
*** Test Cases ***
Login Happy Path
    [Tags]    smoke    cf:area=auth    cf:browsers=chrome,firefox
    Open Browser    ${URL}
    Input Text      id=user    admin
    ...
```

The keys must match active custom-field definitions of `entity_type=execution` on the project — unknown keys are silently discarded. Values are sent as raw strings, so use `text` or `single_select` / `multi_select` for tag-driven fields; `bool`, `number` and `date` reject string payloads.

## Tips

- **Idempotent**: re-running the same suite never duplicates cases. Add, rename and delete operations propagate to Testjam.
- **Listener pollution**: by default every sync writes a revision per touched case. A future improvement will collapse those into a single revision per sync.
- **Failure tolerance**: if Testjam is unreachable, the listener degrades gracefully — Robot keeps running and prints a warning. No state is buffered, so reconnect mid-run means the in-flight test will not have its events backfilled.

## Beyond the listener

If your test framework is not Robot, drive the REST API directly. The shape mirrors the listener:

```bash
# 1. Create an automatic execution
curl -X POST -H "X-API-Key: $KEY" $API/projects/$PID/executions \
  -d '{"name":"CI build #1234","plan_id":42,"type":"automatic"}'

# 2. Patch each result as the test reports
curl -X PATCH -H "X-API-Key: $KEY" $API/executions/$EID/results/$RID \
  -d '{"status":"passed","duration_ms":4321}'

# 3. Close the execution
curl -X PATCH -H "X-API-Key: $KEY" $API/executions/$EID \
  -d '{"status":"completed"}'
```

The REST contract is documented at `/api/docs` (Swagger UI) on every running instance.
