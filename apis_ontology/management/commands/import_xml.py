import datetime
import logging
import re
from apis_core.apis_metainfo.models import Uri
from django.db.models import CharField, TextField
import unidecode
import unicodedata
import json
import xml.etree.ElementTree as ET
import pathlib
from django.core.management.base import BaseCommand
from simple_history.utils import get_history_model_for_model

from apis_ontology.models import Person, Source, Profession, ProfessionCategory

ns = {"b": "http://www.biographien.ac.at"}

logging.basicConfig(
    filename=f"create_harmonized_xmls_{datetime.datetime.now().strftime('%d-%m-%Y_%H:%M:%S')}.log",
    filemode="a",
    format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.DEBUG,
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
    pubinfo = re.sub(r"\n\s+", " ", pubinfo)
    date = None
    if pubinfo.startswith("\u00d6BL 1815-1950, Bd. ") or pubinfo.startswith(
        "\u00d6BL Online-Edition, Bd."
    ):
        close_pos = pubinfo.find(")")
        date = pubinfo[close_pos - 4 : close_pos]
        try:
            date = datetime.datetime(int(date), 1, 1)
        except ValueError:
            date = datetime.datetime(1950, 1, 1)
            print(f"Could not parse date from {pubinfo}, using 1950-01-01")
    if pubinfo.startswith("\u00d6BL Online-Edition, Lfg."):
        close_pos = pubinfo.find(")")
        day, month, year = pubinfo[close_pos - 10 : close_pos].split(".")
        date = datetime.datetime(int(year), int(month), int(day))
    return date.isoformat()


def extractperson(file):
    logger.info(f"Processing {file}")
    root = ET.parse(file).getroot()

    person = {}
    person["surname"] = (
        root.find("./Lexikonartikel/Schlagwort/Hauptbezeichnung")
        .text.replace(",", "")
        .strip()
    )
    person["forename"] = (
        root.find("./Lexikonartikel/Schlagwort/Nebenbezeichnung[@Type='Vorname']")
        .text.replace(",", "")
        .strip()
    )
    eoebl_id = root.get("eoebl_id")
    metadata = {
        "pdf_file": root.get("pdf_file", ""),
        "gnd": root.get("gnd", ""),
        "doi": root.get("doi", ""),
        "nummer": root.get("Nummer", ""),
        "oebl_id": int(eoebl_id) if eoebl_id is not None else None,
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
        professions = professions.replace(" und ", ",")
        person["profession"] = [
            Profession.objects.get_or_create(name=profession.strip())[0]
            for profession in professions.split(",")
            if profession
        ]

        person["professioncategory"] = ProfessionCategory.objects.get_or_create(
            name=berufsgruppe.get("Berufsgruppe", "?")
        )[0]

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
        if literatur.text is not None:
            person["references"] = text_or_iter(literatur).replace("L.: ", "").strip()
    externe_verweise = root.findall("./Lexikonartikel/Externer_Verweis")
    person["external_resources"] = [el.get("href") for el in externe_verweise]
    bilder = root.findall("./Lexikonartikel/Medien/Bild")
    person["external_resources"].extend([el.get("src") for el in bilder])

    if not metadata["nummer"].endswith(".xml"):
        metadata["nummer"] += ".xml"

    metadata["nummer"] = metadata["nummer"].replace("_print", "")

    dbperson = None
    source = Source.objects.filter(orig_filename=metadata["nummer"])
    if source.count() == 0 and metadata.get("oebl_id", None) is not None:
        source = Source.objects.filter(orig_id=metadata["oebl_id"])
    if source.count() == 1:
        dbperson = source.first().content_object
    else:
        print(f"Does not exist {metadata['nummer']}, searching for GND")
        if "gnd" in person["metadata"]:
            if len(person["metadata"]["gnd"]) > 2:
                dbperson = Uri.objects.filter(
                    uri__contains=f"//d-nb.info/gnd/{person['metadata']['gnd']}"
                ).first()
                if dbperson is not None:
                    dbperson = dbperson.root_object
                else:
                    logger.info(f"Could not find {person['metadata']['gnd']} in DB")
    if dbperson is None:
        logger.info(f"Could not find {metadata['nummer']} in DB")
    check_hp = False
    history_date_recalc = False
    if dbperson is not None and "oebl_haupttext" in person:
        try:
            if len(dbperson.oebl_haupttext) + 5 < len(person["oebl_haupttext"]):
                check_hp = False
                history_date_recalc = True
            else:
                check_hp = True
        except TypeError as e:
            logger.warning(f"Error in comparing lengths of Haupttexts {e}")
        try:
            if len(dbperson.oebl_haupttext.strip()) == person["oebl_haupttext"].strip():
                dbperson.oebl_haupttext = person["oebl_haupttext"]
                dbperson.oebl_kurzinfo = person["oebl_kurzinfo"]
                dbperson.oebl_werkverzeichnis = person["oebl_werkverzeichnis"]
                dbperson.references = person["references"]
                dbperson.skip_history_when_saving = True
                dbperson.save()
        except Exception as e:
            logger.warning(f"Error in comparing Haupttexts {e}")
    if check_hp:
        HistoricalPerson = get_history_model_for_model(Person)
        attributes = dict(person)
        # Add empty string for all CharFields and TextFields that are not set in person dict yet
        for field in Person._meta.get_fields():
            if isinstance(field, (CharField, TextField)) and (
                field.name not in attributes or attributes[field.name] is None
            ):
                attributes[field.name] = ""
        if "profession" in attributes:
            profession = attributes.pop("profession")
        del attributes["metadata"]
        attributes["history_date"] = metadata["date"]
        attributes["history_user"] = None
        attributes["history_change_reason"] = ""
        attributes["history_type"] = "~"
        attributes["id"] = dbperson.id
        attributes["rootobject_ptr_id"] = dbperson.id
        hp = HistoricalPerson.objects.create(**attributes)
        for p in profession:
            thtb = Person.profession.through.objects.filter(
                person_id=hp.id, profession_id=p.id
            )
            if thtb.count() == 1:
                id_ent = thtb[0].id
            else:
                id_ent = 1
            hp.profession.model(
                id=id_ent, history=hp, profession=p, person=dbperson
            ).save()
    else:
        logger.info(f"No source found Creating {metadata['nummer']}")
        attributes = dict(person)
        # Add empty string for all CharFields and TextFields that are not set in person dict yet
        for field in Person._meta.get_fields():
            if isinstance(field, (CharField, TextField)) and (
                field.name not in attributes or attributes[field.name] is None
            ):
                attributes[field.name] = ""
        if "profession" in attributes:
            profession = attributes.pop("profession")
        del attributes["metadata"]
        if history_date_recalc:
            db_h_rec = dbperson.history.most_recent()
            db_h_rec.history_date = datetime.datetime.fromisoformat(
                metadata["date"]
            ) - datetime.timedelta(days=1)
            db_h_rec.save()
        attributes["_history_date"] = metadata["date"]
        if dbperson is not None:
            for key, value in attributes.items():
                setattr(dbperson, key, value)
            dbperson.save()
        else:
            dbperson = Person.objects.create(**attributes)
        for p in profession:
            dbperson.profession.add(p)
        author = root.find(".//Lexikonartikel/Autor")
        if author is not None:
            author = author.text
            if author is not None:
                author = author.replace("(", "").replace(")", "").strip()
            else:
                author = ""
        else:
            author = ""
        source = Source.objects.create(
            orig_filename=metadata["nummer"],
            content_object=dbperson,
            author=author,
            pdf_filename=metadata["pdf_file"],
            orig_id=metadata["oebl_id"],
        )
    if "gnd" in person["metadata"]:
        if len(person["metadata"]["gnd"]) > 2:
            u1 = Uri.objects.filter(
                uri=f"https://d-nb.info/gnd/{person['metadata']['gnd']}",
                root_object=dbperson,
            )
            if u1.count() == 0:
                try:
                    Uri.objects.create(
                        uri=f"https://d-nb.info/gnd/{person['metadata']['gnd']}",
                        root_object=dbperson,
                    )
                except Exception as e:
                    logger.error(
                        f"Could not create GND uri for {person['metadata']['gnd']}, person id: {dbperson.id}, {e}"
                    )

    if "doi" in person["metadata"]:
        if len(person["metadata"]["doi"]) > 2:
            u2 = Uri.objects.filter(
                uri=f"https://doi.org/{person['metadata']['doi']}", root_object=dbperson
            )
            if u2.count() == 0:
                try:
                    Uri.objects.create(
                        uri=f"https://doi.org/{person['metadata']['doi']}",
                        root_object=dbperson,
                    )
                except Exception as e:
                    logger.error(
                        f"Could not create DOI uri for {person['metadata']['doi']}, person id: {dbperson.id}, {e}"
                    )


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
