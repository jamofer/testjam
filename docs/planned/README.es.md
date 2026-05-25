# Funcionalidades planificadas

> Translation: [README.md](README.md).

Esta carpeta describe funcionalidades **planificadas** pero **aún no disponibles** en Testjam v1.0. Cada página captura el objetivo de cara al usuario, el esquema de datos previsto, los endpoints de API esperados y las decisiones de diseño abiertas.

Estas páginas son **prospectivas**. Cualquier cosa aquí puede cambiar sin aviso hasta que la funcionalidad se publique y se mueva al [manual de usuario](../manual/README.es.md).

## Índice

| Funcionalidad | Estado | Motivación |
|---------------|--------|------------|
| [Runner Docker](docker-runner.es.md) | Sin empezar | Ejecutar tests automáticos sin un worker CI externo. |
| [Multi-tenant (organizaciones)](multi-tenant.es.md) | Sin empezar | Capa de organizaciones sobre proyectos (sólo si Testjam pasa a hosting gestionado). |

## Convenciones de estas páginas

Cada página planificada sigue el mismo esqueleto:

1. **Por qué** — el problema de cara al usuario.
2. **Qué verás** — esbozo de la UI / UX.
3. **Modelo de datos** — nuevas tablas, columnas, relaciones.
4. **API** — tabla de endpoints.
5. **Preguntas abiertas** — decisiones de diseño en curso.
6. **Fuera de alcance** — exclusiones explícitas que acotan el trabajo.

Una página se mueve de `planned/` a `manual/` cuando la funcionalidad está completamente fusionada.

## Enviadas en v1.0 (antes planificadas)

Tracker de bugs, dashboards de proyecto, modo oscuro, webhooks salientes, linking externo a Jira / GitHub / GitLab / Azure DevOps / OpenProject, grupos con herencia de rol y operaciones de administración extendidas, todas se publicaron con v1.0 y ahora viven en el manual de usuario.
