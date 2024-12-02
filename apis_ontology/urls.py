from django.urls import include, path
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from apis_acdhch_default_settings.urls import urlpatterns

urlpatterns += [
    path("highlighter/", include("apis_highlighter.urls", namespace="highlighter")),
]

urlpatterns += staticfiles_urlpatterns()
urlpatterns += [
    path("", include("apis_acdhch_django_auditlog.urls")),
]
