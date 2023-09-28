import requests

from django.core.management.base import BaseCommand

from apis_ontology.models import Event, Institution, Person, Place, Work, Title, Profession
from apis_core.apis_metainfo.models import Uri, RootObject
from apis_core.apis_relations.models import Property, TempTriple

SRC="https://apis.acdh.oeaw.ac.at/apis/api"


class Command(BaseCommand):
    help = "Import data from legacy APIS instance"

    def add_arguments(self, parser):
        parser.add_argument("--entities", action="store_true")
        parser.add_argument("--urls", action="store_true")
        parser.add_argument("--relations", action="store_true")
        parser.add_argument("--all")


    def handle(self, *args, **options):
        if options["all"]:
            options["entities"] = True
            options["urls"] = True
            options["relations"] = True

        entities = {
                "event": {
                    "dst": Event
                },
                "institution": {
                    "dst": Institution,
                },
                "person": {
                    "dst": Person,
                },
                "place": {
                    "dst": Place,
                },
                "work": {
                    "dst": Work,
                }
        }

        if options["entities"]:
            # Migrate entities
            for entity, entitysettings in entities.items():
                nextpage = f"{SRC}/entities/{entity}/?format=json&limit=500"
                while nextpage:
                    print(nextpage)
                    page = requests.get(nextpage)
                    data = page.json()
                    nextpage = data['next']
                    for result in data["results"]:
                        print(result["url"])
                        result_id = result["id"]
                        if "kind" in result and result["kind"] is not None:
                            result["kind"] = result["kind"]["label"]
                        professionlist = []
                        if "profession" in result:
                            for profession in result["profession"]:
                                newprofession, created = Profession.objects.get_or_create(name=profession["label"])
                                professionlist.append(newprofession)
                            del result["profession"]
                        titlelist = []
                        if "title" in result:
                            for title in result["title"]:
                                newtitle, created = Title.objects.get_or_create(name=title)
                                titlelist.append(newtitle)
                            del result["title"]
                        newentity, created = entitysettings["dst"].objects.get_or_create(pk=result_id)
                        for attribute in result:
                            if hasattr(newentity, attribute):
                                setattr(newentity, attribute, result[attribute])
                        for title in titlelist:
                            newentity.title.add(title)
                        for profession in professionlist:
                            newentity.profession.add(profession)
                        newentity.save()

        if options["urls"]:
            # Migrate URIs
            nextpage = f"{SRC}/metainfo/uri/?format=json"
            while nextpage:
                print(nextpage)
                page = requests.get(nextpage)
                data = page.json()
                nextpage = data['next']
                for result in data["results"]:
                    print(result["url"])
                    newuri, created = Uri.objects.get_or_create(uri=result["uri"])
                    if hasattr(result["entity"], "id"):
                        try:
                            result["root_object"] = RootObject.objects.get(pk=result["entity"]["id"])
                            for attribute in result:
                                if hasattr(newuri, attribute):
                                    setattr(newuri, attribute, result[attribute])
                            newuri.save()
                        except RootObject.DoesNotExist as e:
                            print(e)
                    else:
                        print(f"No entity.id set for URI: {result}")

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
        }
        if options["relations"]:
            for relation, relationsettings in relations.items():
                nextpage = f"{SRC}/relations/{relation}/?format=json&limit=500"
                while nextpage:
                    print(nextpage)
                    page = requests.get(nextpage)
                    data = page.json()
                    nextpage = data["next"]
                    for result in data["results"]:
                        print(result["url"])
                        if result["relation_type"]:
                            prop, created = Property.objects.get_or_create(id=result["relation_type"]["id"])
                            if created:
                                proppage = requests.get(result["relation_type"]["url"])
                                propdata = proppage.json()
                                prop.name = propdata["name"]
                                prop.name_reverse = propdata["name_reverse"]
                                prop.save()
                            try:
                                subj = None
                                if result[relationsettings["subj"]]:
                                    subj = RootObject.objects_inheritance.get_subclass(pk=result[relationsettings["subj"]]["id"])
                                    prop.subj_class.add(subj.self_contenttype)
                                obj = None
                                if result[relationsettings["obj"]]:
                                    obj = RootObject.objects_inheritance.get_subclass(pk=result[relationsettings["obj"]]["id"])
                                    prop.obj_class.add(obj.self_contenttype)
                                prop.save()
                                if subj and obj and prop:
                                    tt, created = TempTriple.objects.get_or_create(id=result["id"], prop=prop, subj=subj, obj=obj)
                                else:
                                    print(result)
                            except RootObject.DoesNotExist as e:
                                print(result)
                                print(e)
                        else:
                            print(f"No relation type for relation {result}")
