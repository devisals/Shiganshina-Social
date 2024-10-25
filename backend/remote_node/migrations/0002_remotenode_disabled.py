# Generated by Django 4.2 on 2024-03-20 21:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("remote_node", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="remotenode",
            name="disabled",
            field=models.BooleanField(
                default=True, help_text="whether the remote node is disabled"
            ),
        ),
    ]
