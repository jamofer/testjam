# Suites y casos

> Translation: [suites-and-cases.md](suites-and-cases.md).

Suites y casos forman la **biblioteca de pruebas** de un proyecto. La biblioteca es la fuente de verdad — los planes y ejecuciones sólo la referencian.

## Árbol de suites

Una **suite** es un contenedor jerárquico. Puede contener:

- Subsuites (sin límite duro, pero pasar de ~5 niveles complica la navegación).
- Casos.
- Bloques de setup / teardown que se ejecutan antes y después de cada caso de la suite (los usa el listener Robot y los exportadores de reports).

### Crear

En la landing del proyecto pulsa **+ New suite**. Te pedirá:

- `name` — obligatorio.
- `description` — Markdown opcional.
- `parent_suite_id` — se rellena solo si creas desde dentro de otra suite.

### Reordenar y reasignar padre

Arrastra la suite por el handle del lado izquierdo. Soltarla **encima** de otra suite la convierte en hija; soltarla en el espacio entre dos suites sólo reordena sin cambiar el padre.

### Borrar

El borrado de una suite es **cascada**: subsuites, casos y pasos se van con ella. El diálogo pide confirmación. No hay soft-delete a nivel suite; si necesitas un flujo recuperable, [archiva el proyecto entero](projects.es.md#archivar).

## Caso

Un **caso** vive dentro de una suite y representa un comportamiento testeable.

<p align="center">
  <img src="../screenshots/run.png" alt="Caso dentro de una ejecución" width="80%" />
</p>

### Campos

| Campo            | Tipo         | Notas                                                            |
|------------------|--------------|------------------------------------------------------------------|
| `name`           | string       | Obligatorio. Aparece en el árbol y en listados de ejecución.    |
| `external_id`    | string       | Opcional. Clave estable usada por los importers JUnit/RF.        |
| `description`    | markdown     | Editor Markdown completo con adjuntos.                           |
| `preconditions`  | markdown     | Se muestra encima de los pasos durante una corrida manual.       |
| `tags`           | lista string | Libre. Filtra y agrupa en reports.                               |
| `priority`       | enum         | `low` / `medium` / `high` / `critical`.                          |
| `automation`     | enum         | `manual` / `automatic`. Pista para los runners.                  |
| `assigned_to`    | ref usuario  | Tester por defecto. Overridable por ejecución.                   |

### Pasos

Un **paso** es una instrucción ordenada con dos columnas:

- **Action** — qué hace el tester.
- **Expected result** — qué debería pasar.

Ambas columnas aceptan Markdown. Los pasos se reordenan con drag-and-drop; su `order` se reescribe 1..N atómicamente con el endpoint de bulk reorder.

### Adjuntos

Cada caso puede llevar adjuntos (capturas, payloads, CSV de ejemplo). En los exports HTML se incrustan como data URLs.

### Revisiones

Cada cambio relevante en un caso escribe una fila en `case_revisions` con un snapshot JSON. El panel **Recent History** del caso muestra:

- Quién cambió qué.
- Diff expandible contra la revisión anterior.
- Filtro para esconder cambios automáticos (listener / tokens API) y ver sólo ediciones humanas.

## Referencia rápida API

| Endpoint                                          | Verb   | Acción                                     |
|---------------------------------------------------|--------|--------------------------------------------|
| `/api/v1/projects/{id}/suites`                    | GET    | Listar suites del proyecto.                |
| `/api/v1/projects/{id}/suites`                    | POST   | Crear suite.                               |
| `/api/v1/suites/{id}`                             | PATCH  | Actualizar suite.                          |
| `/api/v1/suites/{id}`                             | DELETE | Borrar suite en cascada.                   |
| `/api/v1/projects/{id}/suites/reorder`            | POST   | Reordenar/reasignar padres en bulk.        |
| `/api/v1/suites/{id}/cases`                       | GET    | Listar casos dentro de la suite.           |
| `/api/v1/suites/{id}/cases`                       | POST   | Crear caso en la suite.                    |
| `/api/v1/cases/{id}`                              | GET    | Leer caso completo (con pasos).            |
| `/api/v1/cases/{id}`                              | PATCH  | Actualizar metadatos del caso.             |
| `/api/v1/cases/{id}/steps`                        | POST   | Añadir un paso.                            |
| `/api/v1/cases/{id}/steps:replace`                | POST   | Borrado + creación atómica de pasos.       |
| `/api/v1/cases/{id}/steps/reorder`                | POST   | Reescribir `order` 1..N.                   |
| `/api/v1/cases/{id}/revisions`                    | GET    | Listar revisiones con snapshots.           |
