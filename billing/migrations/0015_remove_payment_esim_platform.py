# Generated by Django 5.1.4 on 2025-02-10 11:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0014_payment_esim_platform'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='payment',
            name='esim_platform',
        ),
    ]
