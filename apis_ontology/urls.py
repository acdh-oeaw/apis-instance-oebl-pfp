from django.urls import include
from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from apis_core.apis_entities.api_views import GetEntityGeneric

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("apis/", include("apis_core.urls", namespace="apis")),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path(
        "entity/<int:pk>/", GetEntityGeneric.as_view(), name="GetEntityGenericRoot"
    ),
    path("", TemplateView.as_view(template_name="base.html")),
]

urlpatterns += staticfiles_urlpatterns()
