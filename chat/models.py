from django.db import models


class Conversacion(models.Model):
    id = models.BigAutoField(primary_key=True)
    firebase_id = models.CharField(max_length=150, unique=True)
    participantes = models.ManyToManyField(
        'auth_app.Usuario',
        related_name='conversaciones',
    )
    ultimo_mensaje = models.TextField(blank=True)
    ultima_actividad = models.DateTimeField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-ultima_actividad']
        verbose_name = 'Conversación'
        verbose_name_plural = 'Conversaciones'

    def __str__(self):
        return self.firebase_id


class Mensaje(models.Model):
    id = models.BigAutoField(primary_key=True)
    firebase_id = models.CharField(max_length=150, unique=True)
    conversacion = models.ForeignKey(
        Conversacion,
        on_delete=models.CASCADE,
        related_name='mensajes',
    )
    emisor = models.ForeignKey(
        'auth_app.Usuario',
        on_delete=models.PROTECT,
        related_name='mensajes_enviados',
    )
    receptor = models.ForeignKey(
        'auth_app.Usuario',
        on_delete=models.PROTECT,
        related_name='mensajes_recibidos',
    )
    mensaje = models.TextField()
    fecha_mensaje = models.DateTimeField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha_mensaje', 'id']
        verbose_name = 'Mensaje'
        verbose_name_plural = 'Mensajes'

    def __str__(self):
        return self.mensaje[:50]