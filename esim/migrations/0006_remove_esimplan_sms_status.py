# Generated by Django 5.1.4 on 2024-12-24 12:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('esim', '0005_esimplan_esim_status_esimplan_smdp_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='esimplan',
            name='sms_status',
        ),
    ]
