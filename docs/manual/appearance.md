# Appearance (theme + language)

> Traducción: [appearance.es.md](appearance.es.md).

Both the colour theme and the UI language are per-user preferences that persist across devices and drive both the web app and outgoing email notifications.

## Profile → Appearance

The settings live under **Profile → Appearance** (top-right avatar → Profile). Two controls:

- **Theme** — Light · Dark · System (follows the OS / browser preference)
- **Language** — English (`en`) · Spanish (`es`) · Catalan (`ca`) · Galician (`gl`) · Basque (`eu`)

Changes apply immediately and are persisted to your `User` record on the server.

## Dark mode

The dark theme is a full Tailwind palette swap, not a CSS filter — every component, badge, chip, and report panel has dark-aware variants. The locale switcher and theme toggle are also available on the login / forgot-password / reset-password pages, so the choice survives unauthenticated flows.

The selection is stored in `localStorage` under `testjam.theme` for instant first paint without a flash of light content. The `System` option clears the explicit choice and re-reads `prefers-color-scheme` on every page load.

## Language

The active locale drives:

- Every label, button, badge, dialog, and toast in the UI
- The activity timeline labels (`opened`, `commented`, `changed status from X to Y`)
- The "loading…" / "no matches" / "saved" affordances across the app
- **Outgoing notification emails** — the recipient's stored `User.locale` is used at send time, so each recipient gets their preferred language regardless of who triggered the event

Available languages:

| Code | Language | Coverage |
|------|----------|----------|
| `en` | English | Full (default) |
| `es` | Spanish | Full |
| `ca` | Catalan | Full UI + emails; some admin-only panels may fall back to English |
| `gl` | Galician | Full UI + emails; some admin-only panels may fall back to English |
| `eu` | Basque | Full UI + emails; some admin-only panels may fall back to English |

The locale switcher is also surfaced in the sidebar (compact dropdown) and on auth pages, so users can pick their preferred language before signing in.

## Bootstrap behaviour

New users (no `User.locale` set) inherit the browser's `navigator.language`, falling back to `en`. The first explicit choice is persisted; subsequent device changes do not affect the saved preference.

## Adding a language (contributors)

Adding a new locale is a multi-file but mechanical change. At a high level: copy the `en/` JSON namespace folder under `frontend/src/i18n/locales/`, translate every key, copy the `backend/testjam/templates/email/en/` Jinja templates, extend `SUPPORTED_LOCALES`, and register both in `frontend/src/i18n/index.js` and `backend/testjam/services/email_templates.py`.

## Timezone

Independent of language: each user can set a timezone in **Profile → Date & time**. The UI then renders every timestamp in that timezone with a footer label (`Madrid time`, `UTC`, etc.). New users inherit the browser timezone the first time they land in the app. See [Getting started](getting-started.md) for the full bootstrap flow.
