from django.contrib import admin
from reversion.admin import VersionAdmin

from .models import Title, Event, Institution, Person, Place, Work, Source, Text


@admin.register(Title, Event, Institution, Person, Place, Work, Source, Text)
class OeblAdmin(VersionAdmin):
    pass
