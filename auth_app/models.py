from django.db import models


class Rol(models.Model):
    id = models.BigAutoField(primary_key=True)
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    permisos = models.ManyToManyField(
        'Permiso',
        blank=True,
        related_name='roles',
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'

    def __str__(self):
        return self.nombre


class Permiso(models.Model):
    id = models.BigAutoField(primary_key=True)
    codigo = models.CharField(max_length=100, unique=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['codigo']
        verbose_name = 'Permiso'
        verbose_name_plural = 'Permisos'

    def __str__(self):
        return self.nombre


class Usuario(models.Model):
    id = models.BigAutoField(primary_key=True)
    firebase_uid = models.CharField(max_length=128, unique=True)
    nombre = models.CharField(max_length=150)
    email = models.EmailField(max_length=254, unique=True)
    telefono = models.CharField(max_length=30, blank=True)
    foto_perfil = models.TextField(blank=True)
    localidad = models.CharField(max_length=150, blank=True)
    rol = models.ForeignKey(
        Rol,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios',
    )
    permisos = models.ManyToManyField(
        Permiso,
        blank=True,
        related_name='usuarios_directos',
    )
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nombre', 'email']
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f'{self.nombre} ({self.email})'

    def save(self, *args, **kwargs):
        if self.rol_id is None:
            try:
                self.rol = Rol.objects.get(codigo='usuario_basico')
            except Rol.DoesNotExist:
                pass

        super().save(*args, **kwargs)

    def tiene_permiso(self, codigo):
        if not self.activo:
            return False

        permiso_directo = self.permisos.filter(
            codigo=codigo,
            activo=True,
        ).exists()

        permiso_rol = (
            self.rol is not None
            and self.rol.activo
            and self.rol.permisos.filter(
                codigo=codigo,
                activo=True,
            ).exists()
        )

        return permiso_directo or permiso_rol