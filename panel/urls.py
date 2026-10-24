from django.urls import path

from . import views

app_name = 'panel'

def rutas(slug, prefijo, lista, detalle, crear, editar, eliminar):
    return [
        path(f'{prefijo}/', lista.as_view(), name=f'{slug}_list'),
        path(f'{prefijo}/nuevo/', crear.as_view(), name=f'{slug}_create'),
        path(f'{prefijo}/<int:pk>/', detalle.as_view(), name=f'{slug}_detail'),
        path(f'{prefijo}/<int:pk>/editar/', editar.as_view(), name=f'{slug}_update'),
        path(f'{prefijo}/<int:pk>/eliminar/', eliminar.as_view(), name=f'{slug}_delete'),
    ]

urlpatterns = [
    path('', views.PanelIndex.as_view(), name='index'),
    *rutas('usuario', 'usuarios', views.UsuarioList, views.UsuarioDetail, views.UsuarioCreate, views.UsuarioUpdate, views.UsuarioDelete),
    *rutas('grupo', 'grupos', views.GrupoList, views.GrupoDetail, views.GrupoCreate, views.GrupoUpdate, views.GrupoDelete),
    *rutas('permiso', 'permisos', views.PermisoList, views.PermisoDetail, views.PermisoCreate, views.PermisoUpdate, views.PermisoDelete),
    *rutas('reporte', 'reportes', views.ReporteList, views.ReporteDetail, views.ReporteCreate, views.ReporteUpdate, views.ReporteDelete),
    *rutas('chat', 'chats', views.ChatList, views.ChatDetail, views.ChatCreate, views.ChatUpdate, views.ChatDelete),
    *rutas('mensaje', 'mensajes', views.MensajeList, views.MensajeDetail, views.MensajeCreate, views.MensajeUpdate, views.MensajeDelete),
]
