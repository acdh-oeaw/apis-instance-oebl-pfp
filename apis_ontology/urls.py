from apis_acdhch_default_settings.urls import urlpatterns
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path

from apis_ontology.api_views import ListRelationTypesAPIView

urlpatterns += [
    path("highlighter/", include("apis_highlighter.urls", namespace="highlighter")),
]

urlpatterns += staticfiles_urlpatterns()
urlpatterns += [path("", include("django_interval.urls"))]

urlpatterns += [path("apis/api/listrelationtypes", ListRelationTypesAPIView.as_view())]
