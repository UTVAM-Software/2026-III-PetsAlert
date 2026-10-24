from rest_framework.permissions import BasePermission

def requiere_permiso(*permisos):
    class TienePermiso(BasePermission):
        message = 'No tienes permiso para realizar esta acción.'

        def has_permission(self, request, view):
            usuario = request.user
            return bool(
                usuario
                and usuario.is_authenticated
                and usuario.has_perms(permisos)
            )

    TienePermiso.__name__ = 'TienePermiso_' + '_'.join(permisos).replace('.', '_')
    return TienePermiso
