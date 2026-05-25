<div align="center">

<img src="logo.svg" width="96" alt="Testjam logo" />

# Testjam — Documentación

</div>

Esta carpeta agrupa toda la documentación de Testjam destinada a usuarios finales (QA, desarrolladores) y administradores de instancia. Está dividida en dos bloques:

- **[Manual de uso](manual/README.es.md)** — funcionalidad actualmente disponible en la aplicación.
- **[Funciones planificadas](planned/README.es.md)** — esqueleto de features en hoja de ruta, **aún no implementadas**. Útil para entender hacia dónde va el producto y anticipar integraciones.

> English version: [README.md](README.md).

**Idiomas disponibles en la UI:** inglés (`en`, por defecto), español (`es`), catalán (`ca`), gallego (`gl`), euskera (`eu`). Cambia en Perfil → Apariencia → Idioma. La elección se guarda en tu usuario, se aplica tanto a la UI como a los emails de notificación, y para cuentas nuevas toma como base el idioma del navegador.

---

## Navegación rápida

### Manual

| Sección | Para qué sirve |
|---------|----------------|
| [Primeros pasos](manual/getting-started.es.md) | Desplegar Testjam, crear el primer admin, entrar a la UI. |
| [Proyectos](manual/projects.es.md) | Crear, archivar, exportar proyectos. |
| [Dashboard](manual/dashboard.es.md) | Vista de inicio por proyecto con métricas, runs recientes, bugs abiertos. |
| [Suites y casos](manual/suites-and-cases.es.md) | Modelado de la biblioteca de pruebas. |
| [Planes](manual/plans.es.md) | Curar conjuntos de casos versionados. |
| [Ejecuciones](manual/executions.es.md) | Manuales y automáticas, vista en directo. |
| [Bugs](manual/bugs.es.md) | Tracker de bugs nativo acoplado a ejecuciones y versiones. |
| [Menciones](manual/mentions.es.md) | Referencias `@usuario`, `#bug`, `!run`, `~caso` con notificaciones. |
| [Versiones, entornos y cobertura](manual/versions-environments-coverage.es.md) | Organización por release + target del proyecto. |
| [Campos personalizados](manual/custom-fields.es.md) | Extender bugs, casos, ejecuciones con campos estructurados. |
| [Notificaciones](manual/notifications.es.md) | Campana in-app, email, push WebSocket, preferencias por usuario. |
| [Informes públicos](manual/public-reports.es.md) | Shares de sólo lectura tokenizados de bugs y ejecuciones. |
| [Linking externo](manual/external-linking.es.md) | Jira / GitHub / GitLab / Azure DevOps / OpenProject. |
| [Webhooks salientes](manual/webhooks.es.md) | Eventos firmados con HMAC hacia sistemas externos. |
| [Importar y exportar](manual/import-export.es.md) | JUnit, Robot Framework, HTML/PDF/XLSX, ZIP por proyecto. |
| [Listener Robot](manual/robot-listener.es.md) | Streaming de resultados desde CI. |
| [CLI `testjam`](manual/cli.es.md) | Shell interactiva + comandos scripteables contra la API. |
| [Miembros y tokens API](manual/members-and-tokens.es.md) | Roles, permisos, claves `X-API-Key`. |
| [Grupos](manual/groups.es.md) | Agrupar usuarios para conceder acceso al proyecto por grupo. |
| [Apariencia](manual/appearance.es.md) | Modo oscuro + idioma de la UI por usuario. |
| [Administración](manual/admin.es.md) | Usuarios globales, ajustes de instancia, backups. |
| [Atajos de teclado](manual/keyboard-shortcuts.es.md) | Tabla completa de navegación rápida. |

### Planificado (no disponible)

| Sección | Resumen |
|---------|---------|
| [Runner Docker](planned/docker-runner.es.md) | Ejecutar tests automáticos sin CI externo. |
| [Multi-tenant](planned/multi-tenant.es.md) | Organizaciones como nivel sobre proyectos. |

---

## Capturas de referencia

Las imágenes que ilustran este manual viven en [`screenshots/`](screenshots/README.md). Si alguna captura queda obsoleta tras un cambio de UI, regenera el set siguiendo las indicaciones del README de esa carpeta.
