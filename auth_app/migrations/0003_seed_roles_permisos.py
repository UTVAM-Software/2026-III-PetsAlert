from django.db import migrations


def crear_roles_permisos(apps, schema_editor):
    Rol = apps.get_model('auth_app', 'Rol')
    Permiso = apps.get_model('auth_app', 'Permiso')

    permisos_data = [
        (
            'reportes_ver',
            'Ver reportes',
            'Permite consultar y visualizar reportes.',
        ),
        (
            'reportes_crear',
            'Crear reportes',
            'Permite crear nuevos reportes.',
        ),
        (
            'reportes_editar',
            'Editar reportes',
            'Permite modificar reportes existentes.',
        ),
        (
            'reportes_eliminar',
            'Eliminar reportes',
            'Permite eliminar reportes.',
        ),
    ]

    permisos = {}

    for codigo, nombre, descripcion in permisos_data:
        permiso, created = Permiso.objects.get_or_create(
            codigo=codigo,
            defaults={
                'nombre': nombre,
                'descripcion': descripcion,
                'activo': True,
            },
        )

        if not created:
            permiso.nombre = nombre
            permiso.descripcion = descripcion
            permiso.activo = True
            permiso.save()

        permisos[codigo] = permiso

    roles_data = [
        (
            'usuario_basico',
            'Usuario básico',
            'Usuario estándar de Pets Alert.',
            [
                'reportes_ver',
                'reportes_crear',
            ],
        ),
        (
            'veterinario_rescatista',
            'Veterinario / Rescatista',
            'Usuario especializado con permisos ampliados sobre reportes.',
            [
                'reportes_ver',
                'reportes_crear',
                'reportes_editar',
            ],
        ),
        (
            'admin_desarrollador',
            'Admin / Desarrollador',
            'Administrador con control completo sobre reportes.',
            [
                'reportes_ver',
                'reportes_crear',
                'reportes_editar',
                'reportes_eliminar',
            ],
        ),
    ]

    for codigo, nombre, descripcion, permisos_rol in roles_data:
        rol, created = Rol.objects.get_or_create(
            codigo=codigo,
            defaults={
                'nombre': nombre,
                'descripcion': descripcion,
                'activo': True,
            },
        )

        if not created:
            rol.nombre = nombre
            rol.descripcion = descripcion
            rol.activo = True
            rol.save()

        rol.permisos.set(
            [permisos[codigo_permiso] for codigo_permiso in permisos_rol]
        )


def eliminar_roles_permisos(apps, schema_editor):
    Rol = apps.get_model('auth_app', 'Rol')
    Permiso = apps.get_model('auth_app', 'Permiso')

    Rol.objects.filter(
        codigo__in=[
            'usuario_basico',
            'veterinario_rescatista',
            'admin_desarrollador',
        ]
    ).delete()

    Permiso.objects.filter(
        codigo__in=[
            'reportes_ver',
            'reportes_crear',
            'reportes_editar',
            'reportes_eliminar',
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        (
            'auth_app',
            '0002_rol_permisos_alter_permiso_id_alter_rol_id_and_more',
        ),
    ]

    operations = [
        migrations.RunPython(
            crear_roles_permisos,
            eliminar_roles_permisos,
        ),
    ]