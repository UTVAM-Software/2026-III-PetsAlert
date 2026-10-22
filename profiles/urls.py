from django.urls import path
from . import views

urlpatterns = [
    # Tus rutas web
    path('', views.profile_screen, name='profile_screen'),
    path('reports/', views.my_reports_screen, name='my_reports_screen'),
    path('privacy/', views.privacy_screen, name='privacy_screen'),
    
    # Tu nueva ruta API para consultar o actualizar el perfil
    path('api/me/', views.UserProfileDetailView.as_view(), name='api_user_profile'),
]