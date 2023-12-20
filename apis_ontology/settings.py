import os
from apis_acdhch_default_settings.settings import *

DEBUG = True

INSTALLED_APPS += ["apis_highlighter", "django.contrib.postgres"]
INSTALLED_APPS.remove("apis_ontology")
INSTALLED_APPS.insert(0, "apis_ontology")

ROOT_URLCONF = 'apis_ontology.urls'

PROJECT_DEFAULT_MD = {}

CSRF_TRUSTED_ORIGINS = ["https://oebl-pnp.acdh-dev.oeaw.ac.at"]


def institution_form(*args, **kwargs):
    from apis_ontology.forms import InstitutionForm
    return InstitutionForm(*args, **kwargs)


def event_form(*args, **kwargs):
    from apis_ontology.forms import EventForm
    return EventForm(*args, **kwargs)


def person_form(*args, **kwargs):
    from apis_ontology.forms import PersonForm
    return PersonForm(*args, **kwargs)


def place_form(*args, **kwargs):
    from apis_ontology.forms import PlaceForm
    return PlaceForm(*args, **kwargs)


def work_form(*args, **kwargs):
    from apis_ontology.forms import WorkForm
    return WorkForm(*args, **kwargs)

from .filters import name_first_name_filter


APIS_ENTITIES = {
        "Event": {
            "form": event_form
        },
        "Institution": {
            "form": institution_form
        },
        "Person": {
            "form": person_form,
            "list_filters": {
                "name": {"method": name_first_name_filter, "label": "Name or first name"},
            },
        },
        "Place": {
            "form": place_form
        },
        "Work": {
            "form": work_form
        },
}

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.DjangoObjectPermissions",
    ),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

APIS_API_ID_WRITABLE = True

USE_TZ = True

APIS_LIST_LINKS_TO_EDIT = True
