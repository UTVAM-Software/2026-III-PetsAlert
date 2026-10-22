from django.db import models
from django.contrib.auth.models import User

class PetReport(models.Model):
    STATUS_CHOICES = [
        ('PERDIDO', 'Mascota Perdida'),
        ('ENCONTRADO', 'Mascota Encontrada'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PERDIDO')
    name = models.CharField(max_length=100, blank=True, null=True, help_text="Nombre (solo si lo conoce)")
    description = models.TextField(help_text="Descripción detallada del reporte")
    last_seen_location = models.CharField(max_length=255)
    
    # -------------------------------------------------------------
    # NUEVO: URL de Firebase en lugar de Base64
    # -------------------------------------------------------------
    image = models.ImageField(upload_to='pets_photos/', blank=True, null=True, help_text="Foto de la mascota")
    
    # -------------------------------------------------------------
    # CAMPOS DE IA (Para integración con Gemini)
    # -------------------------------------------------------------
    ai_species = models.CharField(max_length=50, blank=True, null=True)
    ai_breed = models.CharField(max_length=100, blank=True, null=True)
    ai_color = models.CharField(max_length=50, blank=True, null=True)
    ai_tags = models.JSONField(blank=True, null=True, help_text="Etiquetas generadas por Gemini")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        especie = self.ai_species if self.ai_species else "Mascota"
        return f"[{self.status}] {especie} - {self.last_seen_location}"