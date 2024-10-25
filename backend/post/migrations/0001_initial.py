# Generated by Django 4.2 on 2024-02-22 18:53

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Post",
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
                ("title", models.CharField(max_length=250)),
                (
                    "source",
                    models.URLField(
                        help_text="The original source of the post", max_length=250
                    ),
                ),
                (
                    "origin",
                    models.URLField(help_text="The origin of the post", max_length=250),
                ),
                ("description", models.CharField(max_length=500)),
                ("content", models.TextField()),
                (
                    "contentType",
                    models.CharField(
                        choices=[
                            ("text/plain", "Plain Text"),
                            ("text/markdown", "Markdown"),
                            ("application/base64", "Base64 Application"),
                            ("image/png;base64", "Base64 PNG Image"),
                            ("image/jpeg;base64", "Base64 JPEG Image"),
                            ("image/gif;base64", "Base64 GIF Image"),
                        ],
                        default="text/plain",
                        help_text="Content type of the post",
                        max_length=250,
                    ),
                ),
                ("published", models.DateTimeField(auto_now_add=True)),
                (
                    "visibility",
                    models.CharField(
                        choices=[
                            ("PUBLIC", "Public"),
                            ("FRIENDS", "Friends"),
                            ("UNLISTED", "Unlisted"),
                        ],
                        default="PUBLIC",
                        help_text="Visibility of the post",
                        max_length=250,
                    ),
                ),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Like",
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
                ("published", models.DateTimeField(auto_now_add=True)),
                (
                    "summary",
                    models.CharField(
                        help_text="Short description of the like (e.g. user likes this post)",
                        max_length=250,
                    ),
                ),
                (
                    "author",
                    models.ForeignKey(
                        help_text="The user who liked the post",
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "post",
                    models.ForeignKey(
                        help_text="The post being liked",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="likes",
                        to="post.post",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Comment",
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
                ("comment", models.TextField(help_text="The content of the comment")),
                ("published", models.DateTimeField(auto_now_add=True)),
                (
                    "contentType",
                    models.CharField(
                        choices=[
                            ("text/plain", "Plain Text"),
                            ("text/markdown", "Markdown"),
                            ("application/base64", "Base64 Application"),
                            ("image/png;base64", "Base64 PNG Image"),
                            ("image/jpeg;base64", "Base64 JPEG Image"),
                            ("image/gif;base64", "Base64 GIF Image"),
                        ],
                        default="text/plain",
                        help_text="Content type of the comment",
                        max_length=250,
                    ),
                ),
                (
                    "author",
                    models.ForeignKey(
                        help_text="The user who made the comment",
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "post",
                    models.ForeignKey(
                        help_text="The post being commented on",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="comments",
                        to="post.post",
                    ),
                ),
            ],
        ),
    ]
