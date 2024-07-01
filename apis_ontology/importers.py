from apis_core.generic.importers import GenericModelImporter


class PersonImporter(GenericModelImporter):
    def mangle_data(self, data):
        if "profession" in data:
            del data["profession"]
        return data
