# Atajos de teclado

> Translation: [keyboard-shortcuts.md](keyboard-shortcuts.md).

Testjam está hecho keyboard-first. Cada página documenta sus atajos bajo `?`; aquí están todos juntos para referencia.

> Los atajos sólo disparan si no hay un input enfocado, salvo los universales (`Esc`, `Cmd+K` / `Ctrl+K`).

## Global

| Tecla                  | Acción                                                 |
|------------------------|--------------------------------------------------------|
| `Cmd+K` / `Ctrl+K`     | Abrir/cerrar el command palette (búsqueda + acciones). |
| `Esc`                  | Cerrar diálogo, palette o panel de notificaciones.     |
| `?`                    | Abrir el diálogo de ayuda contextual de atajos.        |
| `g` luego `p`          | Ir a **Projects**.                                     |
| `g` luego `u`          | Ir a **Profile**.                                      |
| `g` luego `s`          | Ir a **Settings** (sólo admin).                        |

## Landing del proyecto (`/projects/:id`)

| Tecla                  | Acción                                                 |
|------------------------|--------------------------------------------------------|
| `Home` / `End`         | Primer / último treeitem.                              |
| `PageDown` / `PageUp`  | Saltar a la siguiente / anterior suite.                |
| `+` / `−`              | Expandir / colapsar todo el árbol.                     |
| `/`                    | Enfocar la búsqueda.                                   |
| `?`                    | Abrir ayuda de atajos.                                 |

## Página de corrida (`/executions/:id/run`)

| Tecla                  | Acción                                                 |
|------------------------|--------------------------------------------------------|
| `j` / `↓`              | Siguiente paso.                                         |
| `k` / `↑`              | Paso anterior.                                          |
| `J`                    | Siguiente caso (salta pasos).                           |
| `K`                    | Caso anterior (salta pasos).                            |
| `h` / `←`              | Colapsar el resultado enfocado.                         |
| `l` / `→`              | Expandir el resultado enfocado.                         |
| `Home` / `End`         | Primer / último resultado.                              |
| `PageDown` / `PageUp`  | Saltar entre suites.                                    |
| `F`                    | Saltar al siguiente **failed**.                         |
| `B`                    | Saltar al siguiente **blocked**.                        |
| `U`                    | Saltar al siguiente **not_run**.                        |
| `p`                    | Marcar resultado como **passed**.                       |
| `f`                    | Marcar resultado como **failed**.                       |
| `b`                    | Marcar resultado como **blocked**.                      |
| `n`                    | Marcar resultado como **not_run**.                      |
| `o`                    | Toggle expand sobre el enfocado.                        |
| `+` / `−`              | Expandir / colapsar todos.                              |
| `L`                    | Toggle "follow live updates".                           |
| `r`                    | Reanudar follow-live tras scroll manual.                |
| `?`                    | Abrir ayuda de atajos.                                  |

En ejecuciones automáticas, las teclas mutadoras (`p` / `f` / `b` / `n`) están inertes — la UI es observacional.

## Página de caso (`/cases/:id`)

| Tecla                  | Acción                                                 |
|------------------------|--------------------------------------------------------|
| `e`                    | Editar el campo enfocado.                               |
| `Esc`                  | Cancelar edición inline.                                |
| `Cmd+Enter`            | Guardar edición inline.                                 |
| `Cmd+S`                | Guardar el caso entero en modo edición.                 |

## Notas

- Las teclas en mayúscula requieren **Shift** + la minúscula (`J` = `Shift+j`).
- El set exacto lo renderiza `?` en cada página; si un atajo cambia en un release futuro, esta tabla se actualiza con él.
- Internamente todos pasan por `hooks/useKeyboardShortcuts`, que respeta el estado de modificadores e ignora eventos mientras hay foco en un input (`input`, `textarea`, `contenteditable`).
