# Orgs multi-tenant — Planificado

> Translation: [multi-tenant.md](multi-tenant.md). · Estado: **No iniciado · gated**.

## Por qué

Testjam hoy es **single-tenant**: una instancia, un universo de usuarios + proyectos. Aceptable para self-hosted en red privada, insostenible para cualquier SaaS o escenario de instancia compartida (varias empresas en el mismo despliegue, o una empresa con varias unidades de negocio aisladas).

Esta página está **gated**: no empezamos el trabajo hasta que haya demanda real de SaaS o de compartir una instancia entre entidades legalmente separadas.

## Qué vas a ver

Una nueva capa de entidad entre `User` y `Project`:

```
Organization ─┬── Project ── …
              └── User (miembro con rol de org)
```

- Switcher nuevo en la nav superior: **<Nombre org> ▾** con la lista de orgs a las que pertenece el usuario. Cambiar cambia todo el scope (`/orgs/:slug/projects/...`).
- Página **Org settings** nueva (sólo owner / admin de la org): nombre, slug, visibilidad por defecto, allow-list de dominios de email para invitaciones.
- Superficie de billing aparte — fuera de alcance inicial; vive en el repo comercial (`M.5+`).

## Roles de org

| Rol org  | Dentro de los proyectos de la org                                                |
|----------|----------------------------------------------------------------------------------|
| `owner`  | Todo: crear/borrar proyectos, gestionar miembros, gestionar billing.             |
| `admin`  | Igual que owner salvo billing.                                                   |
| `member` | Sólo ve los proyectos a los que ha sido añadido explícitamente.                  |

Un usuario puede pertenecer a varias orgs con roles distintos.

## Modelo de datos

```text
Organization
 ├── id, slug, name, created_by, created_at
 ├── settings (json)
 └── members: OrganizationMember[]

OrganizationMember
 ├── id, org_id, user_id, role
 └── added_at

Project recibe nueva columna:
  org_id (NOT NULL)
```

Migración: se crea una org por defecto `"Personal"` por cada usuario existente; sus proyectos pasan a esa org. Reasignaciones posteriores son manuales (admin mueve proyecto a otra org).

## API

| Endpoint                                          | Verb   | Acción                                         |
|---------------------------------------------------|--------|------------------------------------------------|
| `/api/v1/orgs`                                    | GET    | Orgs a las que pertenece el usuario actual.    |
| `/api/v1/orgs`                                    | POST   | Crear org.                                     |
| `/api/v1/orgs/{slug}`                             | PATCH  | Actualizar settings de la org.                 |
| `/api/v1/orgs/{slug}/members`                     | GET    | Miembros de la org.                            |
| `/api/v1/orgs/{slug}/projects`                    | GET    | Proyectos de la org.                           |
| `/api/v1/orgs/{slug}/projects`                    | POST   | Crear proyecto en esta org.                    |

Las rutas existentes `/api/v1/projects/...` sobreviven pero pasan a ser un wrapper fino que resuelve la org desde el ID de proyecto.

## Preguntas abiertas

- Diseño de URLs: `/orgs/<slug>/projects/<slug>` o mantener el plano `/projects/<id>` y sólo enseñar orgs en la nav. Tendencia: URLs planas para minimizar churn en usuarios single-tenant.
- Compartir casos entre orgs — no de entrada. Cada org está silada.
- Rate limits y quotas por org — bundled con billing, diferido.

## Fuera de alcance

- Billing / Stripe / license keys — viven en el repo enterprise (`M.8`).
- Aislamiento a nivel BBDD (schemas separados) — no necesario; scoping por columna `org_id` basta para v1.
- SSO a nivel org — enterprise (`M.5`).

## Por qué está gated

Multi-tenant añade complejidad permanente a cada endpoint, cada test, cada migración. Vale la pena sólo si Testjam pasa a SaaS o a uso comercial compartido. Hasta que haya demanda real, el trabajo se queda aquí.
