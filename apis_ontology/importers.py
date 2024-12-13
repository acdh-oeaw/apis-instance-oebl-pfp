from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.db.utils import IntegrityError
from apis_core.generic.importers import GenericModelImporter
from apis_core.utils.helpers import create_object_from_uri
from apis_core.apis_metainfo.models import Uri


class BaseEntityImporter(GenericModelImporter):
    """Importer for all OEBL entities. Allows to define related objects directly in the RDF variable names.
    Use `?something__RELATED_OBEJCT_CLASS__RELATION_CLASS` in your variables to auto create relations."""

    def create_instance(self):
        data = self.get_data(drop_unknown_fields=False)
        if "sameas" in data:
            data["sameas"] = data["sameas"].split("|")
            sa = Uri.objects.filter(uri__in=data["sameas"])
            if sa.count() == 1:
                return sa.first().root_object
            elif sa.count() > 1:
                root_set = set([s.root_object for s in sa])
                if len(root_set) > 1:
                    raise IntegrityError(
                        f"Multiple objects found for sameAs URIs {data['sames']}. "
                        f"This indicates a data integrity problem as these URIs should be unique."
                    )
                else:
                    return sa.first().root_object
        modelfields = [field.name for field in self.model._meta.fields]
        data_croped = {key: data[key] for key in data if key in modelfields}
        subj = self.model.objects.create(**data_croped)
        if "sameas" in data:
            for uri in data["sameas"]:
                Uri.objects.create(uri=uri, root_object_id=subj.id)
        related_keys = [
            (x, x.split("__")[1], x.split("__")[2]) for x in data.keys() if "__" in x
        ]
        try:
            for rk in related_keys:
                key, obj, rel = rk
                RelatedModel = apps.get_model("apis_ontology", obj)
                RelationType = apps.get_model("apis_ontology", rel)
                if key in data:
                    related_obj = create_object_from_uri(data[key], RelatedModel)
                    RelationType.objects.create(subj=subj, obj=related_obj)
        except Exception as e:  # noqa: E722
            subj.delete()
            raise ImproperlyConfigured(
                f"Error in creating related Objects for {self.model}: {e}"
            )

        return subj


class EventImporter(BaseEntityImporter):
    pass


class PersonImporter(BaseEntityImporter):
    def mangle_data(self, data):
        if "profession" in data:
            del data["profession"]
        return data


class InstitutionImporter(BaseEntityImporter):
    pass


class PlaceImporter(BaseEntityImporter):
    pass
