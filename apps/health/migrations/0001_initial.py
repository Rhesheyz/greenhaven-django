# Generated by Django 5.1.4 on 2024-12-30 07:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('destinations', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Health',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('slug', models.SlugField(unique=True)),
                ('description', models.TextField()),
                ('description_2', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('destinations', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='health', to='destinations.destinations')),
            ],
        ),
        migrations.CreateModel(
            name='ImageHealth',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='health/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('health', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='health.health')),
            ],
        ),
    ]
