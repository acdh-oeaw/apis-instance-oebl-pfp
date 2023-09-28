from django.contrib import admin
from reversion.admin import VersionAdmin

from .models import Title, Event, Institution, Person, Place, Work, Source


@admin.register(Title, Event, Institution, Person, Place, Work, Source)
class OeblAdmin(VersionAdmin):
    pass
