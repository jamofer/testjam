# Campos personalizados

Los campos personalizados extienden bugs, casos de prueba y ejecuciones con metadatos propios — nivel de prioridad, componente, matriz de navegadores, sprint, fase de release, lo que tu proceso necesite. Cada campo es por proyecto, tipado e indexable para que reportes y filtros lo puedan usar.

> Translation: [custom-fields.md](custom-fields.md).

## Dónde viven

Sidebar del proyecto → **CONFIG → Campos personalizados** abre el panel de admin. Allí puedes definir campos para una de tres entidades:

- **Bugs** — aparecen en cada detalle de bug, en el diálogo de nuevo bug, en los filtros y column-toggle de la lista, y en los reportes HTML / XLSX.
- **Casos de prueba** — aparecen en el detalle de cada caso y en el filtro de búsqueda en `/projects/:id/cases`.
- **Ejecuciones** — aparecen en el formulario de creación manual y persisten en la ejecución.

El panel agrupa por entidad y permite reordenar con drag-and-drop — el orden definido ahí es el que se ve en todos lados (formularios, paneles de detalle, columnas de lista, columnas de reportes).

## Tipos de campo

| Tipo            | Ejemplo                                | Notas                                                                       |
|-----------------|----------------------------------------|-----------------------------------------------------------------------------|
| `text`          | "Ticket Linear"                        | Texto corto libre.                                                          |
| `number`        | "Impacto cliente"                      | Entero o decimal.                                                           |
| `bool`          | "Reportado por cliente"                | Renderiza como checkbox; en reportes aparece como `Yes` / `No`.             |
| `date`          | "Encontrado el"                        | Se guarda como string ISO.                                                  |
| `single_select` | "Prioridad" → `p0` / `p1` / `p2`       | Las opciones llevan label + color opcional usado como fondo del chip.       |
| `multi_select`  | "Plataformas afectadas" → `web`, `ios`…| Comma-list en XLSX, chips individuales en HTML.                             |

Para los tipos de selección, las opciones se definen como pares `valor | etiqueta` (una por línea en el formulario admin). El valor es lo que acepta la API; la etiqueta es lo que ve el usuario.

## Obligatoriedad y valores por defecto

Un campo marcado como **obligatorio** debe llevar siempre un valor. Para las entidades `execution` y `test_case`, los campos obligatorios **deben declarar también un `default_value`** — así se garantiza que los flujos rápidos (creación inline de casos desde el árbol de suites, ejecuciones creadas por el listener) funcionen sin pedir input. El backend rechaza las definiciones required-sin-default para estas dos entidades en create / update.

Para bugs, los campos obligatorios pueden no tener default — el diálogo de nuevo bug bloquea el envío hasta que el usuario elija un valor.

## Filtros y columnas en listas

En la lista de bugs (`/projects/:id/bugs`) y en la búsqueda de casos (`/projects/:id/cases`):

- **Filtro por campo** — elige un campo y un valor para acotar la lista. Los tipos libres muestran un input de texto; los selects muestran un dropdown de valores.
- **Dropdown de columnas** — activa qué campos personalizados aparecen como chips en cada fila. La selección se persiste por navegador via `localStorage`.

## Reportes

Los reportes HTML y XLSX de bugs incluyen automáticamente columnas para cada campo personalizado activo, en el orden definido en el proyecto. Los `single_select` se renderizan con el color configurado; los `multi_select` se renderizan como chips comma-separated en HTML y como una sola celda comma-list en XLSX.

## Robot Framework — etiquetas `cf:`

El listener de Robot parsea las etiquetas con forma `cf:clave=valor` (o `cf:clave=valor1,valor2,...` para multi-select) en cada test, las acumula a lo largo de la corrida y las escribe en la ejecución resultante. Mira [Listener Robot](robot-listener.es.md#campos-personalizados-via-tags) para la convención y ejemplos.

## SDK de Python

El paquete `testjam-client` expone `client.custom_fields` con CRUD completo. Casos típicos:

```python
client.custom_fields.create(
    project_id,
    entity_type="bug",
    key="priority",
    label="Priority",
    type="single_select",
    options=[{"value": "p0", "label": "P0", "color": "#ef4444"}],
)

client.bugs.create(
    project_id,
    title="Search returns 500 on empty query",
    custom_fields={"priority": "p0"},
)
```

Las claves desconocidas son descartadas silenciosamente por el backend; los campos archivados dejan de aparecer en los formularios pero conservan sus valores en las filas existentes.
