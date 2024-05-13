import os
import datetime
import json
import pathlib
import requests
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from apis_core.apis_relations.models import Property, TempTriple
from apis_core.apis_metainfo.models import RootObject
from simple_history.utils import get_history_model_for_model

SRC = "https://apis.acdh.oeaw.ac.at/apis/api"
TOKEN = os.environ.get("TOKEN")
HEADERS = {"Authorization": f"Token {TOKEN}"}
COPYFIELDS = ['review', 'start_date', 'start_start_date', 'start_end_date', 'end_date', 'end_start_date', 'end_end_date', 'start_date_written', 'end_date_written', 'status', 'references', 'notes', 'published', 'source']


relation_file = pathlib.Path("relations.json")


def fetch_relations():
    relations = {
            'personevent': {
                "subj": "related_person",
                "obj": "related_event",
            },
            'personinstitution': {
                "subj": "related_person",
                "obj": "related_institution"
            },
            "personperson": {
                "subj": "related_personA",
                "obj": "related_personB",
            },
            "personplace": {
                "subj": "related_person",
                "obj": "related_place",
            },
            "personwork": {
                "subj": "related_person",
                "obj": "related_work",
            },
            "placeplace": {
                "subj": "related_placeA",
                "obj": "related_placeB",
            },
            "institutioninstitution": {
                "subj": "related_institutionA",
                "obj": "related_institutionB",
            }
    }
    relationlist = {}
    RELATIONS = {}

    s = requests.Session()

    for relation, relationsettings in relations.items():
        nextpage = f"{SRC}/relations/{relation}/?format=json&limit=5000"
        while nextpage:
            print(nextpage)
            page = s.get(nextpage, headers=HEADERS)
            data = page.json()
            nextpage = data["next"]
            for result in data["results"]:
                if result["relation_type"]:
                    propdata = relationlist.get(result["relation_type"]["id"])
                    if not propdata:
                        proppage = s.get(result["relation_type"]["url"])
                        propdata = proppage.json()
                        relationlist[result["relation_type"]["id"]] = propdata
                    if result[relationsettings["subj"]] and result[relationsettings["obj"]]:
                        RELATIONS[result["id"]] = {
                            "type": relation,
                            "name": propdata["name"],
                            "name_reverse": propdata["name_reverse"] or propdata["name"] + " (reverse)",
                            "subj": result[relationsettings["subj"]]["id"],
                            "obj": result[relationsettings["obj"]]["id"],
                        }
                        for field in COPYFIELDS:
                            RELATIONS[result["id"]][field] = result[field]
                    else:
                        print(result)
                else:
                    print(f"No relation type for relation {result}")
    relation_file.write_text(json.dumps(RELATIONS, indent=2))


def is_relation(revision_tuple, rel_id, rel_type):
    r_id, revision = revision_tuple
    return r_id == rel_id and revision["model"] == rel_type


def import_relations():
    relations = json.loads(relation_file.read_text())
    revisions = json.loads(pathlib.Path("data/reversion.json").read_text())

    property_cache = {}
    rev_users = {rev["user"] for revid, rev in revisions.items()}
    user_cache = {}
    for username in rev_users:
        if username:
            user_cache[username], _ = User.objects.get_or_create(username=username)

    l = len(relations)
    p = 0

    for id, relation in relations.items():
        p += 1
        print(f"{p}/{l}:\t {id}: {relation['name']}")
        property_identifier = f"{relation['name']}___{relation['name_reverse']}"
        prop = property_cache.get(property_identifier, {}).get("property", None)
        if prop is None:
            prop, created = Property.objects.get_or_create(name_forward=relation["name"], name_reverse=relation["name_reverse"])
            property_cache[property_identifier] = {"property": prop, "subj_class": [], "obj_class": []}

        try:
            subj = None
            if subj := relation["subj"]:
                subj = RootObject.objects_inheritance.get_subclass(pk=subj)
                ct = ContentType.objects.get_for_model(subj)
                if ct not in property_cache[property_identifier]["subj_class"]:
                    property_cache[property_identifier]["subj_class"].append(ct)
                    # we have to add this before creating the temptriple
                    # otherwise it raises an exception
                    prop.subj_class.add(ct)
            obj = None
            if obj := relation["obj"]:
                obj = RootObject.objects_inheritance.get_subclass(pk=obj)
                ct = ContentType.objects.get_for_model(obj)
                if ct not in property_cache[property_identifier]["obj_class"]:
                    property_cache[property_identifier]["obj_class"].append(ct)
                    # we have to add this before creating the temptriple
                    # otherwise it raises an exception
                    prop.obj_class.add(ct)
            if subj and obj and prop:
                try:
                    tt, created = TempTriple.objects.get_or_create(id=id, prop=prop, subj=subj, obj=obj)
                    for attribute in relation:
                        if hasattr(tt, attribute) and attribute not in ["id", "subj", "obj"]:
                            setattr(tt, attribute, relation[attribute])
                    tt.history.filter(history_date__year=2024).delete()
                    tt.history.filter(history_date__year=2017).delete()
                    tt._history_date = datetime.datetime(2017, 12, 31)
                    rel_revisions = list(filter(lambda x: is_relation(x, str(id), relation["type"]), revisions.items()))
                    if rel_revisions:
                        rid, revision = rel_revisions[0]
                        timestamp = datetime.datetime.fromisoformat(revision["timestamp"])
                        tt._history_date = timestamp
                        if revision.get("user") is not None:
                            tt._history_user = user_cache[revision["user"]]
                    tt.history.filter(history_date=tt._history_date).delete()

                    tt.save()
                    #tt.history.filter(history_date=timestamp).update(history_type="+")
                except Exception as e:
                    print(e)
                    print(relation)
            else:
                print(relation)
        except RootObject.DoesNotExist as e:
            print(relation)
            print(e)

    th = get_history_model_for_model(TempTriple)
    th.objects.filter(id__in=[revid for revid, rev in relations.items()]).update(history_type="+")
    for property_identifier, prop in property_cache.items():
        prop["property"].subj_class.add(*prop["subj_class"])
        prop["property"].obj_class.add(*prop["obj_class"])


class Command(BaseCommand):
    help = "Import relation data from legacy APIS instance"

    def handle(self, *args, **options):
        if not relation_file.exists():
            fetch_relations()
        import_relations()
