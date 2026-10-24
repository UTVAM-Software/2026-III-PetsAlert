from django.apps import apps as global_apps
from django.contrib.auth.management import create_permissions
from django.db import DEFAULT_DB_ALIAS

from .catalogo import GRUPOS_SISTEMA


def crear_grupos_base(sender=None, **kwargs):
    apps = kwargs.get('apps', global_apps)
    using = kwargs.get('using', DEFAULT_DB_ALIAS)

    try:
        Group = apps.get_model('auth', 'Group')
        Permission = apps.get_model('auth', 'Permission')
    except LookupError:
        return

    for config in global_apps.get_app_configs():
        if config.models_module is not None:
            create_permissions(config, verbosity=0, interactive=False, using=using)

    todos = list(Permission.objects.using(using).all())

    for nombre, codigos in GRUPOS_SISTEMA.items():
        grupo, creado = Group.objects.using(using).get_or_create(name=nombre)

        if codigos == '*':
            grupo.permissions.add(*todos)
        elif creado:
            etiquetas = {
                tuple(codigo.split('.', 1)) for codigo in codigos
            }
            seleccion = [
                permiso
                for permiso in Permission.objects.using(using).select_related('content_type')
                if (permiso.content_type.app_label, permiso.codename) in etiquetas
            ]
            grupo.permissions.set(seleccion)
