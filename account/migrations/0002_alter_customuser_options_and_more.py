# Generated by Django 5.1 on 2024-08-31 11:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='customuser',
            options={'permissions': [('can_manage_users', 'Can manage users'), ('can_manage_organization', 'Can manage organization')]},
        ),
        migrations.AlterField(
            model_name='customuser',
            name='organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='users', to='account.organization'),
        ),
    ]
