# Generated by Django 4.2 on 2024-03-25 13:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restapi', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='type',
            field=models.CharField(default='author', editable=False, max_length=250),
        ),
    ]
