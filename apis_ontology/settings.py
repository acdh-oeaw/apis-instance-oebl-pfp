import os

from apis_acdhch_default_settings.settings import *  # noqa: F403

DEBUG = True

INSTALLED_APPS += [  # noqa: F405
    "apis_highlighter",
    "django.contrib.postgres",
]
INSTALLED_APPS.remove("apis_ontology")
INSTALLED_APPS.insert(0, "apis_ontology")
INSTALLED_APPS += ["django_json_editor_field"]
INSTALLED_APPS += ["apis_bibsonomy"]
INSTALLED_APPS += ["django_interval"]

ROOT_URLCONF = "apis_ontology.urls"

CSRF_TRUSTED_ORIGINS = ["https://oebl-pnp.acdh-dev.oeaw.ac.at"]


LANGUAGE_CODE = "de"

ALLOWED_HOSTS.append("oebl-pnp-auto-deploy.apis-oebl-pnp.svc.cluster.local")  # noqa: F405


REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
    "apis_core.generic.renderers.CidocTTLRenderer",
    "apis_core.generic.renderers.CidocXMLRenderer",
]
# this is a workaround to disable pagintation in the relations
# listing on the entities pages
APIS_ENTITIES = {
    "Event": {"relations_per_page": 1000},
    "Institution": {"relations_per_page": 1000},
    "Person": {"relations_per_page": 1000},
    "Place": {"relations_per_page": 1000},
    "Work": {"relations_per_page": 1000},
    "Denomination": {"relations_per_page": 1000},
}

DEFAULT_HIGHLIGTHER_PROJECT = 28

APIS_BIBSONOMY = [
    {
        "type": "zotero",
        "url": "https://api.zotero.org",
        "user": os.environ.get("APIS_BIBSONOMY_USER"),
        "API key": os.environ.get("APIS_BIBSONOMY_PASSWORD"),
        "group": "5867571",
    }
]

APIS_RDF_NAMESPACE_PREFIX = "oebl"
