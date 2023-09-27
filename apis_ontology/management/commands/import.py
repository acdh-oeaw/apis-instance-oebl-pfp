import requests

from django.core.management.base import BaseCommand

from django.contrib.contenttypes.models import ContentType

from apis_ontology.models import Event, Institution, Person, Place, Work, Title, Profession
from apis_core.apis_metainfo.models import Uri, RootObject

SRC="https://apis.acdh.oeaw.ac.at/apis/api"

class Command(BaseCommand):
    help = "Import data from legacy APIS instance"

    def handle(self, *args, **options):
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

        # Migrate URIs
        nextpage = f"{SRC}/metainfo/uri/?format=json"
        while nextpage:
            print(nextpage)
            page = requests.get(nextpage)
            data = page.json()
            nextpage = data['next']
            for result in data["results"]:
                newuri, created = Uri.objects.get_or_create(uri=result["uri"])
                try:
                    result["root_object"] = RootObject.objects.get(pk=result["entity"]["id"])
                    for attribute in result:
                        if hasattr(newuri, attribute):
                            setattr(newuri, attribute, result[attribute])
                except RootObject.DoesNotExist:
                    pass
