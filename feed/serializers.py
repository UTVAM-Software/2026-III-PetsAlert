from rest_framework import serializers
from .models import PetReport

class PetReportSerializer(serializers.ModelSerializer):
    class Meta:
        model =PetReport
        # Exponemos todos los campos, incluyendo la nueva image_url y las etiquetas de IA
        fields = ['id', 'user', 'status', 'name', 'description', 'last_seen_location', 
                  'image', 'ai_species', 'ai_breed', 'ai_color', 'ai_tags', 
                  'is_active', 'created_at', 'updated_at']
        read_only_fields = ['user', 'ai_species', 'ai_breed', 'ai_color', 'ai_tags']