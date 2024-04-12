from apis_ontology.models import Person
from crispy_forms.layout import Layout, HTML, Column, Row
from apis_core.generic.forms import GenericModelForm
from crispy_forms.bootstrap import PrependedText
from apis_core.generic.forms.widgets import NewlineSeparatedListWidget


class PersonForm(GenericModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["external_resources"].widget = NewlineSeparatedListWidget(attrs={"class": "mb-1"})
        # Create a 'More details ...' details html element, so we can
        # put some of the less important form element inside and keep
        # the form clean
        more_details = Layout(
                HTML("<details><summary>More details</summary>"),
                "oebl_kurzinfo",
                "online_edition_haupttext",
                "nachrecherche",
                "soziale_herkunft",
                "verwandtschaft",
                "ausbildung_studium_studienreise",
                "berufstaetigkeit_lebenstationen",
                "mitgliedschaften_orden_auszeichnungen",
                "literatur",
                "berufe",
                "sterbedatum",
                "adelspraedikat",
                "uebersiedlung_emigration",
                "weitere_namensformen",
                "geburtsdatum",
                "sterbeort",
                "geburtsort",
                "religionen",
                "name_text",
                "pseudonyme",
                HTML("</details>"))

        all_other_fields = [f for f in self.fields if f not in more_details]

        # lets combine some of the form elements that belong together
        # into rows in columns and use bootstraps PrependedText to replace
        # the label of the form fields
        if {"forename", "surname"} <= set(all_other_fields):
            all_other_fields.remove("surname")
            all_other_fields.remove("forename")
            row = Row(
                    Column(PrependedText("forename", "Vorname")),
                    Column(PrependedText("surname", self.fields["surname"].label)))
            self.fields["forename"].label = self.fields["surname"].label = False
            all_other_fields.insert(0, row)
        if {"start_date_written", "end_date_written"} <= set(all_other_fields):
            all_other_fields.remove("start_date_written")
            all_other_fields.remove("end_date_written")
            # if we are dealing with a person, we are changing the label
            startlabel = "Geboren am" if self.Meta.model == Person else self.fields["start_date_written"].label
            endlabel = "Gestorben am" if self.Meta.model == Person else self.fields["end_date_written"].label
            row = Row(
                    Column(PrependedText("start_date_written", startlabel)),
                    Column(PrependedText("end_date_written", endlabel)))
            self.fields["start_date_written"].label = self.fields["end_date_written"].label = False
            all_other_fields.insert(1, row)
        if {"gender", "title"} <= set(all_other_fields):
            all_other_fields.remove("gender")
            all_other_fields.remove("title")
            all_other_fields.insert(2, Row(Column("gender"), Column("title")))
        if {"profession", "professioncategory"} <= set(all_other_fields):
            all_other_fields.remove("profession")
            all_other_fields.remove("professioncategory")
            all_other_fields.insert(3, Row(Column("profession"), Column("professioncategory")))
        if {"profession_father", "profession_mother"} <= set(all_other_fields):
            all_other_fields.remove("profession_father")
            all_other_fields.remove("profession_mother")
            all_other_fields.insert(4, Row(Column("profession_father"), Column("profession_mother")))
        if {"notes"} <= set(all_other_fields):
            all_other_fields.remove("notes")
            all_other_fields.insert(5, "notes")

        self.helper.layout = Layout(*all_other_fields, more_details)
