from django.shortcuts import render
from rest_framework import generics, permissions
from .models import PetReport
from .serializers import PetReportSerializer

# ==========================================
# 1. TUS VISTAS ORIGINALES (Pantallas HTML)
# ==========================================
def feed_screen(request):
    return render(request, 'feed/feed_screen.html')

def add_report_screen(request, pk=None):
    return render(
        request,
        'feed/add_report_screen.html',
        {'reporte_id': pk}
    )

def pet_detail_screen(request, pk):
    return render(
        request,
        'feed/pet_detail_screen.html',
        {'reporte_id': pk}
    )

# ==========================================
# 2. NUEVA VISTA API (Recibe la URL de Firebase)
# ==========================================
class PetReportListCreateView(generics.ListCreateAPIView):
    queryset = PetReport.objects.all()
    serializer_class = PetReportSerializer
    # Permite ver sin cuenta, pero exige cuenta para publicar
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        # Guarda el reporte asignándolo al usuario que está enviando la petición
        serializer.save(user=self.request.user)