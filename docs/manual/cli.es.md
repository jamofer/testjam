# CLI `testjam`

> Translation: [cli.md](cli.md).

`testjam` es el frontend en línea de comandos de un servidor Testjam. Mismo paquete que el SDK Python y el listener de Robot Framework — instala [`testjam-client`](../../testjam-client/) con el extra `cli` y obtienes un binario `testjam` en tu `PATH`.

Qué puedes hacer desde la shell:

- Inspeccionar proyectos, suites, casos, planes, ejecuciones y bugs.
- Crear casos de test (con steps en línea o por pipe), planes, bugs y ejecuciones completas.
- Lanzar una ejecución manual o automática y seguirla en vivo con `run tail`.
- Comentar, cambiar status, suscribirte / desuscribirte de bugs.
- Entrar en un REPL interactivo que conserva el auth + proyecto entre comandos.

## Instalar

```bash
pip install "./testjam-client[cli]"
# o, cuando se publique:
pip install "testjam-client[cli]"
```

Verifica:

```bash
testjam --version
```

## Configuración inicial

```bash
testjam config set url https://testjam.example.com/api/v1
testjam login --username alice
# prompt de password (oculto)
```

El JWT se persiste en `~/.config/testjam/config.toml` (XDG; el fichero se chmoda a `0600`). Cambia la ubicación con `TESTJAM_CONFIG`.

Salta el prompt con `--password` o usa una API key de proyecto:

```bash
testjam --api-key tjk_xxxxxxx project list
```

La CLI también respeta la variable de entorno `TESTJAM_API_KEY`.

## Perfiles

Cambia entre servidores / equipos sin re-loginear:

```bash
testjam --profile staging login --url https://staging.example.com/api/v1 -u qa
testjam --profile prod    login --url https://prod.example.com/api/v1    -u qa
testjam --profile staging project list
```

Cada sección `--profile NAME` del TOML lleva sus propios `url`, `token`, `api_key`, `username` y `default_project`.

## Proyecto por defecto

La mayoría de comandos aceptan `--project NAME_OR_ID`. Para no repetirlo, fíjalo:

```bash
testjam config set default_project "Web App"
```

A partir de ahí `testjam suite list`, `testjam bug list`, etc. resuelven el proyecto automáticamente.

## Salida

| Modo    | Flag      | Cuándo                                |
|---------|-----------|---------------------------------------|
| Tabla   | (default) | Uso interactivo — salida Rich estilada. |
| JSON    | `--json`  | Pipelines, scripting, filtros con jq. |

`NO_COLOR=1` quita ANSI del modo tabla (Rich lo gestiona por ti).

## Comandos de lectura

```bash
testjam project list
testjam project show 42
testjam suite list                       # usa default_project
testjam suite show 17
testjam case list --suite 17
testjam case show 308
testjam plan list
testjam plan show 5
testjam execution list --status pending
testjam execution show 91
testjam bug list --severity high
testjam bug show 1240
testjam bug show '#42' --project "Web App"   # por número local de proyecto
```

## Comandos de escritura

```bash
testjam project create "Mobile App" --description "iOS + Android"

testjam case create "Login flow" --suite 17 --steps -
# abrir la página => formulario visible
# enviar credenciales válidas => dashboard cargado
# ^D

testjam plan create "Release 4.2" --description "smoke antes del cut 4.2"

testjam run start "Nightly smoke" --plan 5 --type automatic --yes
testjam run start "Manual sweep" --cases 308,309,310

testjam bug create "Login redirect broken" --severity high --tags auth,login
testjam bug update 1240 --severity critical --assigned-to 7
testjam bug comment add 1240 "Reproducido en Safari 17. Patch en camino."
testjam bug comment add 1240 --file repro.md
testjam bug status change 1240 in_progress --note "Triaged"   # confirma
testjam bug watch 1240
testjam bug unwatch 1240
```

Salta las confirmaciones con el flag global `--yes` / `-y`:

```bash
testjam -y bug status change 1240 resolved
```

### Formatos de entrada de steps

`case create --steps PATH|-` acepta:

- **Líneas planas** — un step por línea. `action => expected` parte en action + expected result.
- **JSON list** — `[{"action": "...", "expected_result": "..."}]` si la entrada empieza por `[` o `{`.

`bug comment add` toma el cuerpo en línea, desde `--file PATH`, o por stdin con `-`.

## Tail de una ejecución

```bash
testjam run tail 91
```

La CLI hace polling cada segundo (`--interval`), actualiza una tabla Rich en vivo por result + step, y sale con:

- `0` si la corrida termina sin fallos.
- `1` si la corrida termina con algún resultado failed o blocked.
- `2` si la corrida se abortó.

En modo `--json`, `run tail` omite la tabla en vivo y emite un snapshot único cuando la corrida termina — útil para asserts en CI.

## REPL

Ejecutar `testjam` sin argumentos (o `testjam repl` explícito) te mete en una shell interactiva que conserva perfil, auth y proyecto entre comandos:

```
$ testjam
testjam> project list
testjam> --json bug list
testjam> :exit
```

El historial se persiste en `~/.local/share/testjam/history` (data dir del sistema).

## Errores legibles

La CLI captura `TestjamError`, `httpx.HTTPError` y `KeyboardInterrupt`, e imprime un mensaje rojo de una línea en lugar de un traceback Python. Los callers programáticos miran el exit code:

| Exit code | Significado                              |
|-----------|------------------------------------------|
| `0`       | OK                                       |
| `1`       | Error de API o de red                    |
| `2`       | Mal uso (flag inválido, key desconocida) |
| `130`     | `Ctrl+C` durante el comando              |

## Atajos útiles

- `testjam --json X | jq` — todo a `jq`.
- `testjam --profile NAME ...` — override de perfil de una vez.
- `testjam --api-key tjk_XXX ...` — key efímera sin tocar el config.
- `TESTJAM_CONFIG=/tmp/sandbox.toml testjam ...` — config aislado para experimentos de CI.
