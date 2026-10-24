from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0003_chat_chatmessage_delete_message_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='chat',
            options={'ordering': ['-updated_at'], 'permissions': [('usar_chat', 'Puede iniciar conversaciones y enviar mensajes')]},
        ),
    ]
