# Generated by Django 5.1.4 on 2025-01-02 16:48

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Authentication', '0013_alter_otpverification_expires_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otpverification',
            name='expires_at',
            field=models.DateTimeField(default=datetime.datetime(2025, 1, 2, 16, 58, 25, 201837, tzinfo=datetime.timezone.utc)),
        ),
    ]
