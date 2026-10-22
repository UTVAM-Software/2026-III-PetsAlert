from rest_framework import serializers
from .models import Message

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'sender', 'receiver', 'content', 'image', 'is_read', 'timestamp']
        # El remitente y la hora se llenan solos, no se piden al frontend
        read_only_fields = ['sender', 'timestamp']