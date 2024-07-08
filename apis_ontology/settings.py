from apis_acdhch_default_settings.settings import *

DEBUG = True

INSTALLED_APPS += ["apis_highlighter", "django.contrib.postgres", "apis_core.collections", "apis_core.history"]
INSTALLED_APPS.remove("apis_ontology")
INSTALLED_APPS.insert(0, "apis_ontology")
INSTALLED_APPS += ["django_acdhch_functions"]
INSTALLED_APPS += ["auditlog"]

ROOT_URLCONF = 'apis_ontology.urls'

PROJECT_DEFAULT_MD = {}

CSRF_TRUSTED_ORIGINS = ["https://oebl-pnp.acdh-dev.oeaw.ac.at"]


APIS_LIST_LINKS_TO_EDIT = True


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    'formatters': {
       'verbose': {
           'format': '%(asctime)s %(name)-6s %(levelname)-8s %(message)s',
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

MIDDLEWARE += ['auditlog.middleware.AuditlogMiddleware']

APIS_BASE_URI = "https://oebl-pfp.acdh-ch-dev.oeaw.ac.at"
