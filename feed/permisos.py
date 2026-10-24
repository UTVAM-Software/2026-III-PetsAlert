from auth_app.catalogo import (
    PERMISO_EDITAR_REPORTE,
    PERMISO_ELIMINAR_REPORTE,
    PERMISO_MODERAR,
)


def puede_ver(usuario, reporte):
    if reporte.is_active:
        return True

    return bool(
        usuario.is_authenticated
        and (
            reporte.user_id == usuario.pk
            or usuario.has_perm(PERMISO_MODERAR)
        )
    )


def puede_editar(usuario, reporte):
    if not usuario.is_authenticated:
        return False

    if usuario.has_perm(PERMISO_MODERAR):
        return True

    return reporte.user_id == usuario.pk and usuario.has_perm(PERMISO_EDITAR_REPORTE)


def puede_eliminar(usuario, reporte):
    if not usuario.is_authenticated:
        return False

    if usuario.has_perm(PERMISO_MODERAR):
        return True

    return reporte.user_id == usuario.pk and usuario.has_perm(PERMISO_ELIMINAR_REPORTE)
