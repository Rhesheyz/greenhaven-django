# Generated by Django 5.1.4 on 2025-02-19 02:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hotel', '0002_alter_detailroom_featured_room_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='hotel',
            name='slug',
            field=models.SlugField(default=0, unique=True),
            preserve_default=False,
        ),
    ]
