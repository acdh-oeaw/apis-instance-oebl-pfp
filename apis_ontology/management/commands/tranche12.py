"""
Import data from 12th tranche of XML files
The files have a slighly different format than the other tranches
and the datamodel changed a bit since we did the earlier imports.
Therefore we use a separate script
"""

import datetime
import pathlib
import xml.etree.ElementTree as ET

from django.core.management.base import BaseCommand

from apis_core.apis_metainfo.models import Uri
from apis_ontology.models import Person, Profession, ProfessionCategory, Source


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
    place = node.find("./{*}Geographischer_Begriff").text
    return date_written, place


def text_or_iter(node) -> str:
    if node:
        return "".join(node.itertext()).strip()
    text = getattr(node, "text")
    if text:
        return text.strip()
    return ""


def gender(value):
    if value is not None:
        match value.attrib["Type"]:
            case "m":
                return "male"
            case "f":
                return "female"
            case "w":
                return "female"
            case other:
                return other
    return value


def parse(filepath):
    root = ET.parse(filepath).getroot()

    person = {}
    person["surname"] = root.find(
        "./{*}Lexikonartikel/{*}Schlagwort/{*}Hauptbezeichnung"
    ).text
    person["forename"] = root.find(
        "./{*}Lexikonartikel/{*}Schlagwort/{*}Nebenbezeichnung[@Type='Vorname']"
    ).text

    uris = []
    if gnd := root.get("pnd"):
        uris.append(f"https://d-nb.info/gnd/{gnd}")

    source = {}
    source["orig_filename"] = root.get("Nummer")
    author = root.find("./{*}Lexikonartikel/{*}Autor")
    if author is not None:
        source["author"] = author.text.strip() if author.text else ""
    pubinfo = root.find("./{*}Lexikonartikel/{*}PubInfo")
    if pubinfo is not None:
        source["pubinfo"] = pubinfo.text
    eoebl_id = root.get("eoebl_id", None)
    if eoebl_id:
        source["orig_id"] = int(eoebl_id)
    else:
        source["orig_id"] = None

    if pubinfo := source.get("pubinfo", False):
        date = get_date_from_pubinfo_string(pubinfo)

    beruf = root.find("./{*}Lexikonartikel/{*}Vita/{*}Beruf")
    if beruf is not None:
        professions = beruf.text or ""
        professions = professions.replace("und", ",")
        professions = professions.split(",")

        berufsgruppe = beruf.get("Berufsgruppe")
        person["professioncategory"] = ProfessionCategory.objects.get(name=berufsgruppe)

    gebdat = root.find("./{*}Lexikonartikel/{*}Vita/{*}Geburt")
    if gebdat is not None:
        b_date_written, b_place = get_b_or_d(gebdat)
        person["start"] = b_date_written
    stdat = root.find("./{*}Lexikonartikel/{*}Vita/{*}Tod")
    if stdat is not None:
        d_date_written, d_place = get_b_or_d(stdat)
        person["end"] = d_date_written

    # geschlecht
    geschlecht = root.find("./{*}Lexikonartikel/{*}Geschlecht")
    person["gender"] = gender(geschlecht)

    kurzinfo = root.find("./{*}Lexikonartikel/{*}Kurzdefinition")
    if kurzinfo is not None:
        person["oebl_kurzinfo"] = text_or_iter(kurzinfo) or ""
    haupttext = root.find("./{*}Lexikonartikel/{*}Haupttext")
    if haupttext is not None:
        person["oebl_haupttext"] = text_or_iter(haupttext) or ""
    werk = root.find("./{*}Lexikonartikel/{*}Werke")
    if werk is not None:
        person["oebl_werkverzeichnis"] = text_or_iter(werk) or ""
    literatur = root.find("./{*}Lexikonartikel/{*}Literatur")
    if literatur is not None:
        person["references"] = text_or_iter(literatur)
    externe_verweise = root.findall("./{*}Lexikonartikel/{*}Externe_Verweise/{*}Link")
    person["external_resources"] = [el.get("href") for el in externe_verweise]
    person["alternative_names"] = []

    dbperson = Person(**person)
    dbperson.skip_history_when_saving = True
    dbperson.save()
    dbperson.skip_history_when_saving = True
    for profession in professions:
        profession = profession.strip()
        dbprofession = Profession.objects.filter(name=profession).first()
        if dbprofession is None:
            dbprofession = Profession.objects.create(name=profession)
        dbperson.profession.add(dbprofession)

    del dbperson.skip_history_when_saving
    dbperson._history_date = date
    dbperson.save()

    dbperson.history.first().delete()

    print(f"Created {dbperson!r}")

    s, _ = Source.objects.get_or_create(**source)
    s.content_object = dbperson
    s.save()
    for uri in uris:
        u, created = Uri.objects.get_or_create(uri=uri)
        if not created:
            print(f"Merge {dbperson!r} with {u.content_object!r}")
        else:
            u.content_object = dbperson
            u.save()


class Command(BaseCommand):
    help = "Import data from legacy xml files"

    def add_arguments(self, parser):
        parser.add_argument("--path", type=pathlib.Path)

    def handle(self, *args, **options):
        if path := options.get("path"):
            files = path.glob("*.xml")
            for file in files:
                parse(file)
