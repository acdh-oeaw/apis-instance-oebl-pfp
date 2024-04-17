import json
import re
import requests
import os
import pathlib
import datetime

from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

from apis_ontology.models import Event, Institution, Person, Place, Work, Title, Profession, Source, ProfessionCategory
from apis_core.apis_metainfo.models import Uri
from apis_core.collections.models import SkosCollection, SkosCollectionContentObject

SRC = "https://apis.acdh.oeaw.ac.at/apis/api"


TOKEN = os.environ.get("TOKEN")
HEADERS = {"Authorization": f"Token {TOKEN}"}

texts_file = pathlib.Path("texts.json")
sources_file = pathlib.Path("sources.json")
uris_file = pathlib.Path("uris.json")


def create_texts_file():
    texts = dict()
    nextpage = f"{SRC}/metainfo/text/?format=json&limit=5000"
    s = requests.Session()
    while nextpage:
        print(nextpage)
        page = s.get(nextpage, headers=HEADERS)
        data = page.json()
        nextpage = data['next']
        for result in data['results']:
            ttype = None
            if result["kind"] is not None:
                ttype = result["kind"]["label"]
                if ttype == "Soziale Herkunft: ":
                    ttype = "Soziale Herkunft"
                if ttype == "\u00dcbersiedlungen, Emigration, Remigration":
                    ttype = "\u00dcbersiedlung, Emigration, Remigration"
            # we ignore the text types
            # * Place description ÖBL (2)
            # * Place review comments and (236)
            # * Commentary Staribacher (5811)
            # See: https://github.com/acdh-oeaw/apis-instance-oebl-pnp/issues/172
            if ttype not in ["Place description ÖBL", "Place review comments", "Commentary Staribacher", None]:
                texts[result["id"]] = {"text": result["text"], "type": ttype}
    texts_file.write_text(json.dumps(texts, indent=2))


def create_sources_file():
    sources = dict()

    nextpage = f"{SRC}/metainfo/source/?format=json&limit=5000"
    s = requests.Session()
    while nextpage:
        print(nextpage)
        page = s.get(nextpage, headers=HEADERS)
        data = page.json()
        nextpage = data['next']
        for result in data["results"]:
            if result["pubinfo"] == "\u00d6BL 1815-1950, Bd. 1 (Lfg. 2), S. 112f.":
                result["pubinfo"] = "\u00d6BL 1815-1950, Bd. 1 (Lfg. 2, 1954), S. 112f."
            if result["pubinfo"] == "\u00d6BL 1815-1950, Bd. 6 (Lfg. 27), S. 126":
                result["pubinfo"] = "\u00d6BL 1815-1950, Bd. 6 (Lfg. 27, 1974), S. 126"
            sources[result["id"]] = {
                    "orig_filename": result["orig_filename"],
                    "pubinfo": result["pubinfo"],
                    "author": result["author"]
            }
    sources_file.write_text(json.dumps(sources, indent=2))


def create_uris_file():
    uris = dict()

    nextpage = f"{SRC}/metainfo/uri/?format=json&limit=5000"
    s = requests.Session()
    while nextpage:
        print(nextpage)
        page = s.get(nextpage, headers=HEADERS)
        data = page.json()
        nextpage = data['next']
        for result in data['results']:
            if result["uri"] == "https://apis-edits.acdh-dev.oeaw.ac.at/entity/None/":
                continue
            if result["uri"] == "":
                continue
            del result["url"]
            uri_id = result.pop("id")
            if entity := result.get("entity"):
                result["entity"] = entity["id"]
            uris[uri_id] = result
    uris_file.write_text(json.dumps(uris, indent=2))


def import_professions():
    nextpage = f"{SRC}/vocabularies/professiontype/?format=json&limit=1000"
    while nextpage:
        print(nextpage)
        page = requests.get(nextpage, headers=HEADERS)
        data = page.json()
        nextpage = data['next']
        for result in data["results"]:
            tokens = re.split(r" und |,", result["name"])
            for pos, token in enumerate(tokens):
                if token.startswith("-"):
                    token = tokens[pos-1] + token
                profession, created = Profession.objects.get_or_create(name=token.strip())
                if profession.oldids:
                    existing = set(profession.oldids.splitlines())
                    existing.add(str(result["id"]))
                    profession.oldids = '\n'.join(list(existing))
                else:
                    profession.oldids = result["id"]
                if profession.oldnames:
                    existing = set(profession.oldnames.splitlines())
                    existing.add(str(result["name"]))
                    profession.oldnames = '\n'.join(list(existing))
                else:
                    profession.oldnames = result["name"]
                for attribute in result:
                    if hasattr(profession, attribute) and attribute not in ["name", "id"]:
                        setattr(profession, attribute, result[attribute])
                profession.save()
            if result["parent_class"]:
                professioncat, created = ProfessionCategory.objects.get_or_create(id=result["parent_class"]["id"])
                professioncat.name = result["parent_class"]["label"]
                professioncat.save()


def is_entity(revision_tuple, rel_id, rel_type):
    rev_id, revision = revision_tuple
    return rev_id == rel_id and revision["model"] == rel_type


def import_entities(entities=[]):
    texts = json.loads(texts_file.read_text())
    text_to_entity_mapping = dict()
    sources = json.loads(sources_file.read_text())
    uris = json.loads(uris_file.read_text())
    revisions = json.loads(pathlib.Path("data/reversion.json").read_text())
    entities = entities or [Event, Institution, Person, Place, Work]

    for entitymodel in entities:
        entity = entitymodel.__name__.lower()
        nextpage = f"{SRC}/entities/{entity}/?format=json&limit=1000"
        while nextpage:
            print(nextpage)
            page = requests.get(nextpage, headers=HEADERS)
            data = page.json()
            nextpage = data['next']
            for result in data["results"]:
                print(result["url"])
                if entitymodel is Person:
                    result["surname"] = result["name"]
                    result["forename"] = result["first_name"]
                if entitymodel == Place:
                    result["label"] = result["name"]
                result_id = result["id"]
                if "kind" in result and result["kind"] is not None:
                    result["kind"] = result["kind"]["label"]

                professionlist = []
                professioncategory = None
                if "profession" in result:
                    for profession in result["profession"]:
                        if int(profession["id"]) in list(ProfessionCategory.objects.all().values_list('id', flat=True)):
                            professioncategory = ProfessionCategory.objects.get(id=profession["id"])
                        else:
                            for dbprofession in Profession.objects.all():
                                if profession["id"] in list(map(int, dbprofession.oldids.splitlines())):
                                    professionlist.append(dbprofession)
                    del result["profession"]

                titlelist = []
                if "title" in result:
                    for title in result["title"]:
                        newtitle, created = Title.objects.get_or_create(name=title)
                        titlelist.append(newtitle)
                    del result["title"]

                newentity, created = entitymodel.objects.get_or_create(pk=result_id)
                for attribute in result:
                    if hasattr(newentity, attribute):
                        setattr(newentity, attribute, result[attribute])

                if result["source"] is not None:
                    if "id" in result["source"]:
                        source_data = sources.get(str(result["source"]["id"]))
                        source, _ = Source.objects.get_or_create(pk=result["source"]["id"])
                        for field in source_data:
                            setattr(source, field, source_data[field])
                        source.content_object = newentity
                        source.save()
                textids = [str(text["id"]) for text in result["text"]]
                entity_texts = {key: text for key, text in texts.items() if key in textids}
                for key, entity_text in entity_texts.items():
                    done = False
                    text_type = entity_text["type"]
                    for field in newentity._meta.fields:
                        if field.verbose_name == text_type or field.name == text_type.lower():
                            setattr(newentity, field.name, entity_text["text"])
                            done = True
                            text_to_entity_mapping[key] = {"entity_id": newentity.id, "field_name": field.name}
                    if not done:
                        print(f"Could not save text: {entity_text}")
                newentity.save()

                newentity.title.add(*titlelist)
                newentity.profession.add(*professionlist)
                if professioncategory:
                    newentity.professioncategory = professioncategory

                # set up versions
                newentity.history.filter(history_date__year=2024).delete()
                newentity.history.filter(history_date__year=2017).delete()
                newentity._history_date = datetime.datetime(2017, 12, 31)
                ent_revisions = list(filter(lambda x: is_entity(x, str(result_id), entity), revisions.items()))
                revision_user = None
                if ent_revisions:
                    revid, revision = ent_revisions[0]
                    timestamp = datetime.datetime.fromisoformat(revision["timestamp"])
                    newentity.history.filter(history_date__year=timestamp.year, history_date__month=timestamp.month, history_date__day=timestamp.day).delete()
                    newentity._history_date = timestamp
                    revision_user, _ = User.objects.get_or_create(username=revision["user"])

                newentity.save()
                if revision_user:
                    newentity.history.filter(history_date=timestamp).update(history_user=revision_user.id)

                if "collection" in result:
                    for collection in result["collection"]:
                        importcol, created = SkosCollection.objects.get_or_create(name="imported collections")
                        newcol, created = SkosCollection.objects.get_or_create(name=collection["label"])
                        newcol.parent = importcol
                        newcol.save()
                        ct = ContentType.objects.get_for_model(newentity)
                        SkosCollectionContentObject.objects.get_or_create(collection=newcol, content_type_id=ct.id, object_id=newentity.id)

                for uri_id, uri in list((k, v) for k, v in uris.items() if v["entity"] == result_id):
                    uriobj, _ = Uri.objects.get_or_create(uri=uri["uri"])
                    for attribute in uri:
                        setattr(uriobj, attribute, uri[attribute])
                    uriobj.save()
        pathlib.Path("text_to_entity_mapping.json").write_text(json.dumps(text_to_entity_mapping, indent=2))


class Command(BaseCommand):
    help = "Import data from legacy APIS instance"

    def add_arguments(self, parser):
        parser.add_argument("--all", action="store_true")

        parser.add_argument("--professions", action="store_true")
        parser.add_argument("--entities", action="store_true")
        parser.add_argument("--event", action="store_true")
        parser.add_argument("--institution", action="store_true")
        parser.add_argument("--person", action="store_true")
        parser.add_argument("--place", action="store_true")
        parser.add_argument("--work", action="store_true")

    def handle(self, *args, **options):
        if not texts_file.exists():
            create_texts_file()
        if not sources_file.exists():
            create_sources_file()
        if not uris_file.exists():
            create_uris_file()

        if options["all"]:
            options["entities"] = True
            options["professions"] = True

        if options["professions"]:
            import_professions()

        entities = []

        if options["event"]:
            entities.append(Event)
        if options["institution"]:
            entities.append(Institution)
        if options["person"]:
            entities.append(Person)
        if options["place"]:
            entities.append(Place)
        if options["work"]:
            entities.append(Work)

        if options["entities"]:
            import_entities(entities)
