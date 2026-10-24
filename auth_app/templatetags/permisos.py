from django import template

register = template.Library()


@register.filter
def tiene_permiso(usuario, codigo):
    """Uso en plantillas: {% if user|tiene_permiso:'reportes.crear' %}"""
    return bool(
        usuario
        and usuario.is_authenticated
        and usuario.tiene_permiso(codigo)
    )
