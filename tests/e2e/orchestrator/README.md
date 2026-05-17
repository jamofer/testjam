# orchestrator

Launches one `robot` execution per leaf suite in parallel against a Testjam
server. Each subprocess gets its own `TestjamListener` instance so each leaf
suite becomes its own Testjam execution — that keeps the live-scroll feature
sane (step events stay serialised inside one execution) while still running
N suites in parallel.

## How it works

1. **Discovery** uses `robot.api.TestSuiteBuilder` to walk a root directory,
   collecting every leaf suite (a suite that owns tests directly). Names come
   from Robot itself, so the orchestrator's `longname` matches the listener's
   view of the world.
2. **Pre-flight**: the listener bootstraps the project + version
   (`TESTJAM_VERSION` env) at construction time via the SDK.
3. **Pool**: a `ProcessPoolExecutor` runs `robot.run` per leaf, feeding it a
   freshly-built `TestjamListener` and overriding
   `TESTJAM_EXECUTION_TITLE` with the suite's dotted longname.
4. **Summary** prints a coloured per-suite table; exit code is the max of
   children.

## CLI

```bash
python -m orchestrator [root] \
    [--workers N] \
    [--output-dir DIR] \
    [-s SUITE_PATTERN]... \
    [-t TEST_PATTERN]... \
    [--list]
```

- `root` defaults to `suites/`.
- `-s` filters discovered suites (matches against `leaf_name` and full
  `longname`; accepts `fnmatch` patterns).
- `-t` is passed through to `robot.run` so each subprocess narrows tests
  inside its leaf suite.
- `--list` prints discovered suites and exits.
- `--workers` defaults to `ORCHESTRATOR_WORKERS` env or 4.

## Env vars forwarded to every worker

Anything starting with `TESTJAM_` (`TESTJAM_API_URL`, `TESTJAM_USER`,
`TESTJAM_PASS`, `TESTJAM_PROJECT`, `TESTJAM_VERSION`, …) is inherited by
each Robot subprocess and read by `TestjamListener.__init__`.

## Makefile

```bash
make test-e2e                                  # run every suite, 4 workers
make test-e2e WORKERS=8                        # 8 workers
make test-e2e ARGS="-s 'Api Server.01 Auth'"  # one nested suite
make test-e2e ARGS="-s 'Api Server.*'"         # glob
make test-e2e ARGS="-t 'Successful*'"          # test pattern
make test-e2e ARGS="--list"                    # print + exit
make test-orchestrator                         # unit tests
```
