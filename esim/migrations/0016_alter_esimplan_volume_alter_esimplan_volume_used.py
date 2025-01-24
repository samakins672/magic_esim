# Generated by Django 5.1.4 on 2025-01-22 18:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('esim', '0015_alter_esimplan_activated_on'),
    ]

    operations = [
        migrations.AlterField(
            model_name='esimplan',
            name='volume',
            field=models.IntegerField(max_length=255),
        ),
        migrations.AlterField(
            model_name='esimplan',
            name='volume_used',
            field=models.IntegerField(blank=True, default=None, max_length=255, null=True),
        ),
    ]
