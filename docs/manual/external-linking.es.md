# Linking externo

> Translation: [external-linking.md](external-linking.md).

Testjam vincula bugs a trackers externos sin copiar los datos. Cada bug guarda un link a uno o más tickets externos (o work items, o issues, o stories — el término depende del proveedor) y los renderiza como chips en el panel de contexto del bug.

## Proveedores soportados

| Proveedor | Método de auth | Objeto vinculado |
|-----------|----------------|------------------|
| GitHub Issues | personal access token | issue |
| Jira Cloud | API token (email + token) | issue |
| GitLab Issues | personal access token | issue |
| Azure DevOps | personal access token | work item |
| OpenProject | API key | work package |

La lista de proveedores es fija en v1.0. El patrón adapter en `services/integrations/providers/` hace que añadir nuevos proveedores sea barato.

## Configuración

**Proyecto → Integraciones** lista cada integración configurada para el proyecto. **Nueva integración** abre un diálogo pidiendo:

- **Proveedor** — uno de los cinco soportados
- **Base URL** — la raíz de API de tu tenant (e.g. `https://tu-org.atlassian.net`, `https://github.com`)
- **Credencial** — token / API key, cifrada en reposo con Fernet
- **Mapeo de estados** — mapea estados de bug de Testjam → nombres de estado del proveedor. Usado durante el pull-sync (ver abajo)

Un proyecto puede tener varias integraciones del mismo proveedor (e.g. dos tenants de Jira). Cada integración lleva un nombre opaco usado en el panel de contexto del bug.

## Vincular un bug

Desde el panel de contexto del detalle del bug, **Añadir link → Tracker externo** abre un diálogo con:

- **Integración** — elige de la lista configurada
- **Acción** — *Crear nuevo* (push) o *Vincular existente* (pull)

### Push (crear)

Testjam crea un ticket nuevo en el sistema externo usando el título + descripción del bug como body. El markdown se convierte al formato rich-text nativo del proveedor (HTML para GitHub, ADF para Jira, etc.). El id + URL del ticket devueltos se guardan en el bug; el nuevo chip aparece en el panel de contexto.

### Pull (vincular existente)

Pega una URL o id de ticket. Testjam lo valida contra la API de la integración y guarda el link sin crear nada. Útil cuando el ticket ya existe en el tracker externo.

En ambos casos la **URL del bug de Testjam** se puede pegar en el ticket externo como back-link — no hay round-trip automático en v1.0.

## Sync de estado

El mapeo de estados que configuraste por integración se usa para **pull sync manual**: un botón en cada link externo refresca el nombre de estado cacheado desde el proveedor. No hay polling en background en v1.0; versiones futuras pueden añadir sync programado.

Cambiar el estado de un bug en Testjam **no** hace push automático al tracker externo. Disparar el push es una acción explícita separada (`Push status`) en el chip del link. Es intencional — evita updates sorpresa en tickets propiedad de otros equipos.

## Rotación de tokens

Edita la integración para pegar una credencial nueva. La vieja se sobrescribe y re-cifra. Los links existentes siguen funcionando con la credencial nueva inmediatamente; no hace falta re-vincular.

## Permisos

| Acción | Rol requerido |
|--------|---------------|
| Listar integraciones | viewer / tester / owner / admin |
| Añadir / editar / eliminar integración | owner / admin |
| Crear o vincular tickets externos | tester / owner / admin |
| Quitar un link de un bug | tester / owner / admin (eliminar bug = owner/admin) |

## Notas de seguridad

- Las credenciales se cifran en reposo con la clave Fernet configurada en `INTEGRATION_ENCRYPTION_KEY`. Rota esta clave siguiendo el script de migración en `scripts/rotate_fernet.py`.
- La autenticación fallida devuelve 503 con el mensaje de error del proveedor — nunca la credencial.
- Push y pull usan la API REST oficial del proveedor; nada se scrapea.
- Los tests de integración cubren el happy path por proveedor usando un shim `FakeProvider`.
