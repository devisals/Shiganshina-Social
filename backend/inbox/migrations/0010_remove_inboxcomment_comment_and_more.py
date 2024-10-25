# Generated by Django 4.2 on 2024-03-25 17:55

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inbox", "0009_inboxpost_alter_inbox_post"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="inboxcomment",
            name="comment",
        ),
        migrations.RemoveField(
            model_name="inboxcomment",
            name="contentType",
        ),
        migrations.RemoveField(
            model_name="inboxcomment",
            name="published",
        ),
        migrations.AddField(
            model_name="inboxcomment",
            name="commentUrl",
            field=models.URLField(
                default=1, editable=False, help_text="the URL ID of the comment"
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="inboxcomment",
            name="author",
            field=models.URLField(help_text="The user who made the comment"),
        ),
        migrations.AlterField(
            model_name="inboxcomment",
            name="id",
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
    ]
