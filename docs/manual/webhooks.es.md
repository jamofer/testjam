# Webhooks salientes

> Translation: [webhooks.md](webhooks.md).

Los webhooks permiten a sistemas externos reaccionar a eventos de Testjam en near real time: disparar un build, postear en un canal de chat, sincronizar a un data warehouse, paginar al on-call, cualquier cosa HTTP. Cada entrega va firmada con HMAC para que el receptor pueda verificar autenticidad y protegerse de replays.

## Configuración

**Proyecto → Webhooks** lista cada webhook configurado para el proyecto más su log de entregas reciente. **Nuevo webhook** abre un diálogo con:

- **URL** — endpoint HTTPS completo (el receptor)
- **Secret** — string opaca usada para firmar cada payload; rotable en cualquier momento
- **Eventos** — multi-selección de los tipos de evento a los que suscribirse (ver tabla abajo)
- **Descripción** — texto libre, opcional

Un webhook se puede pausar (toggle) sin perder su historial de entregas. Pausar detiene las nuevas entregas; las activas terminan su budget de reintentos.

## Catálogo de eventos

| Evento | Se dispara cuando |
|--------|-------------------|
| `execution.created` | Se crea una nueva ejecución |
| `execution.completed` | Una ejecución pasa a `completed` |
| `execution.aborted` | Una ejecución pasa a `aborted` |
| `result.updated` | El estado de un resultado cambia (pass / fail / blocked / not_run) |
| `bug.created` | Se reporta un bug nuevo |
| `bug.status_changed` | Un bug cambia de estado |
| `bug.commented` | Se añade un comentario a un bug |

Añade más eventos a demanda — el framework es genérico.

## Formato del payload

Cada payload es JSON con un envoltorio estable:

```json
{
  "event": "bug.created",
  "delivered_at": "2026-05-25T12:34:56.789Z",
  "project_id": 42,
  "data": { "id": 123, "number": 7, "title": "Login broken", "severity": "high", "status": "open", "..." }
}
```

`data` es el recurso serializado tal como lo devuelve `GET /<resource>/<id>`. Los campos son estables entre versiones patch.

## Firma HMAC

Cada request lleva una cabecera `X-Testjam-Signature`:

```
X-Testjam-Signature: sha256=<hex digest>
```

El digest es `HMAC-SHA256(secret, raw_request_body)`. El receptor debe:

1. Leer el body raw antes de parsear JSON.
2. Computar `HMAC-SHA256(tu_secret_guardado, raw_body)`.
3. Comparar con comparación en tiempo constante.
4. Rechazar la request si no coincide (devolver non-2xx; Testjam reintentará).

Cabeceras adicionales:

- `X-Testjam-Event` — el tipo de evento
- `X-Testjam-Delivery-Id` — id opaco para idempotencia
- `X-Testjam-Timestamp` — ISO-8601 UTC, también dentro del body

## Entregas, reintentos y el log

Una entrega se intenta con timeout de 10 s. Si el receptor devuelve 5xx, hace timeout o falla DNS, Testjam reintenta con backoff exponencial (1 min, 5 min, 15 min, 1 h, 6 h). Tras ~24 h de fallos la entrega se marca como fallida permanente.

El log de entregas por webhook muestra status code, latencia, número de intento y body de respuesta (truncado). Una entrega fallida se puede reentregar manualmente desde el log.

## Permisos

La configuración de webhooks requiere **owner** o **admin**. Tester / viewer no pueden listar ni modificar webhooks. Los tokens de API project-scoped los pueden usar callers externos; los payloads de webhook no incluyen material de autenticación propio.

## Recomendaciones de seguridad

- Usa siempre endpoints HTTPS. Testjam rechaza URLs `http://` salvo que `ALLOW_INSECURE_WEBHOOKS=1` esté explícitamente fijado.
- Rota el secret periódicamente. Los secrets viejos quedan inválidos al guardar el nuevo.
- Verifica la firma en cada request. No confíes en el tipo de evento ni en el payload antes de validar.
- Usa la cabecera `X-Testjam-Delivery-Id` para idempotencia; Testjam puede reentregar tras un fallo recuperable.
