from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("billing", "0015_remove_payment_esim_platform"),
    ]

    operations = [
        migrations.AddField(
            model_name="payment",
            name="mpgs_success_indicator",
            field=models.CharField(blank=True, default=None, max_length=200, null=True),
        ),
    ]
