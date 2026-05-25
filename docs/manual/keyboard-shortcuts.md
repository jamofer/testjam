# Keyboard shortcuts

> Traducción: [keyboard-shortcuts.es.md](keyboard-shortcuts.es.md).

Testjam is built keyboard-first. Every page documents its bindings under `?`; this page collects them in one place for reference.

> Shortcuts only fire when no input has focus, with the exception of the universal ones (`Esc`, `Cmd+K` / `Ctrl+K`).

## Global

| Keys                   | Action                                                 |
|------------------------|--------------------------------------------------------|
| `Cmd+K` / `Ctrl+K`     | Toggle the command palette (search + actions).         |
| `Esc`                  | Close dialog, palette or notifications panel.          |
| `?`                    | Open the contextual shortcut help dialog.              |
| `g` then `p`           | Go to **Projects**.                                    |
| `g` then `u`           | Go to **Profile**.                                     |
| `g` then `s`           | Go to **Settings** (admin only).                       |

## Project landing (`/projects/:id`)

| Keys                   | Action                                                 |
|------------------------|--------------------------------------------------------|
| `Home` / `End`         | First / last treeitem.                                 |
| `PageDown` / `PageUp`  | Jump to the next / previous suite.                     |
| `+` / `−`              | Expand / collapse the entire tree.                     |
| `/`                    | Focus the search input.                                |
| `?`                    | Open shortcut help.                                    |

## Execution run page (`/executions/:id/run`)

| Keys                   | Action                                                 |
|------------------------|--------------------------------------------------------|
| `j` / `↓`              | Next step.                                              |
| `k` / `↑`              | Previous step.                                          |
| `J`                    | Next case (skip steps).                                 |
| `K`                    | Previous case (skip steps).                             |
| `h` / `←`              | Collapse the focused result.                            |
| `l` / `→`              | Expand the focused result.                              |
| `Home` / `End`         | First / last result.                                    |
| `PageDown` / `PageUp`  | Jump between suites.                                    |
| `F`                    | Jump to next **failed** result.                         |
| `B`                    | Jump to next **blocked** result.                        |
| `U`                    | Jump to next **not-run** result.                        |
| `p`                    | Mark focused result as **passed**.                      |
| `f`                    | Mark focused result as **failed**.                      |
| `b`                    | Mark focused result as **blocked**.                     |
| `n`                    | Mark focused result as **not_run**.                     |
| `o`                    | Toggle expand on the focused result.                    |
| `+` / `−`              | Expand / collapse all results.                          |
| `L`                    | Toggle "follow live updates".                           |
| `r`                    | Resume follow-live after manual scrolling.              |
| `?`                    | Open shortcut help.                                     |

For automated executions, the mutating keys (`p` / `f` / `b` / `n`) are inert — the UI is observational.

## Case page (`/cases/:id`)

| Keys                   | Action                                                 |
|------------------------|--------------------------------------------------------|
| `e`                    | Edit the focused field.                                 |
| `Esc`                  | Cancel inline edit.                                     |
| `Cmd+Enter`            | Save inline edit.                                       |
| `Cmd+S`                | Save the whole case form when in edit mode.             |

## Notes

- Shortcuts marked with capital letters require **Shift** + the lowercase key (`J` = `Shift+j`).
- The exact set is rendered live by `?` on each page; if a shortcut disappears in a future release, this page is updated alongside.
- Internally the bindings flow through `hooks/useKeyboardShortcuts`, which respects modifier state and ignores key events while typing into form fields (`input`, `textarea`, `contenteditable`).
