"""
Fix import from 12th tranche of XML files
The import used an older version of the simple-history
module, which had a bug that led to no history being
created.
This script adds the history entries for those imported XML files.
"""

import datetime
import pathlib
import xml.etree.ElementTree as ET

from django.core.management.base import BaseCommand
from simple_history.utils import get_history_model_for_model

from apis_ontology.models import Person, Profession, ProfessionCategory, Source


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

    nummer = root.get("Nummer")

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

    date = datetime.datetime(2024, 7, 15)

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

    p = Source.objects.get(orig_filename=nummer).content_object

    HistoricalPerson = get_history_model_for_model(Person)
    # print(HistoricalPerson.objects.filter(rootobject_ptr_id=p.id, history_date=date).delete())
    attributes = person
    attributes["history_date"] = date
    attributes["history_user"] = None
    attributes["history_change_reason"] = ""
    attributes["history_type"] = "~"
    attributes["id"] = p.id
    attributes["rootobject_ptr_id"] = p.id
    hp = HistoricalPerson.objects.create(**attributes)
    for profession in professions:
        profession = profession.strip()
        dbprofession = Profession.objects.filter(name=profession).first()
        thtb = Person.profession.through.objects.filter(
            person_id=hp.id, profession_id=dbprofession.id
        )
        if thtb.count() == 1:
            id_ent = thtb[0].id
        else:
            id_ent = 1
        hp.profession.model(
            id=id_ent, history=hp, profession=dbprofession, person=p
        ).save()
    print(hp)


class Command(BaseCommand):
    help = "Import data from legacy xml files"

    def add_arguments(self, parser):
        parser.add_argument("--path", type=pathlib.Path)

    def handle(self, *args, **options):
        if path := options.get("path"):
            files = path.glob("*.xml")
            for file in files:
                parse(file)
