# Grupos

> Translation: [groups.md](groups.md).

Los grupos agrupan usuarios para que los admins puedan conceder acceso a proyectos por grupo en lugar de uno a uno. Cuando un grupo se asigna a un proyecto con un rol, cada miembro del grupo hereda ese rol en ese proyecto — sin una fila `ProjectMember` explícita por usuario.

## Por qué grupos

Sin grupos, onboardear un equipo QA de 12 personas a diez proyectos son 120 operaciones manuales de `añadir miembro`. Con grupos: crear el grupo `QA Team` una vez, asignar cada proyecto a él una vez, total 22 operaciones. Eliminar a la persona del grupo revoca su acceso a los diez proyectos al instante.

## Gestionar grupos

Las definiciones de grupos son globales, gestionadas por admins en **Usuarios (admin) → Grupos**:

- **Nuevo grupo** — nombre + descripción opcional
- **Añadir / quitar miembros** — elegir de la lista de usuarios
- **Renombrar / eliminar** — eliminar sólo permitido si no hay asignaciones de proyecto que referencien al grupo

Un usuario puede pertenecer a varios grupos simultáneamente.

## Asignar un grupo a un proyecto

**Proyecto → Miembros → Acceso por grupo** lista cada grupo asignado al proyecto actual. El formulario **Asignar grupo** elige un grupo candidato y un rol (`owner` / `tester` / `viewer`). Los miembros del grupo ganan instantáneamente ese rol en el proyecto.

Si no aparecen grupos candidatos, la sección explica por qué:

- *Aún no existe ningún grupo.* — ve al admin de Usuarios y crea uno primero
- *Todos los grupos existentes ya están asignados a este proyecto.* — reasigna con un rol distinto o desasigna primero

## Resolución de rol

Un usuario puede tener pertenencia **directa** al proyecto (su propia fila `ProjectMember`) más pertenencia **indirecta** vía uno o más grupos. El rol efectivo es el de mayor privilegio entre todas las fuentes:

```
owner > tester > viewer
```

Así un usuario `viewer` directo pero miembro de un grupo asignado como `tester` obtiene `tester` en ese proyecto. Los admins siempre tienen `owner` implícito en cada proyecto.

## Editar el rol de un grupo en un proyecto

Usa el select de rol junto al grupo en la página de Miembros del proyecto. El cambio afecta a cada miembro del grupo en este proyecto — confirma con cuidado.

## Quitar un grupo de un proyecto

El icono de papelera junto al grupo revoca el rol para cada miembro de ese grupo en este proyecto. Los miembros que sigan en el grupo conservan su acceso a otros proyectos donde el grupo esté asignado.

## Auditoría

Las asignaciones de grupos aparecen en la página de Miembros del proyecto junto a los miembros directos. Ambos son visibles para cualquier miembro del proyecto (viewer incluido) — útil para entender por qué alguien tiene acceso.

No hay log de actividad por grupo en v1.0; los cambios de grupo se loguean sólo a nivel admin.

## Permisos

| Acción | Rol requerido |
|--------|---------------|
| Listar grupos (global) | cualquier usuario autenticado (admins ven todos, otros ven los grupos a los que pertenecen) |
| Crear / editar / eliminar grupo | admin |
| Asignar grupo a proyecto, cambiar rol, desasignar | owner / admin |

## Límites y gotchas

- Un usuario eliminado de un grupo pierde su acceso heredado al proyecto en la siguiente request. Las sesiones abiertas actualmente no se fuerzan a logout — golpean un 403 en la siguiente mutación y la UI lo maneja con gracia.
- El acceso por grupo es sólo aditivo; no hay regla "deny". Para revocar, quita al usuario del grupo o desasigna el grupo del proyecto.
- Eliminar un grupo falla con `409 Conflict` si algún proyecto sigue referenciándolo. Desasigna primero.
