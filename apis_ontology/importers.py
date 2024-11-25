from apis_core.generic.importers import GenericModelImporter
from apis_core.utils.helpers import create_object_from_uri
from apis_ontology.models import FandStattIn, Place


class PersonImporter(GenericModelImporter):
    def mangle_data(self, data):
        if "profession" in data:
            del data["profession"]
        return data


class EventImporter(GenericModelImporter):
    def create_instance(self):
        data = self.get_data(drop_unknown_fields=False)
        modelfields = [field.name for field in self.model._meta.fields]
        data_croped = {key: data[key] for key in data if key in modelfields}
        subj = self.model.objects.create(**data_croped)
        if "related_place" in data:
            place = create_object_from_uri(data["related_place"], Place)
            FandStattIn.objects.create(subj=subj, obj=place)
        return subj
