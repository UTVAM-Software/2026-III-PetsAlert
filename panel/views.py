from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import Group, Permission
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from auth_app.catalogo import GRUPOS_SISTEMA, PERMISO_PANEL, PERMISOS_PROTEGIDOS
from auth_app.models import Usuario
from chat.models import Chat, ChatMessage
from feed.models import PetReport

from .forms import (
    ChatForm,
    GrupoForm,
    MensajeForm,
    PermisoForm,
    ReporteForm,
    UsuarioForm,
)


def valor(objeto, accesor):
    if callable(accesor):
        return accesor(objeto)

    actual = getattr(objeto, accesor)

    if callable(actual):
        actual = actual()

    return actual


def lista_texto(elementos):
    return ', '.join(str(elemento) for elemento in elementos) or '—'


class PanelAcceso(PermissionRequiredMixin):
    raise_exception = False
    slug = ''
    titulo = ''
    titulo_plural = ''
    columnas = []
    campos_detalle = None
    campos_busqueda = []

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        meta = self.model._meta
        usuario = self.request.user

        contexto.update(
            slug=self.slug,
            titulo=self.titulo,
            titulo_plural=self.titulo_plural,
            url_lista=reverse(f'panel:{self.slug}_list'),
            url_crear=reverse(f'panel:{self.slug}_create'),
            puede_crear=usuario.has_perm(f'{meta.app_label}.add_{meta.model_name}'),
            puede_editar=usuario.has_perm(f'{meta.app_label}.change_{meta.model_name}'),
            puede_eliminar=usuario.has_perm(f'{meta.app_label}.delete_{meta.model_name}'),
        )

        objeto = getattr(self, 'object', None)
        if objeto is not None and objeto.pk is not None:
            contexto['url_detalle'] = reverse(f'panel:{self.slug}_detail', args=[objeto.pk])
            contexto['url_editar'] = reverse(f'panel:{self.slug}_update', args=[objeto.pk])
            contexto['url_eliminar'] = reverse(f'panel:{self.slug}_delete', args=[objeto.pk])

        return contexto


class PanelList(PanelAcceso, ListView):
    template_name = 'panel/list.html'
    paginate_by = 20

    def get_queryset(self):
        consulta = super().get_queryset()
        texto = self.request.GET.get('q', '').strip()

        if texto and self.campos_busqueda:
            condicion = Q()
            for campo in self.campos_busqueda:
                condicion |= Q(**{f'{campo}__icontains': texto})
            consulta = consulta.filter(condicion)

        return consulta

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['q'] = self.request.GET.get('q', '').strip()
        contexto['encabezados'] = [etiqueta for etiqueta, _ in self.columnas]
        contexto['filas'] = [
            {
                'celdas': [valor(objeto, accesor) for _, accesor in self.columnas],
                'url_detalle': reverse(f'panel:{self.slug}_detail', args=[objeto.pk]),
                'url_editar': reverse(f'panel:{self.slug}_update', args=[objeto.pk]),
                'url_eliminar': reverse(f'panel:{self.slug}_delete', args=[objeto.pk]),
            }
            for objeto in contexto['object_list']
        ]
        return contexto


class PanelDetail(PanelAcceso, DetailView):
    template_name = 'panel/detail.html'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        campos = self.campos_detalle or self.columnas
        contexto['campos'] = [
            (etiqueta, valor(self.object, accesor)) for etiqueta, accesor in campos
        ]
        return contexto


class PanelFormulario(PanelAcceso):
    template_name = 'panel/form.html'

    def get_success_url(self):
        return reverse(f'panel:{self.slug}_list')


class PanelCreate(PanelFormulario, CreateView):
    def form_valid(self, form):
        respuesta = super().form_valid(form)
        messages.success(self.request, f'{self.titulo} creado correctamente.')
        return respuesta


class PanelUpdate(PanelFormulario, UpdateView):
    def form_valid(self, form):
        respuesta = super().form_valid(form)
        messages.success(self.request, f'{self.titulo} actualizado correctamente.')
        return respuesta


class PanelDelete(PanelAcceso, DeleteView):
    template_name = 'panel/confirm_delete.html'

    def get_success_url(self):
        return reverse(f'panel:{self.slug}_list')

    def motivo_bloqueo(self, objeto):
        return None

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['bloqueo'] = self.motivo_bloqueo(self.object)
        return contexto

    def post(self, request, *args, **kwargs):
        objeto = self.get_object()
        motivo = self.motivo_bloqueo(objeto)

        if motivo:
            messages.error(request, motivo)
            return redirect(self.get_success_url())

        respuesta = super().post(request, *args, **kwargs)
        messages.success(request, f'{self.titulo} eliminado correctamente.')
        return respuesta


class PanelIndex(PermissionRequiredMixin, TemplateView):
    permission_required = PERMISO_PANEL
    raise_exception = False
    template_name = 'panel/index.html'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        usuario = self.request.user
        modulos = [
            ('usuario', 'Usuarios', 'group', Usuario, 'auth_app.view_usuario'),
            ('grupo', 'Grupos', 'groups', Group, 'auth.view_group'),
            ('permiso', 'Permisos', 'key', Permission, 'auth.view_permission'),
            ('reporte', 'Reportes', 'pets', PetReport, 'feed.view_petreport'),
            ('chat', 'Chats', 'chat', Chat, 'chat.view_chat'),
            ('mensaje', 'Mensajes', 'forum', ChatMessage, 'chat.view_chatmessage'),
        ]
        contexto['modulos'] = [
            {
                'titulo': titulo,
                'icono': icono,
                'total': modelo.objects.count(),
                'url': reverse(f'panel:{slug}_list'),
            }
            for slug, titulo, icono, modelo, permiso in modulos
            if usuario.has_perm(permiso)
        ]
        return contexto

class UsuarioBase:
    model = Usuario
    slug = 'usuario'
    titulo = 'Usuario'
    titulo_plural = 'Usuarios'
    columnas = [
        ('Nombre', 'nombre'),
        ('Correo', 'email'),
        ('Grupos', 'nombres_grupos'),
        ('Activo', 'is_active'),
        ('Correo verificado', 'email_verificado'),
        ('Registro', 'fecha_registro'),
    ]
    campos_detalle = columnas + [
        ('Teléfono', 'telefono'),
        ('Localidad', 'localidad'),
        ('Acceso a /admin/', 'is_staff'),
        ('Superusuario', 'is_superuser'),
        ('Permisos directos', lambda u: lista_texto(u.user_permissions.all())),
        ('Último acceso', 'last_login'),
    ]
    campos_busqueda = ['nombre', 'email']

    def get_queryset(self):
        consulta = super().get_queryset()
        if not self.request.user.is_superuser:
            consulta = consulta.filter(is_superuser=False)
        return consulta


class UsuarioFormBase(UsuarioBase):
    form_class = UsuarioForm

    def get_form_kwargs(self):
        argumentos = super().get_form_kwargs()
        argumentos['actor'] = self.request.user
        return argumentos


class UsuarioList(UsuarioBase, PanelList):
    permission_required = (PERMISO_PANEL, 'auth_app.view_usuario')


class UsuarioDetail(UsuarioBase, PanelDetail):
    permission_required = (PERMISO_PANEL, 'auth_app.view_usuario')


class UsuarioCreate(UsuarioFormBase, PanelCreate):
    permission_required = (PERMISO_PANEL, 'auth_app.add_usuario')


class UsuarioUpdate(UsuarioFormBase, PanelUpdate):
    permission_required = (PERMISO_PANEL, 'auth_app.change_usuario')


class UsuarioDelete(UsuarioBase, PanelDelete):
    permission_required = (PERMISO_PANEL, 'auth_app.delete_usuario')

    def motivo_bloqueo(self, objeto):
        if objeto.pk == self.request.user.pk:
            return 'No puedes eliminar tu propia cuenta.'
        return None


class GrupoBase:
    model = Group
    slug = 'grupo'
    titulo = 'Grupo'
    titulo_plural = 'Grupos'
    columnas = [
        ('Nombre', 'name'),
        ('Permisos', lambda g: g.permissions.count()),
        ('Usuarios', lambda g: g.user_set.count()),
    ]
    campos_detalle = [
        ('Nombre', 'name'),
        ('Usuarios', lambda g: g.user_set.count()),
        ('Permisos', lambda g: lista_texto(g.permissions.select_related('content_type'))),
    ]
    campos_busqueda = ['name']


class GrupoList(GrupoBase, PanelList):
    permission_required = (PERMISO_PANEL, 'auth.view_group')


class GrupoDetail(GrupoBase, PanelDetail):
    permission_required = (PERMISO_PANEL, 'auth.view_group')


class GrupoCreate(GrupoBase, PanelCreate):
    permission_required = (PERMISO_PANEL, 'auth.add_group')
    form_class = GrupoForm


class GrupoUpdate(GrupoBase, PanelUpdate):
    permission_required = (PERMISO_PANEL, 'auth.change_group')
    form_class = GrupoForm


class GrupoDelete(GrupoBase, PanelDelete):
    permission_required = (PERMISO_PANEL, 'auth.delete_group')

    def motivo_bloqueo(self, objeto):
        if objeto.name in GRUPOS_SISTEMA:
            return 'Los grupos base del sistema no se pueden eliminar.'
        return None


class PermisoBase:
    model = Permission
    slug = 'permiso'
    titulo = 'Permiso'
    titulo_plural = 'Permisos'
    columnas = [
        ('Nombre', 'name'),
        ('Código', 'codename'),
        ('Aplicación', lambda p: p.content_type.app_label),
        ('Modelo', lambda p: p.content_type.model),
    ]
    campos_busqueda = ['name', 'codename']

    def get_queryset(self):
        return super().get_queryset().select_related('content_type')


class PermisoList(PermisoBase, PanelList):
    permission_required = (PERMISO_PANEL, 'auth.view_permission')


class PermisoDetail(PermisoBase, PanelDetail):
    permission_required = (PERMISO_PANEL, 'auth.view_permission')


class PermisoCreate(PermisoBase, PanelCreate):
    permission_required = (PERMISO_PANEL, 'auth.add_permission')
    form_class = PermisoForm


class PermisoUpdate(PermisoBase, PanelUpdate):
    permission_required = (PERMISO_PANEL, 'auth.change_permission')
    form_class = PermisoForm


class PermisoDelete(PermisoBase, PanelDelete):
    permission_required = (PERMISO_PANEL, 'auth.delete_permission')

    def motivo_bloqueo(self, objeto):
        codigo = f'{objeto.content_type.app_label}.{objeto.codename}'
        if codigo in PERMISOS_PROTEGIDOS:
            return 'Este permiso lo usa la aplicación y no se puede eliminar.'
        return None


class ReporteBase:
    model = PetReport
    slug = 'reporte'
    titulo = 'Reporte'
    titulo_plural = 'Reportes'
    columnas = [
        ('ID', 'id'),
        ('Tipo', 'get_status_display'),
        ('Especie', 'get_species_display'),
        ('Ubicación', 'last_seen_location'),
        ('Autor', 'user'),
        ('Visible', 'is_active'),
        ('Resuelto', 'is_resolved'),
        ('Fecha', 'created_at'),
    ]
    campos_detalle = columnas + [
        ('Nombre de la mascota', 'name'),
        ('Raza', 'breed'),
        ('Color', 'color'),
        ('Descripción', 'description'),
    ]
    campos_busqueda = ['description', 'last_seen_location', 'name', 'user__nombre']

    def get_queryset(self):
        return super().get_queryset().select_related('user')


class ReporteList(ReporteBase, PanelList):
    permission_required = (PERMISO_PANEL, 'feed.view_petreport')


class ReporteDetail(ReporteBase, PanelDetail):
    permission_required = (PERMISO_PANEL, 'feed.view_petreport')


class ReporteCreate(ReporteBase, PanelCreate):
    permission_required = (PERMISO_PANEL, 'feed.add_petreport')
    form_class = ReporteForm


class ReporteUpdate(ReporteBase, PanelUpdate):
    permission_required = (PERMISO_PANEL, 'feed.change_petreport')
    form_class = ReporteForm


class ReporteDelete(ReporteBase, PanelDelete):
    permission_required = (PERMISO_PANEL, 'feed.delete_petreport')


class ChatBase:
    model = Chat
    slug = 'chat'
    titulo = 'Chat'
    titulo_plural = 'Chats'
    columnas = [
        ('ID', 'id'),
        ('Reporte', 'report'),
        ('Dueño', 'owner'),
        ('Interesado', 'interested'),
        ('Actualizado', 'updated_at'),
    ]
    campos_busqueda = ['owner__nombre', 'interested__nombre', 'report__last_seen_location']

    def get_queryset(self):
        return super().get_queryset().select_related('report', 'owner', 'interested')


class ChatList(ChatBase, PanelList):
    permission_required = (PERMISO_PANEL, 'chat.view_chat')


class ChatDetail(ChatBase, PanelDetail):
    permission_required = (PERMISO_PANEL, 'chat.view_chat')


class ChatCreate(ChatBase, PanelCreate):
    permission_required = (PERMISO_PANEL, 'chat.add_chat')
    form_class = ChatForm


class ChatUpdate(ChatBase, PanelUpdate):
    permission_required = (PERMISO_PANEL, 'chat.change_chat')
    form_class = ChatForm


class ChatDelete(ChatBase, PanelDelete):
    permission_required = (PERMISO_PANEL, 'chat.delete_chat')


class MensajeBase:
    model = ChatMessage
    slug = 'mensaje'
    titulo = 'Mensaje'
    titulo_plural = 'Mensajes'
    columnas = [
        ('ID', 'id'),
        ('Chat', 'chat'),
        ('Remitente', 'sender'),
        ('Contenido', lambda m: m.content[:60]),
        ('Leído', 'is_read'),
        ('Fecha', 'created_at'),
    ]
    campos_detalle = [
        ('ID', 'id'),
        ('Chat', 'chat'),
        ('Remitente', 'sender'),
        ('Contenido', 'content'),
        ('Leído', 'is_read'),
        ('Fecha', 'created_at'),
    ]
    campos_busqueda = ['content', 'sender__nombre']

    def get_queryset(self):
        return super().get_queryset().select_related('chat', 'sender')


class MensajeList(MensajeBase, PanelList):
    permission_required = (PERMISO_PANEL, 'chat.view_chatmessage')


class MensajeDetail(MensajeBase, PanelDetail):
    permission_required = (PERMISO_PANEL, 'chat.view_chatmessage')


class MensajeCreate(MensajeBase, PanelCreate):
    permission_required = (PERMISO_PANEL, 'chat.add_chatmessage')
    form_class = MensajeForm


class MensajeUpdate(MensajeBase, PanelUpdate):
    permission_required = (PERMISO_PANEL, 'chat.change_chatmessage')
    form_class = MensajeForm


class MensajeDelete(MensajeBase, PanelDelete):
    permission_required = (PERMISO_PANEL, 'chat.delete_chatmessage')
