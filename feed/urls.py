from django.urls import path
from . import views

urlpatterns = [
    # Tus rutas web
    path('', views.feed_screen, name='feed_screen'),
    path('add/', views.add_report_screen, name='add_report_screen'),
    path('add/<str:pk>/', views.add_report_screen, name='edit_report_screen'),
    path('<str:pk>/', views.pet_detail_screen, name='pet_detail_screen'),
    
    # Tu nueva ruta para conectar el guardado con la base de datos
    path('api/reports/', views.PetReportListCreateView.as_view(), name='api_report_list_create'),
]