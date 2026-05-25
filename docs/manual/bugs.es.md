# Tracker de bugs

> Translation: [bugs.md](bugs.md).

Testjam incluye un tracker de bugs nativo acoplado al ciclo de testing. Las incidencias nacen de resultados fallados o bloqueados con todo el contexto de la ejecución adjunto, evolucionan por un flujo de estados y pueden vincularse a tickets externos sin salir de la app.

## Reportar un bug

Desde un resultado fallado o bloqueado en `ExecutionRunPage` o `ExecutionDetailPage`, pulsa **Reportar bug**. El diálogo prerellena:

- Versión afectada y entorno de la ejecución
- Severidad (por defecto `medium`) y etiquetas
- Descripción, con el log del paso fallado adjuntado automáticamente
- Vínculo opcional al resultado / ejecución

También puedes crear bugs manualmente desde la página **Bugs** del proyecto (**Nuevo bug**) sin un resultado de origen.

## Flujo de estados

| Estado | Significado |
|--------|-------------|
| `open` | Reportado, sin asignar trabajo |
| `in_progress` | En investigación o arreglo |
| `resolved` | Fix aplicado, pendiente de verificar |
| `closed` | Verificado y publicado |
| `wont_fix` | Reconocido, intencionalmente no se arregla |
| `not_a_bug` | Triado como no-defecto |

Las transiciones se registran en el timeline con actor, timestamp y nota opcional.

## Severidad

`critical` · `high` · `medium` · `low`. Visualizado como pill en cada fila y en el detalle. Los campos personalizados pueden añadir dimensiones extra (prioridad, impacto de negocio, versión objetivo) — ver [Campos personalizados](custom-fields.md).

## Detalle del bug

La página agrupa:

- **Cabecera**: título, badge de severidad, pill de estado, toggle de seguimiento, eliminar (sólo owner/admin)
- **Descripción**: editor markdown con preview inline
- **Comentarios**: hilos en markdown, edición con diff inline en el timeline
- **Adjuntos**: drag-and-drop, copy MD link, descarga autenticada. Cap de tamaño + lista de MIME bloqueados aplicados en backend (no HTML / SVG / ejecutables)
- **Timeline de actividad**: cambios de estado, edits de campos, comentarios, adjuntos, links añadidos/eliminados, diffs de custom fields — actor + timestamp en cada entrada
- **Panel de contexto** (derecha): asignado, versión afectada, versión corregida, entorno, watchers, resultados/ejecuciones vinculados, links de trackers externos, custom fields

## Watchers

Pulsa **Seguir** para recibir notificaciones sobre cambios de estado, comentarios y reasignaciones. El reportador y el asignado se auto-watch. Lista visible a miembros del proyecto; el usuario puede dejar de seguir cuando quiera.

## Menciones

Escribe `@usuario` para mencionar a cualquier miembro del proyecto (notificación email + in-app). `#numero-bug`, `!id-ejecucion`, `~id-caso` renderizan como pills tipo breadcrumb con título + estado. Ver [Menciones](mentions.md) para la gramática completa.

## Linking externo

Un bug se puede vincular a uno o más trackers externos (Jira, GitHub Issues, GitLab Issues, Azure DevOps Work Items, OpenProject). El linking es **push manual** + **pull manual** en v1.0 (sin sync en background). Ver [Linking externo](external-linking.md).

## Filtros y búsqueda

La lista de bugs admite filtros por estado, severidad, versión, custom field, búsqueda libre (título) y etiquetas. Los filtros persisten en la URL — refrescar o compartir el enlace preserva la vista filtrada.

Las acciones masivas no están en v1.0; planificadas para v1.1.

## Notas de versión

**Proyecto → Bugs → Notas de versión** genera un informe HTML imprimible agrupado por `fixed_in_version`, con título del bug, severidad y fecha de resolución. Útil como changelog de release. Disponible vía el mismo endpoint que el token de informe público puede exponer externamente.

## Compartir públicamente

Genera una URL tokenizada de sólo lectura para un bug o para la lista de bugs de una versión. Ver [Informes públicos](public-reports.md).

## Permisos

| Acción | Rol requerido |
|--------|---------------|
| Ver bugs | viewer / tester / owner / admin |
| Crear, editar, comentar, cambiar estado | tester / owner / admin |
| Eliminar bug, eliminar comentario ajeno | owner / admin |
| Eliminar comentario propio | autor |

Los viewers ven la superficie de sólo lectura; los botones destructivos se ocultan en la UI para evitar toasts 403.
