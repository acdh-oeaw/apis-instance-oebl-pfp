import reversion
from django.db import models
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


# we are overriding the LegacyDateMixin save method for now
# because the DateParser returns datetime instead of date
# and the API does not like that
class FixLegacyDateMixin:
    def save(self, *args, **kwargs):
        start = None
        start_start = None
        start_end = None
        end = None
        end_start = None
        end_end = None

        if self.start_date_written:
            start, start_start, start_end = DateParser.parse_date(
                self.start_date_written
            )
            if start:
                start = start.date()
            if start_start:
                start_start = start_start.date()
            if start_end:
                start_end = start_end.date()

        if self.end_date_written:
            end, end_start, end_end = DateParser.parse_date(self.end_date_written)
            if end:
                end = end.date()
            if end_start:
                end_start = end_start.date()
            if end_end:
                end_end = end_end.date()

        self.start_date = start
        self.start_start_date = start_start
        self.start_end_date = start_end
        self.end_date = end
        self.end_start_date = end_start
        self.end_end_date = end_end

        super().save(*args, **kwargs)

class Title(models.Model):
    name = models.CharField(max_length=255, blank=True)


@reversion.register(follow=["rootobject_ptr"])
class Event(LegacyStuffMixin, LegacyDateMixin, FixLegacyDateMixin, AbstractEntity):
    kind = models.CharField(max_length=255, blank=True)


@reversion.register(follow=["rootobject_ptr"])
class Institution(LegacyStuffMixin, LegacyDateMixin, FixLegacyDateMixin, AbstractEntity):
    kind = models.CharField(max_length=255, blank=True)


@reversion.register(follow=["rootobject_ptr"])
class Person(LegacyStuffMixin, LegacyDateMixin, FixLegacyDateMixin, AbstractEntity):
    GENDER_CHOICES = (
        ("female", "female"),
        ("male", "male"),
        ("third gender", "third gender"),
    )
    first_name = models.CharField(max_length=255, help_text="The persons´s forename. In case of more then one name...", blank=True, null=True)
    profession = models.CharField(max_length=255, blank=True)
    title = models.ManyToManyField(Title, blank=True)
    gender = models.CharField(max_length=15, choices=GENDER_CHOICES, blank=True, null=True)


@reversion.register(follow=["rootobject_ptr"])
class Place(LegacyStuffMixin, LegacyDateMixin, FixLegacyDateMixin, AbstractEntity):
    kind = models.CharField(max_length=255, blank=True)
    lat = models.FloatField(blank=True, null=True, verbose_name="latitude")
    lng = models.FloatField(blank=True, null=True, verbose_name="longitude")


@reversion.register(follow=["rootobject_ptr"])
class Work(LegacyStuffMixin, LegacyDateMixin, FixLegacyDateMixin, AbstractEntity):
    kind = models.CharField(max_length=255, blank=True)
