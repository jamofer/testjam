# `testjam` CLI

> Traducción: [cli.es.md](cli.es.md).

`testjam` is the command-line front-end to a Testjam server. Same package as the Python SDK and the Robot Framework listener — install the [`testjam-client`](../../testjam-client/) package with the `cli` extra and you get a `testjam` binary on your `PATH`.

What you can do from the shell:

- Inspect projects, suites, cases, plans, executions and bugs.
- Create test cases (with inline or piped steps), plans, bugs, and full executions.
- Start a manual or automatic execution and follow it live with `run tail`.
- Comment, change status, watch and unwatch bugs.
- Drop into an interactive REPL that keeps your auth + project context across commands.

## Install

```bash
pip install "./testjam-client[cli]"
# or, when published:
pip install "testjam-client[cli]"
```

Verify:

```bash
testjam --version
```

## First-time setup

```bash
testjam config set url https://testjam.example.com/api/v1
testjam login --username alice
# password prompt (hidden)
```

The JWT lands in `~/.config/testjam/config.toml` (XDG; the file is chmoded `0600`). Override the location with `TESTJAM_CONFIG`.

Skip the password prompt with `--password` or use a project-scoped API key instead:

```bash
testjam --api-key tjk_xxxxxxx project list
```

The CLI also honours the `TESTJAM_API_KEY` env var.

## Profiles

Switch between servers / teams without re-logging:

```bash
testjam --profile staging login --url https://staging.example.com/api/v1 -u qa
testjam --profile prod    login --url https://prod.example.com/api/v1    -u qa
testjam --profile staging project list
```

Each `--profile NAME` section in the TOML keeps its own `url`, `token`, `api_key`, `username`, and `default_project`.

## A default project

Most commands accept `--project NAME_OR_ID`. To avoid repeating it, pin a default:

```bash
testjam config set default_project "Web App"
```

From then on `testjam suite list`, `testjam bug list`, etc. resolve the project automatically.

## Output

| Mode    | Flag      | When                                  |
|---------|-----------|---------------------------------------|
| Table   | (default) | Interactive use — Rich-styled output. |
| JSON    | `--json`  | Pipelines, scripting, jq filtering.   |

`NO_COLOR=1` strips ANSI from the table mode (Rich handles this for you).

## Read commands

```bash
testjam project list
testjam project show 42
testjam suite list                       # uses default_project
testjam suite show 17
testjam case list --suite 17
testjam case show 308
testjam plan list
testjam plan show 5
testjam execution list --status pending
testjam execution show 91
testjam bug list --severity high
testjam bug show 1240
testjam bug show '#42' --project "Web App"   # by project-local number
```

## Write commands

```bash
testjam project create "Mobile App" --description "iOS + Android"

testjam case create "Login flow" --suite 17 --steps -
# open the page => form visible
# submit valid credentials => dashboard loads
# ^D

testjam plan create "Release 4.2" --description "smoke before 4.2 cut"

testjam run start "Nightly smoke" --plan 5 --type automatic --yes
testjam run start "Manual sweep" --cases 308,309,310

testjam bug create "Login redirect broken" --severity high --tags auth,login
testjam bug update 1240 --severity critical --assigned-to 7
testjam bug comment add 1240 "Repro on Safari 17. Patch incoming."
testjam bug comment add 1240 --file repro.md
testjam bug status change 1240 in_progress --note "Triaged"   # confirms
testjam bug watch 1240
testjam bug unwatch 1240
```

Skip the confirmation prompts with the global `--yes` / `-y` flag:

```bash
testjam -y bug status change 1240 resolved
```

### Step input formats

`case create --steps PATH|-` accepts:

- **Plain lines** — one step per line. `action => expected` splits into action + expected result.
- **JSON list** — `[{"action": "...", "expected_result": "..."}]` if the input starts with `[` or `{`.

`bug comment add` takes the body inline, from `--file PATH`, or from stdin via `-`.

## Tailing a run

```bash
testjam run tail 91
```

The CLI polls every second (`--interval`), updates a Rich live table per result + step, and exits with:

- `0` when the run completes with no failures.
- `1` when the run completes with any failed or blocked result.
- `2` when the run is aborted.

In `--json` mode `run tail` skips the live table and emits a single snapshot when the run terminates — useful for CI assertions.

## REPL

Running `testjam` with no arguments (or `testjam repl` explicitly) drops you into an interactive shell that keeps your profile, auth and project context across commands:

```
$ testjam
testjam> project list
testjam> --json bug list
testjam> :exit
```

History persists at `~/.local/share/testjam/history` (platform-specific data dir).

## Pretty errors

The CLI catches `TestjamError`, `httpx.HTTPError` and `KeyboardInterrupt`, printing a one-line red message instead of a Python traceback. Programmatic callers should inspect the exit code:

| Exit code | Meaning                                  |
|-----------|------------------------------------------|
| `0`       | OK                                       |
| `1`       | API error or network failure              |
| `2`       | Misuse (bad flag, unknown config key)    |
| `130`     | `Ctrl+C` mid-command                     |

## Useful shortcuts

- `testjam --json X | jq` — pipe everything to `jq`.
- `testjam --profile NAME ...` — one-shot profile override.
- `testjam --api-key tjk_XXX ...` — ephemeral key without touching the config.
- `TESTJAM_CONFIG=/tmp/sandbox.toml testjam ...` — fully sandboxed config for CI experiments.
