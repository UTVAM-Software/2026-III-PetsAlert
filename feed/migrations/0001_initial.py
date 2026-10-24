
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PetReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('PERDIDO', 'Mascota Perdida'), ('ENCONTRADO', 'Mascota Encontrada')], default='PERDIDO', max_length=15)),
                ('name', models.CharField(blank=True, help_text='Nombre (solo si lo conoce)', max_length=100, null=True)),
                ('description', models.TextField(help_text='Descripción detallada del reporte')),
                ('last_seen_location', models.CharField(max_length=255)),
                ('image_url', models.URLField(blank=True, help_text='Enlace público de Firebase Storage', max_length=500, null=True)),
                ('ai_species', models.CharField(blank=True, max_length=50, null=True)),
                ('ai_breed', models.CharField(blank=True, max_length=100, null=True)),
                ('ai_color', models.CharField(blank=True, max_length=50, null=True)),
                ('ai_tags', models.JSONField(blank=True, help_text='Etiquetas generadas por Gemini', null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reports', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
