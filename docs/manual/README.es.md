# Manual de uso

Guía completa de Testjam orientada a usuarios finales (QA, desarrolladores) y administradores de instancia. Cubre solo lo que está disponible en la versión actual; las features futuras viven en [`../planned/`](../planned/README.es.md).

> Translation: [README.md](README.md).

<p align="center">
  <img src="../screenshots/hero.png" alt="Testjam — vista general" width="80%" />
</p>

## Itinerario sugerido

Si vienes nuevo a Testjam, sigue las secciones en este orden:

1. **[Primeros pasos](getting-started.es.md)** — instalar y entrar por primera vez.
2. **[Proyectos](projects.es.md)** — crear el contenedor de tu trabajo.
3. **[Dashboard](dashboard.es.md)** — la vista de inicio por proyecto.
4. **[Suites y casos](suites-and-cases.es.md)** — construir la biblioteca de pruebas.
5. **[Planes](plans.es.md)** — agrupar casos para una versión concreta.
6. **[Ejecuciones](executions.es.md)** — ejecutar el plan manualmente o desde CI.
7. **[Bugs](bugs.es.md)** — tracker de bugs nativo acoplado al ciclo de testing.
8. **[Menciones](mentions.es.md)** — referencias cross-entidad que renderizan como chips y notifican.
9. **[Versiones, entornos y cobertura](versions-environments-coverage.es.md)** — organizar ejecuciones por dónde + cuándo.
10. **[Campos personalizados](custom-fields.es.md)** — extiende bugs, casos y ejecuciones con campos estructurados.
11. **[Notificaciones](notifications.es.md)** — campana in-app, email, push WebSocket, preferencias por usuario.
12. **[Informes públicos](public-reports.es.md)** — shares de sólo lectura tokenizados de bugs y ejecuciones.
13. **[Linking externo](external-linking.es.md)** — Jira, GitHub, GitLab, Azure DevOps, OpenProject.
14. **[Webhooks salientes](webhooks.es.md)** — eventos firmados con HMAC a sistemas externos.
15. **[Importar y exportar](import-export.es.md)** — entrar y sacar datos.
16. **[Listener Robot](robot-listener.es.md)** — automatizar la ingestión desde Robot Framework.
17. **[CLI `testjam`](cli.es.md)** — shell interactiva + comandos scripteables contra la API.
18. **[Miembros y tokens API](members-and-tokens.es.md)** — colaborar con tu equipo.
19. **[Grupos](groups.es.md)** — agrupa usuarios para conceder acceso al proyecto por grupo.
20. **[Apariencia](appearance.es.md)** — modo oscuro + idioma de la UI por usuario.
21. **[Administración](admin.es.md)** — solo si eres admin de la instancia.
22. **[Atajos de teclado](keyboard-shortcuts.es.md)** — exprime la productividad.

## Conceptos básicos

```
Proyecto
 ├── Suite (puede anidar más suites)
 │    └── Caso
 │         └── Paso
 ├── Plan (referencia a múltiples casos, M2M)
 ├── Ejecución
 │    └── Resultado (uno por caso ejecutado)
 │         └── Resultado de paso
 └── Bug (vinculado a resultados, versiones, entornos)
```

- Una **suite** es jerárquica y puede contener subsuites además de casos.
- Un **plan** es una colección curada de casos atados a una versión.
- Una **ejecución** materializa un plan en una corrida concreta (`manual` o `automatic`).
- Los **resultados** y los **resultados de paso** comparten cuatro estados: `not_run`, `passed`, `failed`, `blocked`.
- Un **bug** nace de un resultado fallado o bloqueado (o manualmente) y vive a través de su propio flujo de estados.

## Roles y permisos resumidos

| Rol               | Ámbito       | Acciones                                                 |
|-------------------|--------------|----------------------------------------------------------|
| `admin` global    | Instancia    | Todo lo de proyecto + usuarios + ajustes + backup.       |
| `owner` proyecto  | 1 proyecto   | Configuración del proyecto, miembros, archivar, borrar. |
| `tester` proyecto | 1 proyecto   | Crear/editar/borrar suites, casos, planes, ejecuciones, bugs. |
| `viewer` proyecto | 1 proyecto   | Solo lectura. Puede exportar reportes.                  |
| Token API         | 1 proyecto   | Permisos según el rol del usuario emisor.               |

Los detalles por endpoint están en [Miembros y tokens API](members-and-tokens.es.md). Los grupos pueden conceder cualquiera de los roles de proyecto a muchos usuarios a la vez — ver [Grupos](groups.es.md).
