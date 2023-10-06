import os
# from apis_acdhch_default_settings.settings import *
import dj_database_url


SECRET_KEY = os.environ.get("SECRET_KEY")
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
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
    "charts",
    # api
    "rest_framework",
    "rest_framework.authtoken",
    # for swagger ui generation
    "drf_spectacular",
    # highlighter
    "apis_highlighter",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allow_cidr.middleware.AllowCIDRMiddleware',
    "reversion.middleware.RevisionMiddleware",
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
                # we need this for listing entities in the base template
                "apis_core.context_processors.custom_context_processors.list_entities",
                # we need this for accessing `basetemplate`
                "apis_core.context_processors.custom_context_processors.list_apis_settings",
            ],
        },
    },
]

DATABASES = {"default": dj_database_url.config(conn_max_age=600)}

STATIC_URL = '/static/'
STATIC_ROOT = '/tmp/staticfiles'

REDMINE_ID = ""

ALLOWED_CIDR_NETS = ["10.0.0.0/8", "127.0.0.0/8"]

PROJECT_DEFAULT_MD = {}

ALLOWED_HOSTS = ["oebl-pnp.acdh-dev.oeaw.ac.at", "localhost"]

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


APIS_ENTITIES = {
        "Event": {
            "form": event_form
        },
        "Institution": {
            "form": institution_form
        },
        "Person": {
            "form": person_form
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
