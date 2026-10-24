from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from auth_app.catalogo import PERMISO_CREAR_REPORTE

from .models import PetReport
from .permisos import puede_editar, puede_eliminar, puede_ver
from .serializers import PetReportSerializer


# ==========================================
# 1. Pantallas HTML (los datos los carga el JS desde la API)
# ==========================================

@login_required
def feed_screen(request):
    return render(request, 'feed/feed_screen.html')


@login_required
@ensure_csrf_cookie
def add_report_screen(request, pk=None):
    if pk is None:
        if not request.user.has_perm(PERMISO_CREAR_REPORTE):
            raise PermissionDenied
    else:
        reporte = get_object_or_404(PetReport, pk=pk)
        if not puede_editar(request.user, reporte):
            raise PermissionDenied

    return render(request, 'feed/add_report_screen.html', {'reporte_id': pk})


@login_required
@ensure_csrf_cookie
def pet_detail_screen(request, pk):
    reporte = get_object_or_404(PetReport, pk=pk)

    if not puede_ver(request.user, reporte):
        raise Http404

    return render(request, 'feed/pet_detail_screen.html', {'reporte_id': pk})


# ==========================================
# 2. API de reportes
# ==========================================

class PermisosReporte(BasePermission):
    """
    - Todas las acciones exigen sesión iniciada.
    - Crear: permiso feed.add_petreport.
    - Editar o eliminar: el dueño (con change/delete_petreport) o quien tenga feed.moderar_reportes.
    """

    message = 'No tienes permiso para realizar esta acción.'

    def has_permission(self, request, view):
        usuario = request.user
        if not (usuario and usuario.is_authenticated):
            return False

        if view.action == 'create':
            return usuario.has_perm(PERMISO_CREAR_REPORTE)

        return True

    def has_object_permission(self, request, view, obj):
        usuario = request.user

        if view.action == 'retrieve':
            if not puede_ver(usuario, obj):
                raise Http404
            return True

        if view.action in ('update', 'partial_update'):
            return puede_editar(usuario, obj)

        if view.action == 'destroy':
            return puede_eliminar(usuario, obj)

        return False


class PaginacionReportes(PageNumberPagination):
    page_size = 24
    page_size_query_param = 'page_size'
    max_page_size = 100


class PetReportViewSet(viewsets.ModelViewSet):
    serializer_class = PetReportSerializer
    permission_classes = [PermisosReporte]
    pagination_class = PaginacionReportes
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    # La edición siempre es parcial (PATCH).
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        reportes = PetReport.objects.select_related('user')

        if self.action != 'list':
            return reportes

        # El feed solo muestra reportes visibles y sin resolver.
        reportes = reportes.filter(is_active=True, is_resolved=False)

        parametros = self.request.query_params

        especie = parametros.get('species', '').strip().upper()
        if especie:
            reportes = reportes.filter(species=especie)

        tipo = parametros.get('status', '').strip().upper()
        if tipo:
            reportes = reportes.filter(status=tipo)

        texto = parametros.get('search', '').strip()
        if texto:
            reportes = reportes.filter(
                Q(description__icontains=texto)
                | Q(last_seen_location__icontains=texto)
                | Q(name__icontains=texto)
                | Q(breed__icontains=texto)
                | Q(color__icontains=texto)
            )

        return reportes

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def mine(self, request):
        """Todos los reportes del usuario (también los resueltos), del más reciente al más antiguo."""
        reportes = PetReport.objects.filter(user=request.user).select_related('user')
        serializer = self.get_serializer(reportes, many=True)
        return Response(serializer.data)
