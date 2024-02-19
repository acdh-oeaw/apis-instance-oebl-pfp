import json
import logging
import os
import urllib
from django.db.models.functions import Collate
from django.conf import settings
from django.template.loader import render_to_string

from .models import Person

logger = logging.getLogger(__name__)

DB_COLLATION = ("binary" if "sqlite" in settings.DATABASES["default"]["ENGINE"] else "en-x-icu")

PersonListViewQueryset = Person.objects.all().order_by(Collate("name", DB_COLLATION), Collate("first_name", DB_COLLATION))


class TypeSense_ExternalAutocomplete:
    collections = None
    template = None

    def get_result_label(self, hit={}):
        if self.template:
            return render_to_string(self.template, {"hit": hit})
        return f'{hit["document"]["label"]} <a href="{hit["document"]["id"]}">{hit["document"]["id"]}</a>'

    def extract(self, res):
        if res.get("document"):
            return {"id": res["document"]["id"], "text": self.get_result_label(res), "selected_text": self.get_result_label(res)}
        logger.error("Could not parse result from typesense collection %s: %s", self.collections, res)
        return False

    def get_results(self, q):
        typesensetoken = os.getenv("TYPESENSE_TOKEN", None)
        typesenseserver = os.getenv("TYPESENSE_SERVER", None)
        if typesensetoken and typesenseserver:
            match self.collections:
                # if there is only on collection configured, we hit that collection directly
                case str() as collection:
                    data = None
                    url = f"{typesenseserver}/collections/{collection}/documents/search?q={q}&query_by=description&query_by=label"
                    req = urllib.request.Request(url)
                # if there are multiple collections configured, we use the `multi_search` endpoint
                case list() as collectionlist:
                    url = f"{typesenseserver}/multi_search?q={q}&query_by=description&query_by=label"
                    data = {"searches": []}
                    for collection in collectionlist:
                        data["searches"].append({"collection": collection})
                    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"))
                case unknown:
                    logger.error("Don't know what to do with collection %s", unknown)

            req.add_header("X-TYPESENSE-API-KEY", typesensetoken)
            with urllib.request.urlopen(req) as f:
                data = json.loads(f.read())
                hits = data.get("hits", [])
                for result in data.get("results", []):
                    hits.extend(result.get("hits", []))
                return list(filter(bool, map(self.extract, hits)))
        return {}


class PlaceExternalAutocomplete(TypeSense_ExternalAutocomplete):
    collections = ["prosnet-wikidata-place-index", "prosnet-geonames-place-index"]
    template = "apis_ontology/place_external_autocomplete_result.html"


class PersonExternalAutocomplete(TypeSense_ExternalAutocomplete):
    collections = "prosnet-wikidata-person-index"


class InstitutionExternalAutocomplete(TypeSense_ExternalAutocomplete):
    collections = "prosnet-wikidata-organization-index"
