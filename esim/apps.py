from django.apps import AppConfig


class EsimConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'esim'

    def ready(self):
        import esim.signals  # Import the signals module to connect the signal
