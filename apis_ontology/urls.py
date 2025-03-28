from apis_acdhch_default_settings.urls import urlpatterns
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path

urlpatterns += [
    path("highlighter/", include("apis_highlighter.urls", namespace="highlighter")),
]

urlpatterns += staticfiles_urlpatterns()
urlpatterns += [
    path("", include("apis_acdhch_django_auditlog.urls")),
]
urlpatterns += [path("", include("django_interval.urls"))]
