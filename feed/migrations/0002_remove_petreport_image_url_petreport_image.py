
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('feed', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='petreport',
            name='image_url',
        ),
        migrations.AddField(
            model_name='petreport',
            name='image',
            field=models.ImageField(blank=True, help_text='Foto de la mascota', null=True, upload_to='pets_photos/'),
        ),
    ]
