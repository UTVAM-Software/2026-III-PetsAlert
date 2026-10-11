from django.urls import path
from . import views

urlpatterns = [
    path('', views.profile_screen, name='profile_screen'),
    path('reports/', views.my_reports_screen, name='my_reports_screen'),
    path('privacy/', views.privacy_screen, name='privacy_screen'),
]
