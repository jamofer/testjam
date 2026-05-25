# Menciones

> Translation: [mentions.md](mentions.md).

Las menciones son referencias cross-entidad que se resuelven a chips enriquecidos (título + estado + enlace) en cualquier sitio donde se renderice markdown: descripciones de bug, comentarios, discusiones de casos, informes públicos, informes HTML. También se distribuyen como notificaciones + emails a los usuarios mencionados.

## Sintaxis

| Patrón | Objetivo | Ejemplo | Se renderiza como |
|--------|----------|---------|-------------------|
| `@usuario` | Un usuario | `@alice` | pill `@alice` enlazando al perfil |
| `#N` | Un bug del proyecto actual, por número | `#42` | pill `#42 Login broken` |
| `!N` | Una ejecución del proyecto actual, por id | `!100` | pill `!100 Nightly run` |
| `!N/M` | Un resultado dentro de una ejecución | `!100/12` | breadcrumb `Nightly run › Login flow` |
| `!N/M/S` | Un step result dentro de un resultado | `!100/12/3` | breadcrumb `Nightly run › Login flow › Enter password` |
| `~N` | Un caso de prueba por id | `~57` | pill `~57 Login flow` |

Las menciones se parsean en cuerpos markdown ignorando bloques de código fenced o inline, así que `\`#42\`` o fenced `!100` se mantienen verbatim.

## Comportamiento del resolver

Cuando la página renderiza, cada mención se resuelve en backend:

- **Encontrado + el miembro tiene acceso** → chip con título + estado de la entidad, link al detalle
- **Encontrado + el miembro no tiene acceso** (proyecto ajeno, usuario borrado) → degrada a texto plano del token (`#42`, `@alice`) — sin filtración de información
- **No encontrado** → degrada a texto plano

La resolución ocurre en una llamada batch por render, no por ocurrencia — informes grandes con cientos de menciones permanecen rápidos.

## Autocompletado

En cualquier editor markdown (descripción de bug, comentario, descripción de caso, comentario de caso), escribir uno de los caracteres trigger abre un dropdown Floating UI con hasta 10 coincidencias:

- `@` → usuarios que son miembros del proyecto + admins, rankeados por match de nombre
- `#` → bugs del proyecto actual, por número o substring de título
- `!` → ejecuciones del proyecto actual, por id o substring de título
- `~` → casos del proyecto actual, por id o substring de nombre

La selección inserta el token canónico (`@alice`, `#42`, `!100/12`).

## Notificaciones

Cuando publicas un cuerpo markdown con una mención `@usuario`, Testjam distribuye:

- Una **notificación in-app** a cada usuario mencionado (visible desde la campana en la topbar)
- Un **email** a cada usuario que tenga el evento `mention_received` activado en sus preferencias

Sólo las menciones `@user` notifican. Las menciones `#bug` / `!run` / `~case` renderizan como chips pero no notifican a los watchers del bug / ejecución / caso (esos flujos tienen sus propios triggers de notificación).

La distribución es **estricta miembro-only**: las menciones a usuarios que no son miembros del proyecto (ni admins) renderizan el chip pero saltan la notificación — sin fuga cross-proyecto.

## Semántica al editar

Cuando un cuerpo se edita, el diff entre las menciones viejas y las nuevas decide quién recibe notificación:

- Nuevas menciones añadidas → notifica
- Menciones eliminadas → no notifica
- Menciones sin cambios → no re-notifica (sin spam por edits de whitespace)

## Informes públicos

Las menciones renderizan como chips en el informe HTML público servido por la URL con token. Sólo los miembros del proyecto ven el enriquecimiento completo; el viewer anónimo ve la etiqueta visible sin enlaces de follow-up. Ver [Informes públicos](public-reports.md).

## Dónde aparecen las menciones

| Superficie | Parsing | Notificaciones |
|------------|---------|----------------|
| Descripción / comentarios de bug | sí | sí (usuarios) |
| Descripción / comentarios de caso | sí | sí (usuarios) |
| Comentarios de ejecución / resultado | sí | sí (usuarios) |
| Informe HTML (lista de bugs) | sí | n/a (sólo render) |
| Informes públicos | sí | n/a (sólo render) |

## Permisos

Cualquier persona con acceso de escritura a una superficie puede publicar una mención. El resolver respeta los permisos del viewer — los viewers sin acceso al proyecto ven el chip degradar a texto plano en lugar de un enlace funcional.
