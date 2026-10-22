from django.shortcuts import render
from rest_framework import generics, permissions
from .models import UserProfile
from .serializers import UserProfileSerializer

# ==========================================
# 1. TUS VISTAS ORIGINALES (Pantallas HTML)
# ==========================================
def profile_screen(request):
    return render(request, 'profiles/profile_screen.html')

def my_reports_screen(request):
    return render(request, 'profiles/my_reports_screen.html')

def privacy_screen(request):
    return render(request, 'profiles/privacy_screen.html')

# ==========================================
# 2. NUEVA VISTA API (Ver / Editar Perfil)
# ==========================================
class UserProfileDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Obtiene o crea automáticamente el perfil del usuario autenticado
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile