import unidecode
import json
import xml.etree.ElementTree as ET
import pathlib
from django.core.management.base import BaseCommand

ns = {'b': 'http://www.biographien.ac.at'}

def transliterate_v1(text: str) -> str:
    text = text.strip()
    return unidecode.unidecode(text)

def extractperson(file):
    print(file)
    root = ET.parse(file).getroot()
    person = {}
    person["surname"] = root.find("./b:Lexikonartikel/b:Schlagwort/b:Hauptbezeichnung", ns).text
    person["first_name"] = root.find("./b:Lexikonartikel/b:Schlagwort/b:Nebenbezeichnung[@Type='Vorname']", ns).text


    # vita
    if profession := root.find("./b:Lexikonartikel/b:Vita/b:Beruf", ns).text:
        profession = profession.replace("und", ",")
        person["professions"] = [profession.strip() for profession in profession.split(",")]
    person["professioncategory"] = root.find("./b:Lexikonartikel/b:Vita/b:Beruf", ns).attrib["Berufsgruppe"]
    #TODO: geburt/tod/+orte

    # geschlecht
    gender = root.find("./b:Lexikonartikel/b:Geschlecht", ns).attrib["Type"]
    match gender:
        case "m":
            person["gender"] = "male"
        case "f":
            person["gender"] = "female"
        case other:
            person["gender"] = other

    kurzinfo = root.find("./b:Lexikonartikel/b:Kurzdefinition", ns)
    if kurzinfo:
        person["kurzinfo"] = transliterate_v1(''.join(kurzinfo.itertext()))
    else:
        person["kurzinfo"] = transliterate_v1(getattr(kurzinfo, "text"))
    haupttext = root.find("./b:Lexikonartikel/b:Haupttext", ns)
    if haupttext:
        person["haupttext"] = transliterate_v1(''.join(haupttext.itertext()))
    else:
        person["haupttext"] = transliterate_v1(getattr(haupttext, "text"))

    print(json.dumps(person, indent=2))


class Command(BaseCommand):
    help = "Import data from legacy xml files"

    def add_arguments(self, parser):
        # point to XML_RESOLVE_IN_PROGRESS folder
        parser.add_argument("--path", type=pathlib.Path, nargs="+")

    def handle(self, *args, **options):
        files = []
        for path in options["path"]:
            if path.is_dir():
                for file in path.glob('**/*.xml'):
                    files.append(file)
            else:
                files.append(path)

        for file in sorted(files):
            extractperson(file)
