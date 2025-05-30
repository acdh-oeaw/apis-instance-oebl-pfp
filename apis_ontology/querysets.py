import logging
import os

from django.conf import settings
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Case, FloatField, Value, When
from django.db.models.functions import Collate, Greatest, Length

from apis_core.utils.autocomplete import (
    ExternalAutocomplete,
    LobidAutocompleteAdapter,
    TypeSenseAutocompleteAdapter,
)

from .models import Institution, Person, Place

logger = logging.getLogger(__name__)

DB_COLLATION = (
    "binary" if "sqlite" in settings.DATABASES["default"]["ENGINE"] else "en-x-icu"
)


def PersonListViewQueryset(*args):
    return Person.objects.all().order_by(
        Collate("surname", DB_COLLATION), Collate("forename", DB_COLLATION)
    )


def InstitutionViewSetQueryset(*args):
    return Institution.objects.all().distinct()


def PersonViewSetQueryset(*args):
    return Person.objects.all().distinct()


def PlaceViewSetQueryset(*args):
    return Place.objects.all().distinct()


def InstitutionAutocompleteQueryset(model, query):
    # We use two ranking approaches:
    # we check if the query is contained in the result, if so we
    # calculate a rank based on the difference in length
    # if the query is *not* contained in the result, we
    # use the trigram similarity score
    if query.startswith("http"):
        return model.objects.none()
    insitutions = (
        model.objects.annotate(
            icontains_rank=Case(
                When(
                    label__unaccent__icontains=query,
                    then=Value(10.0)
                    / (
                        Length("label", output_field=FloatField())
                        - Value(len(query))
                        + Value(1)
                    ),
                )
            ),
            similarity=TrigramSimilarity("label", query),
        )
        .annotate(rank=Greatest("icontains_rank", "similarity"))
        .order_by("-rank")
    )
    return insitutions


class PlaceExternalAutocomplete(ExternalAutocomplete):
    adapters = [
        TypeSenseAutocompleteAdapter(
            collections=[
                "prosnet-wikidata-place-index",
                "prosnet-geonames-place-index",
            ],
            template="apis_ontology/place_external_autocomplete_result.html",
            token=os.getenv("TYPESENSE_TOKEN", None),
            server=os.getenv("TYPESENSE_SERVER", None),
        ),
        LobidAutocompleteAdapter(
            params={
                "filter": "type:PlaceOrGeographicName",
                "format": "json:preferredName",
            }
        ),
    ]


class PersonExternalAutocomplete(ExternalAutocomplete):
    adapters = [
        TypeSenseAutocompleteAdapter(
            collections="prosnet-wikidata-person-index",
            token=os.getenv("TYPESENSE_TOKEN", None),
            server=os.getenv("TYPESENSE_SERVER", None),
        ),
        LobidAutocompleteAdapter(
            params={
                "filter": "type:Person",
                "format": "json:preferredName,professionOrOccupation",
            }
        ),
    ]


class InstitutionExternalAutocomplete(ExternalAutocomplete):
    adapters = [
        TypeSenseAutocompleteAdapter(
            collections="prosnet-wikidata-organization-index",
            token=os.getenv("TYPESENSE_TOKEN", None),
            server=os.getenv("TYPESENSE_SERVER", None),
        ),
        LobidAutocompleteAdapter(
            params={"filter": "type:CorporateBody", "format": "json:preferredName"}
        ),
    ]
