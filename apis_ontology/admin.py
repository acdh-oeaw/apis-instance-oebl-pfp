from django.contrib import admin
from reversion.admin import VersionAdmin

from .models import Title, Event, Institution, Person, Place, Work


@admin.register(Title, Event, Institution, Person, Place, Work)
class OeblAdmin(VersionAdmin):
    pass
