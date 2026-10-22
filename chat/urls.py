from django.urls import path
from . import views

urlpatterns = [
    # Tus rutas web
    path('', views.chat_list_screen, name='chat_list_screen'),
    path('room/<str:receiver_id>/', views.chat_room_screen, name='chat_room_screen'),
    
    # Tu nueva ruta para conectar el chat con el frontend/Flutter
    path('api/messages/', views.MessageListCreateView.as_view(), name='api_messages'),
]