import json
import pathlib

from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from apis_core.collections.models import SkosCollection, SkosCollectionContentObject


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--path", type=pathlib.Path)

    def handle(self, *args, **options):
        if options["path"]:
            sc, _ = SkosCollection.objects.get_or_create(name="20240123 - xml and db match")
            data = json.loads(options["path"].read_text())
            for key, entry in data.items():
                print(key)
                content_type = ContentType.objects.get(pk=entry["content_type_id"])
                SkosCollectionContentObject.objects.get_or_create(collection = sc, content_type=content_type, object_id=entry["object_id"])
