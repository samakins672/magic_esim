# Generated by Django 5.1.4 on 2025-02-10 11:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0013_payment_esim_plan'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='esim_platform',
            field=models.CharField(blank=True, default=None, max_length=25, null=True),
        ),
    ]
