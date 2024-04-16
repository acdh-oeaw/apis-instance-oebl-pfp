import json
import pathlib
import datetime
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from apis_core.apis_relations.models import Property, TempTriple
from apis_core.apis_metainfo.models import RootObject


def parse_source_date(source):
    date = None
    if source.pubinfo.startswith("\u00d6BL 1815-1950, Bd. ") or source.pubinfo.startswith("\u00d6BL Online-Edition, Bd."):
        close_pos = source.pubinfo.find(")")
        date = source.pubinfo[close_pos-4:close_pos]
        date = datetime.datetime(int(date), 1, 1)
    if source.pubinfo.startswith("\u00d6BL Online-Edition, Lfg."):
        close_pos = source.pubinfo.find(")")
        # we should parse the whole date
        day, month, year = source.pubinfo[close_pos-10:close_pos].split(".")
        date = datetime.datetime(int(year), int(month), int(day))
    return date


def timestamp(obj: object):
    date = None
    if obj.sources.exists():
        date = parse_source_date(obj.sources.first())
    return date


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
                dates = []
                if (obj_date := timestamp(obj)) is not None:
                    dates.append(obj_date)
                if (subj_date := timestamp(subj)) is not None:
                    dates.append(subj_date)
                try:
                    tt, created = TempTriple.objects.get_or_create(id=id, prop=prop, subj=subj, obj=obj)
                    for attribute in relation:
                        if hasattr(tt, attribute) and attribute not in ["id", "subj", "obj"]:
                            setattr(tt, attribute, relation[attribute])
                    if dates:
                        tt._history_date = min(dates)
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
