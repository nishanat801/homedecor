# Generated by Django 5.1.4 on 2025-01-26 10:11

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0045_alter_userdetails_estimated_delivery'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userdetails',
            name='estimated_delivery',
            field=models.DateField(default=datetime.datetime(2025, 2, 2, 10, 11, 19, 12134, tzinfo=datetime.timezone.utc)),
        ),
    ]
