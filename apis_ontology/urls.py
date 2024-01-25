from django.contrib import admin
from django.urls import include
from django.contrib.contenttypes.models import ContentType
from django.http import Http404
from django.urls import include, path, register_converter
from django.shortcuts import get_list_or_404
from django.views.generic import TemplateView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from apis_core.apis_entities.api_views import GetEntityGeneric
from apis_core.apis_entities.models import AbstractEntity
from apis_core.generic.views import List


class EntityToContenttypeConverter:
    """
    A converter that converts from a the name of an entity class
    (i.e. `person`) to the actual Django model class.
    """

    regex = r"\w+"

    def to_python(self, value):
        candiates = get_list_or_404(ContentType, model=value)
        candiates = list(filter(lambda ct: issubclass(ct.model_class(), AbstractEntity), candiates))
        if len(candiates) > 1:
            raise Http404("Multiple entities match the <%s> identifier" % value)
        return candiates[0]

    def to_url(self, value):
        return value


register_converter(EntityToContenttypeConverter, "entitytocontenttype")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("apis/entities/entity/<entitytocontenttype:contenttype>/list/", List.as_view(), name="generic_entities_list"),
    path("apis/", include("apis_core.urls", namespace="apis")),
    path("apis/collections/", include("apis_core.collections.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path(
        "entity/<int:pk>/", GetEntityGeneric.as_view(), name="GetEntityGenericRoot"
    ),
    path("", TemplateView.as_view(template_name="base.html")),
    path("highlighter/", include("apis_highlighter.urls", namespace="highlighter")),
]

urlpatterns += staticfiles_urlpatterns()
