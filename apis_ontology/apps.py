from django.apps import AppConfig


class ApisOntologyConfig(AppConfig):
    default_auto_field = "django.db.models.AutoField"
    name = 'apis_ontology'

    def ready(self):
        from . import signals
