# Versiones, entornos y cobertura

> Translation: [versions-environments-coverage.md](versions-environments-coverage.md).

Tres catálogos scoped al proyecto que organizan ejecuciones y bugs por dónde + cuándo se ejecutaron los tests.

## Versiones

Una versión representa una release candidate, un sprint, un build number — lo que sea que entregues. Los bugs se etiquetan con la versión en la que se detectaron (`version_id`) y la versión en la que se arreglaron (`fixed_in_version_id`). Las ejecuciones se etiquetan con la versión bajo prueba.

**Proyecto → Versiones** lista cada versión con:

- **Nombre** — texto libre, único por proyecto
- **Estado** — `active` (por defecto) o `released`
- **VCS tag** — opcional, vincula a un tag de git para trazabilidad
- **Fecha de release** — opcional, usada en notas de versión
- **Adjuntos** — release notes PDFs, change logs, etc. (sujeto a límites de tamaño + MIME — ver [Administración](admin.md))

Las versiones `released` aparecen primero en el filtro de bugs; las `active` arriba. Cambiar una versión a `released` estampa `released_at` automáticamente.

### Editar y eliminar

Renombra o cambia el estado desde la fila de versión. La eliminación se bloquea mientras bugs o ejecuciones referencian la versión — archívala o migra las referencias primero. Las versiones no se pueden recuperar; restaura de backup si destruyes una por error.

### En notas de versión

El filtro `fixed_in_version_id == <version>` de los bugs dirige el informe **Notas de versión** en la página de bugs — ver [Bugs](bugs.md#release-notes).

## Entornos

Un entorno nombra un target donde ejecutas tests: `staging`, `prod-eu`, `chrome-canary`, etc. Los entornos viven por proyecto en el panel Settings → Entornos del proyecto.

Cuando se crea una ejecución, puedes elegir del catálogo o teclear un valor libre. Los valores de texto libre se auto-añaden al catálogo si no existen (el llamado *upsert*) así la próxima ejecución puede elegir la misma cadena del dropdown. Los bugs reportados desde un resultado heredan el entorno de la ejecución.

El entorno se renderiza como un pill coloreado en la lista de bugs, en el panel de contexto del detalle de bug y en el detalle de ejecución. Los colores son estables por slug (hasheados) así el mismo entorno se ve igual en todas las páginas.

## Matriz de cobertura

**Proyecto → Cobertura** renderiza una matriz de 2 ejes `versiones × entornos`. Cada celda muestra la última ejecución que corrió el plan activo en esa combinación, con su badge de pass rate.

| | staging | prod-eu | chrome-canary |
|---|---|---|---|
| **v1.0** | 95% (12/13) | 100% (13/13) | — |
| **v1.1-rc1** | 80% (10/13) | 70% (9/13) | 92% (12/13) |

Útil como gate de release-readiness: una fila con badges verdes en cada entorno es shippable; una fila con celdas `—` o badges rojos señala cobertura faltante.

Click en cualquier celda salta a esa ejecución.

## Permisos

| Acción | Rol requerido |
|--------|---------------|
| Listar versiones / entornos / cobertura | viewer / tester / owner / admin |
| Crear / editar versión | tester / owner / admin |
| Eliminar versión | owner / admin |
| Añadir / quitar entorno del catálogo | tester / owner / admin |

## Notas

- Las versiones son scoped al proyecto — no hay registro global de versiones. Usa una convención de nombres consistente si quieres trackear la misma release entre varios proyectos.
- La matriz de cobertura usa la última ejecución **completed** por tupla (versión, entorno, plan). Las runs in-flight no rellenan celdas.
- Los valores de entorno en texto libre se normalizan (trimmed, lowercased para matching) antes de hacer upsert al catálogo así `Staging` y ` staging ` resuelven a la misma entrada.
