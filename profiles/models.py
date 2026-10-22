from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True, null=True, help_text="Breve biografía del usuario")
    phone_number = models.CharField(max_length=20, blank=True, null=True, help_text="Número de contacto")
    
    # URL de Firebase Storage para la foto de perfil en lugar de Base64
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"