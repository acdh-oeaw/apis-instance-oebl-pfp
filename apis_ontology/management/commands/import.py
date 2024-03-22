import re
import requests
import os

from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType

from apis_ontology.models import Event, Institution, Person, Place, Work, Title, Profession, Source, Text, ProfessionCategory
from apis_core.apis_metainfo.models import Uri, RootObject
from apis_core.collections.models import SkosCollection, SkosCollectionContentObject

from django.db import utils

SRC = "https://apis.acdh.oeaw.ac.at/apis/api"


TOKEN = os.environ.get("TOKEN")
HEADERS = {"Authorization": f"Token {TOKEN}"}

def import_texts():
    nextpage = f"{SRC}/metainfo/text/?format=json&limit=1000"
    while nextpage:
        print(nextpage)
        page = requests.get(nextpage, headers=HEADERS)
        data = page.json()
        nextpage = data['next']
        for result in data['results']:
            print(result['url'])
            newtext, created = Text.objects.get_or_create(id=result["id"])
            newtext.text = result["text"]
            if "kind" in result and result["kind"] is not None:
                newtext.kind = result["kind"]["label"]
            newtext.save()


def import_sources():
    nextpage = f"{SRC}/metainfo/source/?format=json&limit=1000"
    while nextpage:
        print(nextpage)
        page = requests.get(nextpage, headers=HEADERS)
        data = page.json()
        nextpage = data['next']
        for result in data["results"]:
            print(result["url"])
            newsource, created = Source.objects.get_or_create(id=result["id"])
            for attribute in result:
                if hasattr(newsource, attribute):
                    setattr(newsource, attribute, result[attribute])
                newsource.save()


def import_uris():
    nextpage = f"{SRC}/metainfo/uri/?format=json&limit=1000"
    while nextpage:
        print(nextpage)
        page = requests.get(nextpage, headers=HEADERS)
        data = page.json()
        nextpage = data['next']
        for result in data["results"]:
            # this is an error in the source data, it has
            # 60485 == 60379
            # 64341 == 64338
            # 64344 == 64342
            # 65675 == 65470
            # 67843 == 67841
            # 67866 == 67862
            # 67870 == 67868
            # 67872 == 67874, 67876, 67878
            # 74055 == 74051
            # 74057 == 74053
            # 82548 == 82544
            # 82550 == 82546
            # 86445 == 86441
            # 86447 == 86443
            # 86703 == 86699
            # 86705 == 86701
            # 89010 == 89008
            # 89026 == 89024
            # 89050 == 89046
            # 91406 == 91405
            # 91477 == 91476
            # 92307 == 92305
            # 92311 == 92309
            # 92317 == 92313
            # 92319 == 92315
            # 92916 == 63941
            # 92933 == 19323
            # 92941 == 19406
            # 92950 == 48
            # 92969 == 7566
            # 92988 == 18870
            # 92992 == 19242
            # 93001 == 64175
            # 93007 == 178
            # 93040 == 13
            # 93044 == 4
            # 93050 == 898
            # 93054 == 3860
            # 93059 == 40
            # 93064 == 67324
            # 93088 == 19370
            # 93109 == 80929
            # 93113 == 19156
            # 93119 == 64139
            # 93142 == 64812
            # 93149 == 11388
            # 93155 == 89054
            # 93213 == 64068
            # 93237 == 19232
            # 93250 == 65268
            # 93260 == 18961
            # 93262 == 512
            # 93266 == 78171
            # 93295 == 105
            # 93318 == 63882
            # 93320 == 63882
            # ...
            if result["id"] in [60485, 64341, 64344, 65675, 67843, 67866, 67870, 67874, 67876, 67878, 74055, 74057, 82548, 82550, 86445, 86447, 86703, 86705, 89010, 89026, 89050, 91406, 91477, 92307, 92311, 92317, 92319, 92916, 92933, 92941, 92950, 92969, 92988, 92992, 93001, 93007, 93040, 93044, 93050, 93054, 93059, 93064, 93088, 93109, 93113, 93119, 93142, 93149, 93155, 93213, 93237, 93250, 93260, 93262, 93266, 93295, 93318, 93320, 93324, 93341, 93358, 93376, 93388, 93392, 93409, 93442, 93459, 93478, 93482, 93499, 93517, 93531, 93548, 93555, 93589, 93609, 93616, 93697, 93720, 93727, 93740, 93747, 93756, 93785, 93851, 93863, 93926, 93934, 93948, 93958, 93968, 93980, 94004, 94044, 94072, 94111, 94198, 94202, 94206, 94237, 94268, 94317, 94354, 94375, 94398, 94450, 94456, 94463, 94477, 94490, 94498, 94511, 94622, 94638, 94683, 94779, 94873, 94919, 94958, 95111, 95124, 95146, 95190, 95194, 95274, 95284, 95305, 95309, 95339, 95449, 95534, 95610, 95616, 95620, 95626, 95655, 95668, 95672, 95696]:
                continue
            if result["uri"] == "https://apis-edits.acdh-dev.oeaw.ac.at/entity/None/":
                continue
            if result["uri"] == "":
                continue
            print(result["url"])
            try:
                newuri, created = Uri.objects.get_or_create(id=result["id"], uri=result["uri"])
            except utils.IntegrityError:
                print(f"IntegrityErro: {result['id']}")
            del result["uri"]
            del result["id"]
            if result["entity"] and "id" in result["entity"]:
                try:
                    result["root_object"] = RootObject.objects.get(pk=result["entity"]["id"])
                except RootObject.DoesNotExist:
                    result["root_object"] = None
                    print(f"RootObject with ID {result['entity']['id']} not found")
            else:
                print(f"No entity.id set for URI: {result}")
            for attribute in result:
                if hasattr(newuri, attribute):
                    setattr(newuri, attribute, result[attribute])
            newuri.save()


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


def import_entities(entities=[]):
    entities = entities or [Event, Institution, Person, Place, Work]

    for entitymodel in entities:
        entity = entitymodel.__name__.lower()
        nextpage = f"{SRC}/entities/{entity}/?format=json&limit=500"
        while nextpage:
            print(nextpage)
            page = requests.get(nextpage, headers=HEADERS)
            data = page.json()
            nextpage = data['next']
            for result in data["results"]:
                print(result["url"])
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
                for title in titlelist:
                    newentity.title.add(title)
                for profession in professionlist:
                    newentity.profession.add(profession)
                if professioncategory:
                    newentity.professioncategory = professioncategory
                newentity.save()
                if "collection" in result:
                    for collection in result["collection"]:
                        importcol, created = SkosCollection.objects.get_or_create(name="imported collections")
                        newcol, created = SkosCollection.objects.get_or_create(name=collection["label"])
                        newcol.parent = importcol
                        newcol.save()
                        ct = ContentType.objects.get_for_model(newentity)
                        SkosCollectionContentObject.objects.get_or_create(collection=newcol, content_type_id=ct.id, object_id=newentity.id)
                if result["source"] is not None:
                    if "id" in result["source"]:
                        try:
                            source = Source.objects.get(pk=result["source"]["id"])
                            source.content_object = newentity
                            source.save()
                        except Source.DoesNotExist:
                            print(f"Source does not exist: {result['source']['id']}")
                for rtext in result["text"]:
                    if "id" in rtext:
                        try:
                            text = Text.objects.get(pk=rtext["id"])
                            text.content_object = newentity
                            text.save()
                        except Text.DoesNotExist:
                            print(f"Text does not exist: {rtext['id']}")


class Command(BaseCommand):
    help = "Import data from legacy APIS instance"

    def add_arguments(self, parser):
        parser.add_argument("--all", action="store_true")

        parser.add_argument("--professions", action="store_true")
        parser.add_argument("--entities", action="store_true")
        parser.add_argument("--uris", action="store_true")
        parser.add_argument("--sources", action="store_true")
        parser.add_argument("--texts", action="store_true")
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
            options["texts"] = True

        if options["texts"]:
            import_texts()

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
