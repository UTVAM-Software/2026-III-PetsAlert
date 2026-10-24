from django.conf import settings
from django.db import models
from django.db.models import F, Q


class Chat(models.Model):
    """
    Conversación entre el dueño de un reporte y un usuario interesado en él.
    Hay un solo chat por cada pareja (reporte, interesado).
    """

    report = models.ForeignKey('feed.PetReport', on_delete=models.CASCADE, related_name='chats')
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chats_como_dueno'
    )
    interested = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chats_como_interesado'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        permissions = [
            ('usar_chat', 'Puede iniciar conversaciones y enviar mensajes'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['report', 'interested'],
                name='chat_unico_por_reporte_e_interesado',
            ),
            models.CheckConstraint(
                condition=~Q(owner_id=F('interested_id')),
                name='chat_dueno_distinto_de_interesado',
            ),
        ]

    def __str__(self):
        return f'Chat #{self.pk} del reporte {self.report_id}'

    def tiene_participante(self, usuario):
        return usuario.pk in (self.owner_id, self.interested_id)

    def otro_participante(self, usuario):
        return self.interested if usuario.pk == self.owner_id else self.owner


class ChatMessage(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_messages'
    )
    content = models.TextField(help_text='Texto del mensaje')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'id']
        indexes = [models.Index(fields=['chat', 'id'])]

    def __str__(self):
        return f'{self.sender.nombre} en chat #{self.chat_id} - {self.created_at:%H:%M}'
