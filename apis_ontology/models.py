from apis_core.relations.models import Relation
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apis_core.apis_entities.models import AbstractEntity
from apis_core.core.models import LegacyDateMixin
from apis_core.utils.helpers import create_object_from_uri
from apis_core.generic.abc import GenericModel
from apis_core.apis_entities.abc import E53_Place
from apis_core.history.models import VersionMixin
from apis_core.utils.fields import NewlineSeparatedListField

from auditlog.registry import auditlog


class OEBLBaseEntity:
    pass


class LegacyStuffMixin(models.Model):
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


class Source(GenericModel, models.Model):
    orig_filename = models.CharField(max_length=255, blank=True)
    indexed = models.BooleanField(default=False)
    pubinfo = models.CharField(max_length=400, blank=True)
    author = models.CharField(max_length=255, blank=True)
    orig_id = models.PositiveIntegerField(blank=True, null=True)
    pdf_filename = models.CharField(blank=True)

    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, blank=True, null=True
    )
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey("content_type", "object_id")

    def __str__(self):
        if retstr := self.orig_filename:
            if self.author:
                retstr += f" stored by {self.author}"
            return retstr
        return f"(ID: {self.id})".format(self.id)


class Title(GenericModel, models.Model):
    name = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Title")
        verbose_name_plural = _("Titles")


class ProfessionCategory(GenericModel, models.Model):
    name = models.CharField(max_length=255, blank=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Profession Category")
        verbose_name_plural = _("Profession Categories")


class Profession(GenericModel, models.Model):
    _default_search_fields = ["name"]

    class Meta:
        ordering = ("name",)
        verbose_name = _("Profession")
        verbose_name_plural = _("Professions")

    name = models.CharField(max_length=255, blank=True)
    oldids = models.TextField(null=True)
    oldnames = models.TextField(null=True)

    def __str__(self):
        return self.name or f"No name ({self.id})"


class Parentprofession(GenericModel, models.Model):
    label = models.CharField()


class Event(
    LegacyStuffMixin, VersionMixin, LegacyDateMixin, AbstractEntity, OEBLBaseEntity
):
    kind = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, verbose_name="Name", blank=True)
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))

    _default_search_fields = ["name", "notes", "kind"]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Event")
        verbose_name_plural = _("Events")


class Institution(
    VersionMixin, LegacyStuffMixin, LegacyDateMixin, AbstractEntity, OEBLBaseEntity
):
    kind = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, verbose_name="Name", blank=True)
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Institution")
        verbose_name_plural = _("Institutions")


class Person(
    VersionMixin, LegacyStuffMixin, LegacyDateMixin, AbstractEntity, OEBLBaseEntity
):
    GENDER_CHOICES = (
        ("female", "female"),
        ("male", "male"),
        ("third gender", "third gender"),
    )
    surname = models.CharField(max_length=255, verbose_name="Name", blank=True)
    forename = models.CharField(
        max_length=255,
        help_text="The persons´s forename. In case of more then one name...",
        blank=True,
        null=True,
    )
    profession = models.ManyToManyField(Profession, blank=True)
    professioncategory = models.ForeignKey(
        ProfessionCategory, on_delete=models.CASCADE, null=True, blank=True
    )
    profession_father = models.ManyToManyField(
        Parentprofession, blank=True, related_name="father_person_set"
    )
    profession_mother = models.ManyToManyField(
        Parentprofession, blank=True, related_name="mother_person_set"
    )
    title = models.ManyToManyField(Title, blank=True)
    gender = models.CharField(
        max_length=15, choices=GENDER_CHOICES, blank=True, null=True
    )
    external_resources = models.CharField(
        verbose_name="Externe Verweise", blank=True, null=True
    )
    references = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))
    alternative_names = NewlineSeparatedListField(
        blank=True, verbose_name=_("Alternative Names")
    )

    # texts
    # "ÖBL Haupttext"
    oebl_haupttext = models.TextField(blank=True, verbose_name="ÖBL Haupttext")
    # "ÖBL Kurzinfo"
    oebl_kurzinfo = models.TextField(blank=True, verbose_name="ÖBL Kurzinfo")
    # "Online Edition Haupttext"
    online_edition_haupttext = models.TextField(
        blank=True, verbose_name="Online Edition Haupttext"
    )
    # "Nachrecherche"
    nachrecherche = models.TextField(blank=True)
    # "Soziale Herkunft"
    soziale_herkunft = models.TextField(blank=True, verbose_name="Soziale Herkunft")
    # "Verwandtschaft"
    verwandtschaft = models.TextField(blank=True)
    # "Ausbildung / Studium / Studienreisen und diesbezügliche Ortsangaben"
    ausbildung_studium_studienreise = models.TextField(
        blank=True,
        verbose_name="Ausbildung / Studium / Studienreisen und diesbezügliche Ortsangaben",
    )
    # "Berufstätigkeit / Lebensstationen und geographische Lebensmittelpunkte"
    berufstaetigkeit_lebenstationen = models.TextField(
        blank=True,
        verbose_name="Berufstätigkeit / Lebensstationen und geographische Lebensmittelpunkte",
    )
    # "Mitgliedschaften, Orden, Auszeichnungen und diesbezügliche Ortsangaben"
    mitgliedschaften_orden_auszeichnungen = models.TextField(
        blank=True,
        verbose_name="Mitgliedschaften, Orden, Auszeichnungen und diesbezügliche Ortsangaben",
    )
    # "Literatur"
    literatur = models.TextField(blank=True)
    # "Beruf(e)"
    berufe = models.TextField(blank=True, verbose_name="Beruf(e)")
    # "Sterbedatum"
    sterbedatum = models.TextField(blank=True)
    # "Adelsprädikat"
    adelspraedikat = models.TextField(blank=True, verbose_name="Adelsprädikat")
    # "Übersiedlung, Emigration, Remigration"
    uebersiedlung_emigration = models.TextField(
        blank=True, verbose_name="Übersiedlung, Emigration, Remigration"
    )
    # "Weitere Namensformen"
    weitere_namensformen = models.TextField(
        blank=True, verbose_name="Weitere Namensformen"
    )
    # "Geburtsdatum"
    geburtsdatum = models.TextField(blank=True)
    # "Sterbeort"
    sterbeort = models.TextField(blank=True)
    # "Geburtsort"
    geburtsort = models.TextField(blank=True)
    # "Religion(en)"
    religionen = models.TextField(blank=True, verbose_name="Religion(en)")
    # "Name"
    name_text = models.TextField(blank=True, verbose_name="Name")
    # "Pseudonyme"
    pseudonyme = models.TextField(blank=True)
    # "ÖBL Werkverzeichnis"
    oebl_werkverzeichnis = models.TextField(
        blank=True, verbose_name="ÖBL Werkverzeichnis"
    )

    def __str__(self):
        return f"{self.forename} {self.surname}"

    @property
    def biographien_urls(self):
        base = "https://www.biographien.ac.at/oebl/oebl_"
        links = [
            f"{base}{source.orig_filename[0]}/{source.orig_filename}"
            for source in self.sources.all()
            if source.orig_filename.endswith(".xml")
        ]
        return links

    class Meta:
        verbose_name = _("Person")
        verbose_name_plural = _("Persons")


class Place(
    E53_Place,
    VersionMixin,
    LegacyStuffMixin,
    LegacyDateMixin,
    AbstractEntity,
    OEBLBaseEntity,
):
    kind = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))

    def __str__(self):
        return self.label

    class Meta:
        verbose_name = _("Place")
        verbose_name_plural = _("Places")


class Work(
    LegacyStuffMixin, VersionMixin, LegacyDateMixin, AbstractEntity, OEBLBaseEntity
):
    kind = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, verbose_name="Name", blank=True)
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))

    _default_search_fields = ["name", "notes", "kind"]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Work")
        verbose_name_plural = _("Works")


class Denomination(AbstractEntity):
    name = models.CharField()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Denomination")
        verbose_name_plural = _("Denominations")


auditlog.register(Source, serialize_data=True)
auditlog.register(Title, serialize_data=True)
auditlog.register(ProfessionCategory, serialize_data=True)
auditlog.register(Profession, serialize_data=True)
auditlog.register(Parentprofession, serialize_data=True)
auditlog.register(Event, serialize_data=True)
auditlog.register(Institution, serialize_data=True)
auditlog.register(
    Person,
    serialize_data=True,
    m2m_fields={"profession", "title", "profession_mother", "profession_mother"},
)
auditlog.register(Place, serialize_data=True)
auditlog.register(Work, serialize_data=True)
auditlog.register(Denomination, serialize_data=True)


class TempTripleGenericAttributes(models.Model):
    """
    This class is used to store legacy attributes from the old triple model.
    It is used to store the attributes that are not part of the new relations model.
    """

    class Meta:
        abstract = True

    review = models.BooleanField(
        default=False,
        help_text="Should be set to True, if the data record holds up quality standards.",
        editable=False,
    )
    status = models.CharField(max_length=100, blank=True, null=True, editable=False)
    references = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)


class TempTripleLegacyAttributes(models.Model):
    """
    Adds common attributes of the legact relation classes
    """

    class Meta:
        abstract = True

    legacy_relation_vocab_label = models.CharField(
        max_length=255, blank=True, null=True
    )
    legacy_relation_vocab_label_reverse = models.CharField(
        max_length=255, blank=True, null=True
    )

    def name(self) -> str:
        return self.legacy_relation_vocab_label

    def reverse_name(self) -> str:
        return self.legacy_relation_vocab_label_reverse


################################################
# auto generated relation classes from properties
################################################


class HatReligionszugehoerigkeit(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 164936"""

    _legacy_property_id = 164936

    subj_model = Person
    obj_model = Denomination

    @classmethod
    def name(self) -> str:
        return "hat Religionszugehörigkeit"

    @classmethod
    def reverse_name(self) -> str:
        return "hat Mitglieder"


class PersonEventLegacyRelation(
    Relation,
    VersionMixin,
    TempTripleGenericAttributes,
    TempTripleLegacyAttributes,
    LegacyDateMixin,
):
    """automatically generated class"""

    subj_model = Person
    obj_model = Event

    @classmethod
    def name(self) -> str:
        return "PersonEvent"

    @classmethod
    def reverse_name(self) -> str:
        return "PersonEvent reverse"


class PersonInstitutionLegacyRelation(
    Relation,
    VersionMixin,
    TempTripleGenericAttributes,
    TempTripleLegacyAttributes,
    LegacyDateMixin,
):
    """automatically generated class"""

    subj_model = Person
    obj_model = Institution

    @classmethod
    def name(self) -> str:
        return "PersonInstitution"

    @classmethod
    def reverse_name(self) -> str:
        return "PersonInstitution reverse"


class PersonPersonLegacyRelation(
    Relation,
    VersionMixin,
    TempTripleGenericAttributes,
    TempTripleLegacyAttributes,
    LegacyDateMixin,
):
    """automatically generated class"""

    subj_model = Person
    obj_model = Person

    @classmethod
    def name(self) -> str:
        return "PersonPerson"

    @classmethod
    def reverse_name(self) -> str:
        return "PersonPerson reverse"


class InstitutionInstitutionLegacyRelation(
    Relation,
    VersionMixin,
    TempTripleGenericAttributes,
    TempTripleLegacyAttributes,
    LegacyDateMixin,
):
    """automatically generated class"""

    subj_model = Institution
    obj_model = Institution

    @classmethod
    def name(self) -> str:
        return "InstitutionInstitution"

    @classmethod
    def reverse_name(self) -> str:
        return "InstitutionInstitution reverse"


class PersonPlaceLegacyRelation(
    Relation,
    VersionMixin,
    TempTripleGenericAttributes,
    TempTripleLegacyAttributes,
    LegacyDateMixin,
):
    """automatically generated class"""

    subj_model = Person
    obj_model = Place

    @classmethod
    def name(self) -> str:
        return "PersonPlace"

    @classmethod
    def reverse_name(self) -> str:
        return "PersonPlace reverse"


class PersonWorkLegacyRelation(
    Relation,
    VersionMixin,
    TempTripleGenericAttributes,
    TempTripleLegacyAttributes,
    LegacyDateMixin,
):
    """automatically generated class"""

    subj_model = Person
    obj_model = Work

    @classmethod
    def name(self) -> str:
        return "PersonWork"

    @classmethod
    def reverse_name(self) -> str:
        return "PersonWork reverse"


class PlacePlaceLegacyRelation(
    Relation,
    VersionMixin,
    TempTripleGenericAttributes,
    TempTripleLegacyAttributes,
    LegacyDateMixin,
):
    """automatically generated class"""

    subj_model = Place
    obj_model = Place

    @classmethod
    def name(self) -> str:
        return "PlacePlace"

    @classmethod
    def reverse_name(self) -> str:
        return "PlacePlace reverse"


class WarGeschwisterVon(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 167024"""

    _legacy_property_id = 167024

    subj_model = Person
    obj_model = Person

    @classmethod
    def name(self) -> str:
        return "war Geschwister von [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "war Geschwister von [PIO]"


class WarSchwagerschwaegerinVon(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 167025"""

    _legacy_property_id = 167025

    subj_model = Person
    obj_model = Person

    @classmethod
    def name(self) -> str:
        return "war Schwager/Schwägerin von [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "war Schwager/Schwägerin von [PIO]"


class WarSchwiegersohnschwiegertochterVon(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 167026"""

    _legacy_property_id = 167026

    subj_model = Person
    obj_model = Person

    @classmethod
    def name(self) -> str:
        return "war Schwiegersohn/Schwiegertochter von [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "war Schwiegervater/Schwiegermutter von [PIO]"


class WarVerwandtMit(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 167027"""

    _legacy_property_id = 167027

    subj_model = Person
    obj_model = Person

    @classmethod
    def name(self) -> str:
        return "war verwandt mit [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "war verwandt mit [PIO]"


class HatteAlsTrauzeugenzeugin(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 167029"""

    _legacy_property_id = 167029

    subj_model = Person
    obj_model = Person

    @classmethod
    def name(self) -> str:
        return "hatte als Trauzeugen/-zeugin [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "war Trauzeuge/-zeugin von [PIO]"


class WarPatenkindVon(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 167031"""

    _legacy_property_id = 167031

    subj_model = Person
    obj_model = Person

    @classmethod
    def name(self) -> str:
        return "war Patenkind von [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "war Taufpate/-patin von [PIO]"


class DissertierteBeiunter(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 167032"""

    _legacy_property_id = 167032

    subj_model = Person
    obj_model = Person

    @classmethod
    def name(self) -> str:
        return "dissertierte bei/unter [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "war Doktorvater von [PIO]"


class WurdeGeborenIn(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 167036"""

    _legacy_property_id = 167036

    subj_model = Person
    obj_model = Place

    @classmethod
    def name(self) -> str:
        return "wurde geboren in [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "war Geburtsort von [PIO]"


class StarbIn(Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin):
    """automatically generated class from property with id 167037"""

    _legacy_property_id = 167037

    subj_model = Person
    obj_model = Place

    @classmethod
    def name(self) -> str:
        return "starb in [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "war Sterbeort von [PIO]"


class ErhieltAusbildungIn(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 167038"""

    _legacy_property_id = 167038

    subj_model = Person
    obj_model = Place

    @classmethod
    def name(self) -> str:
        return "erhielt Ausbildung in [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "war Ausbildungsort von [PIO]"


class WirkteforschtehieltSichAufIn(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 167039"""

    _legacy_property_id = 167039

    subj_model = Person
    obj_model = Place

    @classmethod
    def name(self) -> str:
        return "wirkte/forschte/hielt sich auf in [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "war Wirkungs-/Aufenthaltsort von [PIO]"


class StudiertelernteAn(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 167041"""

    _legacy_property_id = 167041

    subj_model = Person
    obj_model = Institution

    @classmethod
    def name(self) -> str:
        return "studierte/lernte an [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "war Studien-/Ausbildungseinrichtung für [PIO]"


class HabilitierteSichAn(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 167042"""

    _legacy_property_id = 167042

    subj_model = Person
    obj_model = Institution

    @classmethod
    def name(self) -> str:
        return "habilitierte sich an [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "hatte als Habilitant:in [PIO]"


class WarAssistentinAn(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 167043"""

    _legacy_property_id = 167043

    subj_model = Person
    obj_model = Institution

    @classmethod
    def name(self) -> str:
        return "war Assistent:in an [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "hatte als Assistent:in [PIO]"


class WarPrivatdozentinAn(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 167044"""

    _legacy_property_id = 167044

    subj_model = Person
    obj_model = Institution

    @classmethod
    def name(self) -> str:
        return "war Privatdozent:in an [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "hatte als Privatdozent:in [PIO]"


class WarOTitoProfessorinAn(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 167045"""

    _legacy_property_id = 167045

    subj_model = Person
    obj_model = Institution

    @classmethod
    def name(self) -> str:
        return "war o. / tit.o. Professor:in an [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "hatte als o. / tit.o. Professor:in [PIO]"


class WarAoTitaoProfessorinAn(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 167046"""

    _legacy_property_id = 167046

    subj_model = Person
    obj_model = Institution

    @classmethod
    def name(self) -> str:
        return "war ao./ tit.ao. Professor:in an [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "hatte als ao./ tit.ao. Professor:in [PIO]"


class WarHonorarprofessorinAn(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 167048"""

    _legacy_property_id = 167048

    subj_model = Person
    obj_model = Institution

    @classmethod
    def name(self) -> str:
        return "war Honorarprofessor:in an [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "hatte als Honorarprofessor:in [PIO]"


class WarEhrendoktorinAn(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 167049"""

    _legacy_property_id = 167049

    subj_model = Person
    obj_model = Institution

    @classmethod
    def name(self) -> str:
        return "war Ehrendoktor:in an [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "vergab Ehrendoktorat an [PIO]"


class WarTaetigFuerwirkteAnbei(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 167050"""

    _legacy_property_id = 167050

    subj_model = Person
    obj_model = Institution

    @classmethod
    def name(self) -> str:
        return "war tätig für/wirkte an/bei [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "war Tätigkeits-/Wirkungseinrichtung von [PIO]"


class WarMitgruenderinVon(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 167051"""

    _legacy_property_id = 167051

    subj_model = Person
    obj_model = Institution

    @classmethod
    def name(self) -> str:
        return "war (Mit-)Gründer:in von [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "wurde (mit-)begründet durch [PIO]"


class HatteLeitungsfunktionAn(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 167053"""

    _legacy_property_id = 167053

    subj_model = Person
    obj_model = Institution

    @classmethod
    def name(self) -> str:
        return "hatte Leitungsfunktion an [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "hatte als leitenden/leitende Mitarbeiter:in [PIO]"


class WarMitgliedVon(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 167052"""

    _legacy_property_id = 167052

    subj_model = Person
    obj_model = Institution

    @classmethod
    def name(self) -> str:
        return "war Mitglied von [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "zählte zu ihren Mitgliedern [PIO]"


class WarGrossvatermutterVon(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 167183"""

    _legacy_property_id = 167183

    subj_model = Person
    obj_model = Person

    @classmethod
    def name(self) -> str:
        return "war Großvater/-mutter von [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "war Enkel:in von [PIO]"


class WarRektorinAn(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 167196"""

    _legacy_property_id = 167196

    subj_model = Person
    obj_model = Institution

    @classmethod
    def name(self) -> str:
        return "war Rektor:in an [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "hatte als Rektor:in [PIO]"


class WarDekaninAn(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 167195"""

    _legacy_property_id = 167195

    subj_model = Person
    obj_model = Institution

    @classmethod
    def name(self) -> str:
        return "war Dekan:in an [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "hatte als Dekan:in [PIO}"


class PromovierteAn(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 167184"""

    _legacy_property_id = 167184

    subj_model = Person
    obj_model = Institution

    @classmethod
    def name(self) -> str:
        return "promovierte an [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "verlieh Doktorat an [PIO]"


class KaempfteInbei(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 167405"""

    _legacy_property_id = 167405

    subj_model = Person
    obj_model = Place

    @classmethod
    def name(self) -> str:
        return "kämpfte in/bei [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "war Kampfschauplatz für [PIO]"


class WarProfessorinAn(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 167419"""

    _legacy_property_id = 167419

    subj_model = Person
    obj_model = Institution

    @classmethod
    def name(self) -> str:
        return "war Professor:in an [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "hatte als Professor:in [PIO]"


class GraduierteAn(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 167799"""

    _legacy_property_id = 167799

    subj_model = Person
    obj_model = Institution

    @classmethod
    def name(self) -> str:
        return "graduierte an [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "war absolvierte Studien- bzw. Ausbildungseinrichtung von [PIO]"


class MitbiographiertUnter(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 168104"""

    _legacy_property_id = 168104

    subj_model = Person
    obj_model = Person

    @classmethod
    def name(self) -> str:
        return "mitbiographiert unter [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "hat als Subbiographie [PIO]"


class WarHonorardozentinAn(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 168310"""

    _legacy_property_id = 168310

    subj_model = Person
    obj_model = Institution

    @classmethod
    def name(self) -> str:
        return "war Honorardozent:in an [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "hatte als Honorardozent:in [PIO]"


class HatteLeitungsfunktionBei(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 168434"""

    _legacy_property_id = 168434

    subj_model = Person
    obj_model = Event

    @classmethod
    def name(self) -> str:
        return "hatte Leitungsfunktion bei [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "wurde geleitet von [PIO]"


class NahmTeilAn(Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin):
    """automatically generated class from property with id 168435"""

    _legacy_property_id = 168435

    subj_model = Person
    obj_model = Event

    @classmethod
    def name(self) -> str:
        return "nahm teil an [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "hatte als Teilnehmer:in [PIO]"


class WarElternteilVon(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 168488"""

    _legacy_property_id = 168488

    subj_model = Person
    obj_model = Person

    @classmethod
    def name(self) -> str:
        return "war Elternteil von [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "war Kind von [PIO]"


class WarSchuelerinVon(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 168489"""

    _legacy_property_id = 168489

    subj_model = Person
    obj_model = Person

    @classmethod
    def name(self) -> str:
        return "war Schüler:in von [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "war Lehrer:in von [PIO]"


class WarVerheiratetMit(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 168490"""

    _legacy_property_id = 168490

    subj_model = Person
    obj_model = Person

    @classmethod
    def name(self) -> str:
        return "war verheiratet mit [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "war verheiratet mit [PIO]"


class StandInKontaktMit(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    """automatically generated class from property with id 168491"""

    _legacy_property_id = 168491

    subj_model = Person
    obj_model = Person

    @classmethod
    def name(self) -> str:
        return "stand in Kontakt mit [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "stand in Kontakt mit [PIO]"


class ArbeiteteZusammenMit(
    Relation, VersionMixin, TempTripleGenericAttributes, LegacyDateMixin
):
    subj_model = Person
    obj_model = Person

    @classmethod
    def name(self) -> str:
        return "arbeitete zusammmen mit [PIO]"

    @classmethod
    def reverse_name(self) -> str:
        return "arbeitete zusammmen mit [PIO]"
