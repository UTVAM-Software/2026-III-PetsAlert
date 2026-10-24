import os
import shutil
import tempfile
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image
from rest_framework.test import APITestCase

from django.contrib.auth.models import Group

from auth_app.catalogo import GRUPO_MODERADOR
from auth_app.models import Usuario

from .models import PetReport

MEDIA_TEMPORAL = tempfile.mkdtemp(prefix='petsalert_tests_')
CLAVE = 'Clave#2026x'

def crear_usuario(email, nombre='Usuario', **extra):
    return Usuario.objects.create_user(
        email=email, password=CLAVE, nombre=nombre, email_verificado=True, **extra
    )

def foto(nombre='foto.jpg'):
    buffer = BytesIO()
    Image.new('RGB', (40, 40), 'orange').save(buffer, format='JPEG')
    return SimpleUploadedFile(nombre, buffer.getvalue(), content_type='image/jpeg')

def crear_reporte(usuario, **extra):
    datos = {
        'status': 'PERDIDO',
        'species': 'PERRO',
        'description': 'Collar rojo',
        'last_seen_location': 'Centro',
        'image': foto(),
    }
    datos.update(extra)
    return PetReport.objects.create(user=usuario, **datos)

def datos_validos(**extra):
    datos = {
        'status': 'ENCONTRADO',
        'species': 'GATO',
        'description': 'Gato gris con manchas blancas',
        'last_seen_location': 'Parque central',
        'image': foto(),
    }
    datos.update(extra)
    return datos

@override_settings(MEDIA_ROOT=MEDIA_TEMPORAL)
class ReportesApiTests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TEMPORAL, ignore_errors=True)

    def setUp(self):
        self.ana = crear_usuario('ana@example.com', nombre='Ana')
        self.luis = crear_usuario('luis@example.com', nombre='Luis')

    def test_lista_es_publica_y_solo_muestra_reportes_activos_sin_resolver(self):
        visible = crear_reporte(self.ana)
        crear_reporte(self.ana, is_resolved=True)
        crear_reporte(self.ana, is_active=False)

        respuesta = self.client.get(reverse('report-list'))

        self.assertEqual(respuesta.status_code, 200)
        ids = [reporte['id'] for reporte in respuesta.data['results']]
        self.assertEqual(ids, [visible.id])

    def test_filtro_por_especie(self):
        perro = crear_reporte(self.ana, species='PERRO')
        crear_reporte(self.ana, species='GATO')

        respuesta = self.client.get(reverse('report-list'), {'species': 'perro'})

        ids = [reporte['id'] for reporte in respuesta.data['results']]
        self.assertEqual(ids, [perro.id])

    def test_busqueda_por_texto(self):
        coincide = crear_reporte(self.ana, description='Perro con collar azul')
        crear_reporte(self.ana, description='Gato siamés')

        respuesta = self.client.get(reverse('report-list'), {'search': 'azul'})

        ids = [reporte['id'] for reporte in respuesta.data['results']]
        self.assertEqual(ids, [coincide.id])

    def test_detalle_oculto_solo_lo_ve_el_dueno(self):
        oculto = crear_reporte(self.ana, is_active=False)
        url = reverse('report-detail', args=[oculto.id])

        self.assertEqual(self.client.get(url).status_code, 404)

        self.client.force_authenticate(self.luis)
        self.assertEqual(self.client.get(url).status_code, 404)

        self.client.force_authenticate(self.ana)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_mis_reportes_incluye_los_resueltos_y_solo_los_propios(self):
        propio = crear_reporte(self.ana)
        resuelto = crear_reporte(self.ana, is_resolved=True)
        crear_reporte(self.luis)

        self.client.force_authenticate(self.ana)
        respuesta = self.client.get(reverse('report-mine'))

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual({r['id'] for r in respuesta.data}, {propio.id, resuelto.id})

    def test_mis_reportes_requiere_sesion(self):
        respuesta = self.client.get(reverse('report-mine'))
        self.assertIn(respuesta.status_code, (401, 403))

    def test_crear_requiere_sesion(self):
        respuesta = self.client.post(reverse('report-list'), datos_validos(), format='multipart')
        self.assertIn(respuesta.status_code, (401, 403))
        self.assertEqual(PetReport.objects.count(), 0)

    def test_crear_reporte_con_foto(self):
        self.client.force_authenticate(self.ana)
        respuesta = self.client.post(reverse('report-list'), datos_validos(), format='multipart')

        self.assertEqual(respuesta.status_code, 201, respuesta.data)

        reporte = PetReport.objects.get()
        self.assertEqual(reporte.user, self.ana)
        self.assertEqual(reporte.species, 'GATO')
        self.assertTrue(os.path.exists(reporte.image.path))

        self.assertTrue(respuesta.data['is_mine'])
        self.assertTrue(respuesta.data['can_edit'])
        self.assertTrue(respuesta.data['can_delete'])
        self.assertIn('pets_photos', respuesta.data['image'])

    def test_crear_sin_foto_falla(self):
        self.client.force_authenticate(self.ana)
        datos = datos_validos()
        del datos['image']

        respuesta = self.client.post(reverse('report-list'), datos, format='multipart')

        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('image', respuesta.data)

    def test_crear_sin_descripcion_falla(self):
        self.client.force_authenticate(self.ana)

        respuesta = self.client.post(
            reverse('report-list'), datos_validos(description='   '), format='multipart'
        )

        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('description', respuesta.data)

    def test_crear_sin_permiso_se_rechaza(self):
        self.ana.groups.clear()
        self.client.force_authenticate(Usuario.objects.get(pk=self.ana.pk))

        respuesta = self.client.post(reverse('report-list'), datos_validos(), format='multipart')

        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(PetReport.objects.count(), 0)

    def test_el_dueno_edita_su_reporte(self):
        reporte = crear_reporte(self.ana)
        self.client.force_authenticate(self.ana)

        respuesta = self.client.patch(
            reverse('report-detail', args=[reporte.id]),
            {'description': 'Ahora con placa'},
            format='json',
        )

        self.assertEqual(respuesta.status_code, 200)
        reporte.refresh_from_db()
        self.assertEqual(reporte.description, 'Ahora con placa')

    def test_otro_usuario_no_puede_editar(self):
        reporte = crear_reporte(self.ana)
        self.client.force_authenticate(self.luis)

        respuesta = self.client.patch(
            reverse('report-detail', args=[reporte.id]),
            {'description': 'Hackeado'},
            format='json',
        )

        self.assertEqual(respuesta.status_code, 403)
        reporte.refresh_from_db()
        self.assertEqual(reporte.description, 'Collar rojo')

    def test_el_moderador_puede_editar_cualquier_reporte(self):
        reporte = crear_reporte(self.ana)
        self.luis.groups.set([Group.objects.get(name=GRUPO_MODERADOR)])
        self.client.force_authenticate(Usuario.objects.get(pk=self.luis.pk))

        respuesta = self.client.patch(
            reverse('report-detail', args=[reporte.id]),
            {'description': 'Corregido por moderación'},
            format='json',
        )

        self.assertEqual(respuesta.status_code, 200)

    def test_marcar_como_resuelto_lo_quita_del_feed(self):
        reporte = crear_reporte(self.ana)
        self.client.force_authenticate(self.ana)

        respuesta = self.client.patch(
            reverse('report-detail', args=[reporte.id]), {'is_resolved': True}, format='json'
        )
        self.assertEqual(respuesta.status_code, 200)

        lista = self.client.get(reverse('report-list'))
        self.assertEqual(lista.data['results'], [])

    def test_reemplazar_la_foto_borra_la_anterior(self):
        reporte = crear_reporte(self.ana)
        ruta_anterior = reporte.image.path
        self.assertTrue(os.path.exists(ruta_anterior))

        self.client.force_authenticate(self.ana)
        respuesta = self.client.patch(
            reverse('report-detail', args=[reporte.id]),
            {'image': foto('nueva.jpg')},
            format='multipart',
        )

        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        reporte.refresh_from_db()
        self.assertFalse(os.path.exists(ruta_anterior))
        self.assertTrue(os.path.exists(reporte.image.path))

    def test_el_dueno_elimina_su_reporte_y_se_borra_la_foto(self):
        reporte = crear_reporte(self.ana)
        ruta = reporte.image.path
        self.client.force_authenticate(self.ana)

        respuesta = self.client.delete(reverse('report-detail', args=[reporte.id]))

        self.assertEqual(respuesta.status_code, 204)
        self.assertFalse(PetReport.objects.filter(pk=reporte.id).exists())
        self.assertFalse(os.path.exists(ruta))

    def test_otro_usuario_no_puede_eliminar(self):
        reporte = crear_reporte(self.ana)
        self.client.force_authenticate(self.luis)

        respuesta = self.client.delete(reverse('report-detail', args=[reporte.id]))

        self.assertEqual(respuesta.status_code, 403)
        self.assertTrue(PetReport.objects.filter(pk=reporte.id).exists())

@override_settings(MEDIA_ROOT=MEDIA_TEMPORAL)
class PantallasReportesTests(TestCase):
    def setUp(self):
        self.ana = crear_usuario('ana@example.com', nombre='Ana')
        self.luis = crear_usuario('luis@example.com', nombre='Luis')
        self.reporte = crear_reporte(self.ana)

    def test_feed_y_detalle_piden_iniciar_sesion(self):
        for url in (
            reverse('feed_screen'),
            reverse('pet_detail_screen', args=[self.reporte.id]),
        ):
            respuesta = self.client.get(url)
            self.assertEqual(respuesta.status_code, 302, url)
            self.assertIn('next=', respuesta['Location'])

    def test_feed_y_detalle_con_sesion(self):
        self.client.force_login(self.luis)
        self.assertEqual(self.client.get(reverse('feed_screen')).status_code, 200)
        self.assertEqual(
            self.client.get(reverse('pet_detail_screen', args=[self.reporte.id])).status_code, 200
        )

    def test_detalle_de_reporte_inexistente(self):
        self.client.force_login(self.luis)
        self.assertEqual(self.client.get(reverse('pet_detail_screen', args=[9999])).status_code, 404)

    def test_la_api_de_lectura_pide_sesion(self):
        from rest_framework.test import APIClient

        cliente = APIClient()
        self.assertIn(cliente.get(reverse('report-list')).status_code, (401, 403))
        self.assertIn(
            cliente.get(reverse('report-detail', args=[self.reporte.id])).status_code, (401, 403)
        )

    def test_crear_reporte_pide_iniciar_sesion(self):
        respuesta = self.client.get(reverse('add_report_screen'))

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn('next=', respuesta['Location'])

    def test_crear_reporte_con_sesion(self):
        self.client.force_login(self.ana)
        self.assertEqual(self.client.get(reverse('add_report_screen')).status_code, 200)

    def test_editar_reporte_ajeno_esta_prohibido(self):
        self.client.force_login(self.luis)
        respuesta = self.client.get(reverse('edit_report_screen', args=[self.reporte.id]))
        self.assertEqual(respuesta.status_code, 403)

    def test_editar_reporte_propio(self):
        self.client.force_login(self.ana)
        respuesta = self.client.get(reverse('edit_report_screen', args=[self.reporte.id]))
        self.assertEqual(respuesta.status_code, 200)

    def test_mis_reportes_pide_iniciar_sesion(self):
        respuesta = self.client.get(reverse('my_reports_screen'))

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn('next=', respuesta['Location'])

        self.client.force_login(self.ana)
        self.assertEqual(self.client.get(reverse('my_reports_screen')).status_code, 200)
