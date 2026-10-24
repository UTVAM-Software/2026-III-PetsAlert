from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import Group, PermissionsMixin
from django.db import models

from .catalogo import GRUPO_ADMINISTRADOR, GRUPO_BASICO


class UsuarioManager(BaseUserManager):
    def get_by_natural_key(self, email):
        return self.get(email__iexact=email.strip())

    def _crear(self, email, password, **extra):
        if not email:
            raise ValueError('El correo es obligatorio.')
        email = self.normalize_email(email).strip().lower()
        usuario = self.model(email=email, **extra)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_user(self, email, password=None, **extra):
        extra.setdefault('is_staff', False)
        extra.setdefault('is_superuser', False)
        return self._crear(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        extra.setdefault('email_verificado', True)

        if extra.get('is_staff') is not True:
            raise ValueError('Un superusuario debe tener is_staff=True.')
        if extra.get('is_superuser') is not True:
            raise ValueError('Un superusuario debe tener is_superuser=True.')

        usuario = self._crear(email, password, **extra)

        grupo = Group.objects.filter(name=GRUPO_ADMINISTRADOR).first()
        if grupo is not None:
            usuario.groups.set([grupo])

        return usuario


class Usuario(AbstractBaseUser, PermissionsMixin):
    nombre = models.CharField(max_length=150)
    email = models.EmailField(max_length=254, unique=True)
    telefono = models.CharField(max_length=30, blank=True)
    localidad = models.CharField(max_length=150, blank=True)
    foto = models.ImageField(upload_to='avatars/', blank=True, null=True)

    email_verificado = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre']

    class Meta:
        ordering = ['nombre', 'email']
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        permissions = [
            ('acceder_panel', 'Puede acceder al panel de administración'),
        ]

    def __str__(self):
        return f'{self.nombre} ({self.email})'

    def save(self, *args, **kwargs):
        creando = self._state.adding

        if creando:
            self.email = (self.email or '').strip().lower()

        super().save(*args, **kwargs)

        if creando and not self.is_superuser:
            grupo = Group.objects.filter(name=GRUPO_BASICO).first()
            if grupo is not None:
                self.groups.add(grupo)

    def get_full_name(self):
        return self.nombre

    def get_short_name(self):
        return self.nombre.split(' ')[0] if self.nombre else self.email

    @property
    def nombres_grupos(self):
        return ', '.join(self.groups.values_list('name', flat=True))
