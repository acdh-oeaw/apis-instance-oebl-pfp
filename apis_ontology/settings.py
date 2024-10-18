from apis_acdhch_default_settings.settings import *  # noqa: F403

DEBUG = True

INSTALLED_APPS += [  # noqa: F405
    "apis_highlighter",
    "django.contrib.postgres",
    "apis_core.collections",
    "apis_core.history",
]
INSTALLED_APPS.remove("apis_ontology")
INSTALLED_APPS.insert(0, "apis_ontology")
INSTALLED_APPS += ["auditlog"]

ROOT_URLCONF = "apis_ontology.urls"

CSRF_TRUSTED_ORIGINS = ["https://oebl-pnp.acdh-dev.oeaw.ac.at"]


APIS_LIST_LINKS_TO_EDIT = True


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s %(name)-6s %(levelname)-8s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
}

LOG_LIST_NOSTAFF_EXCLUDE_APP_LABELS = ["reversion", "admin", "sessions", "auth"]

LANGUAGE_CODE = "de"

MIDDLEWARE += [  # noqa: F405
    "auditlog.middleware.AuditlogMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
]

APIS_BASE_URI = "https://oebl-pfp.acdh-ch-dev.oeaw.ac.at"

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
