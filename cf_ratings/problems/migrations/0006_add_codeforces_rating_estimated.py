from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0005_add_codeforces_rating'),
    ]

    operations = [
        migrations.AddField(
            model_name='problem',
            name='codeforces_rating_estimated',
            field=models.BooleanField(default=False),
        ),
    ]
