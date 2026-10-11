from django.contrib import admin
from .models import Mascota, Ubicacion, Reporte


@admin.register(Mascota)
class MascotaAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'nombre',
        'especie',
    )
    search_fields = (
        'nombre',
        'especie',
        'descripcion',
    )
    list_filter = (
        'especie',
    )
    ordering = (
        'especie',
        'nombre',
    )


@admin.register(Ubicacion)
class UbicacionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'localidad',
    )
    search_fields = (
        'localidad',
    )
    ordering = (
        'localidad',
    )


@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'firebase_id',
        'usuario',
        'tipo_reporte',
        'estado',
        'fecha_publicacion',
    )
    search_fields = (
        'firebase_id',
        'usuario__nombre',
        'usuario__email',
        'mascota__nombre',
        'mascota__especie',
        'ubicacion__localidad',
    )
    list_filter = (
        'tipo_reporte',
        'estado',
    )
    ordering = (
        '-fecha_publicacion',
        '-id',
    )
    autocomplete_fields = (
        'usuario',
        'mascota',
        'ubicacion',
    )