import json
import re
import requests
import os
import pathlib
import datetime

from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType

from apis_ontology.models import Event, Institution, Person, Place, Work, Title, Profession, Source, ProfessionCategory
from apis_core.apis_metainfo.models import Uri
from apis_core.collections.models import SkosCollection, SkosCollectionContentObject

SRC = "https://apis.acdh.oeaw.ac.at/apis/api"


TOKEN = os.environ.get("TOKEN")
HEADERS = {"Authorization": f"Token {TOKEN}"}


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
    texts = json.loads(pathlib.Path("texts.json").read_text())
    text_to_entity_mapping = dict()
    sources = json.loads(pathlib.Path("sources.json").read_text())
    uris = json.loads(pathlib.Path("uris.json").read_text())
    revisions = json.loads(pathlib.Path("data/reversion.json").read_text())
    entities = entities or [Event, Institution, Person, Place, Work]

    for entitymodel in entities:
        entity = entitymodel.__name__.lower()
        nextpage = f"{SRC}/entities/{entity}/?format=json&limit=100"
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
                        print(entity_text)
                newentity.save()

                newentity.title.add(*titlelist)
                newentity.profession.add(*professionlist)
                if professioncategory:
                    newentity.professioncategory = professioncategory

                newentity.history.filter(history_date__year=2024).delete()
                newentity.history.filter(history_date__year=2017).delete()
                newentity._history_date = datetime.datetime(2017, 12, 31)
                ent_revisions = list(filter(lambda x: is_entity(x, str(result_id), entity), revisions.items()))
                if ent_revisions:
                    revid, revision = ent_revisions[0]
                    timestamp = datetime.datetime.fromisoformat(revision["timestamp"])
                    newentity.history.filter(history_date__year=timestamp.year, history_date__month=timestamp.month, history_date__day=timestamp.day).delete()
                    newentity._history_date = timestamp

                newentity.save()

                if "collection" in result:
                    for collection in result["collection"]:
                        importcol, created = SkosCollection.objects.get_or_create(name="imported collections")
                        newcol, created = SkosCollection.objects.get_or_create(name=collection["label"])
                        newcol.parent = importcol
                        newcol.save()
                        ct = ContentType.objects.get_for_model(newentity)
                        SkosCollectionContentObject.objects.get_or_create(collection=newcol, content_type_id=ct.id, object_id=newentity.id)

                for uri_id, uri in list((k, v) for k, v in uris.items() if v["entity"] == result_id):
                    # we skip this one, as it has the same uri as 60379
                    if uri_id == "60485":
                        continue
                    uriobj, _ = Uri.objects.get_or_create(pk=uri_id)
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
        parser.add_argument("--uris", action="store_true")
        parser.add_argument("--sources", action="store_true")
        parser.add_argument("--event", action="store_true")
        parser.add_argument("--institution", action="store_true")
        parser.add_argument("--person", action="store_true")
        parser.add_argument("--place", action="store_true")
        parser.add_argument("--work", action="store_true")

    def handle(self, *args, **options):
        if options["all"]:
            options["entities"] = True
            options["urls"] = True
            options["sources"] = True
            options["professions"] = True

        if options["professions"]:
            import_professions()

        if options["sources"]:
            import_sources()

        if options["uris"]:
            import_uris()

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
