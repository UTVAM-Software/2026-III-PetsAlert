from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register('chats', views.ChatViewSet, basename='chat')

urlpatterns = [

    path('', views.chat_list_screen, name='chat_list_screen'),
    path('room/<int:chat_id>/', views.chat_room_screen, name='chat_room_screen'),

    path('api/', include(router.urls)),
]
