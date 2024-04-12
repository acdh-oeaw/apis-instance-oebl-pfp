import logging
import os
from django.db.models.functions import Collate
from django.conf import settings

from apis_core.utils.autocomplete import ExternalAutocomplete, TypeSenseAutocompleteAdapter, LobidAutocompleteAdapter

from .models import Person

logger = logging.getLogger(__name__)

DB_COLLATION = ("binary" if "sqlite" in settings.DATABASES["default"]["ENGINE"] else "en-x-icu")


def PersonListViewQueryset(*args):
    return Person.objects.all().order_by(Collate("surname", DB_COLLATION), Collate("forename", DB_COLLATION))


class PlaceExternalAutocomplete(ExternalAutocomplete):
    adapters = [
            TypeSenseAutocompleteAdapter(
                collections=["prosnet-wikidata-place-index", "prosnet-geonames-place-index"],
                template="apis_ontology/place_external_autocomplete_result.html",
                token=os.getenv("TYPESENSE_TOKEN", None),
                server=os.getenv("TYPESENSE_SERVER", None)),
            LobidAutocompleteAdapter(params={"filter": "type:PlaceOrGeographicName", "format": "json:preferredName"})
            ]


class PersonExternalAutocomplete(ExternalAutocomplete):
    adapters = [
            TypeSenseAutocompleteAdapter(collections="prosnet-wikidata-person-index",
                                         token=os.getenv("TYPESENSE_TOKEN", None),
                                         server=os.getenv("TYPESENSE_SERVER", None)),
            LobidAutocompleteAdapter(params={"filter": "type:Person", "format": "json:preferredName,professionOrOccupation"})
            ]


class InstitutionExternalAutocomplete(ExternalAutocomplete):
    adapters = [
            TypeSenseAutocompleteAdapter(collections="prosnet-wikidata-organization-index",
                                         token=os.getenv("TYPESENSE_TOKEN", None),
                                         server=os.getenv("TYPESENSE_SERVER", None)),
            LobidAutocompleteAdapter(params={"filter": "type:CorporateBody", "format": "json:preferredName"})
            ]
