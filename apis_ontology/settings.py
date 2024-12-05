from apis_acdhch_default_settings.settings import *  # noqa: F403

DEBUG = True

INSTALLED_APPS += [  # noqa: F405
    "apis_highlighter",
    "django.contrib.postgres",
    "apis_core.collections",
    "apis_core.history",
]
INSTALLED_APPS.insert(0, "apis_core.relations")
INSTALLED_APPS.remove("apis_ontology")
INSTALLED_APPS.insert(0, "apis_ontology")
INSTALLED_APPS += ["auditlog", "apis_acdhch_django_auditlog"]

ROOT_URLCONF = "apis_ontology.urls"

CSRF_TRUSTED_ORIGINS = ["https://oebl-pnp.acdh-dev.oeaw.ac.at"]


LANGUAGE_CODE = "de"

MIDDLEWARE += [  # noqa: F405
    "auditlog.middleware.AuditlogMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
]

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
    "apis_ontology.renderer.CidocTTLRenderer",
    "apis_ontology.renderer.CidocXMLRenderer",
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
