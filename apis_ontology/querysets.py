import logging
import os
from django.db.models.functions import Collate
from django.conf import settings
from django.db.models import Value
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Case, When, FloatField
from django.db.models.functions import Greatest, Length

from apis_core.utils.autocomplete import ExternalAutocomplete, TypeSenseAutocompleteAdapter, LobidAutocompleteAdapter

from .models import Person

logger = logging.getLogger(__name__)

DB_COLLATION = ("binary" if "sqlite" in settings.DATABASES["default"]["ENGINE"] else "en-x-icu")


def PersonListViewQueryset(*args):
    return Person.objects.all().order_by(Collate("surname", DB_COLLATION), Collate("forename", DB_COLLATION))


def InstitutionAutocompleteQueryset(model, query):
    # We use two ranking approaches:
    # we check if the query is contained in the result, if so we
    # calculate a rank based on the difference in length
    # if the query is *not* contained in the result, we
    # use the trigram similarity score
    insitutions = model.objects.annotate(
            icontains_rank=Case(
                When(name__unaccent__icontains=query, then=Value(10.0) / (Length("name", output_field=FloatField()) - Value(len(query)) + Value(1)))
            ),
            similarity=TrigramSimilarity("name", query)
            ).annotate(rank=Greatest("icontains_rank", "similarity")).order_by("-rank")
    return insitutions


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
