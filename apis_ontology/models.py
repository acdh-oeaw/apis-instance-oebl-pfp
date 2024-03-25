import reversion
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from apis_core.apis_entities.models import AbstractEntity
from apis_core.core.models import LegacyDateMixin
from apis_core.utils.helpers import create_object_from_uri
from apis_core.generic.abc import GenericModel


class LegacyStuffMixin(models.Model):
    review = review = models.BooleanField(default=False, help_text="Should be set to True, if the data record holds up quality standards.")
    status = models.CharField(max_length=100, blank=True)
    references = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    published = models.BooleanField(default=False)

    texts = GenericRelation("Text")
    sources = GenericRelation("Source")

    class Meta:
        abstract = True

    @classmethod
    def get_or_create_uri(cls, uri):
        print(f"using custom get_or_create_uri with {uri}")
        return create_object_from_uri(uri, cls) or cls.objects.get(pk=uri)

    @property
    def uri(self):
        contenttype = ContentType.objects.get_for_model(self)
        uri = reverse("apis_core:generic:detail", args=[contenttype, self.pk])
        return uri


@reversion.register
class Source(GenericModel, models.Model):
    orig_filename = models.CharField(max_length=255, blank=True)
    indexed = models.BooleanField(default=False)
    pubinfo = models.CharField(max_length=400, blank=True)
    author = models.CharField(max_length=255, blank=True)
    orig_id = models.PositiveIntegerField(blank=True, null=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        if retstr := self.orig_filename:
            if self.author:
                retstr += f" stored by {self.author}"
            return retstr
        return f"(ID: {self.id})".format(self.id)


@reversion.register
class Title(GenericModel, models.Model):
    name = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name


@reversion.register
class ProfessionCategory(GenericModel, models.Model):
    name = models.CharField(max_length=255, blank=False)

    def __str__(self):
        return self.name


@reversion.register
class Profession(GenericModel, models.Model):
    class Meta:
        ordering = ("name",)

    name = models.CharField(max_length=255, blank=True)
    oldids = models.TextField(null=True)
    oldnames = models.TextField(null=True)

    def __str__(self):
        return self.name or f"No name ({self.id})"


@reversion.register(follow=["rootobject_ptr"])
class Event(LegacyStuffMixin, LegacyDateMixin, AbstractEntity):
    kind = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, verbose_name="Name", blank=True)

    def __str__(self):
        return self.name

@reversion.register(follow=["rootobject_ptr"])
class Institution(LegacyStuffMixin, LegacyDateMixin, AbstractEntity):
    kind = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, verbose_name="Name", blank=True)

    def __str__(self):
        return self.name

@reversion.register(follow=["rootobject_ptr"])
class Person(LegacyStuffMixin, LegacyDateMixin, AbstractEntity):
    GENDER_CHOICES = (
        ("female", "female"),
        ("male", "male"),
        ("third gender", "third gender"),
    )
    surname = models.CharField(max_length=255, verbose_name="Name", blank=True)
    first_name = models.CharField(max_length=255, help_text="The persons´s forename. In case of more then one name...", blank=True, null=True)
    profession = models.ManyToManyField(Profession, blank=True)
    professioncategory = models.ForeignKey(ProfessionCategory, on_delete=models.CASCADE, null=True)
    title = models.ManyToManyField(Title, blank=True)
    gender = models.CharField(max_length=15, choices=GENDER_CHOICES, blank=True, null=True)

    @property
    def oebl_kurzinfo(self):
        if self.texts.filter(kind="ÖBL Kurzinfo").exists():
            return self.texts.get(kind="ÖBL Kurzinfo")
        return None

    @property
    def oebl_haupttext(self):
        if self.texts.filter(kind="ÖBL Haupttext").exists():
            return self.texts.get(kind="ÖBL Haupttext")
        return None

    def __str__(self):
        return f"{self.first_name} {self.surname}"


@reversion.register(follow=["rootobject_ptr"])
class Place(LegacyStuffMixin, LegacyDateMixin, AbstractEntity):
    kind = models.CharField(max_length=255, blank=True, null=True)
    label = models.CharField(max_length=255, verbose_name="Name", blank=True)
    latitude = models.FloatField(blank=True, null=True, verbose_name="latitude")
    longitude = models.FloatField(blank=True, null=True, verbose_name="longitude")

    def __str__(self):
        return self.label

@reversion.register(follow=["rootobject_ptr"])
class Work(LegacyStuffMixin, LegacyDateMixin, AbstractEntity):
    kind = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, verbose_name="Name", blank=True)

    def __str__(self):
        return self.name

@reversion.register
class Text(GenericModel, models.Model):
    TEXTTYPE_CHOICES = [
            (1, "Place description ÖBL"),
            (2, "ÖBL Haupttext"),
            (3, "ÖBL Kurzinfo"),
            (4, "Place review comments"),
            (5, "Commentary Staribacher"),
            (6, "Online Edition Haupttext"),
            (7, "Nachrecherche"),
            (8, "Soziale Herkunft"),
            (9, "Verwandtschaft"),
            (10, "Ausbildung / Studium / Studienreisen und diesbezügliche Ortsangaben"),
            (11, "Berufstätigkeit / Lebensstationen und geographische Lebensmittelpunkte"),
            (12, "Mitgliedschaften, Orden, Auszeichnungen und diesbezügliche Ortsangaben"),
            (13, "Literatur"),
            (14, "Beruf(e)"),
            (15, "Sterbedatum"),
            (16, "Adelsprädikat"),
            (17, "Übersiedlung, Emigration, Remigration"),
            (18, "Weitere Namensformen"),
            (19, "Geburtsdatum"),
            (20, "Sterbeort"),
            (21, "Geburtsort"),
            (22, "Religion(en)"),
            (23, "Name"),
            (24, "Übersiedlungen, Emigration, Remigration"),
            (25, "Pseudonyme"),
            (26, "Soziale Herkunft"),
            (27, "ÖBL Werkverzeichnis"),
    ]

    text = models.TextField(blank=True)
    kind = models.CharField(max_length=255, blank=True, null=True, choices=TEXTTYPE_CHOICES)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
