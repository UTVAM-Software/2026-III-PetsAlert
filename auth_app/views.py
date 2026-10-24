import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.views import PasswordResetConfirmView
from django.shortcuts import redirect, render, resolve_url
from django.urls import reverse_lazy
from django.utils.encoding import force_str
from django.utils.http import url_has_allowed_host_and_scheme, urlsafe_base64_decode
from django.views.decorators.http import require_POST

from . import throttle
from .emails import enviar_verificacion_email
from .forms import LoginForm, RegistroForm, ReenviarVerificacionForm
from .models import Usuario
from .tokens import token_verificacion_email

logger = logging.getLogger(__name__)


def _errores(form):
    """Lista plana con los mensajes de error de un formulario."""
    return [mensaje for lista in form.errors.values() for mensaje in lista]


def _destino_seguro(request):
    """Devuelve el parámetro ?next= solo si apunta a este mismo sitio."""
    destino = request.POST.get('next') or request.GET.get('next')

    if destino and url_has_allowed_host_and_scheme(
        destino,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return destino

    return resolve_url(settings.LOGIN_REDIRECT_URL)


def login_view(request):
    if request.user.is_authenticated:
        return redirect(_destino_seguro(request))

    errores = []
    mostrar_reenvio = False
    email = ''

    if request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            ip = throttle.ip_de(request)

            if throttle.bloqueado('login', email, ip):
                errores = ['Demasiados intentos fallidos. Intenta más tarde.']
            else:
                usuario = authenticate(request, username=email, password=password)

                if usuario is None:
                    throttle.registrar('login', email, ip)
                    errores = ['Correo o contraseña incorrectos.']
                elif not usuario.email_verificado:
                    errores = ['Debes verificar tu correo antes de iniciar sesión.']
                    mostrar_reenvio = True
                else:
                    throttle.limpiar('login', email, ip)
                    login(request, usuario)
                    return redirect(_destino_seguro(request))
        else:
            email = request.POST.get('email', '')
            errores = _errores(form)

    return render(
        request,
        'auth_app/login.html',
        {
            'errores': errores,
            'email': email,
            'mostrar_reenvio': mostrar_reenvio,
            'next': request.POST.get('next') or request.GET.get('next') or '',
        },
    )


def register_view(request):
    if request.user.is_authenticated:
        return redirect(resolve_url(settings.LOGIN_REDIRECT_URL))

    if request.method == 'POST':
        form = RegistroForm(request.POST)

        if form.is_valid():
            usuario = form.guardar()

            if enviar_verificacion_email(request, usuario):
                messages.success(
                    request,
                    'Cuenta creada. Revisa tu correo para verificar tu cuenta.',
                )
            else:
                messages.warning(
                    request,
                    'Cuenta creada, pero no pudimos enviar el correo de verificación. '
                    'Solicita que te lo reenviemos.',
                )

            return redirect('login')

        errores = _errores(form)
        valores = {
            'nombre': request.POST.get('nombre', ''),
            'email': request.POST.get('email', ''),
        }
    else:
        errores = []
        valores = {'nombre': '', 'email': ''}

    return render(
        request,
        'auth_app/register.html',
        {'errores': errores, 'valores': valores},
    )


@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, 'Sesión cerrada.')
    return redirect('login')


def verify_email_view(request, uidb64, token):
    try:
        pk = force_str(urlsafe_base64_decode(uidb64))
        usuario = Usuario.objects.get(pk=pk)
    except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
        usuario = None

    if usuario is not None and token_verificacion_email.check_token(usuario, token):
        usuario.email_verificado = True
        usuario.save(update_fields=['email_verificado'])
        messages.success(request, 'Correo verificado. Ya puedes iniciar sesión.')
    else:
        messages.error(
            request,
            'El enlace de verificación no es válido o ya expiró. Solicita uno nuevo.',
        )

    return redirect('login')


def resend_verification_view(request):
    errores = []
    email = request.GET.get('email', '')

    if request.method == 'POST':
        form = ReenviarVerificacionForm(request.POST)
        email = request.POST.get('email', '')

        if form.is_valid():
            email = form.cleaned_data['email']
            ip = throttle.ip_de(request)

            if throttle.bloqueado('reenvio', email, ip):
                errores = ['Demasiados intentos. Inténtalo más tarde.']
            else:
                throttle.registrar('reenvio', email, ip)

                usuario = Usuario.objects.filter(
                    email__iexact=email,
                    is_active=True,
                    email_verificado=False,
                ).first()

                if usuario is not None:
                    enviar_verificacion_email(request, usuario)

                # Mismo mensaje exista o no el correo, para no revelar qué cuentas existen.
                messages.success(
                    request,
                    'Si el correo está registrado y pendiente de verificar, '
                    'te enviamos un nuevo enlace.',
                )
                return redirect('login')
        else:
            errores = _errores(form)

    return render(
        request,
        'auth_app/resend_verification.html',
        {'errores': errores, 'email': email},
    )


def forgot_password_view(request):
    errores = []
    email = ''

    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        email = request.POST.get('email', '')

        if form.is_valid():
            email = form.cleaned_data['email'].strip().lower()
            ip = throttle.ip_de(request)

            if throttle.bloqueado('recuperar', email, ip):
                errores = ['Demasiados intentos. Inténtalo más tarde.']
            else:
                throttle.registrar('recuperar', email, ip)

                try:
                    form.save(
                        request=request,
                        use_https=request.is_secure(),
                        from_email=None,
                        email_template_name='auth_app/emails/password_reset.txt',
                        subject_template_name='auth_app/emails/password_reset_subject.txt',
                    )
                except Exception:
                    logger.exception('No se pudo enviar el correo de recuperación a %s', email)

                # Mismo mensaje exista o no el correo, para no revelar qué cuentas existen.
                messages.success(
                    request,
                    'Si el correo está registrado, te enviamos un enlace para '
                    'restablecer tu contraseña.',
                )
                return redirect('login')
        else:
            errores = ['Ingresa un correo válido.']

    return render(
        request,
        'auth_app/forgot_password.html',
        {'errores': errores, 'email': email},
    )


class RestablecerContrasenaView(PasswordResetConfirmView):
    """Pantalla a la que llega el enlace del correo para elegir una contraseña nueva."""

    template_name = 'auth_app/password_reset_confirm.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        # Quien abre el enlace del correo demuestra que controla ese correo.
        self.user.email_verificado = True
        messages.success(
            self.request,
            'Contraseña actualizada. Ya puedes iniciar sesión.',
        )
        return super().form_valid(form)
