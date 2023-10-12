import csv
import argparse
from django.core.management.base import BaseCommand

from apis_highlighter.models import AnnotationProject


class Command(BaseCommand):
    help = "Import data from legacy APIS instance"

    def add_arguments(self, parser):
        parser.add_argument("--file", type=argparse.FileType('r'))

    def handle(self, *args, **options):
        reader = csv.DictReader(options["file"])
        for row in reader:
            ap, _ = AnnotationProject.objects.get_or_create(pk=row["id"])
            ap.name = row["name"]
            ap.save()
