from unittest import mock

from django.contrib.auth import SESSION_KEY
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import Group, Permission
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .catalogo import (
    GRUPO_ADMINISTRADOR,
    GRUPO_BASICO,
    GRUPO_MODERADOR,
    GRUPOS_SISTEMA,
    PERMISO_CHAT,
    PERMISO_MODERAR,
    PERMISO_PANEL,
)
from .models import Usuario
from .tokens import token_verificacion_email

CLAVE = 'Clave#2026x'


def crear_usuario(email='ana@example.com', verificado=True, **extra):
    return Usuario.objects.create_user(
        email=email,
        password=CLAVE,
        nombre=extra.pop('nombre', 'Ana Pérez'),
        email_verificado=verificado,
        **extra,
    )


class CatalogoInicialTests(TestCase):
    def test_se_crean_los_grupos_base(self):
        for nombre in GRUPOS_SISTEMA:
            self.assertTrue(Group.objects.filter(name=nombre).exists())

    def test_administrador_tiene_todos_los_permisos(self):
        admin = Group.objects.get(name=GRUPO_ADMINISTRADOR)
        self.assertEqual(admin.permissions.count(), Permission.objects.count())
        self.assertTrue(admin.permissions.filter(codename='acceder_panel').exists())

    def test_usuario_basico_no_accede_al_panel(self):
        basico = Group.objects.get(name=GRUPO_BASICO)
        self.assertFalse(basico.permissions.filter(codename='acceder_panel').exists())
        self.assertTrue(basico.permissions.filter(codename='usar_chat').exists())


class PermisosTests(TestCase):
    def test_usuario_nuevo_recibe_el_grupo_basico(self):
        usuario = crear_usuario()
        self.assertEqual(list(usuario.groups.values_list('name', flat=True)), [GRUPO_BASICO])
        self.assertTrue(usuario.has_perm('feed.add_petreport'))
        self.assertTrue(usuario.has_perm(PERMISO_CHAT))
        self.assertFalse(usuario.has_perm(PERMISO_MODERAR))
        self.assertFalse(usuario.has_perm(PERMISO_PANEL))

    def test_permiso_directo(self):
        usuario = crear_usuario()
        usuario.user_permissions.add(Permission.objects.get(codename='moderar_reportes'))
        usuario = Usuario.objects.get(pk=usuario.pk)
        self.assertTrue(usuario.has_perm(PERMISO_MODERAR))

    def test_el_moderador_modera_pero_no_entra_al_panel(self):
        usuario = crear_usuario()
        usuario.groups.set([Group.objects.get(name=GRUPO_MODERADOR)])
        usuario = Usuario.objects.get(pk=usuario.pk)
        self.assertTrue(usuario.has_perm(PERMISO_MODERAR))
        self.assertFalse(usuario.has_perm(PERMISO_PANEL))

    def test_usuario_inactivo_no_tiene_permisos(self):
        usuario = crear_usuario(is_active=False)
        self.assertFalse(usuario.has_perm('feed.add_petreport'))

    def test_superusuario_queda_en_el_grupo_administrador(self):
        admin = Usuario.objects.create_superuser(
            email='admin@example.com', password=CLAVE, nombre='Admin'
        )
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.email_verificado)
        self.assertEqual(list(admin.groups.values_list('name', flat=True)), [GRUPO_ADMINISTRADOR])
        self.assertTrue(admin.has_perm(PERMISO_PANEL))

    def test_correo_se_guarda_en_minusculas(self):
        usuario = crear_usuario(email='Ana@Example.COM')
        self.assertEqual(usuario.email, 'ana@example.com')


class RegistroTests(TestCase):
    datos = {
        'nombre': 'Luis Gómez',
        'email': 'luis@example.com',
        'password': CLAVE,
        'confirm_password': CLAVE,
    }

    @mock.patch('auth_app.views.enviar_verificacion_email', return_value=True)
    def test_registro_crea_usuario_sin_verificar(self, enviar):
        respuesta = self.client.post(reverse('register'), self.datos)

        self.assertRedirects(respuesta, reverse('login'))
        usuario = Usuario.objects.get(email='luis@example.com')
        self.assertFalse(usuario.email_verificado)
        self.assertTrue(usuario.check_password(CLAVE))
        enviar.assert_called_once()

    @mock.patch('auth_app.views.enviar_verificacion_email', return_value=True)
    def test_registro_rechaza_contrasena_debil(self, enviar):
        datos = dict(self.datos, password='sololetras', confirm_password='sololetras')
        respuesta = self.client.post(reverse('register'), datos)

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(Usuario.objects.filter(email='luis@example.com').exists())
        enviar.assert_not_called()

    @mock.patch('auth_app.views.enviar_verificacion_email', return_value=True)
    def test_registro_rechaza_contrasenas_distintas(self, enviar):
        datos = dict(self.datos, confirm_password='Otra#2026x')
        respuesta = self.client.post(reverse('register'), datos)

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(Usuario.objects.filter(email='luis@example.com').exists())

    @mock.patch('auth_app.views.enviar_verificacion_email', return_value=True)
    def test_registro_rechaza_correo_repetido(self, enviar):
        crear_usuario(email='luis@example.com')
        respuesta = self.client.post(reverse('register'), self.datos)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Usuario.objects.filter(email='luis@example.com').count(), 1)


class LoginTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_login_correcto(self):
        usuario = crear_usuario()
        respuesta = self.client.post(
            reverse('login'), {'email': 'ANA@example.com', 'password': CLAVE}
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(self.client.session[SESSION_KEY], str(usuario.pk))

    def test_login_bloqueado_si_el_correo_no_esta_verificado(self):
        crear_usuario(verificado=False)
        respuesta = self.client.post(
            reverse('login'), {'email': 'ana@example.com', 'password': CLAVE}
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertNotIn(SESSION_KEY, self.client.session)
        self.assertContains(respuesta, 'Debes verificar tu correo')

    def test_login_con_contrasena_incorrecta(self):
        crear_usuario()
        respuesta = self.client.post(
            reverse('login'), {'email': 'ana@example.com', 'password': 'mala'}
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertNotIn(SESSION_KEY, self.client.session)
        self.assertContains(respuesta, 'Correo o contraseña incorrectos.')

    def test_login_se_bloquea_tras_varios_intentos(self):
        crear_usuario()
        for _ in range(5):
            self.client.post(reverse('login'), {'email': 'ana@example.com', 'password': 'mala'})

        respuesta = self.client.post(
            reverse('login'), {'email': 'ana@example.com', 'password': CLAVE}
        )
        self.assertNotIn(SESSION_KEY, self.client.session)
        self.assertContains(respuesta, 'Demasiados intentos')

    def test_next_externo_se_ignora(self):
        crear_usuario()
        respuesta = self.client.post(
            reverse('login'),
            {'email': 'ana@example.com', 'password': CLAVE, 'next': 'https://sitio-malo.example/'},
        )
        self.assertEqual(respuesta.status_code, 302)
        self.assertNotIn('sitio-malo', respuesta['Location'])

    def test_logout_requiere_post(self):
        crear_usuario()
        self.client.post(reverse('login'), {'email': 'ana@example.com', 'password': CLAVE})

        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)
        self.assertIn(SESSION_KEY, self.client.session)

        self.client.post(reverse('logout'))
        self.assertNotIn(SESSION_KEY, self.client.session)


class VerificacionEmailTests(TestCase):
    def _url(self, usuario, token=None):
        return reverse(
            'verify_email',
            kwargs={
                'uidb64': urlsafe_base64_encode(force_bytes(usuario.pk)),
                'token': token or token_verificacion_email.make_token(usuario),
            },
        )

    def test_enlace_valido_verifica_el_correo(self):
        usuario = crear_usuario(verificado=False)
        self.client.get(self._url(usuario))

        usuario.refresh_from_db()
        self.assertTrue(usuario.email_verificado)

    def test_enlace_de_un_solo_uso(self):
        usuario = crear_usuario(verificado=False)
        token = token_verificacion_email.make_token(usuario)
        self.client.get(self._url(usuario, token))

        usuario.refresh_from_db()
        self.assertTrue(usuario.email_verificado)
        # Una vez verificado el correo, el mismo token ya no sirve.
        self.assertFalse(token_verificacion_email.check_token(usuario, token))

    def test_token_invalido_no_verifica(self):
        usuario = crear_usuario(verificado=False)
        self.client.get(self._url(usuario, token='abc-123'))

        usuario.refresh_from_db()
        self.assertFalse(usuario.email_verificado)

    @mock.patch('auth_app.views.enviar_verificacion_email', return_value=True)
    def test_reenvio_solo_para_cuentas_pendientes(self, enviar):
        cache.clear()
        crear_usuario(email='pendiente@example.com', verificado=False)
        crear_usuario(email='listo@example.com', verificado=True)

        self.client.post(reverse('resend_verification'), {'email': 'pendiente@example.com'})
        self.assertEqual(enviar.call_count, 1)

        self.client.post(reverse('resend_verification'), {'email': 'listo@example.com'})
        self.client.post(reverse('resend_verification'), {'email': 'nadie@example.com'})
        self.assertEqual(enviar.call_count, 1)


class RecuperarContrasenaTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_solicitud_responde_igual_exista_o_no_el_correo(self):
        crear_usuario()

        for correo in ('ana@example.com', 'nadie@example.com'):
            respuesta = self.client.post(reverse('forgot_password'), {'email': correo})
            self.assertRedirects(respuesta, reverse('login'))

    def test_restablecer_con_enlace_valido(self):
        usuario = crear_usuario(verificado=False)
        uid = urlsafe_base64_encode(force_bytes(usuario.pk))
        token = default_token_generator.make_token(usuario)

        # Django redirige el enlace del correo a una URL interna con el token en sesión.
        respuesta = self.client.get(
            reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token}),
            follow=True,
        )
        self.assertEqual(respuesta.status_code, 200)
        url_formulario = respuesta.redirect_chain[-1][0]

        nueva = 'Nueva#2026y'
        respuesta = self.client.post(
            url_formulario, {'new_password1': nueva, 'new_password2': nueva}
        )
        self.assertRedirects(respuesta, reverse('login'))

        usuario.refresh_from_db()
        self.assertTrue(usuario.check_password(nueva))
        self.assertTrue(usuario.email_verificado)

    def test_enlace_invalido_muestra_aviso(self):
        usuario = crear_usuario()
        uid = urlsafe_base64_encode(force_bytes(usuario.pk))
        respuesta = self.client.get(
            reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': 'mal-token'}),
            follow=True,
        )
        self.assertContains(respuesta, 'Enlace no válido')
