# Generated by Django 5.1.4 on 2025-01-25 17:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('address', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='address',
            name='phone_number',
            field=models.CharField(max_length=15),
        ),
    ]
