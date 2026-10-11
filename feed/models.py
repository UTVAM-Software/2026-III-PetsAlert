from django.db import models


class Mascota(models.Model):
    id = models.BigAutoField(primary_key=True)
    especie = models.CharField(max_length=50)
    nombre = models.CharField(max_length=100, blank=True)
    descripcion = models.TextField()
    fotos_url = models.JSONField(default=list, blank=True)
    foto_base64 = models.TextField(blank=True)

    class Meta:
        ordering = ['especie', 'nombre']
        verbose_name = 'Mascota'
        verbose_name_plural = 'Mascotas'

    def __str__(self):
        if self.nombre:
            return f'{self.nombre} - {self.especie}'
        return self.especie


class Ubicacion(models.Model):
    id = models.BigAutoField(primary_key=True)
    localidad = models.CharField(max_length=150)

    class Meta:
        ordering = ['localidad']
        verbose_name = 'Ubicación'
        verbose_name_plural = 'Ubicaciones'

    def __str__(self):
        return self.localidad


class Reporte(models.Model):
    TIPO_REPORTE_CHOICES = [
        ('se busca', 'Se busca'),
        ('encontrado', 'Encontrado'),
    ]

    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    ]

    id = models.BigAutoField(primary_key=True)
    firebase_id = models.CharField(max_length=150, unique=True)
    usuario = models.ForeignKey(
        'auth_app.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reportes',
    )
    mascota = models.OneToOneField(
        Mascota,
        on_delete=models.CASCADE,
        related_name='reporte',
    )
    ubicacion = models.OneToOneField(
        Ubicacion,
        on_delete=models.CASCADE,
        related_name='reporte',
    )
    tipo_reporte = models.CharField(
        max_length=30,
        choices=TIPO_REPORTE_CHOICES,
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='activo',
    )
    fecha_publicacion = models.DateTimeField(null=True, blank=True)
    fecha_actualizacion = models.DateTimeField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_publicacion']
        verbose_name = 'Reporte'
        verbose_name_plural = 'Reportes'

    def __str__(self):
        return f'{self.tipo_reporte} - {self.mascota.especie}'