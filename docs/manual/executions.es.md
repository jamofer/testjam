# Ejecuciones

> Translation: [executions.md](executions.md).

Una **ejecución** es una corrida concreta de un plan. Cada ejecución lleva:

- `type` — `manual` o `automatic`.
- `status` — `pending`, `in_progress`, `completed`, `aborted`.
- Un snapshot de los casos del plan como **resultados** (una fila por caso).
- Cada resultado lleva su propio snapshot de los pasos del caso como **resultados de paso**.

<p align="center">
  <img src="../screenshots/run.png" alt="Página de corrida con resultado enfocado" width="80%" />
</p>

## Crear

Desde **Project → Executions → New execution** (o el botón **Run plan** del plan):

| Campo         | Obligatorio | Notas                                                          |
|---------------|-------------|----------------------------------------------------------------|
| `plan_id`     | sí          | Pre-rellenado si entras desde la página del plan.              |
| `name`        | sí          | Ej. *Smoke 1.4 — staging*.                                     |
| `type`        | sí          | `manual` para corrida humana, `automatic` para ingestión CI.   |
| `version_id`  | no          | Default: la versión fijada en el plan.                         |
| `environment` | no          | Etiqueta libre (ej. `staging`, `prod-eu-1`).                   |
| `assigned_to` | no          | Tester por defecto; override por resultado permitido.          |

Al pulsar **Create** se materializan los casos en resultados con estado `not_run`.

## Corrida manual

Abre la ejecución desde `/projects/:id/executions` y pulsa **Run**. La página de corrida (`/executions/:id/run`) está pensada para ir rápido.

### Teclado

| Tecla                         | Acción                                              |
|-------------------------------|-----------------------------------------------------|
| `j` / `k`                     | Siguiente / anterior paso.                          |
| `↓` / `↑`                     | Igual que `j` / `k`.                                |
| `J` / `K`                     | Siguiente / anterior **caso** (salta pasos).        |
| `h` / `l`                     | Colapsar / expandir el resultado enfocado.          |
| `Home` / `End`                | Primer / último resultado.                          |
| `PageDown` / `PageUp`         | Saltar entre suites.                                |
| `F` / `B` / `U`               | Siguiente failed / blocked / not-run.               |
| `p` / `f` / `b` / `n`         | Marcar resultado como passed / failed / blocked / not run. |
| `+` / `−`                     | Expandir / colapsar todos.                          |
| `o`                           | Toggle expand sobre el enfocado.                    |
| `L`                           | Toggle "follow live updates".                       |
| `r`                           | Reanudar follow-live tras scroll manual.            |
| `?`                           | Abrir panel de ayuda de atajos.                     |

El ratón sigue funcionando — el teclado es aditivo.

### Inputs por paso

Cada fila de paso expone:

- Una pill de estado (mismos cuatro estados que el resultado).
- Campo libre **notes** (Markdown).
- **Actual result** — qué vio realmente el tester.
- Subida de adjuntos — capturas, payloads, lo que sea.

### Operaciones bulk

La barra superior de la página puede asignar estado / responsable a todos los resultados seleccionados. Selección por checkbox de fila o `Shift+Click` para rangos.

## Ejecución automática

Cuando `type = automatic`, la ejecución la conduce un proceso externo (CI, [listener Robot](robot-listener.es.md), o tus propios scripts vía REST). La UI muestra la misma vista pero con las teclas mutadoras deshabilitadas — observas en vez de conducir.

- `POST /executions/{id}/results/{result_id}` acepta cuerpo parcial: un CI puede streamear estado + duración + logs de pasos según corre.
- Hay un websocket abierto en `/api/v1/ws/executions/{id}`. Cada cambio de estado, línea de log o transición de paso se publica como evento JSON. La página de corrida se suscribe sola.

## Reports

Desde la página de detalle de una ejecución, el botón **Export** ofrece:

| Formato | Notas                                                                                 |
|---------|---------------------------------------------------------------------------------------|
| HTML    | Autocontenido. Adjuntos como data URLs base64. Se puede mandar por email.             |
| PDF     | Renderiza el HTML vía Chromium headless.                                              |
| XLSX    | Una fila por resultado + hoja resumen con pass/fail/block por suite.                   |

<p align="center">
  <img src="../screenshots/report.png" alt="Export HTML" width="60%" />
</p>

## Referencia rápida API

| Endpoint                                          | Verb   | Acción                                    |
|---------------------------------------------------|--------|-------------------------------------------|
| `/api/v1/projects/{id}/executions`                | GET    | Listar ejecuciones.                       |
| `/api/v1/projects/{id}/executions`                | POST   | Crear ejecución desde un plan.            |
| `/api/v1/executions/{id}`                         | GET    | Leer ejecución + resultados.              |
| `/api/v1/executions/{id}/abort`                   | POST   | Abortar una ejecución en curso.           |
| `/api/v1/executions/{id}/results/{result_id}`     | PATCH  | Actualizar resultado (status, notes, …).  |
| `/api/v1/results/{result_id}/steps/{step_id}`     | PATCH  | Actualizar un paso de resultado.          |
| `/api/v1/executions/{id}/export?format=html`      | GET    | Descargar report.                         |
| `/api/v1/ws/executions/{id}`                      | WS     | Suscribirse a eventos en vivo.            |
