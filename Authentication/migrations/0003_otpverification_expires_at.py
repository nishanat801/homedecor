# Generated by Django 5.1.4 on 2024-12-31 14:26

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Authentication', '0002_otpverification'),
    ]

    operations = [
        migrations.AddField(
            model_name='otpverification',
            name='expires_at',
            field=models.DateTimeField(default=datetime.datetime(2024, 12, 31, 14, 36, 56, 313198, tzinfo=datetime.timezone.utc)),
        ),
    ]
