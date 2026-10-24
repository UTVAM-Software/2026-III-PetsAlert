"""Límite simple de intentos por correo e IP, usando la caché de Django."""

from django.core.cache import cache

MAX_INTENTOS = 5
VENTANA_SEGUNDOS = 15 * 60


def _clave(accion, email, ip):
    return f'throttle:{accion}:{(email or "").lower()}:{ip or "-"}'


def ip_de(request):
    return request.META.get('REMOTE_ADDR') or '-'


def bloqueado(accion, email, ip):
    return cache.get(_clave(accion, email, ip), 0) >= MAX_INTENTOS


def registrar(accion, email, ip):
    clave = _clave(accion, email, ip)
    cache.set(clave, cache.get(clave, 0) + 1, VENTANA_SEGUNDOS)


def limpiar(accion, email, ip):
    cache.delete(_clave(accion, email, ip))
