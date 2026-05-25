# Dashboard de proyecto

> Translation: [dashboard.md](dashboard.md).

Cada proyecto abre en una pestaña **Dashboard** que resume el estado del proyecto en una ventana temporal configurable (últimos 7 / 30 / 90 días). El dashboard es de sólo lectura — expone lo que ocurre sin entrar a ninguna página más profunda hasta que haces click.

## Widgets

### Contadores de proyecto

Card arriba a la izquierda. Cuatro estadísticas en una grid 2×2:

- **Suites** — número total de suites
- **Casos** — número total de casos
- **Planes** — número total de planes
- **En curso** — ejecuciones actualmente en `pending` o `in_progress`

### Pass rate

Card arriba a la derecha. Dos partes:

- Pass rate global en la ventana, como porcentaje. `—` si no hay resultados
- Una sparkline del pass rate diario en la ventana

### Ejecuciones recientes

Lista las últimas ejecuciones con el estado *derivado* (no la etiqueta raw `completed`):

- `Pass` (verde) — completed sin fallos y al menos un pass
- `Fail` (rojo) — completed con al menos un fallo
- `Blocked` (amarillo) — completed con al menos un bloqueado
- `Aborted` / `En curso` / `Pendiente` — passthrough verbatim
- `Not run` — completed sin nada ejecutado

Un strip compacto a la derecha muestra los contadores `✓P · ✗F · ⚠B · ◦NR` para ver de un vistazo cómo fue la ejecución. Click en cualquier fila salta al run.

### Casos con más fallos

Casos ordenados por fail count en la ventana. Útil para encontrar tests flaky a investigar.

### Bugs abiertos

Card lista bugs activos (`open` / `in_progress`) por severidad, más los 5 más recientes como enlaces clickables. Ordenados por número de bug descendente para que los nuevos vayan primero. Enlace "View all" a la página completa de bugs.

### Versiones

Versiones activas, cada una con runs totales en la ventana + pass rate. Color: verde ≥80%, amarillo ≥50%, rojo por debajo. Útil como gate de release-readiness.

## Selector de rango

Tres botones arriba: **7d** · **30d** · **90d**. Por defecto 30 días. Selección por página (no persistida entre sesiones en v1.0).

## Estado vacío

Un proyecto recién creado sin ejecuciones muestra la card de contadores y los estados vacíos "Sin ejecuciones / Sin fallos / Sin versiones activas" en los otros widgets — sin gráficas rotas, sin `NaN%`.

## Refresh y live updates

El dashboard auto-refresca al volver a entrar a la página. Las actualizaciones en vivo de ejecuciones in-flight (WebSocket) mantienen el contador **En curso** preciso sin refresh manual.

## Permisos

Cualquier miembro del proyecto (`viewer` y superior) puede ver el dashboard. Los datos por debajo se filtran por pertenencia al proyecto, así los valores cross-proyecto nunca se filtran.
