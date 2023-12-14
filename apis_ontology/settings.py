import os
from apis_acdhch_default_settings.settings import *


SECRET_KEY = os.environ.get("SECRET_KEY")
DEBUG = True

# Application definition

INSTALLED_APPS = [
    "apis_override_select2js",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'apis_ontology',
    'apis_core.core',
    'apis_core.apis_metainfo',
    'apis_core.apis_vocabularies',
    'apis_core.apis_relations',
    'apis_core.apis_entities',
    'apis_core.apis_labels',
    "reversion",
    # ui stuff
    "crispy_forms",
    "django_filters",
    "django_tables2",
    "dal",
    "dal_select2",
    # api
    "rest_framework",
    "rest_framework.authtoken",
    # for swagger ui generation
    "drf_spectacular",
    # highlighter
    "apis_highlighter",
]

ROOT_URLCONF = 'apis_ontology.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

STATIC_URL = '/static/'
STATIC_ROOT = '/tmp/staticfiles'

REDMINE_ID = ""


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

CRISPY_TEMPLATE_PACK = "bootstrap4"
DJANGO_TABLES2_TEMPLATE = "django_tables2/bootstrap4.html"

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
