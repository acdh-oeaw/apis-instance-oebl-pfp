from django.test import TestCase

from apis_core.apis_metainfo.models import Uri
from apis_ontology.importers import OEBLBaseEntityImporter as imp
from apis_ontology.models import (
    Event,
    FandStattIn,
    GelegenIn,
    Institution,
    Person,
    Place,
    StarbIn,
    WurdeGeborenIn,
)


class RDFImportTestCase(TestCase):
    """Test cases for RDF import functionality."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_person_from_gnd_import(self):
        """Test importing a person from GND RDF."""
        uri = "https://d-nb.info/gnd/118566512"
        pers = imp(uri, Person).create_instance()
        self.assertEqual(pers.start, "1911-01-22")
        self.assertEqual(pers.end, "1990-07-29")
        self.assertEqual(pers.forename, "Bruno")
        self.assertEqual(pers.surname, "Kreisky")
        self.assertQuerySetEqual(
            WurdeGeborenIn.objects.filter(subj_object_id=pers.id),
            ["Wien"],
            transform=lambda x: x.obj.label,
        )
        self.assertQuerySetEqual(
            StarbIn.objects.filter(subj_object_id=pers.id),
            ["Wien"],
            transform=lambda x: x.obj.label,
        )
        self.assertQuerySetEqual(
            pers.profession.all(),
            ["Jurist", "Politiker"],
            transform=lambda x: x.name,
        )

    def test_person_from_wikidata_import(self):
        """Test importing a person from Wikidata RDF."""
        uri = "https://www.wikidata.org/wiki/Q44517"
        pers = imp(uri, Person).create_instance()
        self.assertEqual(pers.start, "1911-01-22")
        self.assertEqual(pers.end, "1990-07-29")
        self.assertEqual(pers.forename, "Bruno")
        self.assertEqual(pers.surname, "Kreisky")
        self.assertQuerySetEqual(
            WurdeGeborenIn.objects.filter(subj_object_id=pers.id),
            ["Wien"],
            transform=lambda x: x.obj.label,
        )
        self.assertQuerySetEqual(
            StarbIn.objects.filter(subj_object_id=pers.id),
            ["Wien"],
            transform=lambda x: x.obj.label,
        )
        self.assertQuerySetEqual(
            pers.profession.all(),
            ["Diplomat", "Kriegsreporter", "Politiker"],
            transform=lambda x: x.name,
        )

    def test_place_from_gnd_import(self):
        """Test importing a place from GND RDF."""
        uri = "https://d-nb.info/gnd/4066009-6"
        place = imp(uri, Place).create_instance()
        self.assertEqual(place.label, "Wien")
        self.assertEqual(place.longitude, 16.37169)
        self.assertEqual(place.latitude, 48.208199)
        self.assertQuerySetEqual(
            Uri.objects.filter(object_id=place.id)
            .exclude(uri__contains="oeaw.ac.at")
            .order_by("uri"),
            [
                "http://viaf.org/viaf/238999862",
                "http://www.wikidata.org/entity/Q1741",
                "https://d-nb.info/gnd/1012345-3",
                "https://sws.geonames.org/2761367/",
            ],
            transform=lambda x: x.uri,
        )

    def test_place_from_wikidata_import(self):
        """Test importing a place from Wikidata RDF."""
        uri = "https://www.wikidata.org/wiki/Q1741"
        place = imp(uri, Place).create_instance()
        self.assertEqual(place.label, "Wien")
        self.assertEqual(place.longitude, 16.3725)
        self.assertEqual(place.latitude, 48.208333333333)
        self.assertQuerySetEqual(
            Uri.objects.filter(object_id=place.id)
            .exclude(uri__contains="oeaw.ac.at")
            .order_by("uri"),
            [
                "http://id.loc.gov/authorities/names/n79018895",
                "http://viaf.org/viaf/155870729",
                "http://viaf.org/viaf/238999862",
                "http://viaf.org/viaf/45145424500086831364",
                "https://d-nb.info/gnd/4066009-6",
                "https://sws.geonames.org/2761369/",
            ],
            transform=lambda x: x.uri,
        )

    def test_place_from_geonames_import(self):
        """Test importing a place from GeoNames RDF."""
        uri = "https://sws.geonames.org/2761369/about.rdf"
        place = imp(uri, Place).create_instance()
        self.assertEqual(place.label, "Wien")
        self.assertEqual(place.longitude, 16.37208)
        self.assertEqual(place.latitude, 48.20849)
        self.assertQuerySetEqual(
            Uri.objects.filter(object_id=place.id)
            .exclude(uri__contains="oeaw.ac.at")
            .order_by("uri"),
            [
                "https://dbpedia.org/resource/Vienna",
                "https://en.wikipedia.org/wiki/Vienna",
                "https://ru.wikipedia.org/wiki/%D0%92%D0%B5%D0%BD%D0%B0",
            ],
            transform=lambda x: x.uri,
        )

    def test_institution_from_gnd(self):
        """Test import of institution from GND RDF."""
        uri = "https://d-nb.info/gnd/1001454-8"
        inst = imp(uri, Institution).create_instance()
        self.assertEqual(inst.name, "Österreichische Akademie der Wissenschaften")
        self.assertEqual(inst.start, "1947")
        self.assertQuerySetEqual(
            GelegenIn.objects.filter(subj_object_id=inst.id).order_by("id"),
            [
                "Wien",
            ],
            transform=lambda x: x.obj.label,
        )
        self.assertQuerySetEqual(
            Uri.objects.filter(object_id=inst.id)
            .exclude(uri__contains="oeaw.ac.at")
            .order_by("uri"),
            [
                "http://viaf.org/viaf/141312644",
                "http://www.wikidata.org/entity/Q299015",
                "https://d-nb.info/gnd/108595336X",
                "https://d-nb.info/gnd/1090414722",
                "https://d-nb.info/gnd/4079277-8",
            ],
            transform=lambda x: x.uri,
        )

    def test_institution_from_wikidata(self):
        """Test import of institution from Wikidata RDF."""
        uri = "https://www.wikidata.org/wiki/Q299015"
        inst = imp(uri, Institution).create_instance()
        self.assertEqual(inst.name, "Österreichische Akademie der Wissenschaften")
        self.assertEqual(inst.start, "1847-05-14")
        #        self.assertQuerySetEqual(  TODO: add again when relation gets added to toml def
        #            GelegenIn.objects.filter(subj_object_id=inst.id).order_by("id"),
        #            [
        #                "Wien",
        #            ],
        #            transform=lambda x: x.obj.label,
        #        )
        self.assertQuerySetEqual(
            Uri.objects.filter(object_id=inst.id)
            .exclude(uri__contains="oeaw.ac.at")
            .order_by("uri"),
            [
                "http://viaf.org/viaf/141312644",
                "http://www.wikidata.org/entity/Q299015",
                "https://d-nb.info/gnd/108595336X",
                "https://d-nb.info/gnd/1090414722",
                "https://d-nb.info/gnd/4079277-8",
            ],
            transform=lambda x: x.uri,
        )

    def test_event_from_gnd(self):
        """Test import of event from GND"""
        uri = "https://d-nb.info/gnd/1186415460"
        ev = imp(uri, Event).create_instance()
        self.assertEqual(ev.name, "Novara-Expedition (1857-1859)")
        self.assertEqual(ev.start, "1857-1859")

    def test_event_from_gnd_with_place(self):
        """Test import of event from GND"""
        uri = "https://d-nb.info/gnd/2104874-5"
        ev = imp(uri, Event).create_instance()
        self.assertEqual(ev.name, "Weltausstellung (1873 : Wien)")
        self.assertEqual(ev.start, "1873")
        self.assertQuerySetEqual(
            FandStattIn.objects.filter(subj_object_id=ev.id).order_by("id"),
            [
                "Wien",
            ],
            transform=lambda x: x.obj.label,
        )
