# Generated by Django 5.1.4 on 2024-12-30 21:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0005_payment_currency'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='gateway_transaction_id',
            field=models.CharField(blank=True, default=None, max_length=200, null=True),
        ),
    ]
