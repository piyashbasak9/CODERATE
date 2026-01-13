from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('problems', '0004_userproblem_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='problem',
            name='codeforces_rating',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
