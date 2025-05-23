# Generated by Django 5.1.4 on 2025-01-11 17:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fauna', '0002_remove_fauna_description_2'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fauna',
            name='title',
            field=models.CharField(help_text='Dont more than 255 characters', max_length=255),
        ),
        migrations.AlterField(
            model_name='imagefauna',
            name='image',
            field=models.ImageField(help_text='Image size max 10MB and max resolution 2000x2000px auto compress', upload_to='fauna/'),
        ),
    ]
