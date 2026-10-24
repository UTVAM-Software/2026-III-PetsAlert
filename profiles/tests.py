from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase

from auth_app.models import Usuario

CLAVE = 'Clave#2026x'

def crear_usuario(email='ana@example.com', nombre='Ana Pérez', **extra):
    return Usuario.objects.create_user(
        email=email, password=CLAVE, nombre=nombre, email_verificado=True, **extra
    )

class PerfilApiTests(APITestCase):
    def setUp(self):
        self.ana = crear_usuario(telefono='5512345678')

    def test_requiere_sesion(self):
        respuesta = self.client.get(reverse('api_user_profile'))
        self.assertIn(respuesta.status_code, (401, 403))

    def test_ver_mi_perfil(self):
        self.client.force_authenticate(self.ana)

        respuesta = self.client.get(reverse('api_user_profile'))

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data['nombre'], 'Ana Pérez')
        self.assertEqual(respuesta.data['email'], 'ana@example.com')
        self.assertEqual(respuesta.data['telefono'], '5512345678')
        self.assertEqual(respuesta.data['rol'], 'Usuario básico')

    def test_editar_nombre_y_telefono(self):
        self.client.force_authenticate(self.ana)

        respuesta = self.client.patch(
            reverse('api_user_profile'),
            {'nombre': 'Ana María Pérez', 'telefono': '+52 55 1234 5678'},
            format='json',
        )

        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        self.ana.refresh_from_db()
        self.assertEqual(self.ana.nombre, 'Ana María Pérez')
        self.assertEqual(self.ana.telefono, '+52 55 1234 5678')

    def test_no_se_puede_cambiar_el_correo_ni_el_rol(self):
        self.client.force_authenticate(self.ana)

        self.client.patch(
            reverse('api_user_profile'),
            {'email': 'otro@example.com', 'rol': 'Administrador', 'is_superuser': True},
            format='json',
        )

        self.ana.refresh_from_db()
        self.assertEqual(self.ana.email, 'ana@example.com')
        self.assertFalse(self.ana.is_superuser)
        self.assertEqual(list(self.ana.groups.values_list('name', flat=True)), ['Usuario básico'])

    def test_nombre_vacio_se_rechaza(self):
        self.client.force_authenticate(self.ana)

        respuesta = self.client.patch(reverse('api_user_profile'), {'nombre': '   '}, format='json')

        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('nombre', respuesta.data)

    def test_telefono_invalido_se_rechaza(self):
        self.client.force_authenticate(self.ana)

        respuesta = self.client.patch(reverse('api_user_profile'), {'telefono': 'abc<script>'}, format='json')

        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('telefono', respuesta.data)

    def test_se_puede_borrar_el_telefono(self):
        self.client.force_authenticate(self.ana)

        respuesta = self.client.patch(reverse('api_user_profile'), {'telefono': ''}, format='json')

        self.assertEqual(respuesta.status_code, 200)
        self.ana.refresh_from_db()
        self.assertEqual(self.ana.telefono, '')

class PantallasPerfilTests(TestCase):
    def setUp(self):
        self.ana = crear_usuario()

    def test_las_pantallas_piden_iniciar_sesion(self):
        for nombre in ('profile_screen', 'privacy_screen', 'my_reports_screen'):
            respuesta = self.client.get(reverse(nombre))
            self.assertEqual(respuesta.status_code, 302, nombre)
            self.assertIn('next=', respuesta['Location'])

    def test_el_perfil_muestra_nombre_correo_y_telefono(self):
        self.ana.telefono = '5512345678'
        self.ana.save()
        self.client.force_login(self.ana)

        respuesta = self.client.get(reverse('profile_screen'))

        self.assertContains(respuesta, 'Ana Pérez')
        self.assertContains(respuesta, 'ana@example.com')
        self.assertContains(respuesta, '5512345678')

    def test_el_perfil_sin_telefono_dice_sin_numero(self):
        self.client.force_login(self.ana)
        self.assertContains(self.client.get(reverse('profile_screen')), 'Sin número')
