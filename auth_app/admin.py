from django.contrib import admin
from .models import Permiso, Rol, Usuario


@admin.register(Permiso)
class PermisoAdmin(admin.ModelAdmin):
    list_display = (
        'codigo',
        'nombre',
        'activo',
        'fecha_creacion',
        'fecha_actualizacion',
    )
    search_fields = (
        'codigo',
        'nombre',
        'descripcion',
    )
    list_filter = ('activo',)
    ordering = ('codigo',)


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = (
        'codigo',
        'nombre',
        'activo',
        'fecha_creacion',
        'fecha_actualizacion',
    )
    search_fields = (
        'codigo',
        'nombre',
        'descripcion',
    )
    list_filter = ('activo',)
    filter_horizontal = ('permisos',)
    ordering = ('nombre',)


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = (
        'firebase_uid',
        'nombre',
        'email',
        'rol',
        'activo',
        'fecha_registro',
    )
    search_fields = (
        'firebase_uid',
        'nombre',
        'email',
        'telefono',
    )
    list_filter = (
        'rol',
        'activo',
    )
    autocomplete_fields = ('rol',)
    filter_horizontal = ('permisos',)
    ordering = ('nombre', 'email')

    fieldsets = (
        (
            'Identificación',
            {
                'fields': (
                    'firebase_uid',
                    'nombre',
                    'email',
                ),
            },
        ),
        (
            'Información personal',
            {
                'fields': (
                    'telefono',
                    'foto_perfil',
                    'localidad',
                ),
            },
        ),
        (
            'Autorización',
            {
                'fields': (
                    'rol',
                    'permisos',
                    'activo',
                ),
            },
        ),
        (
            'Fechas',
            {
                'fields': (
                    'fecha_registro',
                    'fecha_creacion',
                    'fecha_actualizacion',
                ),
            },
        ),
    )

    readonly_fields = (
        'fecha_creacion',
        'fecha_actualizacion',
    )

admin.site.site_header = 'Pets Alert - Administración'
admin.site.site_title = 'Pets Alert Admin'
admin.site.index_title = 'Panel de administración'