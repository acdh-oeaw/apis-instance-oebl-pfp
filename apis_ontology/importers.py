from apis_core.generic.importers import GenericImporter
from apis_core.utils.rdf import get_definition_and_attributes_from_uri


class PlaceImporter(GenericImporter):
    def request(self, uri):
        model, data = get_definition_and_attributes_from_uri(uri)
        return data


class PersonImporter(GenericImporter):

    def request(self, uri):
        model, data = get_definition_and_attributes_from_uri(uri)
        if "profession" in data:
            del data["profession"]
        return data
