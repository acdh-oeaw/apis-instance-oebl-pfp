import django_filters
from apis_core.generic.filtersets import GenericFilterSet, GenericFilterSetForm

from apis_core.utils.filtermethods import (
    related_entity_name,
)
from apis_core.apis_relations.models import Property
from apis_core.collections.models import SkosCollection, SkosCollectionContentObject
from django.contrib.contenttypes.models import ContentType
from .filters import trigram_search_filter

ABSTRACT_ENTITY_FILTERS_EXCLUDE = [
    "self_contenttype",
    "review",
    "start_date",
    "start_start_date",
    "start_end_date",
    "end_date",
    "end_start_date",
    "end_end_date",
    "notes",
    "text",
    "published",
    "status",
    "references",
]
HELP_TEXT = "Search for similar words in <em>first_name</em> & <em>name</em> based on <a href='https://www.postgresql.org/docs/current/pgtrgm.html#PGTRGM-CONCEPTS'>trigram matching</a>."


def related_property(queryset, name, value):
    p = Property.objects.get(name=value)
    queryset = queryset.filter(triple_set_from_subj__prop=p).distinct()
    return queryset


def collection_method(queryset, name, value):
    if value:
        content_type = ContentType.objects.get_for_model(queryset.model)
        scco = SkosCollectionContentObject.objects.filter(content_type=content_type, collection__in=value)
        return queryset.filter(id__in=scco)
    return queryset


class PersonFilterSetForm(GenericFilterSetForm):
    columns_exclude = ABSTRACT_ENTITY_FILTERS_EXCLUDE


class PersonFilterSet(GenericFilterSet):
    related_entity_name = django_filters.CharFilter(
        method=related_entity_name, label="Related entity"
    )
    related_property = django_filters.ModelChoiceFilter(
        queryset=Property.objects.all().order_by('name'),
        label="Related Property",
        method=related_property,
    )
    collection = django_filters.ModelMultipleChoiceFilter(
        queryset=SkosCollection.objects.all().order_by("name"),
        label="Collections",
        method=collection_method,
    )
    search = django_filters.CharFilter(
            method=trigram_search_filter,
            label="Search",
            help_text=HELP_TEXT)

    class Meta:
        form = PersonFilterSetForm
        exclude = ABSTRACT_ENTITY_FILTERS_EXCLUDE

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters.move_to_end("first_name", False)
        self.filters.move_to_end("collection", False)
        self.filters.move_to_end("search", False)
