from rest_framework import serializers

from feed.models import PetReport

from .models import Chat, ChatMessage

MAX_CARACTERES_MENSAJE = 2000


class CrearChatSerializer(serializers.Serializer):
    report = serializers.PrimaryKeyRelatedField(
        queryset=PetReport.objects.all(),
        error_messages={
            'required': 'Indica el reporte.',
            'does_not_exist': 'El reporte no existe.',
            'incorrect_type': 'El reporte no es válido.',
        },
    )


class ChatSerializer(serializers.ModelSerializer):
    report = serializers.SerializerMethodField()
    other_user = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ['id', 'report', 'other_user', 'unread_count', 'last_message', 'created_at', 'updated_at']

    def _usuario(self):
        return self.context['request'].user

    def get_report(self, obj):
        reporte = obj.report
        request = self.context.get('request')
        imagen = None

        if reporte.image and request is not None:
            imagen = request.build_absolute_uri(reporte.image.url)

        return {
            'id': reporte.id,
            'status': reporte.status,
            'status_display': reporte.get_status_display(),
            'species_display': reporte.get_species_display(),
            'name': reporte.name or '',
            'last_seen_location': reporte.last_seen_location,
            'image': imagen,
        }

    def get_other_user(self, obj):
        otro = obj.otro_participante(self._usuario())
        return {'id': otro.id, 'nombre': otro.nombre}

    def get_unread_count(self, obj):
        return getattr(obj, 'unread_count', 0)

    def get_last_message(self, obj):
        contenido = getattr(obj, 'last_message_content', None)

        if contenido is None:
            return None

        return {
            'content': contenido,
            'created_at': obj.last_message_at,
            'is_mine': obj.last_message_sender_id == self._usuario().pk,
        }


class ChatMessageSerializer(serializers.ModelSerializer):
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = ['id', 'content', 'is_mine', 'is_read', 'created_at']
        read_only_fields = ['is_read', 'created_at']
        extra_kwargs = {
            'content': {'error_messages': {'blank': 'Escribe un mensaje.', 'required': 'Escribe un mensaje.'}},
        }

    def get_is_mine(self, obj):
        return obj.sender_id == self.context['request'].user.pk

    def validate_content(self, valor):
        valor = valor.strip()

        if not valor:
            raise serializers.ValidationError('Escribe un mensaje.')

        if len(valor) > MAX_CARACTERES_MENSAJE:
            raise serializers.ValidationError(
                f'El mensaje es demasiado largo (máximo {MAX_CARACTERES_MENSAJE} caracteres).'
            )

        return valor
