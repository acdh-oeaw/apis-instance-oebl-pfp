import json
import logging
import os
import urllib
from django.db.models.functions import Collate
from django.conf import settings

from .models import Person

logger = logging.getLogger(__name__)

DB_COLLATION = ("binary" if "sqlite" in settings.DATABASES["default"]["ENGINE"] else "en-x-icu")

PersonListViewQueryset = Person.objects.all().order_by(Collate("name", DB_COLLATION), Collate("first_name", DB_COLLATION))


class TypeSense_ExternalAutocomplete:
    def extract(self, res):
        match res:
            case {"document": {"id": id, "label": text}, **rest}:
                label = rest.get("highlight", {}).get("label", {})
                text = label.get("snippet", text) if isinstance(label, dict) else text
                text += f' <a href="{id}">{id}</a>'
                return {"id": id, "text": text, "selected_text": text}
            case unknown:
                logger.error("Could not parse result from typesense collection %s: %s", self.collectionname, unknown,)
        return False

    def get_results(self, q):
        typesensetoken = os.getenv("TYPESENSE_TOKEN", None)
        typesenseserver = os.getenv("TYPESENSE_SERVER", None)
        if typesensetoken and typesenseserver and getattr(self, "collectionname"):
            url = f"{typesenseserver}/collections/{self.collectionname}/documents/search?q={q}&query_by=description&query_by=label"
            req = urllib.request.Request(url)
            req.add_header("X-TYPESENSE-API-KEY", typesensetoken)
            with urllib.request.urlopen(req) as f:
                data = json.loads(f.read())
                results = list(filter(bool, map(self.extract, data.get("hits", []))))
                return results
        return {}


class PlaceExternalAutocomplete(TypeSense_ExternalAutocomplete):
    collectionname = "prosnet-wikidata-place-index"


class PersonExternalAutocomplete(TypeSense_ExternalAutocomplete):
    collectionname = "prosnet-wikidata-person-index"
