from django.forms import CharField, Textarea
from apis_ontology.models import Person, Text
from crispy_forms.layout import Layout, HTML, Column, Row
from apis_core.generic.forms import GenericModelForm
from crispy_forms.bootstrap import PrependedText

TEXTTYPE_CHOICES_MAIN = ["ÖBL Haupttext", "ÖBL Werkverzeichnis"]


class PersonForm(GenericModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Create a 'More details ...' details html element, so we can
        # put some of the less important form element inside and keep
        # the form clean
        more_details = Layout(HTML("<details><summary>More details</summary>"))
        for ttypenr, ttype in Text.TEXTTYPE_CHOICES:
            self.fields[ttype] = CharField(required=False, widget=Textarea)
            if instance := kwargs.get("instance"):
                try:
                    text = instance.texts.get(kind=ttype)
                    self.fields[ttype].initial = text.text
                except Text.DoesNotExist:
                    pass
            if ttype not in TEXTTYPE_CHOICES_MAIN:
                more_details.append(ttype)
        more_details.extend(["notes", "status", "review", "published"])
        more_details.append(HTML("</details>"))

        all_other_fields = [f for f in self.fields if f not in more_details]

        # lets combine some of the form elements that belong together
        # into rows in columns and use bootstraps PrependedText to replace
        # the label of the form fields
        if {"first_name", "surname"} <= set(all_other_fields):
            all_other_fields.remove("surname")
            all_other_fields.remove("first_name")
            row = Row(
                    Column(PrependedText("first_name", self.fields["first_name"].label)),
                    Column(PrependedText("surname", self.fields["surname"].label)))
            self.fields["first_name"].label = self.fields["surname"].label = False
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

        self.helper.layout = Layout(*all_other_fields, more_details)

    def save(self, *args, **kwargs):
        obj = super().save(*args, **kwargs)
        for ttypenr, ttype in Text.TEXTTYPE_CHOICES:
            if self.cleaned_data[ttype]:
                text, created = obj.texts.get_or_create(kind=ttype)
                text.text = self.cleaned_data[ttype]
                text.save()
        return obj
