import re

from rest_framework import serializers

from auth_app.models import Usuario

PATRON_TELEFONO = re.compile(r'^[0-9+()\-\s]{0,30}$')


class PerfilSerializer(serializers.ModelSerializer):
    rol = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ['id', 'nombre', 'email', 'telefono', 'localidad', 'foto', 'rol', 'fecha_registro']
        # Solo se pueden editar el nombre, el teléfono y la localidad.
        read_only_fields = ['email', 'foto', 'fecha_registro']
        extra_kwargs = {
            'nombre': {'error_messages': {'blank': 'Ingresa tu nombre.', 'required': 'Ingresa tu nombre.'}},
            'telefono': {'required': False, 'allow_blank': True},
            'localidad': {'required': False, 'allow_blank': True},
        }

    def get_rol(self, obj):
        grupo = obj.groups.order_by('name').first()
        return grupo.name if grupo else None

    def validate_telefono(self, valor):
        valor = valor.strip()

        if not PATRON_TELEFONO.match(valor):
            raise serializers.ValidationError('Ingresa un teléfono válido.')

        return valor
