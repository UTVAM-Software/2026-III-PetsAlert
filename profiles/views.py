from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import generics, permissions

from .serializers import PerfilSerializer

@login_required
@ensure_csrf_cookie
def profile_screen(request):
    return render(request, 'profiles/profile_screen.html')

@login_required
@ensure_csrf_cookie
def my_reports_screen(request):
    return render(request, 'profiles/my_reports_screen.html')

@login_required
def privacy_screen(request):
    return render(request, 'profiles/privacy_screen.html')

class PerfilView(generics.RetrieveUpdateAPIView):
    """GET /profile/api/me/ y PATCH /profile/api/me/ (nombre, teléfono y localidad)."""

    serializer_class = PerfilSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_object(self):
        return self.request.user
