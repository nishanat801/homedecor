# Generated by Django 5.1.4 on 2025-01-03 07:31

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Authentication', '0021_alter_otpverification_expires_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otpverification',
            name='expires_at',
            field=models.DateTimeField(default=datetime.datetime(2025, 1, 3, 7, 41, 31, 813022, tzinfo=datetime.timezone.utc)),
        ),
    ]
