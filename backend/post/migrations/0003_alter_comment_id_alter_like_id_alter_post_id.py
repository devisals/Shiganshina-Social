# Generated by Django 4.2 on 2024-03-08 18:47

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("post", "0002_post_count"),
    ]

    operations = [
        migrations.AlterField(
            model_name="comment",
            name="id",
            field=models.CharField(
                default=uuid.uuid4,
                editable=False,
                help_text="the ID of the user",
                max_length=250,
                primary_key=True,
                serialize=False,
                unique=True,
            ),
        ),
        migrations.AlterField(
            model_name="like",
            name="id",
            field=models.CharField(
                default=uuid.uuid4,
                editable=False,
                help_text="the ID of the user",
                max_length=250,
                primary_key=True,
                serialize=False,
                unique=True,
            ),
        ),
        migrations.AlterField(
            model_name="post",
            name="id",
            field=models.CharField(
                default=uuid.uuid4,
                editable=False,
                help_text="the ID of the user",
                max_length=250,
                primary_key=True,
                serialize=False,
                unique=True,
            ),
        ),
    ]
