# Planes

> Translation: [plans.md](plans.md).

Un **plan de prueba** es un conjunto curado y versionado de casos. Los planes son la forma de decir *"estos son los casos que quiero ejercitar para la v1.4.0"*. Un caso puede pertenecer a varios planes (M2M), y un plan puede tirar de casos de cualquier suite del proyecto.

## Modelo mental

```
Proyecto ── Plan ── (M2M) ── Caso ── Paso
                  \
                   └── fijado a → Versión
```

Los planes nunca son dueños de los casos — los referencian. Editar un caso desde un plan edita la biblioteca subyacente; no puedes "forkear" un caso dentro del plan.

## Crear

Ve a **Project → Plans** y pulsa **New plan**.

| Campo         | Obligatorio | Notas                                                          |
|---------------|-------------|----------------------------------------------------------------|
| `name`        | sí          | Ej. *Smoke v1.4* o *Release candidate 2026-Q2*.                |
| `description` | no          | Markdown. Se renderiza en la página del plan.                  |
| `version_id`  | no          | Fija el plan a una de las [versiones](#versiones) del proyecto. Se usa como default en el diálogo New Execution. |

## Añadir casos

Desde la página del plan (`/plans/:id`):

- **+ Add cases** abre un picker enraizado en el árbol de suites. Selecciona casos sueltos o suites enteras — el picker recursa.
- Los seleccionados aparecen en la lista ordenada del plan. Reordena con drag-and-drop.
- Quita con el icono de papelera de la fila — sólo se desliga, el caso queda en la biblioteca.

## Versiones

Las versiones son etiquetas simples gestionadas en **Project → Versions** (`/projects/:id/versions`). Las usan los planes y las ejecuciones, y aparecen en la columna *version* de los exports.

Uso típico:

- Una versión por release de software (`1.0.0`, `1.1.0`, …).
- Cada plan fijado a su versión correspondiente.
- En el momento de ejecutar, sólo cambias la versión si reejecutas un plan histórico.

## Ejecutar un plan

Pulsa **Run plan** en la página del plan. El botón abre el diálogo **New execution** con el plan y la versión ya rellenos. Continúa en [Ejecuciones](executions.es.md).

## Referencia rápida API

| Endpoint                                  | Verb   | Acción                                   |
|-------------------------------------------|--------|------------------------------------------|
| `/api/v1/projects/{id}/plans`             | GET    | Listar planes del proyecto.              |
| `/api/v1/projects/{id}/plans`             | POST   | Crear plan.                              |
| `/api/v1/plans/{id}`                      | GET    | Leer plan con sus casos.                 |
| `/api/v1/plans/{id}`                      | PATCH  | Actualizar nombre / descripción / versión.|
| `/api/v1/plans/{id}/cases`                | POST   | Asociar casos (body: `{case_ids:[…]}`).  |
| `/api/v1/plans/{id}/cases/{case_id}`      | DELETE | Desasociar un caso del plan.             |
| `/api/v1/plans/{id}/cases/reorder`        | POST   | Reescribir el orden de casos.            |
| `/api/v1/projects/{id}/versions`          | GET    | Listar versiones.                        |
| `/api/v1/projects/{id}/versions`          | POST   | Crear versión.                           |
