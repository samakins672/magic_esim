# Generated by Django 5.1.4 on 2024-12-23 19:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0003_rename_amount_payment_price'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='payment',
            name='plan',
        ),
    ]
