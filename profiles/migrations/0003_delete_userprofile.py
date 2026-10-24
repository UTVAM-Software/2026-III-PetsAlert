
from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0002_remove_userprofile_avatar_url_userprofile_avatar'),
    ]

    operations = [
        migrations.DeleteModel(
            name='UserProfile',
        ),
    ]
