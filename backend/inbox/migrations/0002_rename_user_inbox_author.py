# Generated by Django 4.2 on 2024-03-07 18:38

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("inbox", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="inbox",
            old_name="user",
            new_name="author",
        ),
    ]
