# Importar y exportar

> Translation: [import-export.md](import-export.md).

Testjam soporta de serie ingerir resultados de pipelines CI existentes y enviar reports a humanos.

## Importar resultados

Dos formatos soportados de fábrica:

| Formato           | Endpoint                                                | Detección |
|-------------------|---------------------------------------------------------|-----------|
| JUnit XML         | `POST /api/v1/executions/{id}/import?format=junit`      | `<testsuite>` / `<testcase>` |
| Robot Framework   | `POST /api/v1/executions/{id}/import?format=robot`      | `output.xml` de `robot` |

Ambos endpoints esperan una ejecución `automatic` en curso. El import:

1. Recorre el fichero y extrae cada test case.
2. Matchea contra los resultados de la ejecución, primero por `external_id`, después por `name` exacto.
3. Actualiza el resultado con status, duración, mensaje de error y logs por paso.
4. Devuelve como warnings los tests sin match — **no** los crea en silencio.

### Estrategia: external_id estables

El matcher trabaja a gusto cuando cada caso tiene un `external_id` estable que el CI también emite. En Robot eso es `[Tags]` `id:<valor>`. En JUnit es el classname o el atributo `name` — elige uno y sé consistente.

Si la suite es pequeña y los nombres únicos, basta con matching por nombre. A medida que crece, la ausencia de external_id genera falsos negativos al renombrar.

## Salida de reports

La página de detalle de ejecución ofrece tres formatos:

- **HTML** — fichero autocontenido. Los adjuntos van inline como data URLs base64; el resultado es portátil pero pesado (20 MB con capturas es normal).
- **PDF** — el mismo HTML renderizado vía Chromium headless. Más lento; orientado a impresión / archivo.
- **XLSX** — tabla plana más pivote por suite. Ideal para pivot tables y dashboards de management.

Los reports incluyen cabecera de metadatos, tabla de resultados, desglose por paso y pie con `generated_at` + usuario que lanzó el export.

## Export ZIP de proyecto

El export completo de **proyecto** sale desde la cabecera del proyecto (cubierto en [Proyectos → Exportar](projects.es.md#exportar)). Contiene la biblioteca, planes y adjuntos seleccionados, útil para mover un proyecto entre instancias.

## Backup de instancia

El flujo a nivel instancia **Download backup** / **Restore from backup** bajo **Admin → Settings** está documentado en [Administración → Backups](admin.es.md#backups). Captura el dump de base de datos más todo el árbol `uploads/`.

## Referencia rápida API

| Endpoint                                              | Verb   | Acción                               |
|-------------------------------------------------------|--------|--------------------------------------|
| `/api/v1/executions/{id}/import?format=junit`         | POST   | Ingerir JUnit XML.                   |
| `/api/v1/executions/{id}/import?format=robot`         | POST   | Ingerir `output.xml` de Robot.       |
| `/api/v1/executions/{id}/export?format=html`          | GET    | Descargar report HTML.               |
| `/api/v1/executions/{id}/export?format=pdf`           | GET    | Descargar report PDF.                |
| `/api/v1/executions/{id}/export?format=xlsx`          | GET    | Descargar report XLSX.               |
| `/api/v1/projects/{id}/export`                        | GET    | Descargar ZIP del proyecto.          |
| `/api/v1/projects/import`                             | POST   | Importar un ZIP de proyecto.         |
