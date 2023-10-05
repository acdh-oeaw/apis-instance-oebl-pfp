from django.forms import ModelForm, CharField, Textarea
from apis_ontology.models import Institution, Text, Event, Person, Place, Work
from crispy_forms.helper import FormHelper



class EntityForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for ttypenr, ttype in Text.TEXTTYPE_CHOICES:
            self.fields[ttype] = CharField(required=False, widget=Textarea)
            if instance := kwargs.get("instance"):
                try:
                    text = instance.texts.get(kind=ttype)
                    self.fields[ttype].initial = text.text
                except Text.DoesNotExist:
                    pass

        self.helper = FormHelper()
        self.helper.form_tag = False

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
