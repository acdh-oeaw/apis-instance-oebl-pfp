import json
import pathlib
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from apis_core.apis_relations.models import Property, TempTriple
from apis_core.apis_metainfo.models import RootObject


def import_relations():
    relations = json.loads(pathlib.Path("relations.json").read_text())

    l = len(relations)
    p = 0

    for id, relation in relations.items():
        p += 1
        print(f"{p}/{l}:\t {id}: {relation['name']}")
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
                    tt, created = TempTriple.objects.get_or_create(id=id, prop=prop, subj=subj, obj=obj)
                    for attribute in relation:
                        if hasattr(tt, attribute) and attribute not in ["id", "subj", "obj"]:
                            setattr(tt, attribute, relation[attribute])
                    tt.save()
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
        import_relations()
