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

    l = len(relations)
    p = 0

    for id, relation in relations.items():
        p += 1
        #print(f"{p}/{l}:\t {id}: {relation['name']}")
        prop, created = Property.objects.get_or_create(name_forward=relation["name"], name_reverse=relation["name_reverse"])
        try:
            subj = None
            if subj := relation["subj"]:
                subj = RootObject.objects_inheritance.get_subclass(pk=subj)
                ct = ContentType.objects.get_for_model(subj)
                prop.subj_class.add(ct)
            obj = None
            if obj := relation["obj"]:
                obj = RootObject.objects_inheritance.get_subclass(pk=obj)
                ct = ContentType.objects.get_for_model(obj)
                prop.obj_class.add(ct)
            if subj and obj and prop:
                try:
                    tt, created = TempTriple.objects.get_or_create(id=id)
                    tt.prop = prop
                    tt.subj = subj
                    tt.obj = obj
                    for attribute in relation:
                        if hasattr(tt, attribute) and attribute not in ["id", "subj", "obj"]:
                            setattr(tt, attribute, relation[attribute])
                    tt.save()
                    tt.history.filter(history_date__year=2024).delete()
                    tt.history.filter(history_date__year=2017).delete()
                    tt._history_date = datetime.datetime(2017, 12, 31)
                    rel_revisions = list(filter(lambda x: is_relation(x, str(id), relation["type"]), revisions.items()))
                    revision_user = None
                    if rel_revisions:
                        rid, revision = rel_revisions[0]
                        timestamp = datetime.datetime.fromisoformat(revision["timestamp"])
                        tt.history.filter(history_date__year=timestamp.year, history_date__month=timestamp.month, history_date__day=timestamp.day).delete()
                        tt._history_date = timestamp
                        if revision.get("user") is not None:
                            revision_user, _ = User.objects.get_or_create(username=revision["user"])
                    tt.save()
                    tt.history.filter(history_date=timestamp).update(history_type="+")
                    if revision_user:
                        tt.history.filter(history_date=timestamp).update(history_user=revision_user.id)
                except Exception as e:
                    print(e)
                    print(relation)
            else:
                print(relation)
        except RootObject.DoesNotExist as e:
            print(relation)
            print(e)


class Command(BaseCommand):
    help = "Import relation data from legacy APIS instance"

    def handle(self, *args, **options):
        if not relation_file.exists():
            fetch_relations()
        import_relations()
