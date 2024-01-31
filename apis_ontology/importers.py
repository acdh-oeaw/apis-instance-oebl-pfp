from apis_core.generic.importers import GenericImporter
from apis_core.utils.rdf import get_modelname_and_dict_from_uri


class PersonImporter(GenericImporter):

    def request(self, uri):
        model, data = get_modelname_and_dict_from_uri(uri)
        if "profession" in data:
            del data["profession"]
        return data
