# Generated by Django 5.1.4 on 2025-01-03 04:42

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Authentication', '0017_alter_otpverification_expires_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otpverification',
            name='expires_at',
            field=models.DateTimeField(default=datetime.datetime(2025, 1, 3, 4, 52, 1, 271775, tzinfo=datetime.timezone.utc)),
        ),
    ]
