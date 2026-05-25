# Docker runner — Planned

> Traducción: [docker-runner.es.md](docker-runner.es.md). · Status: **Not started**. · Roadmap reference: **P4.1**.

## Why

Today Testjam can ingest results from external CI but cannot **run** the tests. A user must keep Jenkins / GH Actions / GitLab CI around. The Docker runner closes that gap: declare a runner once, point it at a repo, click **Run**, and Testjam will spin up a container, execute the script, capture the output, and ingest the results through the existing listener path.

This is the single biggest differentiator vs every commercial OSS competitor (Kiwi, TestLink, Squash, Testiny self-host).

## What you will see

- A new **Project → Runners** sub-page listing configured runners (name, repo URL, image, last run, status).
- A **+ New runner** dialog asking for: name, Docker image, Git repo (URL + branch + SSH key or PAT), path to a `testjam.yml` inside the repo.
- A **Run** button next to each runner. It opens a form with the arguments declared in the `testjam.yml`, plus optional version override and assignee.
- A live **Run page** with streaming logs over websocket, identical to the existing Robot listener experience.

## `testjam.yml` (per repo)

A declarative file inside the repo's root, similar to `.gitlab-ci.yml`:

```yaml
image: python:3.12-slim

variables:
  PYTHONDONTWRITEBYTECODE: "1"

before_script:
  - pip install -r requirements.txt

script:
  - pytest --junitxml=results.xml tests/

result_format: junit
result_path: results.xml

arguments:
  - name: marker
    type: string
    description: pytest marker to filter
    default: smoke
```

Testjam interpolates `arguments` into the env on launch. The runner emits the result file at `result_path`; Testjam ingests it through the matching importer (`junit` / `robot`).

## Execution model

```
┌────────────┐    spawn       ┌──────────────────────────┐
│ Testjam api│ ─────────────► │ docker run --rm <image>  │
│            │                │   workdir = /workspace   │
│            │ ◄───── logs ── │   git clone <repo>       │
│ uploads    │ ◄── result ─── │   bash -c "$before; $script"│
│ results    │                └──────────────────────────┘
└────────────┘
```

Two host requirements:

- Access to `/var/run/docker.sock` **or** a dedicated `docker:dind` sidecar (depending on the deploy mode).
- Outbound git access from the runner network.

The execution table gets a new row with `type = automatic` so the rest of Testjam (reports, listener log path, etc.) is unaffected.

## Data model

```text
Runner
 ├── id, project_id, name, image
 ├── repo_url, repo_ref, repo_credentials_id (FK secret)
 ├── manifest_path  (default: testjam.yml)
 └── created_by, created_at

RunnerRun
 ├── id, runner_id, execution_id, status, started_at, finished_at, exit_code
 ├── arguments (json), version_id?, environment?
 └── log_path (chunked storage)
```

## API

| Endpoint                                       | Verb   | Purpose                                       |
|------------------------------------------------|--------|-----------------------------------------------|
| `/api/v1/projects/{id}/runners`                | GET    | List runners.                                 |
| `/api/v1/projects/{id}/runners`                | POST   | Create runner.                                |
| `/api/v1/runners/{id}/run`                     | POST   | Trigger a run (returns `RunnerRun` + new execution). |
| `/api/v1/runner-runs/{id}/cancel`              | POST   | Cancel an in-flight run.                      |
| `/api/v1/runner-runs/{id}/log`                 | GET    | Stream the captured log.                      |

## Security

The runner mounts code and runs untrusted user-controlled scripts. Threats:

- **Container escape** — every run uses an unprivileged image; `--cap-drop ALL`, `--security-opt no-new-privileges`, optional `gVisor` runtime.
- **Network exposure** — runners by default run in their own bridge network with egress only to the Testjam API and the configured git remote.
- **Secrets** — repo credentials stored encrypted with Fernet; injected into the runner as env at launch only.
- **Resource limits** — per-run `--memory`, `--cpus`, `--pids-limit` set from the project quota (planned).

## Open questions

- Multi-host scaling: run on a remote Docker host or a Kubernetes pod template? Start with local Docker socket; defer K8s.
- Concurrent runs per project — global queue or unlimited? Start with a per-project semaphore (default 2).
- How do we surface the manifest's `arguments` in the **Run** dialog? Lazy fetch by cloning to a tmpdir and parsing.

## Out of scope

- IDE-style scheduled runs (cron) inside Testjam — defer to an external scheduler.
- Browser-based code editing of `testjam.yml` — out, push changes via git.
- Build matrices (multiple `arguments` combinations) — out for v1.
