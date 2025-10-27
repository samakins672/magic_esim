from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_alter_user_phone_number'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccountDeletionLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_pk', models.BigIntegerField(blank=True, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True, null=True)),
                ('method', models.CharField(default='self-service', max_length=32)),
                ('request_path', models.CharField(blank=True, max_length=255, null=True)),
                ('deleted_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
    ]

