import django_tables2 as tables
from apis_core.apis_entities.tables import AbstractEntityTable
from django_tables2.utils import A
from .models import Person


class PersonTable(AbstractEntityTable):
    class Meta:
        model = Person
        fields = ["surname", "first_name", "start_date", "end_date"]
        exclude = ["desc"]
        row_attrs = {"title": lambda record: record.oebl_kurzinfo.text if record.oebl_kurzinfo else None }


    surname = tables.LinkColumn("apis:apis_entities:generic_entities_edit_view", args=[A("self_contenttype.name"), A("pk")], empty_values=[],)
    first_name = tables.LinkColumn("apis:apis_entities:generic_entities_edit_view", args=[A("self_contenttype.name"), A("pk")], empty_values=[],)

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
