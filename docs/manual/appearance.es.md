# Apariencia (tema + idioma)

> Translation: [appearance.md](appearance.md).

Tanto el tema de colores como el idioma de la UI son preferencias por usuario que persisten entre dispositivos y dirigen tanto la web app como los emails de notificación salientes.

## Perfil → Apariencia

Los ajustes viven en **Perfil → Apariencia** (avatar arriba a la derecha → Perfil). Dos controles:

- **Tema** — Claro · Oscuro · Sistema (sigue la preferencia del OS / navegador)
- **Idioma** — Inglés (`en`) · Español (`es`) · Catalán (`ca`) · Gallego (`gl`) · Euskera (`eu`)

Los cambios se aplican inmediatamente y se persisten en tu registro `User` en el servidor.

## Modo oscuro

El tema oscuro es un swap completo de la paleta Tailwind, no un filtro CSS — cada componente, badge, chip y panel de informe tiene variantes dark-aware. El switcher de locale y el toggle de tema también están disponibles en las páginas de login / forgot-password / reset-password, así que la elección sobrevive a flujos sin autenticar.

La selección se guarda en `localStorage` bajo `testjam.theme` para un primer pintado instantáneo sin flash de contenido claro. La opción `Sistema` borra la elección explícita y re-lee `prefers-color-scheme` en cada carga.

## Idioma

El locale activo dirige:

- Cada etiqueta, botón, badge, diálogo y toast de la UI
- Las etiquetas del timeline de actividad (`abrió`, `comentó`, `cambió el estado de X a Y`)
- Los affordances de "cargando…" / "sin coincidencias" / "guardado" en toda la app
- **Los emails de notificación salientes** — se usa el `User.locale` guardado del destinatario en el momento del envío, así cada destinatario recibe su idioma preferido sin importar quién disparó el evento

Idiomas disponibles:

| Código | Idioma | Cobertura |
|--------|--------|-----------|
| `en` | Inglés | Completa (por defecto) |
| `es` | Español | Completa |
| `ca` | Catalán | UI + emails completos; algunos paneles sólo-admin pueden caer en inglés |
| `gl` | Gallego | UI + emails completos; algunos paneles sólo-admin pueden caer en inglés |
| `eu` | Euskera | UI + emails completos; algunos paneles sólo-admin pueden caer en inglés |

El locale switcher también está expuesto en la sidebar (dropdown compacto) y en las páginas auth, así los usuarios pueden elegir su idioma antes de hacer login.

## Comportamiento de bootstrap

Los usuarios nuevos (sin `User.locale`) heredan el `navigator.language` del navegador, cayendo a `en`. La primera elección explícita se persiste; los cambios posteriores de dispositivo no afectan la preferencia guardada.

## Añadir un idioma (contribuidores)

Añadir un locale nuevo es un cambio multi-archivo pero mecánico. A alto nivel: copiar la carpeta de namespace JSON `en/` bajo `frontend/src/i18n/locales/`, traducir cada clave, copiar las plantillas Jinja `backend/testjam/templates/email/en/`, extender `SUPPORTED_LOCALES`, y registrar ambos en `frontend/src/i18n/index.js` y `backend/testjam/services/email_templates.py`.

## Zona horaria

Independiente del idioma: cada usuario puede fijar una zona horaria en **Perfil → Fecha y hora**. La UI entonces renderiza cada timestamp en esa zona con una etiqueta de pie (`hora de Madrid`, `UTC`, etc.). Los usuarios nuevos heredan la zona del navegador la primera vez que entran. Ver [Primeros pasos](getting-started.es.md) para el flujo de bootstrap completo.
