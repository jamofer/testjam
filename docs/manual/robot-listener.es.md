# Listener de Robot Framework

> Translation: [robot-listener.md](robot-listener.md).

El listener de Robot vive dentro del paquete Python [`testjam-client`](../../testjam-client/) como el extra opcional `robot-listener`. Se enchufa a Robot Framework como [listener interface v3](https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#listener-interface) y es la vía recomendada para que Testjam vea lo que pasa en un pipeline CI.

Qué hace el listener en cada `robot`:

1. Se autentica contra Testjam (Bearer o `X-API-Key`).
2. Descubre y sincroniza **suites / casos / pasos** desde el árbol Robot al proyecto Testjam correspondiente.
3. Crea una **ejecución automática** nueva para la corrida.
4. Stream en vivo de status, duración y logs por paso a Testjam — la página de corrida se actualiza en tiempo real.

## Instalar

Instala el paquete `testjam-client` con el extra `robot-listener` en el mismo virtualenv que ejecuta Robot:

```bash
pip install "./testjam-client[robot-listener]"
# o, cuando se publique:
pip install "testjam-client[robot-listener]"
```

## Ejecutar

```bash
TESTJAM_API_URL=http://tu-host:8080/api/v1 \
TESTJAM_USER=admin TESTJAM_PASS=secret \
TESTJAM_PROJECT="Mi Proyecto" \
robot --listener testjam_client.listener.TestjamListener tests/
```

Autenticación: una de las dos:

- `TESTJAM_USER` + `TESTJAM_PASS` (cualquier usuario; admin recomendado).
- `TESTJAM_API_KEY` (clave scoped a proyecto desde **Members → API tokens**).

Con `TESTJAM_API_KEY` el proyecto queda fijado por la clave — `TESTJAM_PROJECT` pasa a ser un sanity check, no un router.

## Variables de entorno

| Variable              | Default          | Para qué                                                       |
|-----------------------|------------------|----------------------------------------------------------------|
| `TESTJAM_API_URL`     | obligatoria      | URL base hasta `/api/v1`.                                      |
| `TESTJAM_USER`        | —                | Usuario para auth Bearer.                                      |
| `TESTJAM_PASS`        | —                | Contraseña.                                                    |
| `TESTJAM_API_KEY`     | —                | API key scoped (alternativa a user/pass).                      |
| `TESTJAM_PROJECT`     | obligatoria      | Nombre del proyecto. Se crea al vuelo si falta y el user puede.|
| `TESTJAM_VERSION`     | tag git / `dev`  | Etiqueta de versión adjunta a la ejecución.                    |
| `TESTJAM_ENVIRONMENT` | —                | Etiqueta de entorno opcional.                                  |
| `TESTJAM_EXECUTION`   | auto             | Override del nombre; default `<plan> <UTC>`.                   |
| `TESTJAM_PLAN`        | —                | Plan al que asociar. Sin valor, el listener usa un plan ad-hoc derivado del árbol. |
| `TESTJAM_LOG_LEVEL`   | `INFO`           | Verbosidad del listener.                                       |

## Mapeo Robot → Testjam

El listener crea/actualiza entidades en este orden:

| Construcción Robot     | Entidad Testjam        | Notas                                                |
|------------------------|------------------------|------------------------------------------------------|
| Directorio suite Robot | `TestSuite` (anidada)  | Jerarquía reflejada 1:1.                             |
| Fichero `.robot`       | `TestSuite` (hoja)     | Setup / teardown como bloques de suite.              |
| `Test Case`            | `TestCase`             | `[Tags]` mapean a tags Testjam.                      |
| Paso Robot             | `TestStep`             | Keyword + args → action del paso.                    |
| Tag Robot `id:<valor>` | `TestCase.external_id` | Usado por importers y matchers.                      |

## Campos personalizados via tags

Las etiquetas Robot con forma `cf:clave=valor` (o `cf:clave=valor1,valor2` para campos multi-select) se parsean en cada test, se acumulan a lo largo de la corrida y se escriben en `execution.custom_fields` cuando se cierra. Las etiquetas posteriores sobrescriben a las anteriores para la misma clave.

```robotframework
*** Test Cases ***
Login Happy Path
    [Tags]    smoke    cf:area=auth    cf:browsers=chrome,firefox
    Open Browser    ${URL}
    Input Text      id=user    admin
    ...
```

Las claves deben coincidir con definiciones activas de tipo `execution` en el proyecto — las desconocidas se descartan en silencio. Los valores se envían como strings, así que usa `text` o `single_select` / `multi_select` para los campos manejados por tags; `bool`, `number` y `date` rechazan payloads string.

## Consejos

- **Idempotente**: reejecutar la misma suite nunca duplica casos. Altas, renames y bajas se propagan.
- **Polución por listener**: por defecto, cada sync escribe una revisión por caso tocado. El item de roadmap [P1.6](../../ROADMAP.md) colapsa eso a una revisión por sync.
- **Tolerancia a fallos**: si Testjam no responde, el listener degrada con elegancia — Robot sigue corriendo, hay un warning. No buffea estado: reconectar a mitad de corrida no recupera los eventos perdidos del test en vuelo.

## Más allá del listener

Si tu framework no es Robot, conduce la REST directamente. La forma replica al listener:

```bash
# 1. Crear ejecución automatica
curl -X POST -H "X-API-Key: $KEY" $API/projects/$PID/executions \
  -d '{"name":"CI build #1234","plan_id":42,"type":"automatic"}'

# 2. Patch de cada resultado según reporta el test
curl -X PATCH -H "X-API-Key: $KEY" $API/executions/$EID/results/$RID \
  -d '{"status":"passed","duration_ms":4321}'

# 3. Cerrar la ejecución
curl -X PATCH -H "X-API-Key: $KEY" $API/executions/$EID \
  -d '{"status":"completed"}'
```

El contrato REST está documentado en `/api/docs` (Swagger UI) de cada instancia corriendo.
