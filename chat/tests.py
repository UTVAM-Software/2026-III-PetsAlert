from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase

from auth_app.models import Usuario
from feed.models import PetReport

from .models import Chat, ChatMessage

CLAVE = 'Clave#2026x'


def crear_usuario(email, nombre='Usuario', **extra):
    return Usuario.objects.create_user(
        email=email, password=CLAVE, nombre=nombre, email_verificado=True, **extra
    )


def crear_reporte(usuario, **extra):
    datos = {
        'status': 'PERDIDO',
        'species': 'PERRO',
        'description': 'Collar rojo',
        'last_seen_location': 'Centro',
    }
    datos.update(extra)
    return PetReport.objects.create(user=usuario, **datos)


class ChatApiTests(APITestCase):
    def setUp(self):
        self.ana = crear_usuario('ana@example.com', nombre='Ana')      # dueña del reporte
        self.luis = crear_usuario('luis@example.com', nombre='Luis')    # interesado
        self.eva = crear_usuario('eva@example.com', nombre='Eva')       # ajena a la conversación
        self.reporte = crear_reporte(self.ana)

    def abrir_chat(self, usuario=None, reporte=None):
        self.client.force_authenticate(usuario or self.luis)
        return self.client.post(
            reverse('chat-list'), {'report': (reporte or self.reporte).id}, format='json'
        )

    # --- Abrir un chat ------------------------------------------------------

    def test_abrir_chat_crea_la_conversacion_con_el_dueno_del_reporte(self):
        respuesta = self.abrir_chat()

        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        chat = Chat.objects.get()
        self.assertEqual(chat.report, self.reporte)
        self.assertEqual(chat.owner, self.ana)
        self.assertEqual(chat.interested, self.luis)
        self.assertEqual(respuesta.data['other_user']['nombre'], 'Ana')

    def test_abrir_otra_vez_devuelve_el_mismo_chat(self):
        primero = self.abrir_chat()
        segundo = self.abrir_chat()

        self.assertEqual(segundo.status_code, 200)
        self.assertEqual(primero.data['id'], segundo.data['id'])
        self.assertEqual(Chat.objects.count(), 1)

    def test_el_dueno_no_puede_chatear_consigo_mismo(self):
        respuesta = self.abrir_chat(usuario=self.ana)

        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('report', respuesta.data)
        self.assertEqual(Chat.objects.count(), 0)

    def test_no_se_puede_abrir_chat_de_un_reporte_oculto(self):
        oculto = crear_reporte(self.ana, is_active=False)

        respuesta = self.abrir_chat(reporte=oculto)

        self.assertEqual(respuesta.status_code, 400)

    def test_reporte_inexistente(self):
        self.client.force_authenticate(self.luis)
        respuesta = self.client.post(reverse('chat-list'), {'report': 9999}, format='json')
        self.assertEqual(respuesta.status_code, 400)

    def test_requiere_sesion(self):
        respuesta = self.client.post(reverse('chat-list'), {'report': self.reporte.id}, format='json')
        self.assertIn(respuesta.status_code, (401, 403))

    def test_requiere_el_permiso_usar_chat(self):
        self.luis.groups.clear()

        respuesta = self.abrir_chat(usuario=Usuario.objects.get(pk=self.luis.pk))

        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(Chat.objects.count(), 0)

    def test_la_base_impide_chats_repetidos_y_chat_consigo_mismo(self):
        Chat.objects.create(report=self.reporte, owner=self.ana, interested=self.luis)

        with self.assertRaises(IntegrityError), transaction.atomic():
            Chat.objects.create(report=self.reporte, owner=self.ana, interested=self.luis)

        with self.assertRaises(IntegrityError), transaction.atomic():
            Chat.objects.create(report=self.reporte, owner=self.ana, interested=self.ana)

    # --- Mensajes -----------------------------------------------------------

    def test_enviar_y_leer_mensajes(self):
        chat_id = self.abrir_chat().data['id']
        url = reverse('chat-messages', args=[chat_id])

        enviado = self.client.post(url, {'content': '  Hola, vi a tu perro  '}, format='json')
        self.assertEqual(enviado.status_code, 201, enviado.data)
        self.assertEqual(enviado.data['content'], 'Hola, vi a tu perro')
        self.assertTrue(enviado.data['is_mine'])

        # La dueña responde y ve los dos mensajes.
        self.client.force_authenticate(self.ana)
        self.client.post(url, {'content': '¿Dónde?'}, format='json')

        lectura = self.client.get(url)
        self.assertEqual([m['content'] for m in lectura.data], ['Hola, vi a tu perro', '¿Dónde?'])
        self.assertEqual([m['is_mine'] for m in lectura.data], [False, True])

    def test_pedir_solo_los_mensajes_nuevos(self):
        chat_id = self.abrir_chat().data['id']
        url = reverse('chat-messages', args=[chat_id])

        primero = self.client.post(url, {'content': 'uno'}, format='json').data['id']
        self.client.post(url, {'content': 'dos'}, format='json')

        respuesta = self.client.get(url, {'after': primero})

        self.assertEqual([m['content'] for m in respuesta.data], ['dos'])

    def test_mensaje_vacio_o_muy_largo(self):
        chat_id = self.abrir_chat().data['id']
        url = reverse('chat-messages', args=[chat_id])

        self.assertEqual(self.client.post(url, {'content': '   '}, format='json').status_code, 400)
        self.assertEqual(self.client.post(url, {'content': 'x' * 2001}, format='json').status_code, 400)
        self.assertEqual(ChatMessage.objects.count(), 0)

    def test_un_ajeno_no_puede_ver_ni_escribir(self):
        chat_id = self.abrir_chat().data['id']
        url = reverse('chat-messages', args=[chat_id])
        self.client.post(url, {'content': 'privado'}, format='json')

        self.client.force_authenticate(self.eva)

        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, {'content': 'intruso'}, format='json').status_code, 404)
        self.assertEqual(self.client.get(reverse('chat-detail', args=[chat_id])).status_code, 404)
        self.assertEqual(ChatMessage.objects.count(), 1)

    def test_abrir_la_conversacion_marca_como_leidos_los_mensajes_del_otro(self):
        chat_id = self.abrir_chat().data['id']
        url = reverse('chat-messages', args=[chat_id])
        self.client.post(url, {'content': 'Hola'}, format='json')

        # Antes de que la dueña abra el chat, tiene 1 mensaje sin leer.
        self.client.force_authenticate(self.ana)
        lista = self.client.get(reverse('chat-list'))
        self.assertEqual(lista.data[0]['unread_count'], 1)

        self.client.get(url)

        lista = self.client.get(reverse('chat-list'))
        self.assertEqual(lista.data[0]['unread_count'], 0)
        self.assertTrue(ChatMessage.objects.get().is_read)

    # --- Lista de chats -----------------------------------------------------

    def test_la_lista_solo_muestra_mis_chats_con_el_ultimo_mensaje(self):
        chat_id = self.abrir_chat().data['id']
        self.client.post(reverse('chat-messages', args=[chat_id]), {'content': 'Hola'}, format='json')

        otro_reporte = crear_reporte(self.eva)
        self.abrir_chat(usuario=self.ana, reporte=otro_reporte)  # chat entre Ana y Eva

        self.client.force_authenticate(self.luis)
        lista = self.client.get(reverse('chat-list'))

        self.assertEqual(len(lista.data), 1)
        chat = lista.data[0]
        self.assertEqual(chat['id'], chat_id)
        self.assertEqual(chat['other_user']['nombre'], 'Ana')
        self.assertEqual(chat['last_message']['content'], 'Hola')
        self.assertTrue(chat['last_message']['is_mine'])
        self.assertEqual(chat['unread_count'], 0)
        self.assertEqual(chat['report']['id'], self.reporte.id)

    def test_el_chat_con_actividad_reciente_va_primero(self):
        otro_reporte = crear_reporte(self.ana, description='Otro')
        viejo = self.abrir_chat().data['id']
        reciente = self.abrir_chat(reporte=otro_reporte).data['id']

        self.client.post(reverse('chat-messages', args=[viejo]), {'content': 'Subo el chat'}, format='json')

        lista = self.client.get(reverse('chat-list'))
        self.assertEqual([c['id'] for c in lista.data], [viejo, reciente])


class PantallasChatTests(TestCase):
    def setUp(self):
        self.ana = crear_usuario('ana@example.com', nombre='Ana')
        self.luis = crear_usuario('luis@example.com', nombre='Luis')
        self.eva = crear_usuario('eva@example.com', nombre='Eva')
        self.reporte = crear_reporte(self.ana)
        self.chat = Chat.objects.create(report=self.reporte, owner=self.ana, interested=self.luis)

    def test_la_lista_pide_iniciar_sesion(self):
        respuesta = self.client.get(reverse('chat_list_screen'))

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn('next=', respuesta['Location'])

        self.client.force_login(self.luis)
        self.assertEqual(self.client.get(reverse('chat_list_screen')).status_code, 200)

    def test_la_sala_solo_la_ven_los_participantes(self):
        url = reverse('chat_room_screen', args=[self.chat.id])

        self.client.force_login(self.luis)
        respuesta = self.client.get(url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Ana')

        self.client.force_login(self.ana)
        self.assertEqual(self.client.get(url).status_code, 200)

        self.client.force_login(self.eva)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_al_borrar_el_reporte_se_borran_sus_chats(self):
        ChatMessage.objects.create(chat=self.chat, sender=self.luis, content='Hola')

        self.reporte.delete()

        self.assertEqual(Chat.objects.count(), 0)
        self.assertEqual(ChatMessage.objects.count(), 0)
