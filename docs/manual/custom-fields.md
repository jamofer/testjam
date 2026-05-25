# Custom fields

Custom fields let you extend bugs, test cases and executions with your own structured metadata — priority tier, component, browser matrix, sprint, release phase, anything your process needs. Each field is per-project, typed, and indexable so reports and filters can use it.

> Traducción: [custom-fields.es.md](custom-fields.es.md).

## Where they live

Project sidebar → **CONFIG → Custom fields** opens the admin panel. From there you can define fields for one of three entity types:

- **Bugs** — surface on every bug detail, the new-bug dialog, the bug list filters and column-toggle, and on HTML / XLSX bug reports.
- **Test cases** — surface on every case detail page and the case search filter on `/projects/:id/cases`.
- **Executions** — surface on the manual run creation form and persist on the execution.

The panel groups definitions by entity type and supports drag-and-drop reordering — the order you set there is the order shown everywhere else (forms, detail panels, list columns, report columns).

## Field types

| Type            | Example                                  | Notes                                                                        |
|-----------------|------------------------------------------|------------------------------------------------------------------------------|
| `text`          | "Linear ticket"                          | Free-form short string.                                                      |
| `number`        | "Customer impact score"                  | Integer or float.                                                            |
| `bool`          | "Customer-reported"                      | Renders as checkbox; report values shown as `Yes` / `No`.                    |
| `date`          | "Found on"                               | Stored as ISO date string.                                                   |
| `single_select` | "Priority" → `p0` / `p1` / `p2`          | Options carry a label + optional color shown as chip background in reports.  |
| `multi_select`  | "Affected platforms" → `web`, `ios`...   | Comma-list in XLSX, individual chips in HTML.                                |

For select types, options are defined as `value | label` pairs (one per line in the admin form). The value is what the API accepts; the label is what users see.

## Required fields & defaults

A field marked **required** must always carry a value. For `execution` and `test_case` entities, required fields **must also declare a `default_value`** — this guarantees that quick-create flows (inline case creation from the suite tree, listener-created executions) succeed without prompting. The backend rejects required-no-default definitions for these two entity types at create / update time.

For bugs, required fields can omit a default — the new-bug dialog will block submission until the user picks a value.

## Filtering & list columns

On the bug list (`/projects/:id/bugs`) and the case search list (`/projects/:id/cases`):

- **Field filter** — pick a field then a value to narrow the list. For free-form types a text input shows up; for selects you get a value dropdown.
- **Columns dropdown** — toggle which custom fields appear as inline chips on each row. The selection persists per browser via `localStorage`.

## Reports

HTML and XLSX bug reports automatically include columns for every active custom field, in the project-defined order. `single_select` values render with their configured color; `multi_select` values render as comma-separated chips in HTML and a single comma-list cell in XLSX.

## Robot Framework — `cf:` tags

The Robot listener parses tags of the form `cf:key=value` (or `cf:key=value1,value2,...` for multi-select) on every test, accumulates them across the run, and writes them onto the resulting execution. See [Robot listener](robot-listener.md#tag-driven-custom-fields) for the convention and examples.

## Python SDK

The `testjam-client` package exposes `client.custom_fields` for full CRUD. Typical use cases:

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

Unknown keys are silently discarded by the backend; archived fields stop appearing in forms but retain their stored values on existing rows.
