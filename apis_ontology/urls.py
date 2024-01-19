from django.urls import include
from django.urls import path
from django.views.generic import TemplateView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from apis_core.apis_entities.api_views import GetEntityGeneric

urlpatterns = [
    path("apis/", include("apis_core.urls", namespace="apis")),
    path("accounts/", include("django.contrib.auth.urls")),
    path(
        "entity/<int:pk>/", GetEntityGeneric.as_view(), name="GetEntityGenericRoot"
    ),
    path("", TemplateView.as_view(template_name="base.html")),
    path("highlighter/", include("apis_highlighter.urls", namespace="highlighter")),
]

urlpatterns += staticfiles_urlpatterns()
