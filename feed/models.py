from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver


class PetReport(models.Model):
    STATUS_PERDIDO = 'PERDIDO'
    STATUS_ENCONTRADO = 'ENCONTRADO'
    STATUS_CHOICES = [
        (STATUS_PERDIDO, 'Mascota Perdida'),
        (STATUS_ENCONTRADO, 'Mascota Encontrada'),
    ]

    SPECIES_CHOICES = [
        ('PERRO', 'Perro'),
        ('GATO', 'Gato'),
        ('AVE', 'Ave'),
        ('CONEJO', 'Conejo'),
        ('OTRO', 'Otro'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports')

    # Tipo de reporte: la mascota se busca (perdida) o ya fue encontrada.
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=STATUS_PERDIDO)

    species = models.CharField(max_length=10, choices=SPECIES_CHOICES, default='OTRO')
    name = models.CharField(max_length=100, blank=True, null=True, help_text="Nombre (solo si lo conoce)")
    breed = models.CharField(max_length=100, blank=True, default='', help_text="Raza (si se conoce)")
    color = models.CharField(max_length=50, blank=True, default='', help_text="Color predominante")
    description = models.TextField(help_text="Descripción detallada del reporte")
    last_seen_location = models.CharField(max_length=255)

    # Las fotos se guardan en MEDIA_ROOT/pets_photos/
    image = models.ImageField(upload_to='pets_photos/', blank=True, null=True, help_text="Foto de la mascota")

    # -------------------------------------------------------------
    # CAMPOS DE IA (para la integración con Gemini, aún sin usar)
    # -------------------------------------------------------------
    ai_species = models.CharField(max_length=50, blank=True, null=True)
    ai_breed = models.CharField(max_length=100, blank=True, null=True)
    ai_color = models.CharField(max_length=50, blank=True, null=True)
    ai_tags = models.JSONField(blank=True, null=True, help_text="Etiquetas generadas por Gemini")

    # is_active: el reporte es visible en la app (un moderador puede ocultarlo).
    # is_resolved: el dueño ya resolvió el caso (la mascota apareció o volvió a casa).
    is_active = models.BooleanField(default=True)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        permissions = [
            ('moderar_reportes', 'Puede editar, ocultar y eliminar cualquier reporte'),
        ]

    def __str__(self):
        return f"[{self.status}] {self.get_species_display()} - {self.last_seen_location}"


# --- Limpieza de fotos ---------------------------------------------------

@receiver(post_delete, sender=PetReport)
def borrar_foto_al_eliminar(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)


@receiver(pre_save, sender=PetReport)
def borrar_foto_anterior_al_reemplazar(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        anterior = sender.objects.get(pk=instance.pk).image
    except sender.DoesNotExist:
        return

    if anterior and anterior != instance.image:
        anterior.delete(save=False)
