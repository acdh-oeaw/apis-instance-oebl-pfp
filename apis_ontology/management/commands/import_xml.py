import logging
import unidecode
import json
import xml.etree.ElementTree as ET
import pathlib
from django.core.management.base import BaseCommand

ns = {"b": "http://www.biographien.ac.at"}

logging.basicConfig(level=logging.INFO)


def parse_hmi_file(filename: str) -> dict:
    with open(filename, "r") as file:
        lines = file.readlines()

    data = {}
    for line in lines:
        if "=" in line:
            key, value = line.strip().split("=", 1)
            data[key] = value

    return data


def transliterate_v1(text: str) -> str:
    text = text.strip()
    return unidecode.unidecode(text)


def extractperson(file: pathlib.Path, hmi_file: pathlib.Path):
    print(file)
    root = ET.parse(file).getroot()
    if root.find("./Verweis") is not None:
        logging.info(f"Skipping {file} because it is a reference")
        return
    hmi = parse_hmi_file(hmi_file)
    person = {}
    person["surname"] = (
        root.find("./Lexikonartikel/Schlagwort_Nachname").text.split(",")[0].strip()
    )
    person["first_name"] = (
        root.find("./Lexikonartikel/Schlagwort_Vorname").text.split(",")[0].strip()
    )

    # vita
    if profession := hmi["oebl_Schlagwort_generell"]:
        profession = profession.replace("und", ",")
        person["professions"] = [
            profession.strip() for profession in profession.split(",")
        ]
    person["professioncategory"] = hmi["oebl_Berufsgruppe"]
    # TODO: geburt/tod/+orte

    # geschlecht
    gender = hmi.get("oebl_Geschlecht", None)
    match gender:
        case "m":
            person["gender"] = "male"
        case "f":
            person["gender"] = "female"
        case other:
            person["gender"] = other

    kurzinfo = root.find("./Lexikonartikel/Kurzdefinition", ns)
    if kurzinfo:
        person["kurzinfo"] = transliterate_v1("".join(kurzinfo.itertext()))
    else:
        person["kurzinfo"] = transliterate_v1(getattr(kurzinfo, "text"))
    haupttext = root.find("./Lexikonartikel/Haupttext", ns)
    if haupttext:
        person["haupttext"] = transliterate_v1("".join(haupttext.itertext()))
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
                for file in path.glob("**/*.xml"):
                    files.append(file)
            else:
                files.append(path)

        for file in sorted(files):
            if str(file).endswith("__Verweis.xml"):
                logging.info(f"Skipping {file} because it is a reference")
                continue
            hmi_file = pathlib.Path(str(file) + ".hmi")
            extractperson(file, hmi_file)
            pass
