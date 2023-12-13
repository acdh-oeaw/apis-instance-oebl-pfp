from django.contrib import admin
from reversion.admin import VersionAdmin

from .models import Title, Event, Institution, Person, Place, Work, Source, Text, Profession, ProfessionCategory


@admin.register(Title, Event, Institution, Person, Place, Work, Source, Text, Profession, ProfessionCategory)
class OeblAdmin(VersionAdmin):
    pass
