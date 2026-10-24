from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from auth_app.catalogo import GRUPO_ADMINISTRADOR, GRUPO_BASICO, GRUPO_MODERADOR
from auth_app.models import Usuario
from chat.models import Chat, ChatMessage
from feed.models import PetReport

CLAVE = 'Clave#2026x'

def crear_usuario(email, nombre='Persona', grupo=None, **extra):
    usuario = Usuario.objects.create_user(
        email=email, password=CLAVE, nombre=nombre, email_verificado=True, **extra
    )
    if grupo is not None:
        usuario.groups.set([Group.objects.get(name=grupo)])
    return usuario

class PanelBase(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_superuser(
            email='admin@example.com', password=CLAVE, nombre='Admin'
        )
        self.ana = crear_usuario('ana@example.com', 'Ana')
        self.luis = crear_usuario('luis@example.com', 'Luis', GRUPO_MODERADOR)
        self.reporte = PetReport.objects.create(
            user=self.ana,
            status='PERDIDO',
            species='PERRO',
            description='Collar rojo',
            last_seen_location='Centro',
        )
        self.chat = Chat.objects.create(report=self.reporte, owner=self.ana, interested=self.luis)
        self.mensaje = ChatMessage.objects.create(chat=self.chat, sender=self.luis, content='Hola')

    def urls_panel(self):
        objetos = {
            'usuario': self.ana.pk,
            'grupo': Group.objects.get(name=GRUPO_BASICO).pk,
            'permiso': Permission.objects.first().pk,
            'reporte': self.reporte.pk,
            'chat': self.chat.pk,
            'mensaje': self.mensaje.pk,
        }
        urls = [reverse('panel:index')]
        for slug, pk in objetos.items():
            urls += [
                reverse(f'panel:{slug}_list'),
                reverse(f'panel:{slug}_create'),
                reverse(f'panel:{slug}_detail', args=[pk]),
                reverse(f'panel:{slug}_update', args=[pk]),
                reverse(f'panel:{slug}_delete', args=[pk]),
            ]
        return urls

class ControlDeAccesoPanelTests(PanelBase):
    def test_sin_sesion_redirige_al_login_en_todas_las_pantallas(self):
        for url in self.urls_panel():
            respuesta = self.client.get(url)
            self.assertEqual(respuesta.status_code, 302, url)
            self.assertIn('next=', respuesta['Location'], url)

    def test_sin_sesion_no_se_puede_enviar_por_post(self):
        respuesta = self.client.post(reverse('panel:usuario_delete', args=[self.ana.pk]))
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(Usuario.objects.filter(pk=self.ana.pk).exists())

    def test_usuario_basico_recibe_403_en_todas_las_pantallas(self):
        self.client.force_login(self.ana)
        for url in self.urls_panel():
            self.assertEqual(self.client.get(url).status_code, 403, url)

    def test_usuario_basico_no_puede_borrar_ni_crear_por_post(self):
        self.client.force_login(self.ana)

        respuesta = self.client.post(reverse('panel:reporte_delete', args=[self.reporte.pk]))
        self.assertEqual(respuesta.status_code, 403)
        self.assertTrue(PetReport.objects.filter(pk=self.reporte.pk).exists())

        respuesta = self.client.post(
            reverse('panel:grupo_create'), {'name': 'Intruso', 'permissions': []}
        )
        self.assertEqual(respuesta.status_code, 403)
        self.assertFalse(Group.objects.filter(name='Intruso').exists())

    def test_moderador_no_entra_al_panel(self):
        self.client.force_login(self.luis)
        for url in self.urls_panel():
            self.assertEqual(self.client.get(url).status_code, 403, url)

    def test_administrador_accede_a_todas_las_pantallas(self):
        self.client.force_login(self.admin)
        for url in self.urls_panel():
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_el_panel_exige_el_permiso_del_modelo_ademas_del_acceso(self):
        grupo = Group.objects.create(name='Solo lectura de usuarios')
        grupo.permissions.set(
            Permission.objects.filter(codename__in=['acceder_panel', 'view_usuario'])
        )
        lector = crear_usuario('lector@example.com', 'Lector')
        lector.groups.set([grupo])
        self.client.force_login(lector)

        self.assertEqual(self.client.get(reverse('panel:usuario_list')).status_code, 200)
        self.assertEqual(self.client.get(reverse('panel:usuario_create')).status_code, 403)
        self.assertEqual(
            self.client.get(reverse('panel:usuario_update', args=[self.ana.pk])).status_code, 403
        )
        self.assertEqual(self.client.get(reverse('panel:grupo_list')).status_code, 403)

    def test_quien_no_es_superusuario_no_ve_a_los_superusuarios(self):
        grupo = Group.objects.create(name='Gestores de usuarios')
        grupo.permissions.set(
            Permission.objects.filter(
                codename__in=['acceder_panel', 'view_usuario', 'change_usuario', 'delete_usuario']
            )
        )
        gestor = crear_usuario('gestor@example.com', 'Gestor')
        gestor.groups.set([grupo])
        self.client.force_login(gestor)

        self.assertEqual(
            self.client.get(reverse('panel:usuario_detail', args=[self.admin.pk])).status_code, 404
        )
        self.assertEqual(
            self.client.post(reverse('panel:usuario_delete', args=[self.admin.pk])).status_code, 404
        )
        self.assertTrue(Usuario.objects.filter(pk=self.admin.pk).exists())

    def test_quien_no_es_superusuario_no_puede_volver_superusuario_a_nadie(self):
        grupo = Group.objects.create(name='Editores de usuarios')
        grupo.permissions.set(
            Permission.objects.filter(codename__in=['acceder_panel', 'view_usuario', 'change_usuario'])
        )
        editor = crear_usuario('editor@example.com', 'Editor')
        editor.groups.set([grupo])
        self.client.force_login(editor)

        self.client.post(
            reverse('panel:usuario_update', args=[self.ana.pk]),
            {
                'nombre': 'Ana',
                'email': 'ana@example.com',
                'is_active': 'on',
                'email_verificado': 'on',
                'is_superuser': 'on',
                'is_staff': 'on',
            },
        )

        self.ana.refresh_from_db()
        self.assertFalse(self.ana.is_superuser)
        self.assertFalse(self.ana.is_staff)

class CrudPanelTests(PanelBase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)

    def test_crear_usuario_con_grupo_y_permiso_directo(self):
        moderar = Permission.objects.get(codename='moderar_reportes')
        respuesta = self.client.post(
            reverse('panel:usuario_create'),
            {
                'nombre': 'Marta',
                'email': 'Marta@Example.com',
                'password1': CLAVE,
                'password2': CLAVE,
                'is_active': 'on',
                'email_verificado': 'on',
                'groups': [Group.objects.get(name=GRUPO_MODERADOR).pk],
                'user_permissions': [moderar.pk],
            },
        )

        self.assertRedirects(respuesta, reverse('panel:usuario_list'))
        marta = Usuario.objects.get(email='marta@example.com')
        self.assertTrue(marta.check_password(CLAVE))
        self.assertTrue(marta.email_verificado)
        self.assertEqual(list(marta.groups.values_list('name', flat=True)), [GRUPO_MODERADOR])
        self.assertEqual(list(marta.user_permissions.all()), [moderar])

    def test_crear_usuario_exige_contrasena_valida_y_correo_unico(self):
        respuesta = self.client.post(
            reverse('panel:usuario_create'),
            {'nombre': 'Marta', 'email': 'ana@example.com', 'password1': '', 'password2': ''},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('email', respuesta.context['form'].errors)
        self.assertIn('password1', respuesta.context['form'].errors)

    def test_editar_usuario_cambia_grupos_sin_tocar_la_contrasena(self):
        respuesta = self.client.post(
            reverse('panel:usuario_update', args=[self.ana.pk]),
            {
                'nombre': 'Ana María',
                'email': 'ana@example.com',
                'password1': '',
                'password2': '',
                'is_active': 'on',
                'email_verificado': 'on',
                'groups': [Group.objects.get(name=GRUPO_ADMINISTRADOR).pk],
            },
        )

        self.assertRedirects(respuesta, reverse('panel:usuario_list'))
        self.ana.refresh_from_db()
        self.assertEqual(self.ana.nombre, 'Ana María')
        self.assertTrue(self.ana.check_password(CLAVE))
        self.assertEqual(
            list(self.ana.groups.values_list('name', flat=True)), [GRUPO_ADMINISTRADOR]
        )

    def test_eliminar_usuario(self):
        respuesta = self.client.post(reverse('panel:usuario_delete', args=[self.luis.pk]))
        self.assertRedirects(respuesta, reverse('panel:usuario_list'))
        self.assertFalse(Usuario.objects.filter(pk=self.luis.pk).exists())

    def test_no_se_puede_eliminar_la_propia_cuenta(self):
        self.client.post(reverse('panel:usuario_delete', args=[self.admin.pk]))
        self.assertTrue(Usuario.objects.filter(pk=self.admin.pk).exists())

    def test_crud_de_grupos(self):
        permisos = Permission.objects.filter(codename__in=['view_petreport', 'moderar_reportes'])
        self.client.post(
            reverse('panel:grupo_create'),
            {'name': 'Revisores', 'permissions': [p.pk for p in permisos]},
        )
        grupo = Group.objects.get(name='Revisores')
        self.assertEqual(grupo.permissions.count(), 2)

        self.client.post(
            reverse('panel:grupo_update', args=[grupo.pk]),
            {'name': 'Revisores 2', 'permissions': [permisos[0].pk]},
        )
        grupo.refresh_from_db()
        self.assertEqual(grupo.name, 'Revisores 2')
        self.assertEqual(grupo.permissions.count(), 1)

        self.client.post(reverse('panel:grupo_delete', args=[grupo.pk]))
        self.assertFalse(Group.objects.filter(pk=grupo.pk).exists())

    def test_los_grupos_base_no_se_eliminan_ni_se_renombran(self):
        basico = Group.objects.get(name=GRUPO_BASICO)

        self.client.post(reverse('panel:grupo_delete', args=[basico.pk]))
        self.assertTrue(Group.objects.filter(pk=basico.pk).exists())

        self.client.post(reverse('panel:grupo_update', args=[basico.pk]), {'name': 'Otro'})
        basico.refresh_from_db()
        self.assertEqual(basico.name, GRUPO_BASICO)

    def test_crud_de_permisos(self):
        tipo = Permission.objects.get(codename='moderar_reportes').content_type
        self.client.post(
            reverse('panel:permiso_create'),
            {'name': 'Exportar reportes', 'codename': 'exportar_reportes', 'content_type': tipo.pk},
        )
        permiso = Permission.objects.get(codename='exportar_reportes')

        self.client.post(
            reverse('panel:permiso_update', args=[permiso.pk]),
            {'name': 'Exportar todo', 'codename': 'exportar_reportes', 'content_type': tipo.pk},
        )
        permiso.refresh_from_db()
        self.assertEqual(permiso.name, 'Exportar todo')

        self.client.post(reverse('panel:permiso_delete', args=[permiso.pk]))
        self.assertFalse(Permission.objects.filter(pk=permiso.pk).exists())

    def test_los_permisos_que_usa_la_app_no_se_eliminan(self):
        permiso = Permission.objects.get(codename='moderar_reportes')
        self.client.post(reverse('panel:permiso_delete', args=[permiso.pk]))
        self.assertTrue(Permission.objects.filter(pk=permiso.pk).exists())

    def test_editar_y_eliminar_reporte(self):
        self.client.post(
            reverse('panel:reporte_update', args=[self.reporte.pk]),
            {
                'user': self.ana.pk,
                'status': 'ENCONTRADO',
                'species': 'GATO',
                'description': 'Editado desde el panel',
                'last_seen_location': 'Norte',
                'is_active': 'on',
            },
        )
        self.reporte.refresh_from_db()
        self.assertEqual(self.reporte.species, 'GATO')

        self.client.post(reverse('panel:reporte_delete', args=[self.reporte.pk]))
        self.assertFalse(PetReport.objects.filter(pk=self.reporte.pk).exists())

    def test_crear_chat_valida_dueno_e_interesado(self):
        otro = crear_usuario('otro@example.com', 'Otro')

        respuesta = self.client.post(
            reverse('panel:chat_create'),
            {'report': self.reporte.pk, 'owner': otro.pk, 'interested': self.luis.pk},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('owner', respuesta.context['form'].errors)

        respuesta = self.client.post(
            reverse('panel:chat_create'),
            {'report': self.reporte.pk, 'owner': self.ana.pk, 'interested': otro.pk},
        )
        self.assertRedirects(respuesta, reverse('panel:chat_list'))
        self.assertTrue(Chat.objects.filter(report=self.reporte, interested=otro).exists())

    def test_mensajes_solo_de_participantes(self):
        otro = crear_usuario('otro@example.com', 'Otro')

        respuesta = self.client.post(
            reverse('panel:mensaje_create'),
            {'chat': self.chat.pk, 'sender': otro.pk, 'content': 'Intruso'},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('sender', respuesta.context['form'].errors)

        respuesta = self.client.post(
            reverse('panel:mensaje_update', args=[self.mensaje.pk]),
            {'chat': self.chat.pk, 'sender': self.luis.pk, 'content': 'Editado', 'is_read': 'on'},
        )
        self.assertRedirects(respuesta, reverse('panel:mensaje_list'))
        self.mensaje.refresh_from_db()
        self.assertEqual(self.mensaje.content, 'Editado')

        self.client.post(reverse('panel:mensaje_delete', args=[self.mensaje.pk]))
        self.assertFalse(ChatMessage.objects.filter(pk=self.mensaje.pk).exists())

    def test_busqueda_en_el_listado_de_usuarios(self):
        respuesta = self.client.get(reverse('panel:usuario_list'), {'q': 'luis'})
        self.assertContains(respuesta, 'luis@example.com')
        self.assertNotContains(respuesta, 'ana@example.com')
