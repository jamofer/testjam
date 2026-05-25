# Primeros pasos

> Translation: [getting-started.md](getting-started.md).

Esta página te lleva desde una máquina en blanco hasta una UI de Testjam con sesión iniciada.

## Requisitos previos

- Un host con Docker Engine ≥ 24 y el plugin Compose.
- Salida HTTPS al exterior para descargar las imágenes oficiales (o un mirror configurado).
- (Opcional) Un reverse proxy con terminación TLS — Caddy, nginx, Cloudflare Tunnel, … — apuntando al `APP_PORT` expuesto.

El stack arranca tres contenedores principales, todos descargados del GitHub Container Registry público:

| Contenedor | Imagen                                       | Rol                                                                |
|------------|----------------------------------------------|--------------------------------------------------------------------|
| `db`       | `postgres:18.3-alpine`                       | Base de datos persistente, montada en un volumen nombrado.        |
| `api`      | `ghcr.io/jamofer/testjam-api:v1.0.0`         | FastAPI + Uvicorn, ejecuta las migraciones Alembic al arrancar.   |
| `web`      | `ghcr.io/jamofer/testjam-web:v1.0.0`         | Nginx que sirve la UI compilada y hace proxy de `/api/` al backend.|

Sólo `web` expone puerto al host (`APP_PORT`, por defecto `8080`).

## 1 · Descargar compose + ejemplo de env

No hace falta clonar — sólo dos archivos:

```bash
mkdir testjam && cd testjam
curl -fsSLO https://raw.githubusercontent.com/Jamofer/testjam/v1.0.0/docker-compose.yml
curl -fsSLO https://raw.githubusercontent.com/Jamofer/testjam/v1.0.0/.env.example
cp .env.example .env
```

Edita `.env` y rellena al menos:

```dotenv
POSTGRES_PASSWORD=por-favor-cambialo
SECRET_KEY=$(openssl rand -hex 32)
INTEGRATION_ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
TESTJAM_VERSION=v1.0.0
APP_PORT=8080
```

`SECRET_KEY` firma los JWT — si lo rotas, invalidas todas las sesiones activas. `TESTJAM_VERSION` fija el tag de imagen descargado de GHCR; **evita `latest` en producción** porque el siguiente `docker compose pull` podría traer una release con cambios incompatibles sin avisar.

## 2 · Arrancar el stack

```bash
docker compose up -d
```

Alembic ejecuta `upgrade head` automáticamente en cada arranque del contenedor `api`. El contenedor `db` tiene healthcheck; el `api` espera a que esté listo antes de servir.

Verifica el endpoint de salud:

```bash
curl -fsS http://localhost:8080/api/v1/health
# {"status":"ok","version":"…","db":"ok"}
```

## 3 · Crear el primer admin

**No hay endpoint público de registro.** El primer usuario se crea con un script que escribe directamente en la base de datos:

```bash
docker compose exec api python scripts/create_admin.py \
  --username admin \
  --email admin@example.com \
  --password 'cambia-esto'
```

El script es idempotente: ejecutarlo de nuevo con el mismo usuario actualiza la contraseña.

## 4 · Entrar en la UI

Abre el navegador en:

```
http://localhost:8080/login
```

Escribe tus credenciales. Testjam guarda el JWT en `localStorage` y lo inyecta en cada llamada a la API.

<p align="center">
  <img src="../screenshots/hero.png" alt="Inicio tras iniciar sesión" width="70%" />
</p>

## 5 · (Opcional) Configurar email

El reset de contraseña y las notificaciones necesitan un relay SMTP. Añade en `.env` (lista completa en [Administración](admin.es.md)):

```dotenv
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=postmaster@example.com
SMTP_PASSWORD=…
SMTP_FROM="Testjam <no-reply@example.com>"
SITE_URL=https://testjam.example.com
```

`SITE_URL` se interpola en los enlaces de los emails; apuntarlo al dominio equivocado rompe el flujo en silencio.

## 6 · Actualizar

Cambia `TESTJAM_VERSION` en `.env` al tag nuevo (consulta [releases](https://github.com/Jamofer/testjam/releases)) y luego:

```bash
docker compose pull
docker compose up -d
```

`alembic upgrade head` se ejecuta automáticamente en el nuevo contenedor `api`, así que las migraciones de schema se aplican antes de que el código nuevo empiece a servir.

## 7 · Siguientes pasos

- Crea tu primer proyecto → [Proyectos](projects.es.md).
- Engancha tu CI → [Listener Robot](robot-listener.es.md).
- Invita a tu equipo → [Miembros y tokens API](members-and-tokens.es.md).
