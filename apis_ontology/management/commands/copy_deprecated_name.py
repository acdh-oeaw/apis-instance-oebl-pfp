from django.core.management.base import BaseCommand

from apis_ontology.models import Event, Institution, Person, Place, Work


class Command(BaseCommand):
    help = "copy values from deprecated_name to name"

    def handle(self, *args, **options):
        models = [Event, Institution, Person, Place, Work]
        for model in models:
            all_instances = model.objects.all()
            for instance in all_instances:
                instance.name = instance.deprecated_name
            res = model.objects.bulk_update(all_instances, fields=["name"], batch_size=1_000)
            print(f"Updated {res} {model} instances")
