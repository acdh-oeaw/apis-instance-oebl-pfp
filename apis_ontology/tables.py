import django_tables2 as tables
from django_tables2.utils import A
from .models import Person


class PersonTable(tables.Table):
    class Meta:
        model = Person
        fields = ["name", "first_name", "start_date", "end_date"]
        row_attrs = {"title": lambda record: record.oebl_kurzinfo.text}


    name = tables.LinkColumn("apis:apis_entities:generic_entities_edit_view", args=[A("self_contenttype.name"), A("pk")], empty_values=[],)
    first_name = tables.LinkColumn("apis:apis_entities:generic_entities_edit_view", args=[A("self_contenttype.name"), A("pk")], empty_values=[],)

    def render_name(self, record):
        return record.name or "No name"

    def render_start_date(self, record):
        if record.start_date:
            return record.start_date.year
        return "-"

    def render_end_date(self, record):
        if record.end_date:
            return record.end_date.year
        return "-"
