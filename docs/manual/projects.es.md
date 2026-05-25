# Proyectos

> Translation: [projects.md](projects.md).

Un **proyecto** es el contenedor de mayor nivel en Testjam. Todo lo demás — suites, casos, planes, ejecuciones, miembros, tokens — vive dentro de uno.

<p align="center">
  <img src="../screenshots/suites.png" alt="Detalle de proyecto con suites anidadas" width="80%" />
</p>

## Crear

Desde `/projects` pulsa **New project**.

| Campo         | Obligatorio | Notas                                                              |
|---------------|-------------|--------------------------------------------------------------------|
| `name`        | sí          | Texto libre. Aparece en sidebar y breadcrumbs.                     |
| `slug`        | no          | Se genera desde `name` si se deja en blanco.                       |
| `description` | no          | Soporta Markdown, se renderiza en la landing del proyecto.         |

El usuario que crea el proyecto pasa a ser su **owner**. Los owners pueden añadir miembros más tarde desde [Miembros y tokens API](members-and-tokens.es.md).

## Página de proyecto

La landing (`/projects/:id`) muestra:

- Cabecera con breadcrumbs y enlaces rápidos.
- Árbol jerárquico de **suites** + **casos**.
- Barra de acción para crear suites o casos de primer nivel.
- Recordatorio: pulsa `?` para abrir el panel de atajos.

El árbol de suites permite:

- Drag-and-drop para reordenar y reasignar padres.
- `+` / `−` para expandir/colapsar todo.
- `/` para enfocar la búsqueda.
- `Home` / `End` para saltar al primer/último elemento.
- `PageUp` / `PageDown` para moverse entre suites hermanas.

## Archivar

Desde **Project → Settings → Archive project** marcas el proyecto como solo lectura sin perder datos. Mientras está archivado:

- Cualquier endpoint mutante devuelve `409 Conflict` con `detail = "Project is archived"`.
- Se oculta del listado por defecto en `GET /projects`.
- Para verlo de nuevo, añade `?include_archived=true`.

Puedes desarchivar en cualquier momento desde la misma pantalla o con `POST /projects/{id}/unarchive`.

Archivar es la forma recomendada de retirar proyectos viejos: preserva el histórico para auditorías y exports.

## Borrar

El borrado duro de un proyecto sólo está disponible para admins globales desde **Admin → Projects** (esta vista forma parte del roadmap de [Admin ampliado](../planned/admin-extended.es.md) y **aún no está conectada** en la UI). Mientras tanto, el flujo soportado es archivar.

## Exportar

La cabecera del proyecto tiene un botón **Export** (owner / editor / admin). Construye un ZIP determinista llamado `project-<slug>-<UTC>.zip` con:

```
manifest.json        – versión del formato + metadatos del proyecto
project.json         – suites, casos, pasos, planes (dump JSON)
attachments/         – adjuntos binarios de casos y resultados
```

Útil para:

- Migrar un proyecto entre instancias.
- Archivado a largo plazo antes de borrar.
- Reproducir un bug — adjunta el ZIP al ticket.

Reimportar el ZIP en otra instancia se hace con `POST /projects/import`.

## Referencia rápida API

| Endpoint                                       | Verb   | Acción                                  |
|------------------------------------------------|--------|-----------------------------------------|
| `/api/v1/projects`                             | GET    | Listar proyectos visibles.              |
| `/api/v1/projects`                             | POST   | Crear proyecto.                         |
| `/api/v1/projects/{id}`                        | GET    | Leer metadatos.                         |
| `/api/v1/projects/{id}`                        | PATCH  | Actualizar nombre, slug, descripción.   |
| `/api/v1/projects/{id}/archive`                | POST   | Archivar (read-only).                   |
| `/api/v1/projects/{id}/unarchive`              | POST   | Restaurar del archivo.                  |
| `/api/v1/projects/{id}/export`                 | GET    | Descargar ZIP del proyecto.             |
| `/api/v1/projects/import`                      | POST   | Importar un ZIP de proyecto.            |
