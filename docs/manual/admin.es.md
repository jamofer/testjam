# Administración

> Translation: [admin.md](admin.md).

Esta página va dirigida al **admin global** de una instancia Testjam. Los owners de proyecto no la necesitan.

La sidebar de admin muestra tres áreas (sólo visibles si `is_admin = true`):

- **Users & Groups** (`/users`) — gestiona todas las cuentas de la instancia.
- **Settings** (`/settings`) — configuración global, backups, email.
- (Próximamente) **Projects** — vista global de todos los proyectos, ver [Admin ampliado](../planned/admin-extended.es.md).

## Users & Groups

### Panel Users

La tabla lista todos los usuarios, incluidos los borrados si activas el toggle **Show deleted**.

Operaciones por fila:

- **Activate / deactivate** — flip `is_active`. Los inactivos no pueden entrar pero su atribución en el histórico se conserva.
- **Promote / demote admin** — flip `is_admin`. Debe quedar al menos un admin en la instancia.
- **Reset password** — abre el mismo flujo de reset que el enlace **Forgot password**, pero funciona aunque el SMTP esté roto (se muestra una contraseña temporal en un diálogo).
- **Delete** — soft-delete. El diálogo pregunta qué hacer con los proyectos del que el user es owner:

  > _"User Alice owns 3 projects. Reassign each one to another user or archive it."_

  Por proyecto, elige **Reassign → <user>** o **Archive**. Sin decidir al menos uno, la request devuelve `409 Conflict`.

- **Restore** — aparece en la fila de un usuario borrado. Limpia `deleted_at` y reactiva la cuenta.

### Auto-borrado

Un usuario puede pedir borrarse desde **Profile → Delete account** sólo cuando **Settings → Allow user self-delete** está activado. Aplican las mismas reglas de reassign.

### Groups

Los grupos existen en el modelo pero no se usan para resolver permisos hoy. El plan es darles propósito en [Grupos con propósito](../planned/groups.es.md).

## Settings

La página de settings está hecha de tarjetas pequeñas, editables in-place.

### General

- **Site name** — aparece en el title del navegador y los templates de email.
- **Site URL** — se interpola en los enlaces salientes (reset password, notificaciones). Debe ser la URL **pública** (HTTPS en prod).
- **Default user timezone** — aplicada a usuarios nuevos (planificado, ver [Fechas y zonas](../planned/dashboards.es.md#fechas-y-zonas)).

### Email

- **SMTP host / port / username / password / from**.
- Botón **Test email** — manda un correo de prueba al admin que lo pulsa.

Si el SMTP no está configurado, los emails de reset / notificación se saltan en silencio y se loggean a `WARNING`.

### Security

- **Allow user self-delete** — gatea el flujo **Profile → Delete account**.
- **Account lockout** — número de logins fallidos y duración del bloqueo en minutos.
- **Password policy** — longitud mínima y clases de caracteres requeridas.

### Backups

Aquí viven dos flujos destructivos. Sólo admin.

#### Download backup

Genera un ZIP con:

```
manifest.json   — dialect, versión de la app, timestamp, schema head
dump.sql        — pg_dump de la base de datos
uploads/        — árbol completo de adjuntos
```

El dialecto (`postgresql` / `sqlite`) queda en el manifest. Restaurar cruzando dialectos no está soportado — ver el aviso abajo.

#### Restore from backup

> **Aviso:** Restore es destructivo. Tira las tablas existentes, reproduce el dump y reemplaza el árbol `uploads/`. Los datos actuales se pierden permanentemente.

El formulario exige:

1. Subir el ZIP generado por **Download backup**.
2. Teclear la frase literal `REPLACE ALL DATA` para confirmar.

El servidor valida:

- Que el ZIP contiene `manifest.json` y `dump.sql`.
- Que el `dialect` del manifest coincide con el servidor actual.
- Que el `schema_head` del manifest es `<=` al head Alembic actual; los schemas más antiguos se restauran tal cual y luego debes hacer `alembic upgrade head`.

Ante la duda, haz un **Download backup** **antes** de un restore.

### Script de backup periódico

Para retención automatizada, `scripts/backup.sh` (también `make backup`) escribe un `testjam-<UTC>.tar.gz` en `BACKUP_DIR` (default `./backups`) y poda los archivos > `RETENTION_DAYS` (default 14). Engánchalo a cron o systemd timers.

## Observabilidad

Cada instancia expone:

- `GET /health` — JSON con `status`, `version`, `db`.
- Cabecera `X-Request-ID` en cada respuesta — UUIDv4 para correlación.
- Logs JSON estructurados con `request_id`, `user_id`, `latency_ms`, `path`, `status`.

Si configuras `SENTRY_DSN` (backend) y `VITE_SENTRY_DSN` (frontend), los errores se reenvían con PII scrubeada y `request_id` como tag, de modo que un log y un evento Sentry correlacionan.

## Referencia rápida API

| Endpoint                                       | Verb   | Acción                                  |
|------------------------------------------------|--------|-----------------------------------------|
| `/api/v1/users`                                | GET    | Listar usuarios (admin-only).           |
| `/api/v1/users`                                | POST   | Crear usuario (admin-only).             |
| `/api/v1/users/{id}`                           | PATCH  | Actualizar flags del perfil.            |
| `/api/v1/users/{id}`                           | DELETE | Soft-delete con body de reassign.       |
| `/api/v1/users/{id}/restore`                   | POST   | Restaurar un usuario borrado.           |
| `/api/v1/settings`                             | GET    | Leer settings de instancia.             |
| `/api/v1/settings`                             | PATCH  | Actualizar settings de instancia.       |
| `/api/v1/admin/backup`                         | GET    | Descargar backup ZIP.                   |
| `/api/v1/admin/restore`                        | POST   | Subir + restaurar backup ZIP.           |
| `/api/v1/health`                               | GET    | Endpoint de salud.                      |
