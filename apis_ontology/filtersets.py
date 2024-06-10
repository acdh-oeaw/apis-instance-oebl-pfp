import re
import django_filters
from django.contrib.postgres.search import TrigramWordSimilarity
from django.db.models.functions import Greatest
from django.db import models

from apis_core.apis_entities.filtersets import AbstractEntityFilterSet
from apis_core.collections.models import SkosCollection, SkosCollectionContentObject
from django.contrib.contenttypes.models import ContentType

PERSON_HELP_TEXT = "Search for similar words in <em>forename</em> & <em>name</em> based on <a href='https://www.postgresql.org/docs/current/pgtrgm.html#PGTRGM-CONCEPTS'>trigram matching</a>."
HELP_TEXT = "Search for similar words in <em>name</em> based on <a href='https://www.postgresql.org/docs/current/pgtrgm.html#PGTRGM-CONCEPTS'>trigram matching</a>."


PATTERN = re.compile(r'''((?:[^ "']|"[^"]*"|'[^']*')+)''')

#########
# helpers
#########


def remove_quotes(token):
    return token.strip('"')


################
# filter methods
################


def trigram_search_filter_person(queryset, name, value):
    return trigram_search_filter(queryset, ["surname", "forename"], value)


def trigram_search_filter_institution(queryset, name, value):
    return trigram_search_filter(queryset, ["name"], value)


def trigram_search_filter_place(queryset, name, value):
    return trigram_search_filter(queryset, ["name"], value)


def trigram_search_filter(queryset, fields, value):
    tokens = PATTERN.split(value)
    tokens = list(filter(str.strip, tokens))
    tokens = set(list(map(remove_quotes, tokens)) + [value])
    trig_vector_list = []
    for token in tokens:
        for field in fields:
            trig_vector_list.append(TrigramWordSimilarity(token, field))
    trig_vector = Greatest(*trig_vector_list, None)
    return queryset.annotate(similarity=trig_vector).filter(similarity__gt=0.4).order_by("-similarity")


def collection_method(queryset, name, value):
    if value:
        content_type = ContentType.objects.get_for_model(queryset.model)
        scco = SkosCollectionContentObject.objects.filter(content_type=content_type, collection__in=value).values("object_id")
        return queryset.filter(id__in=scco)
    return queryset


###################
# custom filtersets
###################
class LegacyStuffMixinFilterSet(AbstractEntityFilterSet):
    class Meta(AbstractEntityFilterSet.Meta):
        filter_overrides = {
             models.CharField: {
                 'filter_class': django_filters.CharFilter,
                 'extra': lambda f: {
                     'lookup_expr': 'icontains',
                 },
             },
        }


class PersonFilterSet(LegacyStuffMixinFilterSet):
    collection = django_filters.ModelMultipleChoiceFilter(
        queryset=SkosCollection.objects.all().order_by("name"),
        label="Collections",
        method=collection_method,
    )
    search = django_filters.CharFilter(
            method=trigram_search_filter_person,
            label="Search",
            help_text=PERSON_HELP_TEXT)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters.move_to_end("forename", False)
        self.filters.move_to_end("collection", False)
        self.filters.move_to_end("search", False)


class InstitutionFilterSet(LegacyStuffMixinFilterSet):
    search = django_filters.CharFilter(
            method=trigram_search_filter_institution,
            label="Search",
            help_text=HELP_TEXT)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters.move_to_end("search", False)


class PlaceFilterSet(LegacyStuffMixinFilterSet):
    search = django_filters.CharFilter(
            method=trigram_search_filter_place,
            label="Search",
            help_text=HELP_TEXT)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters.move_to_end("search", False)
