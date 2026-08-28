import datetime
import unidecode
import unicodedata
import json
import xml.etree.ElementTree as ET
import pathlib
from django.core.management.base import BaseCommand
from simple_history.utils import get_history_model_for_model

from apis_ontology.models import Person, Source, Profession, ProfessionCategory

ns = {"b": "http://www.biographien.ac.at"}


def calculate_textual_offsets(parent, field_name):
    offsets = []
    running_offset = 0
    for node in parent.iter():
        if node.tag in ["Haupttext", "Kurzdefinition"]:
            if node.text is not None:
                running_offset += len(
                    unicodedata.normalize("NFC", (node.text if node.text else ""))
                )
            continue
        textlen = len(unicodedata.normalize("NFC", (node.text if node.text else "")))
        offsets.append(
            {
                "orig_string": node.text,
                "start": running_offset,
                "end": running_offset + textlen,
                "text_field_name": field_name,
            }
        )
        running_offset += textlen
        running_offset += len(
            unicodedata.normalize("NFC", (node.tail if node.tail else ""))
        )
    return offsets


def transliterate_v1(text: str) -> str:
    if text is None:
        return text
    text = text.strip()
    return unidecode.unidecode(text)


def text_or_iter(node) -> str:
    if node:
        return "".join(node.itertext())
    return getattr(node, "text")


def get_b_or_d(node):
    date_written = ""
    year = node.get("Metadatum")
    if year:
        date_written += year
    month = node.get("MM")
    if month:
        date_written = f"{month}." + date_written
    day = node.get("TT")
    if day:
        date_written = f"{day}." + date_written
    place = node.find("./Geographischer_Begriff").text
    return date_written, place


def get_date_from_pubinfo_string(pubinfo):
    date = None
    if pubinfo.startswith("\u00d6BL 1815-1950, Bd. ") or pubinfo.startswith(
        "\u00d6BL Online-Edition, Bd."
    ):
        close_pos = pubinfo.find(")")
        date = pubinfo[close_pos - 4 : close_pos]
        date = datetime.datetime(int(date), 1, 1)
    if pubinfo.startswith("\u00d6BL Online-Edition, Lfg."):
        close_pos = pubinfo.find(")")
        day, month, year = pubinfo[close_pos - 10 : close_pos].split(".")
        date = datetime.datetime(int(year), int(month), int(day))
    return date.isoformat()


def extractperson(file):
    print(file)
    root = ET.parse(file).getroot()

    person = {}
    person["surname"] = root.find("./Lexikonartikel/Schlagwort/Hauptbezeichnung").text
    person["forename"] = root.find(
        "./Lexikonartikel/Schlagwort/Nebenbezeichnung[@Type='Vorname']"
    ).text

    metadata = {
        "pdf_file": root.get("pdf_file"),
        "gnd": root.get("gnd"),
        "doi": root.get("doi"),
        "nummer": root.get("Nummer"),
    }
    pubinfo = root.find("./Lexikonartikel/PubInfo")
    if pubinfo is not None:
        pubinfo = pubinfo.text
        metadata["pubinfo"] = pubinfo
        metadata["date"] = get_date_from_pubinfo_string(pubinfo)
    person["metadata"] = metadata

    # vita
    berufsgruppe = root.find("./Lexikonartikel/Vita/Berufsgruppe")
    if berufsgruppe is not None:
        professions = berufsgruppe.text or ""
        professions = professions.replace("und", ",")
        person["profession"] = [
            Profession.objects.get(name=profession.strip())
            for profession in professions.split(",")
            if profession
        ]
        person["professioncategory"] = ProfessionCategory.objects.get(
            name=berufsgruppe.get("Berufsgruppe")
        )

    gebdat = root.find("./Lexikonartikel/Vita/Geburt")
    if gebdat is not None:
        b_date_written, b_place = get_b_or_d(gebdat)
        person["start_date_written"] = b_date_written
        person["metadata"]["start_date_place"] = b_place
    stdat = root.find("./Lexikonartikel/Vita/Tod")
    if stdat is not None:
        d_date_written, d_place = get_b_or_d(stdat)
        person["end_date_written"] = d_date_written
        person["metadata"]["end_date_place"] = d_place

    # geschlecht
    gender = root.find("./Lexikonartikel/Geschlecht")
    if gender is not None:
        gender = gender.attrib["Type"]
        match gender:
            case "m":
                person["gender"] = "male"
            case "f":
                person["gender"] = "female"
            case "w":
                person["gender"] = "female"
            case other:
                person["gender"] = other

    kurzinfo = root.find("./Lexikonartikel/Kurzdefinition")
    if kurzinfo is not None:
        person["oebl_kurzinfo"] = text_or_iter(kurzinfo)
        person["metadata"]["annnotations_kurzinfo"] = calculate_textual_offsets(
            kurzinfo, "oebl_kurzinfo"
        )
    haupttext = root.find("./Lexikonartikel/Haupttext")
    if haupttext is not None:
        person["oebl_haupttext"] = text_or_iter(haupttext)
        person["metadata"]["annotations_haupttext"] = calculate_textual_offsets(
            haupttext, "oebl_haupttext"
        )
    werk = root.find("./Lexikonartikel/Werk")
    if werk is not None:
        person["oebl_werkverzeichnis"] = text_or_iter(werk)
    literatur = root.find("./Lexikonartikel/Literatur")
    if literatur is not None:
        person["references"] = text_or_iter(literatur)
    externe_verweise = root.findall("./Lexikonartikel/Externer_Verweis")
    person["external_resources"] = [el.get("href") for el in externe_verweise]
    bilder = root.findall("./Lexikonartikel/Medien/Bild")
    person["external_resources"].extend([el.get("src") for el in bilder])

    if not metadata["nummer"].endswith(".xml"):
        metadata["nummer"] += ".xml"

    metadata["nummer"] = metadata["nummer"].replace("_print", "")

    dbperson = None
    try:
        source = Source.objects.get(orig_filename=metadata["nummer"])
        dbperson = source.content_object
    except Source.DoesNotExist:
        print(f"Does not exist {metadata['nummer']}")

    # print(person)
    if dbperson is not None:
        HistoricalPerson = get_history_model_for_model(Person)
        attributes = dict(person)
        del attributes["profession"]
        del attributes["metadata"]
        attributes["history_date"] = metadata["date"]
        attributes["history_user"] = None
        attributes["history_change_reason"] = ""
        attributes["history_type"] = "~"
        attributes["id"] = dbperson.id
        attributes["rootobject_ptr_id"] = dbperson.id
        HistoricalPerson.objects.create(**attributes)


class Command(BaseCommand):
    help = "Import data from legacy xml files"

    def add_arguments(self, parser):
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
            extractperson(file)
