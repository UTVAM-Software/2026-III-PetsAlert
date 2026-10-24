from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('feed', '0003_petreport_breed_petreport_color_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='petreport',
            options={'ordering': ['-created_at'], 'permissions': [('moderar_reportes', 'Puede editar, ocultar y eliminar cualquier reporte')]},
        ),
    ]
