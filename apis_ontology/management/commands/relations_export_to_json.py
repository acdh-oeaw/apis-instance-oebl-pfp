import json
import requests
import os
import pathlib

from django.core.management.base import BaseCommand

SRC = "https://apis.acdh.oeaw.ac.at/apis/api"
TOKEN = os.environ.get("TOKEN")
HEADERS = {"Authorization": f"Token {TOKEN}"}
RELATIONS = {}

COPYFIELDS = ['review', 'start_date', 'start_start_date', 'start_end_date', 'end_date', 'end_start_date', 'end_end_date', 'start_date_written', 'end_date_written', 'status', 'references', 'notes', 'published', 'source']

def import_relations():
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

    s = requests.Session()

    for relation, relationsettings in relations.items():
        nextpage = f"{SRC}/relations/{relation}/?format=json&limit=1000"
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


class Command(BaseCommand):
    help = "Import data from legacy APIS instance"

    def handle(self, *args, **options):
        import_relations()
        rj = pathlib.Path("relations.json")
        rj.write_text(json.dumps(RELATIONS, indent=2))
