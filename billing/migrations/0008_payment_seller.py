# Generated by Django 5.1.4 on 2024-12-31 08:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0007_payment_package_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='seller',
            field=models.CharField(blank=True, default=None, max_length=25, null=True),
        ),
    ]
