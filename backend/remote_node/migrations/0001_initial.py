# Generated by Django 4.2 on 2024-03-20 21:31

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="RemoteNode",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "nodeName",
                    models.CharField(
                        help_text="the name of the remote node",
                        max_length=250,
                        unique=True,
                    ),
                ),
                (
                    "displayName",
                    models.CharField(
                        blank=True,
                        help_text="the author's display name",
                        max_length=250,
                        null=True,
                        unique=True,
                    ),
                ),
                (
                    "url",
                    models.URLField(
                        help_text="url to the author's profile", max_length=250
                    ),
                ),
                (
                    "password",
                    models.CharField(
                        blank=True,
                        help_text="password to the remote node",
                        max_length=250,
                        null=True,
                    ),
                ),
            ],
        ),
    ]
