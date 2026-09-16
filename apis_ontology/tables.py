import django_tables2 as tables
from django.db.models import Count

from apis_core.generic.tables import CustomTemplateColumn, GenericTable
from apis_core.relations.tables import RelationsListTable

from .models import Person


class BiographienLinkColumn(tables.TemplateColumn):
    def __init__(self, *args, **kwargs):
        template_name = "columns/biographien_link.html"
        super().__init__(
            template_name=template_name,
            orderable=False,
            exclude_from_export=True,
            verbose_name="",
            empty_values=(),
            *args,
            **kwargs,
        )


class BibsonomyColumn(CustomTemplateColumn):
    template_name = "columns/bibsonomy.html"


class PersonTable(GenericTable):
    class Meta:
        model = Person
        fields = ["surname", "forename", "start", "end"]
        exclude = ["desc"]
        row_attrs = {"title": lambda record: record.oebl_kurzinfo}

    surname = tables.Column(
        linkify=lambda record: record.get_edit_url(),
        empty_values=[],
    )
    forename = tables.Column(
        linkify=lambda record: record.get_edit_url(),
        empty_values=[],
    )
    biographien_link = BiographienLinkColumn()
    start = tables.Column(order_by="start_date_sort")
    end = tables.Column(order_by="end_date_sort")

    def render_surname(self, record):
        return record.surname or "No name"


class OEBLBaseEntityRelationsTable(RelationsListTable):
    start = tables.Column(accessor="start", order_by="start_date_sort")
    end = tables.Column(accessor="end", order_by="end_date_sort")
    notes = tables.Column()
    bibsonomy = BibsonomyColumn()

    class Meta(RelationsListTable.Meta):
        sequence = (
            ["start", "end"]
            + list(RelationsListTable.Meta.sequence)[:-4]
            + ["notes"]
            + list(RelationsListTable.Meta.sequence)[-4:]
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.columns["notes"].column.attrs = {
            "td": {
                "style": "max-width:30vw; word-wrap:break-word; overflow-wrap:break-word; white-space:normal;"
            }
        }


class ProfessionTable(GenericTable):
    count = tables.Column(empty_values=())

    def order_count(self, queryset, is_descending=False):
        queryset = queryset.annotate(person_count=Count("person"))
        queryset = queryset.order_by(("-" if is_descending else "") + "person_count")
        return queryset, True

    def render_count(self, value, record):
        return record.person_set.count()
