from django.apps import AppConfig


class ApisOntologyConfig(AppConfig):
    default_auto_field = "django.db.models.AutoField"
    name = 'oebl'

    def ready(self):
        from . import signals
