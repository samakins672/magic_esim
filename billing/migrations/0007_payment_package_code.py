# Generated by Django 5.1.4 on 2024-12-30 22:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0006_payment_gateway_transaction_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='package_code',
            field=models.CharField(blank=True, default=None, max_length=25, null=True),
        ),
    ]
