# Generated by Django 4.2 on 2024-03-23 04:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("inbox", "0008_alter_followrequest_object"),
    ]

    operations = [
        migrations.CreateModel(
            name="InboxPost",
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
                    "post_id",
                    models.URLField(editable=False, help_text="the ID of the post"),
                ),
            ],
        ),
        migrations.AlterField(
            model_name="inbox",
            name="post",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="inbox.inboxpost",
            ),
        ),
    ]
