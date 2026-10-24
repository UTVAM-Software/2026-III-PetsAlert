from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Count, IntegerField, OuterRef, Q, Subquery, Value
from django.db.models.functions import Coalesce
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from auth_app.catalogo import PERMISO_CHAT
from auth_app.permissions import requiere_permiso
from feed.permisos import puede_ver

from .models import Chat, ChatMessage
from .serializers import (
    ChatMessageSerializer,
    ChatSerializer,
    CrearChatSerializer,
)


# ==========================================
# 1. Pantallas HTML (los datos los carga el JS desde la API)
# ==========================================

@login_required
@permission_required(PERMISO_CHAT, raise_exception=True)
@ensure_csrf_cookie
def chat_list_screen(request):
    return render(request, 'chat/chat_list_screen.html')


@login_required
@permission_required(PERMISO_CHAT, raise_exception=True)
@ensure_csrf_cookie
def chat_room_screen(request, chat_id):
    chat = get_object_or_404(
        Chat.objects.select_related('report', 'owner', 'interested'),
        pk=chat_id,
    )

    if not chat.tiene_participante(request.user):
        raise Http404

    return render(
        request,
        'chat/chat_room_screen.html',
        {'chat': chat, 'otro_usuario': chat.otro_participante(request.user)},
    )


# ==========================================
# 2. API de chats y mensajes
# ==========================================

class ChatViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    GET  /chat/api/chats/                  mis chats (con último mensaje y no leídos)
    POST /chat/api/chats/                  abre (o recupera) el chat de un reporte: {"report": <id>}
    GET  /chat/api/chats/<id>/             un chat
    GET  /chat/api/chats/<id>/messages/    mensajes (opcional ?after=<id> para pedir solo los nuevos)
    POST /chat/api/chats/<id>/messages/    enviar un mensaje: {"content": "..."}
    """

    serializer_class = ChatSerializer
    permission_classes = [requiere_permiso(PERMISO_CHAT)]
    pagination_class = None

    def get_queryset(self):
        usuario = self.request.user

        ultimo = ChatMessage.objects.filter(chat=OuterRef('pk')).order_by('-created_at', '-id')

        no_leidos = (
            ChatMessage.objects
            .filter(chat=OuterRef('pk'), is_read=False)
            .exclude(sender=usuario)
            .order_by()
            .values('chat')
            .annotate(total=Count('pk'))
            .values('total')
        )

        return (
            Chat.objects
            .filter(Q(owner=usuario) | Q(interested=usuario))
            .select_related('report', 'owner', 'interested')
            .annotate(
                unread_count=Coalesce(Subquery(no_leidos, output_field=IntegerField()), Value(0)),
                last_message_content=Subquery(ultimo.values('content')[:1]),
                last_message_at=Subquery(ultimo.values('created_at')[:1]),
                last_message_sender_id=Subquery(ultimo.values('sender_id')[:1]),
            )
        )

    def create(self, request, *args, **kwargs):
        entrada = CrearChatSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        reporte = entrada.validated_data['report']
        usuario = request.user

        if not puede_ver(usuario, reporte):
            raise serializers.ValidationError({'report': 'El reporte no existe.'})

        if reporte.user_id == usuario.pk:
            raise serializers.ValidationError({'report': 'No puedes iniciar un chat contigo mismo.'})

        chat, creado = Chat.objects.get_or_create(
            report=reporte,
            interested=usuario,
            defaults={'owner_id': reporte.user_id},
        )

        chat = self.get_queryset().get(pk=chat.pk)
        datos = self.get_serializer(chat).data

        return Response(datos, status=201 if creado else 200)

    @action(detail=True, methods=['get', 'post'], url_path='messages')
    def messages(self, request, pk=None):
        # get_object() solo encuentra chats donde participa el usuario; en otro caso responde 404.
        chat = self.get_object()
        usuario = request.user
        contexto = {'request': request}

        if request.method == 'GET':
            mensajes = chat.messages.all()

            despues_de = request.query_params.get('after', '')
            if despues_de.isdigit():
                mensajes = mensajes.filter(id__gt=int(despues_de))

            mensajes = list(mensajes)

            # Quien abre la conversación marca como leídos los mensajes de la otra persona.
            por_marcar = [m.id for m in mensajes if m.sender_id != usuario.pk and not m.is_read]
            if por_marcar:
                ChatMessage.objects.filter(id__in=por_marcar).update(is_read=True)

            return Response(ChatMessageSerializer(mensajes, many=True, context=contexto).data)

        serializer = ChatMessageSerializer(data=request.data, context=contexto)
        serializer.is_valid(raise_exception=True)
        mensaje = serializer.save(chat=chat, sender=usuario)

        # Sube el chat al inicio de la lista (updated_at se actualiza solo).
        chat.save(update_fields=['updated_at'])

        return Response(ChatMessageSerializer(mensaje, context=contexto).data, status=201)
