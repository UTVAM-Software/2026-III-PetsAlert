from django.apps import AppConfig
from django.db.models.signals import post_migrate

class AuthAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auth_app'

    def ready(self):
        from .seed import crear_grupos_base

        post_migrate.connect(
            crear_grupos_base,
            sender=self,
            dispatch_uid='auth_app.crear_grupos_base',
        )
