import django_tables2 as tables
from apis_core.apis_entities.tables import AbstractEntityTable
from django_tables2.utils import A

from apis_core.generic.tables import GenericTable
from .models import Person
from apis_core.relations.tables import RelationsListTable


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


class PersonTable(AbstractEntityTable):
    class Meta:
        model = Person
        fields = ["surname", "forename", "start_date", "end_date"]
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

    def render_surname(self, record):
        return record.surname or "No name"

    def render_start_date(self, record):
        if record.start_date:
            return record.start_date.year
        return "-"

    def render_end_date(self, record):
        if record.end_date:
            return record.end_date.year
        return "-"


class RelationsTableMixin(GenericTable):
    start = tables.Column(accessor="start_date_written", order_by="start_date")
    end = tables.Column(accessor="end_date_written", order_by="end_date")


class OEBLBaseEntityPersonRelationsTable(RelationsListTable, RelationsTableMixin):
    class Meta(RelationsListTable.Meta):
        sequence = ["start", "end"] + list(RelationsListTable.Meta.sequence)


class OEBLBaseEntityInstitutionRelationsTable(RelationsListTable, RelationsTableMixin):
    class Meta(RelationsListTable.Meta):
        sequence = ["start", "end"] + list(RelationsListTable.Meta.sequence)


class OEBLBaseEntityPlaceRelationsTable(RelationsListTable, RelationsTableMixin):
    class Meta(RelationsListTable.Meta):
        sequence = ["start", "end"] + list(RelationsListTable.Meta.sequence)


class OEBLBaseEntityWorkRelationsTable(RelationsListTable, RelationsTableMixin):
    class Meta(RelationsListTable.Meta):
        sequence = ["start", "end"] + list(RelationsListTable.Meta.sequence)


class OEBLBaseEntityEventRelationsTable(RelationsListTable, RelationsTableMixin):
    class Meta(RelationsListTable.Meta):
        sequence = ["start", "end"] + list(RelationsListTable.Meta.sequence)


class OEBLBaseEntityDenominationRelationsTable(RelationsListTable, RelationsTableMixin):
    class Meta(RelationsListTable.Meta):
        sequence = ["start", "end"] + list(RelationsListTable.Meta.sequence)
