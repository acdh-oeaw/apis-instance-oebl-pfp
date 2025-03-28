import logging

from django.contrib.contenttypes.models import ContentType

from apis_core.generic.importers import GenericModelImporter

logger = logging.getLogger(__name__)


class OEBLBaseEntityImporter(GenericModelImporter):
    def mangle_data(self, data):
        m2m_tuples = []
        for key, value in data.items():
            if key.endswith("_m2m"):
                k2, obj_model, _ = key.split("_")
                m2m_tuples.append((k2, obj_model, value, key))
            if key in ["start", "end"] and "T" in "".join(value):
                data[key] = [x.split("T")[0] for x in value]
            if key in ["latitude", "longitude"]:
                data[key] = [float(x.replace("+", "").strip()) for x in value]
            if key == "alternative_names":
                data[key] = [{"name": x, "art": "alternativer Name"} for x in value]
        for key in m2m_tuples:
            del data[key[3]]
        self._m2m_tuples = m2m_tuples
        return data

    def create_instance(self):
        instance = super().create_instance()
        for m2m in self._m2m_tuples:
            for inst in m2m[2]:
                if inst.startswith("http"):
                    try:
                        rel_ent = OEBLBaseEntityImporter(
                            inst,
                            ContentType.objects.get(
                                app_label="apis_ontology", model=m2m[1]
                            ).model_class(),
                        ).create_instance()
                        getattr(instance, m2m[0]).add(rel_ent)
                    except Exception as e:
                        logger.debug(
                            f"import of m2m didnt work: {e}. Tried to import {inst}"
                        )
                else:
                    pass
        return instance


class PlaceImporter(OEBLBaseEntityImporter):
    pass


class PersonImporter(OEBLBaseEntityImporter):
    pass


class InstitutionImporter(OEBLBaseEntityImporter):
    pass


class EventImporter(OEBLBaseEntityImporter):
    pass
