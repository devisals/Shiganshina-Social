# Generated by Django 4.2 on 2024-03-18 05:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("post", "0006_remove_like_post_like_author__139e9e_idx_and_more"),
        ("inbox", "0005_alter_inbox_like"),
    ]

    operations = [
        migrations.AlterField(
            model_name="inbox",
            name="like",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="post.like",
            ),
        ),
        migrations.DeleteModel(
            name="InboxLike",
        ),
    ]
