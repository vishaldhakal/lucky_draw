# Generated by Django 5.1 on 2024-09-13 07:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('offers', '0002_luckydrawsystem_hero_subtitle_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='luckydrawsystem',
            name='uuid_key',
            field=models.CharField(default='', max_length=255, unique=True),
        ),
    ]
