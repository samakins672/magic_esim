# Generated by Django 5.1.4 on 2025-01-01 21:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0012_payment_payment_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='esim_plan',
            field=models.CharField(blank=True, default=None, max_length=255, null=True),
        ),
    ]