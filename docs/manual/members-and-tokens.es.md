# Miembros y tokens API

> Translation: [members-and-tokens.md](members-and-tokens.md).

La autenticación de Testjam tiene dos capas:

- **Usuarios** — humanos con username, password y un flag global `is_admin`.
- **Miembros de proyecto** — un usuario añadido a un proyecto concreto con un rol (`owner` / `editor` / `viewer`).

El acceso API para máquinas se monta sobre una de las dos:

- **JWT** del usuario (emitido en `/auth/login`).
- **Token API scoped** emitido en la página de miembros del proyecto.

## Página Members

Ve a **Project → Members** (`/projects/:id/members`). Dos paneles:

### Panel Members

| Columna  | Descripción                                                                |
|----------|----------------------------------------------------------------------------|
| User     | Nombre + username + badges admin / deleted.                                |
| Email    | Lo usan notificaciones y reset de contraseña.                              |
| Role     | `owner` · `editor` · `viewer`. Dropdown para cambiar (owner/admin).        |
| Last seen| Marca del último login correcto.                                           |
| Actions  | Quitar del proyecto. Quitar al owner fuerza elegir sucesor.                |

Añadir miembro abre un diálogo con autocomplete contra el directorio de usuarios. Si el email no está en el directorio, el formulario cae al flujo de "enviar invitación" (sólo visible a admins por ahora).

### Panel Project API tokens

| Columna  | Descripción                                                          |
|----------|----------------------------------------------------------------------|
| Name     | Identificador libre ("CI staging", "Robot listener").               |
| Created  | Marca de emisión + autor.                                            |
| Last used| Marca de la última request autenticada con éxito.                    |
| Expires  | Opcional. A partir de esa fecha el token devuelve 401.               |
| Actions  | Copy (sólo en emisión), regenerate, revoke.                          |

Formato: `tjm_<32 chars base32 random>`. Los tokens se muestran **una sola vez** en la emisión — perder el valor obliga a regenerar.

Cada request con `X-API-Key` devuelve 403 si toca un proyecto distinto al del `project_scope` del token. Endpoints de listado globales (`GET /projects`, `GET /users`) requieren JWT.

## Roles en detalle

| Acción                                | viewer | editor | owner | admin global |
|---------------------------------------|:------:|:------:|:-----:|:------------:|
| Leer suites / casos / planes / runs   | ✓      | ✓      | ✓     | ✓            |
| Exportar reports                      | ✓      | ✓      | ✓     | ✓            |
| Crear / editar suites y casos         |        | ✓      | ✓     | ✓            |
| Crear / editar planes y ejecuciones   |        | ✓      | ✓     | ✓            |
| Gestionar miembros del proyecto       |        |        | ✓     | ✓            |
| Emitir / revocar tokens API           |        |        | ✓     | ✓            |
| Archivar / desarchivar proyecto       |        |        | ✓     | ✓            |
| Borrar proyecto (planificado)         |        |        |       | ✓            |
| Settings de instancia, usuarios, backups |     |        |       | ✓            |

## Autenticarse contra la API

### Token Bearer (usuario)

```bash
TOKEN=$(curl -s -X POST $API/auth/login \
  -d 'username=alice&password=hunter2' | jq -r .access_token)

curl -H "Authorization: Bearer $TOKEN" $API/projects
```

### API key de proyecto

```bash
curl -H "X-API-Key: tjm_abcdefghij…" $API/projects/$PID/cases
```

Las dos cabeceras pueden viajar juntas — si ambas son válidas, gana la API key.

## Referencia rápida API

| Endpoint                                       | Verb   | Acción                                  |
|------------------------------------------------|--------|-----------------------------------------|
| `/api/v1/auth/login`                           | POST   | Emitir JWT.                             |
| `/api/v1/auth/refresh`                         | POST   | Rotar JWT.                              |
| `/api/v1/users/me`                             | GET    | Perfil del usuario actual.              |
| `/api/v1/projects/{id}/members`                | GET    | Listar miembros del proyecto.           |
| `/api/v1/projects/{id}/members`                | POST   | Añadir miembro.                         |
| `/api/v1/projects/{id}/members/{user_id}`      | PATCH  | Cambiar rol.                            |
| `/api/v1/projects/{id}/members/{user_id}`      | DELETE | Quitar miembro.                         |
| `/api/v1/projects/{id}/api-tokens`             | GET    | Listar tokens API del proyecto.         |
| `/api/v1/projects/{id}/api-tokens`             | POST   | Emitir un token nuevo.                  |
| `/api/v1/projects/{id}/api-tokens/{token_id}`  | DELETE | Revocar un token.                       |
