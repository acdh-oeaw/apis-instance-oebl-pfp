from django.contrib import admin

from .models import Title, Event, Institution, Person, Place, Work, Source, Profession, ProfessionCategory


@admin.register(Title, Event, Institution, Person, Place, Work, Source, Profession, ProfessionCategory)
class OeblAdmin(admin.ModelAdmin):
    pass
