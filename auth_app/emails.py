import logging

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .tokens import token_verificacion_email

logger = logging.getLogger(__name__)


def enviar_verificacion_email(request, usuario):
    """
    Envía el enlace para verificar el correo. En desarrollo el correo se imprime
    en la terminal donde corre runserver. Devuelve True si se envió sin errores.
    """
    uid = urlsafe_base64_encode(force_bytes(usuario.pk))
    token = token_verificacion_email.make_token(usuario)
    url = request.build_absolute_uri(
        reverse('verify_email', kwargs={'uidb64': uid, 'token': token})
    )

    cuerpo = render_to_string(
        'auth_app/emails/verify_email.txt',
        {'usuario': usuario, 'url': url},
    )

    try:
        send_mail('Verifica tu correo en Pets Alert', cuerpo, None, [usuario.email])
    except Exception:
        logger.exception('No se pudo enviar el correo de verificación a %s', usuario.email)
        return False

    return True
