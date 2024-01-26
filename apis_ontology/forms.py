from django.forms import CharField, Textarea
from apis_ontology.models import Institution, Text, Event, Person, Place, Work
from crispy_forms.layout import Layout, HTML
from apis_core.generic.forms import GenericModelForm


class EntityForm(GenericModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        text_details = Layout(HTML("<details><summary>Texts</summary>"))
        for ttypenr, ttype in Text.TEXTTYPE_CHOICES:
            self.fields[ttype] = CharField(required=False, widget=Textarea)
            if instance := kwargs.get("instance"):
                try:
                    text = instance.texts.get(kind=ttype)
                    self.fields[ttype].initial = text.text
                except Text.DoesNotExist:
                    pass
            text_details.append(ttype)
        text_details.append(HTML("</details>"))

        all_other_fields = [f for f in self.fields if f not in text_details]
        self.helper.layout = Layout(*all_other_fields, text_details)

    def save(self, *args, **kwargs):
        obj = super().save(*args, **kwargs)
        for ttypenr, ttype in Text.TEXTTYPE_CHOICES:
            if self.cleaned_data[ttype]:
                text, created = obj.texts.get_or_create(kind=ttype)
                text.text = self.cleaned_data[ttype]
                text.save()
        return obj


class InstitutionForm(EntityForm):
    class Meta:
        model = Institution
        fields = "__all__"


class EventForm(EntityForm):
    class Meta:
        model = Event
        fields = "__all__"


class PersonForm(EntityForm):
    field_order = ["first_name", "name", "start_date_written", "end_date_written", "gender", "profession", "title",]

    class Meta:
        model = Person
        fields = "__all__"


class PlaceForm(EntityForm):
    class Meta:
        model = Place
        fields = "__all__"


class WorkForm(EntityForm):
    class Meta:
        model = Work
        fields = "__all__"
