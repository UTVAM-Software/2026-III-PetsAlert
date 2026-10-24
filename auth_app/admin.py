from django.contrib import admin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('email', 'nombre', 'email_verificado', 'is_active', 'is_superuser')
    list_filter = ('groups', 'email_verificado', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('email', 'nombre')
    filter_horizontal = ('groups', 'user_permissions')
    readonly_fields = ('last_login', 'fecha_registro', 'fecha_actualizacion')
    exclude = ('password',)

    def has_add_permission(self, request):
        return False
