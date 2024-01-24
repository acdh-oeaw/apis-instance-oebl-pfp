import csv
import argparse
from django.core.management.base import BaseCommand

from apis_highlighter.models import Annotation, AnnotationProject
from apis_ontology.models import Text, Person
from apis_core.apis_relations.models import TempTriple
from django.contrib.auth.models import User

user_mapping = {
        12: 'sennierer',
        14: 'mkaiser',
        16: 'ABernad',
        24: 'PRumpolt',
        25: 'KLejtovicz',
        26: 'spacy_user',
        27: 'APiechl',
}

class Command(BaseCommand):
    help = "Import data from legacy APIS instance"

    def add_arguments(self, parser):
        parser.add_argument("--file", type=argparse.FileType('r'))

    def handle(self, *args, **options):
        reader = csv.DictReader(options["file"])
        for row in reader:
            if row["content_type_id"] and row["object_id"]:
                ann, _ = Annotation.objects.get_or_create(pk=row["id"], start=row["start"], end=row["end"])
                ann.orig_string = row["orig_string"]
                try:
                    user = User.objects.get(username=user_mapping[int(row["user_added_id"])])
                    ann.user = user
                except User.DoesNotExist:
                    pass

                text = Text.objects.get(pk=row["text_id"])
                ann.text_content_object = text

                if row["content_type_id"] == 8:
                    try:
                        obj = Person.objects.get(pk=row["object_id"])
                    except Person.DoesNotExist:
                        print(f"Did not find person with id {row['object_id']}")
                        obj = None
                else:
                    try:
                        obj = TempTriple.objects.get(pk=row["object_id"])
                    except TempTriple.DoesNotExist:
                        print(f"Did not find temptriple with id {row['object_id']}")
                        obj = None
                if obj:
                    print(obj)
                    ann.content_object = obj

                project, _ = AnnotationProject.objects.get_or_create(pk=row["annotation_project_id"])
                ann.project = project
                ann.save()
