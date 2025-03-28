from django.contrib import admin

from .models import (
    Event,
    Institution,
    Person,
    Place,
    Profession,
    ProfessionCategory,
    Source,
    Title,
    Work,
)


@admin.register(
    Title,
    Event,
    Institution,
    Person,
    Place,
    Work,
    Source,
    Profession,
    ProfessionCategory,
)
class OeblAdmin(admin.ModelAdmin):
    pass
