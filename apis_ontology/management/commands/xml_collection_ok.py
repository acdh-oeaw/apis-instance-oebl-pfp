import json
import xml.etree.ElementTree as ET
import pathlib
import unidecode
from django.core.management.base import BaseCommand

from apis_ontology.models import Source

ns = {'b': 'http://www.biographien.ac.at'}

DATA = {}


def filename_clean(file):
    if "_online_resolved" in file.name:
        return file.name.replace("_online_resolved", "")
    if "__resolved" in file.name:
        return file.name.replace("__resolved", "")
    if "_resolved" in file.name:
        return file.name.replace("_resolved", "")
    return file.name


def transliterate_v1(text: str) -> str:
    return unidecode.unidecode(text)


def equals_database_entry(file):
    root = ET.parse(file).getroot()
    filename = filename_clean(file)
    sources = []
    pubinfo = root.find("./b:Lexikonartikel/b:PubInfo", ns)
    if pubinfo is not None:
        sources = Source.objects.filter(orig_filename=filename, pubinfo=pubinfo.text)
    lieferung = root.find("./b:Lexikonartikel/b:Lieferung", ns)
    if lieferung is not None:
        sources = Source.objects.filter(orig_filename=filename, pubinfo=lieferung.text)
    if len(sources) == 1:
        haupttext = root.find("./b:Lexikonartikel/b:Haupttext", ns)
        if haupttext:
            haupttext = ''.join(haupttext.itertext())
        else:
            haupttext = getattr(haupttext, "text", "") or ""
        kurzdefinition = root.find("./b:Lexikonartikel/b:Kurzdefinition", ns)
        if kurzdefinition:
            kurzdefinition = ''.join(kurzdefinition.itertext())
        else:
            kurzdefinition = getattr(kurzdefinition, "text", "") or ""

        db_haupttext = ""
        if sources[0].content_object.oebl_haupttext is not None:
            db_haupttext = sources[0].content_object.oebl_haupttext.text

        db_kurzinfo = ""
        if sources[0].content_object.oebl_kurzinfo is not None:
            db_kurzinfo = sources[0].content_object.oebl_kurzinfo.text

        if (
                transliterate_v1(haupttext.strip()) == transliterate_v1(db_haupttext.strip()) and
                transliterate_v1(kurzdefinition.strip()) == transliterate_v1(db_kurzinfo.strip())):
            DATA[sources[0].id] = {"content_type_id": sources[0].content_type_id, "object_id": sources[0].object_id}
            return True
    if len(sources) > 1:
        print(f"{file} equals multiple entries")
    return False


class Command(BaseCommand):
    help = "Import data from legacy xml files"

    def add_arguments(self, parser):
        # point to XML_RESOLVE_IN_PROGRESS folder
        parser.add_argument("--path", type=pathlib.Path)

    def handle(self, *args, **options):
        files = []
        if options["path"]:
            if options["path"].is_dir():
                for file in options["path"].glob('**/*.xml'):
                    files.append(file)
            else:
                files = [options["path"]]

        for file in sorted(files):
            print(file)
            equals_database_entry(file)
        pathlib.Path("output.json").write_text(json.dumps(DATA, indent=2))
