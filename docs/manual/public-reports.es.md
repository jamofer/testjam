# Informes públicos

> Translation: [public-reports.md](public-reports.md).

Los informes públicos exponen una snapshot de sólo lectura de un bug, una ejecución o la lista completa de bugs de una versión a cualquiera con la URL — sin login. Útil para compartir resultados de testing con stakeholders externos (PMs, clientes, reguladores) sin darles cuenta.

## Qué se puede compartir

| Tipo | Qué ve el viewer |
|------|------------------|
| `bug` | Un bug: título, estado, severidad, descripción (markdown renderizado), contexto (versión, entorno, asignado), y el timeline de actividad (cambios de estado, comentarios, adjuntos) |
| `execution` | Una ejecución: resumen, cada resultado + step result, logs adjuntos, attachments renderizados inline como data URLs |
| `bug_report` | La lista de bugs de un proyecto filtrada por versión: el mismo HTML estilo release-notes que puedes descargar desde la página de bugs |

En v1.0 los tipos soportados son fijos a esos tres. Cada uno reutiliza el mismo renderer HTML que dirige los botones **Descargar HTML** internos, así el visual es idéntico.

## Crear un token

En la página relevante (detalle de bug, detalle de ejecución, o lista de bugs del proyecto), pulsa **Compartir** (icono de link). El diálogo muestra:

- **Shares existentes** — cada token actualmente activo para este recurso, con etiqueta, fecha de creación y contador de viewers
- **Crear nuevo** — etiqueta (texto libre, sólo visible para ti), fecha de expiración opcional

Pulsa **Generar**. El token nuevo se muestra una vez — cópialo ahora. El formato de URL es `https://tu-instancia/public/<token-corto>/...`.

El diálogo se queda abierto para que puedas copiar la URL o revocar cualquier share existente.

## Tokens y seguridad

- Los tokens son strings aleatorias opacas de 32 caracteres. Cualquiera con la URL puede ver el recurso — no hay autenticación adicional.
- Los tokens están scoped a un recurso único. No se pueden usar para acceder a ningún otro recurso de la instancia.
- Los tokens son revocables. Pulsa **Revocar** para invalidar inmediatamente — la siguiente request desde esa URL devuelve una página 410 estilada con el app name de la instancia.
- Los tokens pueden expirar opcionalmente. Pasada la expiración la URL devuelve 410.
- El viewer anónimo nunca puede mutar nada (comentar, editar, descargar adjuntos detrás de auth) — sólo leer el HTML renderizado.

## Página de error con branding

Si el token está revocado, expirado o inválido, el viewer no ve un 404 genérico. La página de error lleva el app name de la instancia, el locale (basado en `Accept-Language` del navegador) y una sugerencia de contactar al propietario. El viewer sabe que el recurso existió y se eliminó, no que se equivocó al teclear.

## Qué se expone en el HTML

El HTML renderizado es **self-contained**:

- El markdown se renderiza server-side (sin ejecución JS en el viewer)
- Los attachments imagen se inlinean como URLs `data:` (sujeto al cap por instancia de adjuntos inline configurado)
- Las menciones resuelven a etiquetas de texto plano (los viewers anónimos no ven perfiles internos ni siguen links)
- Los valores de custom field renderizan con sus etiquetas y chips de color
- El timeline de actividad completo se incluye, así el viewer ve también el audit trail

Nada interno de la instancia (URLs a otros proyectos, IDs internos de usuario, tokens JWT) se filtra vía la página renderizada.

## Permisos

| Acción | Rol requerido |
|--------|---------------|
| Listar shares para un recurso | viewer / tester / owner / admin |
| Crear un token de share | tester / owner / admin |
| Revocar un token de share | tester / owner / admin |

La pertenencia al proyecto se comprueba al crear el share, no en el acceso del viewer — una vez existe el token, cualquiera con la URL puede usarlo hasta que se revoque.

## Audit trail

La lista de tokens actualmente activos (con etiqueta + creador + fecha de creación) es el audit trail. No hay contador de visitas por token en v1.0; versiones futuras pueden añadir stats de visualizaciones.
