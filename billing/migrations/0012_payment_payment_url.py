# Generated by Django 5.1.4 on 2025-01-01 15:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0011_payment_payment_address'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='payment_url',
            field=models.CharField(blank=True, default=None, max_length=255, null=True),
        ),
    ]
