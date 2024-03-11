from apis_core.generic.importers import GenericImporter
from apis_core.utils.rdf import get_definition_and_attributes_from_uri
from apis_ontology.models import Person, Place, Institution


class PlaceImporter(GenericImporter):
    def request(self, uri):
        model, data = get_definition_and_attributes_from_uri(uri, Place)
        return data


class PersonImporter(GenericImporter):
    def request(self, uri):
        model, data = get_definition_and_attributes_from_uri(uri, Person)
        if "profession" in data:
            del data["profession"]
        return data


class InstitutionImporter(GenericImporter):
    def request(self, uri):
        model, data = get_definition_and_attributes_from_uri(uri, Institution)
        return data
