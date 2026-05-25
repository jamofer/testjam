# Funciones planificadas

> Translation: [README.md](README.md).

Esta carpeta describe funciones **planificadas** que **aún no están disponibles** en Testjam. Cada página captura el objetivo de usuario, el esquema de datos, los endpoints API esperados y las decisiones de diseño abiertas. El objetivo es doble:

- Marcar expectativas para usuarios que navegan el manual ("¿puedo hacer X hoy?").
- Dar a integradores un anticipo estable para preparar webhooks, schemas y hooks de UI.

Estas páginas son **prospectivas**. Cualquier cosa aquí puede cambiar sin aviso hasta que la feature aterrice y pase al [manual](../manual/README.es.md).

El plan de ingeniería autoritativo vive en [`ROADMAP.md`](../../ROADMAP.md) en la raíz del proyecto — más granular e incluye orden de implementación.

## Índice

| Feature | Estado | Motivación |
|---------|--------|------------|
| [Bug tracking nativo](bug-tracking.es.md) | No iniciado | Cerrar el ciclo QA sin salir de Testjam. |
| [Dashboards de proyecto](dashboards.es.md) | No iniciado | Primera impresión al entrar a un proyecto. |
| [Modo oscuro](dark-mode.es.md) | No iniciado | Paridad UX con competidores modernos. |
| [Webhooks salientes](webhooks.es.md) | No iniciado | Integración con ecosistema CI/CD. |
| [Linking externo](external-linking.es.md) | No iniciado | Bidireccional con Jira / GitHub / GitLab / ADO. |
| [Runner Docker](docker-runner.es.md) | No iniciado | Diferenciador vs cualquier OSS comercial. |
| [Grupos con propósito](groups.es.md) | No iniciado | Resolución de permisos por grupo. |
| [Admin ampliado](admin-extended.es.md) | No iniciado | Exponer acciones admin que ya existen en la API. |
| [Orgs multi-tenant](multi-tenant.es.md) | No iniciado | Sólo si Testjam pasa a SaaS. |

## Convenciones de estas páginas

Cada página planificada sigue el mismo esqueleto:

1. **Por qué** — problema de usuario.
2. **Qué vas a ver** — boceto de UI / UX.
3. **Modelo de datos** — tablas, columnas, relaciones nuevas.
4. **API** — tabla de endpoints.
5. **Preguntas abiertas** — decisiones de diseño pendientes.
6. **Fuera de alcance** — exclusiones explícitas para limitar el trabajo.

Una página se mueve de `planned/` a `manual/` cuando la feature entra entera en master. No deben quedar páginas planned obsoletas tras la entrega.
