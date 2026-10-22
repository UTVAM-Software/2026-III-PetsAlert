from django.shortcuts import render
from rest_framework import generics, permissions
from .models import Message
from .serializers import MessageSerializer

# ==========================================
# 1. TUS VISTAS ORIGINALES (Pantallas HTML)
# ==========================================
def chat_list_screen(request):
    return render(request, 'chat/chat_list_screen.html')

def chat_room_screen(request, receiver_id):
    return render(
        request,
        'chat/chat_room_screen.html',
        {'receiver_id': receiver_id},
    )

# ==========================================
# 2. NUEVAS VISTAS API (Para enviar/recibir)
# ==========================================
class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Solo devuelve los mensajes donde el usuario logueado participa
        user = self.request.user
        return Message.objects.filter(sender=user) | Message.objects.filter(receiver=user)

    def perform_create(self, serializer):
        # Asigna automáticamente al usuario logueado como remitente
        serializer.save(sender=self.request.user)