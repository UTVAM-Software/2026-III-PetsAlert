from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_list_screen, name='chat_list_screen'),
    path('room/<str:receiver_id>/', views.chat_room_screen, name='chat_room_screen'),
]
