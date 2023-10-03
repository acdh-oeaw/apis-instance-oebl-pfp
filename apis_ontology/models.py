import reversion
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from apis_core.apis_entities.models import AbstractEntity
from apis_core.core.models import LegacyDateMixin
from apis_core.utils import DateParser


class LegacyStuffMixin(models.Model):
    review = review = models.BooleanField(default=False, help_text="Should be set to True, if the data record holds up quality standards.")
    status = models.CharField(max_length=100, blank=True)
    references = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    published = models.BooleanField(default=False)

    class Meta:
        abstract = True


@reversion.register
class Source(models.Model):
    orig_filename = models.CharField(max_length=255, blank=True)
    indexed = models.BooleanField(default=False)
    pubinfo = models.CharField(max_length=400, blank=True)
    author = models.CharField(max_length=255, blank=True)
    orig_id = models.PositiveIntegerField(blank=True, null=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, blank=True)
    object_id = models.PositiveIntegerField(blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        if self.author and self.orig_filename:
            return f"{self.orig_filename}, stored by {self.author}"
        return f"(ID: {self.id})".format(self.id)


@reversion.register
class Title(models.Model):
    name = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name


@reversion.register
class Profession(models.Model):
    name = models.CharField(max_length=255, blank=True)
    parent = models.ForeignKey('self', blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


@reversion.register(follow=["rootobject_ptr"])
class Event(LegacyStuffMixin, LegacyDateMixin, AbstractEntity):
    kind = models.CharField(max_length=255, blank=True, null=True)


@reversion.register(follow=["rootobject_ptr"])
class Institution(LegacyStuffMixin, LegacyDateMixin, AbstractEntity):
    kind = models.CharField(max_length=255, blank=True, null=True)


@reversion.register(follow=["rootobject_ptr"])
class Person(LegacyStuffMixin, LegacyDateMixin, AbstractEntity):
    GENDER_CHOICES = (
        ("female", "female"),
        ("male", "male"),
        ("third gender", "third gender"),
    )
    first_name = models.CharField(max_length=255, help_text="The persons´s forename. In case of more then one name...", blank=True, null=True)
    profession = models.ManyToManyField(Profession, blank=True)
    title = models.ManyToManyField(Title, blank=True)
    gender = models.CharField(max_length=15, choices=GENDER_CHOICES, blank=True, null=True)


@reversion.register(follow=["rootobject_ptr"])
class Place(LegacyStuffMixin, LegacyDateMixin, AbstractEntity):
    kind = models.CharField(max_length=255, blank=True, null=True)
    lat = models.FloatField(blank=True, null=True, verbose_name="latitude")
    lng = models.FloatField(blank=True, null=True, verbose_name="longitude")


@reversion.register(follow=["rootobject_ptr"])
class Work(LegacyStuffMixin, LegacyDateMixin, AbstractEntity):
    kind = models.CharField(max_length=255, blank=True, null=True)
