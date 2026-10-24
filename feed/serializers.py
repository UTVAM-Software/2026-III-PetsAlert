from rest_framework import serializers

from .models import PetReport
from .permisos import puede_editar, puede_eliminar

MAX_BYTES_IMAGEN = 5 * 1024 * 1024

class PetReportSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    species_display = serializers.CharField(source='get_species_display', read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    user_name = serializers.CharField(source='user.nombre', read_only=True)
    is_mine = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()

    class Meta:
        model = PetReport
        fields = [
            'id', 'status', 'status_display', 'species', 'species_display',
            'name', 'breed', 'color', 'description', 'last_seen_location', 'image',
            'ai_species', 'ai_breed', 'ai_color', 'ai_tags',
            'is_active', 'is_resolved', 'created_at', 'updated_at',
            'user_id', 'user_name', 'is_mine', 'can_edit', 'can_delete',
        ]
        read_only_fields = [
            'ai_species', 'ai_breed', 'ai_color', 'ai_tags',
            'is_active', 'created_at', 'updated_at',
        ]
        extra_kwargs = {
            'description': {'error_messages': {'blank': 'Requerido', 'required': 'Requerido'}},
            'last_seen_location': {'error_messages': {'blank': 'Requerido', 'required': 'Requerido'}},
            'name': {'required': False, 'allow_blank': True, 'allow_null': True},
            'breed': {'required': False, 'allow_blank': True},
            'color': {'required': False, 'allow_blank': True},
        }

    def _usuario(self):
        request = self.context.get('request')
        return getattr(request, 'user', None)

    def get_is_mine(self, obj):
        usuario = self._usuario()
        return bool(usuario and usuario.is_authenticated and obj.user_id == usuario.pk)

    def get_can_edit(self, obj):
        usuario = self._usuario()
        return bool(usuario and puede_editar(usuario, obj))

    def get_can_delete(self, obj):
        usuario = self._usuario()
        return bool(usuario and puede_eliminar(usuario, obj))

    def validate_image(self, imagen):
        if imagen is not None and imagen.size > MAX_BYTES_IMAGEN:
            raise serializers.ValidationError('La imagen pesa más de 5 MB.')
        return imagen

    def validate(self, attrs):
        if self.instance is None and not attrs.get('image'):
            raise serializers.ValidationError(
                {'image': 'Por favor, selecciona una foto de la mascota.'}
            )
        return attrs
