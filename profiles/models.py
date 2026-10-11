from django.db import models


class PreferenciaPrivacidad(models.Model):
    id = models.BigAutoField(primary_key=True)
    usuario = models.OneToOneField(
        'auth_app.Usuario',
        on_delete=models.CASCADE,
        related_name='preferencias_privacidad',
    )
    ocultar_correo_reportes = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Preferencia de privacidad'
        verbose_name_plural = 'Preferencias de privacidad'

    def __str__(self):
        return f'Privacidad de {self.usuario.nombre}'