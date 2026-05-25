# Notificaciones

> Translation: [notifications.md](notifications.md).

Testjam entrega notificaciones de eventos vía tres canales — campana in-app, email y push WebSocket — con preferencias por usuario y por evento. El mismo evento se renderiza consistentemente entre canales y locales.

## Canales

| Canal | Dónde | Persistencia |
|-------|-------|--------------|
| **In-app** | Icono de campana en la topbar; al pulsar abre una lista paginada con badges de no-leído | Persistido en la tabla `Notification`; flag `is_read` |
| **Email** | Enviado por el SMTP configurado en Settings de la instancia | No persistido por Testjam tras envío |
| **WebSocket** | Push en vivo a cualquier pestaña que el usuario tenga abierta; el badge de campana actualiza sin refresh | En memoria, sin persistencia |

In-app + WebSocket siempre disparan juntos para cualquier evento suscrito — el WebSocket es sólo el canal live para la misma fila `Notification`. El email es opt-in por evento.

## Catálogo de eventos

| Evento | Trigger |
|--------|---------|
| `execution_assigned` | Una ejecución se me asigna |
| `execution_finished` | Una ejecución asignada a mí termina (`completed` o `aborted`) |
| `execution_failed` | Una ejecución asignada a mí termina con al menos un fallo |
| `bug_assigned` | Un bug se me asigna |
| `bug_commented` | Un bug que sigo recibe un comentario |
| `bug_status_changed` | Un bug que sigo cambia de estado |
| `mention_received` | Soy mencionado en cualquier cuerpo markdown (`@yo`) |
| `password_reset` | Solicité un reset de contraseña (siempre enviado, no toggleable) |

Las invitaciones de test y las notificaciones admin (cuenta desactivada, etc.) siempre se entregan — no son toggleables por el usuario.

## Preferencias por usuario

**Perfil → Notificaciones** muestra una tabla con una fila por evento y dos checkboxes por fila:

- **In-app** — mostrar en la campana + push WebSocket
- **Email** — enviar por SMTP

Por defecto: in-app on para todo; email on para `execution_failed`, `bug_assigned`, `mention_received`, `password_reset`. Ajusta a gusto.

El locale usado para el subject + body del email es el `User.locale` guardado del destinatario, **no** del actor. Así un usuario hispanohablante mencionado por un colega anglohablante recibe el email en español.

## Campana in-app

El badge de la campana muestra el contador de no-leídos. Al pulsar abre un dropdown / popup con:

- Las notificaciones más recientes (paginadas; scroll para cargar más antiguas)
- Cada fila muestra el icono del evento, la línea resumen localizada, el nombre del actor y el timestamp relativo
- Click en una fila salta a la entidad fuente y marca la notificación como leída
- **Marcar todas como leídas** limpia el badge en un click

Las notificaciones de más de 90 días se purgan automáticamente por un job periódico de limpieza (configurable vía `NOTIFICATION_RETENTION_DAYS`).

## Conexión WebSocket

Al hacer login, Testjam abre un WebSocket por pestaña del navegador. El badge de la campana y la lista de notificaciones se actualizan en vivo sin refresh manual. Si la conexión cae (reinicio de servidor, glitch de red), el cliente reconecta automáticamente con backoff exponencial.

El mismo WebSocket también lleva las actualizaciones en vivo que dirigen la página de ejecución, la página de bugs del proyecto y el dashboard.

## Contenido del email

Cada email sigue una plantilla localizada por evento. El body incluye:

- El resumen del evento
- Un link de vuelta a la entidad fuente (resuelto contra el `site_url` configurado)
- Un pie estándar nombrando la instancia y un link a la página de preferencias de notificación para que el destinatario pueda opt-out sin ayuda del admin

Si `site_url` no está configurado en Settings de la instancia, los endpoints que disparan email devuelven `503` en lugar de enviar enlaces rotos. Ver [Administración](admin.md) para las env vars requeridas.

## Permisos

Las preferencias de notificación son por usuario. No hay override admin en v1.0 — cada usuario controla sus propias suscripciones. Los admins pueden ver la tabla global de notificaciones para debug vía base de datos; no hay UI para ello.
