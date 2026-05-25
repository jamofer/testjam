# Runner Docker — Planificado

> Translation: [docker-runner.md](docker-runner.md). · Estado: **No iniciado**.

## Por qué

Hoy Testjam ingiere resultados de CI externos pero no **ejecuta** los tests. El usuario tiene que mantener Jenkins / GH Actions / GitLab CI al lado. El runner Docker cierra esa brecha: declaras un runner una vez, lo apuntas a un repo, pulsas **Run**, y Testjam levanta un contenedor, ejecuta el script, captura la salida e ingiere los resultados por la ruta del listener.

Es el mayor diferenciador frente a cualquier OSS comercial (Kiwi, TestLink, Squash, Testiny self-host).

## Qué vas a ver

- Sub-página **Project → Runners** con los runners configurados (nombre, repo URL, imagen, último run, status).
- Diálogo **+ New runner** pidiendo: nombre, imagen Docker, repo Git (URL + branch + SSH key o PAT), path al `testjam.yml` en el repo.
- Botón **Run** por fila. Abre un formulario con los argumentos declarados en el `testjam.yml`, más override opcional de versión y assignee.
- **Run page** con logs en streaming por websocket, idéntica a la experiencia del listener Robot.

## `testjam.yml` (por repo)

Fichero declarativo en la raíz del repo, similar a `.gitlab-ci.yml`:

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
    description: marker de pytest para filtrar
    default: smoke
```

Testjam interpola `arguments` en el entorno al lanzar. El runner emite el fichero de resultado en `result_path`; Testjam lo ingiere por el importer correspondiente (`junit` / `robot`).

## Modelo de ejecución

```
┌────────────┐    spawn       ┌──────────────────────────┐
│ Testjam api│ ─────────────► │ docker run --rm <image>  │
│            │                │   workdir = /workspace   │
│            │ ◄───── logs ── │   git clone <repo>       │
│ uploads    │ ◄── result ─── │   bash -c "$before; $script"│
│ results    │                └──────────────────────────┘
└────────────┘
```

Dos requisitos del host:

- Acceso a `/var/run/docker.sock` **o** un sidecar `docker:dind` (según modo de despliegue).
- Salida git desde la red del runner.

La tabla de ejecuciones recibe una fila nueva con `type = automatic`, así el resto de Testjam (reports, ruta del listener log, etc.) no cambia.

## Modelo de datos

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

| Endpoint                                       | Verb   | Acción                                         |
|------------------------------------------------|--------|------------------------------------------------|
| `/api/v1/projects/{id}/runners`                | GET    | Listar runners.                                |
| `/api/v1/projects/{id}/runners`                | POST   | Crear runner.                                  |
| `/api/v1/runners/{id}/run`                     | POST   | Disparar run (devuelve `RunnerRun` + ejecución).|
| `/api/v1/runner-runs/{id}/cancel`              | POST   | Cancelar un run en vuelo.                      |
| `/api/v1/runner-runs/{id}/log`                 | GET    | Stream del log capturado.                      |

## Seguridad

El runner monta código y corre scripts controlados por usuario. Amenazas:

- **Container escape** — cada run usa imagen no privilegiada; `--cap-drop ALL`, `--security-opt no-new-privileges`, runtime `gVisor` opcional.
- **Exposición de red** — los runners corren por defecto en su propia red bridge con egress sólo a la API de Testjam y al remoto git configurado.
- **Secretos** — credenciales de repo cifradas con Fernet; inyectadas como env del runner sólo al arranque.
- **Límites de recursos** — `--memory`, `--cpus`, `--pids-limit` por run, leídos de la cuota del proyecto (planificado).

## Preguntas abiertas

- Escalado multi-host: ¿correr en un Docker host remoto o en un pod template K8s? Empezar por socket local; K8s diferido.
- Runs concurrentes por proyecto — ¿cola global o ilimitado? Semáforo por proyecto (default 2).
- ¿Cómo enseñar los `arguments` del manifest en el diálogo **Run**? Lazy fetch: clone a tmpdir y parseo.

## Fuera de alcance

- Runs programados (cron) dentro de Testjam — usa un scheduler externo.
- Edición del `testjam.yml` desde el navegador — fuera, sólo vía git push.
- Build matrices (combinaciones de `arguments`) — fuera v1.
